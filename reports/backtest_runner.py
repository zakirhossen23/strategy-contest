#!/usr/bin/env python3
"""Backtest runner for strategy templates.

Usage:
  - Demo (generate synthetic 2024-01-01 to 2024-06-30 daily prices):
      python reports/backtest_runner.py --demo

  - CSV replay (CSV with `timestamp,price`):
      python reports/backtest_runner.py --csv path/to/prices.csv

The runner loads the strategy implementation from
`ma_crossover/ma_crossover.py` and simulates
market ticks, executing trades at the current price.

Outputs a markdown report at `reports/backtest_report.md`.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import math
import os
from collections import deque
from datetime import datetime, timedelta
from statistics import mean, pstdev
from typing import List, Tuple

ROOT = os.path.dirname(os.path.dirname(__file__))
STRAT_PATH = os.path.join(ROOT, 'ma_crossover', 'ma_crossover.py')


def load_strategy_class(path: str):
    spec = importlib.util.spec_from_file_location('user_strategy', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    # Strategy class is MaCrossoverStrategy in the template
    cls = getattr(module, 'MaCrossoverStrategy', None)
    if cls is None:
        raise RuntimeError('MaCrossoverStrategy not found in ma_crossover.py')
    return cls


def generate_synthetic_prices(start: datetime, end: datetime) -> List[Tuple[datetime, float]]:
    days = (end - start).days + 1
    prices = []
    price = 30000.0
    drift = 0.0003  # small positive drift
    import random
    for i in range(days):
        # simulate daily return
        ret = drift + random.normalvariate(0, 0.02)
        price = max(0.01, price * (1 + ret))
        prices.append((start + timedelta(days=i), round(price, 2)))
    return prices


def read_csv_prices(path: str) -> List[Tuple[datetime, float]]:
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            ts = r.get('timestamp') or r.get('time') or r.get('date')
            price = float(r.get('price') or r.get('close') or r.get('value'))
            rows.append((datetime.fromisoformat(ts), price))
    rows.sort()
    return rows


def compute_sharpe(returns: List[float], periods_per_year: int = 252) -> float:
    if not returns:
        return 0.0
    mu = mean(returns)
    if len(returns) < 2:
        return 0.0
    sd = pstdev(returns)
    if sd == 0:
        return 0.0
    # Annualize
    return (mu * periods_per_year) / (sd * math.sqrt(periods_per_year))


def max_drawdown(values: List[float]) -> float:
    peak = -float('inf')
    max_dd = 0.0
    for v in values:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd * 100.0


def run_backtest(prices: List[Tuple[datetime, float]], strategy_cls, config: dict, starting_cash: float = 10000.0):
    # instantiate strategy
    strat = strategy_cls(config=config, exchange=None)

    cash = starting_cash
    qty = 0.0
    portfolio_values = []
    trade_log = []

    history = []
    pending_orders = []  # list of (exec_index, order_dict)

    # Simulation params from config
    fee_pct = float(config.get('fee_pct', 0.0))  # e.g., 0.001 = 0.1%
    slippage_pct = float(config.get('slippage_pct', 0.0))  # e.g., 0.0005 = 0.05%
    exec_delay_days = int(config.get('exec_delay_days', 1))  # execute N ticks after signal

    for idx, (ts, price) in enumerate(prices):
        history.append(price)
        # create a simple MarketSnapshot-like object
        class MS:
            def __init__(self, symbol, prices, current_price, timestamp):
                self.symbol = symbol
                self.prices = prices
                self.current_price = current_price
                self.timestamp = timestamp

            @property
            def history(self):
                return self.prices

        ms = MS('BTC-USD', list(history[-300:]), price, ts)

        # generate signals based on current market snapshot and portfolio state
        signal = strat.generate_signal(ms, type('P', (), {'cash': cash, 'quantity': qty}))

        # When a signal is generated, schedule it for execution after exec_delay_days
        if signal.action in ('buy', 'sell') and getattr(signal, 'size', None):
            exec_index = idx + exec_delay_days
            order = {
                'side': signal.action,
                'size': float(signal.size),
                'created_at': ts,
                'reason': getattr(signal, 'reason', None),
            }
            pending_orders.append((exec_index, order))

        # Process any pending orders scheduled for this index
        due = [o for (i, o) in pending_orders if i <= idx]
        pending_orders = [(i, o) for (i, o) in pending_orders if i > idx]
        for order in due:
            side = order['side']
            size = float(order['size'])
            # apply slippage to execution price
            if side == 'buy':
                exec_price = price * (1.0 + slippage_pct)
            else:
                exec_price = price * max(0.0, (1.0 - slippage_pct))

            if side == 'buy':
                # compute total cost and fee
                cost = size * exec_price
                fee = cost * fee_pct
                total_cost = cost + fee
                # if not enough cash, scale down size
                if total_cost > cash and cash > 1e-9:
                    # adjust size so that cost+fee == cash
                    size = cash / (exec_price * (1.0 + fee_pct))
                    cost = size * exec_price
                    fee = cost * fee_pct
                    total_cost = cost + fee
                if total_cost <= cash + 1e-9 and size > 0:
                    cash -= total_cost
                    qty += size
                    trade_log.append((ts.isoformat(), 'buy', size, exec_price, cost, fee))
            elif side == 'sell':
                size = min(size, qty)
                if size <= 0:
                    continue
                proceeds = size * exec_price
                fee = proceeds * fee_pct
                net = proceeds - fee
                qty -= size
                cash += net
                trade_log.append((ts.isoformat(), 'sell', size, exec_price, proceeds, fee))

        pv = cash + qty * price
        portfolio_values.append((ts, pv))

    # compute metrics
    final_value = portfolio_values[-1][1] if portfolio_values else starting_cash
    pnl = final_value - starting_cash

    # daily returns on portfolio value
    vals = [v for (_, v) in portfolio_values]
    returns = []
    for i in range(1, len(vals)):
        if vals[i-1] == 0:
            returns.append(0.0)
        else:
            returns.append((vals[i] - vals[i-1]) / vals[i-1])

    sharpe = compute_sharpe(returns, periods_per_year=252)
    dd = max_drawdown(vals)

    buys = [t for t in trade_log if t[1] == 'buy']
    sells = [t for t in trade_log if t[1] == 'sell']

    summary = {
        'final_value': final_value,
        'pnl': pnl,
        'sharpe': sharpe,
        'max_drawdown_pct': dd,
        'total_trades': len(trade_log),
        'buys': len(buys),
        'sells': len(sells),
    }

    return summary, trade_log, portfolio_values


def write_report(path: str, summary: dict, trade_log: List[tuple], portfolio_values: List[tuple], start: datetime, end: datetime):
    lines = []
    lines.append(f"# Backtest report — MA Crossover (demo)\n")
    lines.append(f"**Period:** {start.date().isoformat()} — {end.date().isoformat()}\n")
    lines.append(f"**Starting capital:** $10,000\n")
    lines.append(f"**Final portfolio value:** ${summary['final_value']:.2f}\n")
    lines.append(f"**Net PnL:** ${summary['pnl']:.2f}\n")
    lines.append(f"**Sharpe ratio (annualised):** {summary['sharpe']:.3f}\n")
    lines.append(f"**Max drawdown:** {summary['max_drawdown_pct']:.2f}%\n")
    lines.append(f"**Total trades executed:** {summary['total_trades']} (buys: {summary['buys']}, sells: {summary['sells']})\n")
    lines.append('\n')
    lines.append('## Trade log (first 20 entries)\n')
    lines.append('| timestamp | side | size | price | notional |')
    lines.append('|---|---:|---:|---:|---:|')
    for t in trade_log[:20]:
        lines.append(f"| {t[0]} | {t[1]} | {t[2]:.8f} | ${t[3]:.2f} | ${t[4]:.2f} |")

    # Add small portfolio series summary
    lines.append('\n')
    lines.append('## Portfolio snapshot (last 5 values)\n')
    lines.append('| date | portfolio_value |')
    lines.append('|---|---:|')
    for ts, v in portfolio_values[-5:]:
        lines.append(f"| {ts.date().isoformat()} | ${v:.2f} |")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--demo', action='store_true')
    p.add_argument('--seed', type=int, default=None, help='Optional RNG seed for reproducible demo runs')
    p.add_argument('--csv', type=str, help='CSV file with timestamp,price')
    p.add_argument('--start', type=str, default='2024-01-01')
    p.add_argument('--end', type=str, default='2024-06-30')
    p.add_argument('--short', type=int, default=5)
    p.add_argument('--long', type=int, default=20)
    p.add_argument('--trade-amount', type=float, default=50.0)
    p.add_argument('--fee-pct', type=float, default=0.0, help='Transaction fee as decimal (e.g. 0.001 = 0.1%)')
    p.add_argument('--slippage-pct', type=float, default=0.0, help='Slippage as decimal (e.g. 0.0005 = 0.05%)')
    p.add_argument('--exec-delay-days', type=int, default=1, help='Execution delay in ticks (days for daily data)')
    args = p.parse_args()

    if not os.path.exists(STRAT_PATH):
        raise FileNotFoundError(f'Cannot find strategy file at {STRAT_PATH}')

    strategy_cls = load_strategy_class(STRAT_PATH)

    if args.seed is not None:
        import random as _rnd
        _rnd.seed(int(args.seed))

    if args.demo:
        start = datetime.fromisoformat(args.start)
        end = datetime.fromisoformat(args.end)
        prices = generate_synthetic_prices(start, end)
    elif args.csv:
        prices = read_csv_prices(args.csv)
        start = prices[0][0]
        end = prices[-1][0]
    else:
        raise SystemExit('Provide --demo or --csv')

    config = {
        'short_period': args.short,
        'long_period': args.long,
        'trade_amount': args.trade_amount,
        'fee_pct': args.fee_pct,
        'slippage_pct': args.slippage_pct,
        'exec_delay_days': args.exec_delay_days,
    }
    summary, trades, pv = run_backtest(prices, strategy_cls, config, starting_cash=10000.0)

    os.makedirs(os.path.join(ROOT, 'reports'), exist_ok=True)
    report_path = os.path.join(ROOT, 'reports', 'backtest_report.md')
    write_report(report_path, summary, trades, pv, start, end)

    print('Backtest complete. Report written to', report_path)


if __name__ == '__main__':
    main()
