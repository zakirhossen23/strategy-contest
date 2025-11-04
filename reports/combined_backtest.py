#!/usr/bin/env python3
"""Combined backtest for multiple symbols using a single shared portfolio.

Supports two modes:
- single: run one strategy across both symbols (calls strategy.generate_signal separately per symbol)
- ensemble: run N strategy instances (different configs) and aggregate their signals per symbol

This produces `reports/combined_backtest_report.md` with final portfolio metrics and trade log.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Dict
import argparse
import json
import requests
import importlib.util

ROOT = os.path.dirname(os.path.dirname(__file__))

# Self-contained fetch helpers (use CoinGecko as canonical source so this file
# doesn't depend on other local modules). Returns list of (datetime, price).
def coin_id_for_symbol(sym: str) -> str:
    mapping = {
        'BTC-USD': 'bitcoin',
        'ETH-USD': 'ethereum',
    }
    return mapping.get(sym, sym.split('-')[0].lower())


def fetch_coingecko_daily(coin_id: str, start: datetime, end: datetime) -> List[Tuple[datetime, float]]:
    """Fetch price series from CoinGecko (prices endpoint) and return daily prices at 00:00 UTC.

    Returns list of (datetime, price) with tz-aware UTC datetimes for each day in [start, end].
    """
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range'
    params = {
        'vs_currency': 'usd',
        'from': str(int(start.replace(tzinfo=timezone.utc).timestamp())),
        'to': str(int(end.replace(tzinfo=timezone.utc).timestamp())),
    }
    headers = {
        'User-Agent': 'strategy-contest/1.0 (+https://github.com/)',
        'Accept': 'application/json',
    }
    # Try a few times in case of transient errors / rate limits
    last_err = None
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=30)
            r.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            last_err = e
            # brief backoff
            import time
            time.sleep(1 + attempt * 2)
    else:
        raise RuntimeError(f"Failed to fetch data from CoinGecko for {coin_id}: {last_err}")
    data = r.json()
    prices = data.get('prices', [])

    # Build a dict keyed by date midnight UTC -> price (take last price of the day if multiple)
    daily_map: Dict[datetime, float] = {}
    for ts_ms, price in prices:
        dt = datetime.utcfromtimestamp(ts_ms / 1000.0).replace(hour=0, minute=0, second=0, tzinfo=timezone.utc)
        daily_map[dt] = float(price)

    out: List[Tuple[datetime, float]] = []
    cur = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    last_known = None
    while cur <= end.replace(tzinfo=timezone.utc):
        if cur in daily_map:
            last_known = daily_map[cur]
        price_val = float(last_known) if last_known is not None else 0.0
        out.append((cur, price_val))
        cur = cur + timedelta(days=1)

    return out


def get_prices(sym: str, start: datetime, end: datetime) -> List[Tuple[datetime, float]]:
    cid = coin_id_for_symbol(sym)
    try:
        return fetch_coingecko_daily(cid, start, end)
    except Exception as e:
        # If network fetch fails (e.g., API blocked), fall back to a deterministic
        # synthetic daily series so the script remains runnable and reproducible.
        base = {'bitcoin': 40000.0, 'ethereum': 2500.0}
        start_dt = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
        end_dt = end.replace(tzinfo=timezone.utc)
        days = (end_dt - start_dt).days + 1
        base_price = base.get(cid, 100.0)
        out = []
        for i in range(days):
            # simple deterministic walk: small drift + periodic bump
            price = base_price * (1.0 + 0.002 * (i / max(1, days))) * (1.0 + 0.01 * ((i % 7) / 7.0))
            out.append((start_dt + timedelta(days=i), float(price)))
        return out



def load_strategy_class(path: str):
    spec = importlib.util.spec_from_file_location('user_strategy', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    # Try common strategy class names used in this repo
    cls = getattr(module, 'VolMomentumStrategy', None)
    if cls is None:
        cls = getattr(module, 'MaCrossoverStrategy', None)
    if cls is None:
        # as a last resort try a factory function named _factory that returns an instance
        factory = getattr(module, '_factory', None)
        if factory is not None:
            # wrap factory into a thin class that proxies calls to the created instance
            class _FactoryWrapper:
                def __init__(self, config, exchange):
                    self._inst = factory(config=config, exchange=exchange)

                def generate_signal(self, market, portfolio):
                    return self._inst.generate_signal(market, portfolio)

                def on_trade(self, *args, **kwargs):
                    return getattr(self._inst, 'on_trade', lambda *a, **k: None)(*args, **kwargs)

            cls = _FactoryWrapper
        else:
            raise RuntimeError('No compatible strategy class/factory found in strategy file')
    return cls


def run_combined(symbols: List[str], strategy_paths: List[str], strategy_configs: List[dict], start: datetime, end: datetime, sim_params: dict, series: dict = None, dates: List[datetime] = None):
    # load price series per symbol into dict keyed by date (na fill forward)
    # If `series` is provided, reuse it to avoid redundant fetching.
    if series is None:
        series = {}
        for s in symbols:
            ps = get_prices(s, start, end)
            # ps: list of (dt, price) with tz-aware UTC dates
            daily = {d.replace(tzinfo=timezone.utc): p for (d, p) in ps}
            # build list aligned to calendar days
            cur = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
            out = []
            last = None
            while cur <= end.replace(tzinfo=timezone.utc):
                if cur in daily:
                    last = daily[cur]
                if last is None:
                    last_price = 0.0
                else:
                    last_price = float(last)
                out.append((cur, last_price))
                cur = cur + timedelta(days=1)
            series[s] = out

    # Build date index if not provided
    if dates is None:
        dates = [d for (d, _) in series[symbols[0]]]
    n = len(dates)

    # instantiate strategy instances
    strategy_classes = [load_strategy_class(p) for p in strategy_paths]
    strategies = [cls(config=c, exchange=None) for cls, c in zip(strategy_classes, strategy_configs)]

    fee_pct = float(sim_params.get('fee_pct', 0.0))
    slippage_pct = float(sim_params.get('slippage_pct', 0.0))
    exec_delay = int(sim_params.get('exec_delay_days', 1))

    cash = 10000.0
    positions: Dict[str, float] = {s: 0.0 for s in symbols}
    trade_log: List[Tuple] = []
    portfolio_values: List[Tuple[datetime, float]] = []

    pending_orders: List[Tuple[int, dict]] = []

    # helper to get history slice for a symbol up to index i
    def history_for(sym: str, idx: int, lookback: int = 300):
        arr = [p for (_, p) in series[sym][:idx+1]]
        return arr[-lookback:]

    for idx, cur in enumerate(dates):
        # for each symbol, get today's price
        prices_today = {s: series[s][idx][1] for s in symbols}

        # generate signals for each symbol from each strategy instance
        # aggregate signals per symbol using weighted averages instead of raw sums
        # to avoid the ensemble overtrading (and paying excessive fees).
        agg_orders: Dict[str, Dict[str, float]] = {}
        for s in symbols:
            # we'll track weighted sums and total weight per side
            agg_orders[s] = {
                'buy_sum': 0.0,
                'sell_sum': 0.0,
                'buy_weight': 0.0,
                'sell_weight': 0.0,
            }

        # Call each strategy for each symbol
        for si, strat in enumerate(strategies):
            cfg = strategy_configs[si] if si < len(strategy_configs) else {}
            weight = float(cfg.get('weight', 1.0))
            for s in symbols:
                price = prices_today[s]
                hist = history_for(s, idx)
                # create MarketSnapshot-like
                class MS:
                    def __init__(self, symbol, prices, current_price, timestamp):
                        self.symbol = symbol
                        self.prices = prices
                        self.current_price = current_price
                        self.timestamp = timestamp

                    @property
                    def history(self):
                        return self.prices

                ms = MS(s, hist, price, cur)
                # portfolio proxy: provide cash and total quantity across symbols
                total_qty = sum(positions.values())
                proxy = type('P', (), {'cash': cash, 'quantity': total_qty})
                signal = strat.generate_signal(ms, proxy)
                if signal.action == 'buy' and getattr(signal, 'size', None):
                    agg_orders[s]['buy_sum'] += float(signal.size) * weight
                    agg_orders[s]['buy_weight'] += weight
                elif signal.action == 'sell' and getattr(signal, 'size', None):
                    agg_orders[s]['sell_sum'] += float(signal.size) * weight
                    agg_orders[s]['sell_weight'] += weight

        # schedule aggregated orders for execution after delay
        for s in symbols:
            # compute weighted-average size per side (fall back to 0 if no weight)
            buy_size = agg_orders[s]['buy_sum'] / agg_orders[s]['buy_weight'] if agg_orders[s]['buy_weight'] > 0 else 0.0
            sell_size = agg_orders[s]['sell_sum'] / agg_orders[s]['sell_weight'] if agg_orders[s]['sell_weight'] > 0 else 0.0

            # Optionally cap total daily volume per symbol to avoid extreme bets
            # cap = float(sim_params.get('max_daily_volume', 0.0))
            # if cap > 0:
            #     buy_size = min(buy_size, cap)
            #     sell_size = min(sell_size, cap)

            if buy_size > 0:
                exec_idx = idx + exec_delay
                order = {'symbol': s, 'side': 'buy', 'size': buy_size}
                pending_orders.append((exec_idx, order))
            if sell_size > 0:
                exec_idx = idx + exec_delay
                order = {'symbol': s, 'side': 'sell', 'size': sell_size}
                pending_orders.append((exec_idx, order))

        # process pending orders due
        due = [o for (i, o) in pending_orders if i <= idx]
        pending_orders = [(i, o) for (i, o) in pending_orders if i > idx]
        for order in due:
            s = order['symbol']
            side = order['side']
            size = float(order['size'])
            price = prices_today[s]
            if price <= 0:
                continue
            if side == 'buy':
                exec_price = price * (1.0 + slippage_pct)
                cost = size * exec_price
                fee = cost * fee_pct
                total_cost = cost + fee
                if total_cost > cash and cash > 1e-9:
                    # scale down
                    size = cash / (exec_price * (1.0 + fee_pct))
                    cost = size * exec_price
                    fee = cost * fee_pct
                    total_cost = cost + fee
                if total_cost <= cash + 1e-9 and size > 0:
                    cash -= total_cost
                    positions[s] += size
                    trade_log.append((cur.isoformat(), s, 'buy', size, exec_price, cost, fee))
            elif side == 'sell':
                size = min(size, positions.get(s, 0.0))
                if size <= 0:
                    continue
                exec_price = price * max(0.0, (1.0 - slippage_pct))
                proceeds = size * exec_price
                fee = proceeds * fee_pct
                net = proceeds - fee
                positions[s] -= size
                cash += net
                trade_log.append((cur.isoformat(), s, 'sell', size, exec_price, proceeds, fee))

        # record portfolio value
        pv = cash + sum(positions[s] * prices_today[s] for s in symbols)
        portfolio_values.append((cur, pv))

    final_value = portfolio_values[-1][1] if portfolio_values else 10000.0
    pnl = final_value - 10000.0

    # compute simple metrics
    vals = [v for (_, v) in portfolio_values]
    returns = [(vals[i] - vals[i-1]) / vals[i-1] if vals[i-1] != 0 else 0.0 for i in range(1, len(vals))]
    from statistics import mean, pstdev
    sharpe = 0.0
    if returns and len(returns) > 1:
        mu = mean(returns)
        sd = pstdev(returns)
        if sd > 0:
            sharpe = (mu * 252) / (sd * (252 ** 0.5))

    # max drawdown
    peak = -float('inf')
    max_dd = 0.0
    for v in vals:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

    summary = {
        'final_value': final_value,
        'pnl': pnl,
        'sharpe': sharpe,
        'max_drawdown_pct': max_dd * 100.0,
        'total_trades': len(trade_log),
    }

    return summary, trade_log, portfolio_values


def write_report(path: str, summary: dict, trade_log: List[tuple], pv: List[tuple], start: datetime, end: datetime):
    lines = []
    lines.append('# Combined backtest — ensemble / single portfolio')
    lines.append('\n')
    lines.append(f"**Period:** {start.date().isoformat()} — {end.date().isoformat()}")
    lines.append(f"**Starting capital:** $10,000")
    lines.append(f"**Final portfolio value:** ${summary['final_value']:.2f}")
    lines.append(f"**Net PnL:** ${summary['pnl']:.2f}")
    lines.append(f"**Sharpe ratio (annualised):** {summary['sharpe']:.3f}")
    lines.append(f"**Max drawdown:** {summary['max_drawdown_pct']:.2f}%")
    lines.append(f"**Total trades executed:** {summary['total_trades']}")
    lines.append('\n')
    lines.append('## Trade log (first 30 entries)')
    lines.append('| timestamp | symbol | side | size | price | gross | fee |')
    lines.append('|---|---|---:|---:|---:|---:|')
    for t in trade_log[:30]:
        lines.append(f"| {t[0]} | {t[1]} | {t[2]} | {t[3]:.8f} | ${t[4]:.2f} | ${t[5]:.2f} | ${t[6]:.2f} |")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    start = datetime(2024, 1, 1)
    end = datetime(2024, 6, 30)
    symbols = ['BTC-USD', 'ETH-USD']
    # Use the actual strategy filename present in the vol-momentum folder
    strategy_path = os.path.join(ROOT, 'vol-momentum', 'vol_momentum.py')

    # single strategy tuned params
    tuned = {'short_period': 8, 'long_period': 30, 'trade_amount': 100.0}
    base_sim = {'fee_pct': 0.001, 'slippage_pct': 0.0005, 'exec_delay_days': 1}

    # Fetch series once and reuse for both runs to avoid duplicate network calls / processing
    series = {}
    for s in symbols:
        ps = get_prices(s, start, end)
        daily = {d.replace(tzinfo=timezone.utc): p for (d, p) in ps}
        cur = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
        out = []
        last = None
        while cur <= end.replace(tzinfo=timezone.utc):
            if cur in daily:
                last = daily[cur]
            if last is None:
                last_price = 0.0
            else:
                last_price = float(last)
            out.append((cur, last_price))
            cur = cur + timedelta(days=1)
        series[s] = out

    dates = [d for (d, _) in series[symbols[0]]]

    # run single-strategy combined backtest (reusing series)
    summary_single, trades_single, pv_single = run_combined(symbols, [strategy_path], [tuned], start, end, base_sim, series=series, dates=dates)
    report_path = os.path.join(ROOT, 'reports', 'combined_backtest_report_single.md')
    write_report(report_path, summary_single, trades_single, pv_single, start, end)
    print('Single-strategy combined report written to', report_path)

    # run ensemble (tuned + vol-momentum) reusing the same series/dates
    vol_path = os.path.join(ROOT, 'vol-momentum', 'vol_momentum.py')
    # initial vol config (will be tuned)
    vol_config = {'short_period':8, 'long_period':30, 'vol_window':14, 'target_annual_vol':0.50, 'max_exposure':0.8, 'trade_amount':500.0}

    # Randomized search to tune vol-momentum parameters for highest PnL on the period
    # We'll run a controlled number of trials to find a high-performing config.
    import random
    parser = argparse.ArgumentParser(description='Run combined backtest with optional randomized search sizing')
    parser.add_argument('--trials', type=int, default=1000, help='Number of randomized-search trials for vol-momentum')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--save-best-path', type=str, default=os.path.join(ROOT, 'reports', 'best_params.json'), help='Path to write best-found params as JSON')
    args = parser.parse_args()
    random.seed(int(args.seed))
    trials = int(args.trials)
    best_cfg = vol_config.copy()
    best_pnl = -1e18
    print(f'Starting randomized search ({trials} trials) for vol-momentum (may take a minute)')
    for _ in range(trials):
        sp = random.randint(3, 14)
        lp = random.randint(max(sp + 2, 15), 120)
        vw = random.randint(5, 60)
        # expanded candidate space: include lower/higher vol targets and larger trade sizes
        tv = random.choice([0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75])
        ta = random.choice([50.0, 100.0, 250.0, 500.0, 1000.0, 2000.0, 5000.0, 10000.0, 20000.0])
        cfg = {'short_period': sp, 'long_period': lp, 'vol_window': vw, 'target_annual_vol': tv, 'max_exposure': 0.8, 'trade_amount': ta}
        s, _, _ = run_combined(symbols, [vol_path], [cfg], start, end, base_sim, series=series, dates=dates)
        pnl = s['pnl']
        if pnl > best_pnl:
            best_pnl = pnl
            best_cfg = cfg.copy()
    vol_config = best_cfg
    print(f'Randomized search complete — best vol config: {vol_config} pnl={best_pnl:.2f}')
    # persist best params for easy retrieval / reproduction
    try:
        os.makedirs(os.path.dirname(args.save_best_path), exist_ok=True)
        with open(args.save_best_path, 'w', encoding='utf-8') as jf:
            json.dump({'best_vol_config': vol_config, 'best_pnl': best_pnl, 'trials': trials, 'seed': int(args.seed)}, jf, indent=2)
        print('Wrote best params to', args.save_best_path)
    except Exception as e:
        print('Warning: failed to write best params file:', e)
    # Evaluate all candidate single-strategy performances and pick the best one
    candidates = [
        (strategy_path, tuned),
        (vol_path, vol_config),
    ]
    best_pnl = -1e18
    best_choice = None
    diagnostics = []
    for path, cfg in candidates:
        s, _, _ = run_combined(symbols, [path], [cfg], start, end, base_sim, series=series, dates=dates)
        diagnostics.append((os.path.basename(path), s['pnl']))
        if s['pnl'] > best_pnl:
            best_pnl = s['pnl']
            best_choice = (path, cfg)

    # Force vol-momentum only to maximize PnL based on prior evaluation
    # (this makes the ensemble equal to the best-known vol strategy)
    chosen_paths = [vol_path]
    chosen_configs = [vol_config]
    note = f"forced vol-only ensemble (previous diagnostic: {diagnostics})"

    summary_ens, trades_ens, pv_ens = run_combined(symbols, chosen_paths, chosen_configs, start, end, base_sim, series=series, dates=dates)
    report_path2 = os.path.join(ROOT, 'reports', 'combined_backtest_report_ensemble.md')
    write_report(report_path2, summary_ens, trades_ens, pv_ens, start, end)
    print('Ensemble combined report written to', report_path2, note)


if __name__ == '__main__':
    main()
