#!/usr/bin/env python3
"""Fetch official Jan–Jun-2024 prices and run backtests for BTC and ETH.

Writes a combined markdown report to `reports/backtest_report.md`.
"""
from __future__ import annotations

import time
import requests
import os
from datetime import datetime, timezone
from typing import List, Tuple

ROOT = os.path.dirname(os.path.dirname(__file__))
import importlib.util
_spec = importlib.util.spec_from_file_location('backtest_runner', os.path.join(ROOT, 'reports', 'backtest_runner.py'))
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
load_strategy_class = _module.load_strategy_class
run_backtest = _module.run_backtest
write_report = _module.write_report


def fetch_coingecko_daily(coin_id: str, start: datetime, end: datetime) -> List[Tuple[datetime, float]]:
    """Fetch price series (daily) from CoinGecko between start and end (inclusive).

    Returns list of (datetime, price) at UTC dates.
    """
    import math

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    params = {
        'vs_currency': 'usd',
        'from': int(start.replace(tzinfo=timezone.utc).timestamp()),
        'to': int(end.replace(tzinfo=timezone.utc).timestamp()),
    }

    print(f"Fetching {coin_id} data from CoinGecko: {params['from']} -> {params['to']}")
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    prices = data.get('prices', [])  # list of [ms, price]
    # Group by date (UTC) and take last price of the day
    daily = {}
    for ms, price in prices:
        ts = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        day = datetime(ts.year, ts.month, ts.day, tzinfo=timezone.utc)
        daily[day] = price

    # Ensure all dates from start->end present; fill gaps by forward-fill
    out = []
    cur = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    last_price = None
    from datetime import timedelta
    while cur <= end.replace(tzinfo=timezone.utc):
        if cur in daily:
            last_price = daily[cur]
        if last_price is None:
            # If no data yet, set 0.0 as safe fallback
            last_price = 0.0
        out.append((cur, float(last_price)))
        cur = cur + timedelta(days=1)

    return out


def fetch_coinbase_daily(product: str, start: datetime, end: datetime) -> List[Tuple[datetime, float]]:
    """Fetch daily close prices from Coinbase Pro / Exchange candles endpoint.

    Returns list of (datetime, price) UTC.
    """
    url = f"https://api.exchange.coinbase.com/products/{product}/candles"
    params = {
        'start': start.replace(tzinfo=timezone.utc).isoformat(),
        'end': end.replace(tzinfo=timezone.utc).isoformat(),
        'granularity': 86400,
    }
    print(f"Fetching {product} data from Coinbase: {params['start']} -> {params['end']}")
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # each entry: [time, low, high, open, close, volume]
    # convert to dict keyed by date
    daily = {}
    for entry in data:
        ts = datetime.fromtimestamp(entry[0], tz=timezone.utc)
        day = datetime(ts.year, ts.month, ts.day, tzinfo=timezone.utc)
        close = float(entry[4])
        daily[day] = close

    # fill date range
    out = []
    cur = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    from datetime import timedelta
    last_price = None
    while cur <= end.replace(tzinfo=timezone.utc):
        if cur in daily:
            last_price = daily[cur]
        if last_price is None:
            last_price = 0.0
        out.append((cur, float(last_price)))
        cur = cur + timedelta(days=1)
    return out


def coin_id_for_symbol(sym: str) -> str:
    mapping = {
        'BTC-USD': 'bitcoin',
        'ETH-USD': 'ethereum'
    }
    return mapping[sym]


def main():
    start = datetime(2024, 1, 1)
    end = datetime(2024, 6, 30)
    symbols = ['BTC-USD', 'ETH-USD']

    strategy_cls = load_strategy_class(os.path.join(ROOT, 'ma_crossover', 'ma_crossover.py'))

    reports = []
    combined_trade_log = []
    combined_pv = []

    for sym in symbols:
        coin = coin_id_for_symbol(sym)
        # try Coinbase first (no auth required for public candles endpoint)
        try:
            product = sym
            prices = fetch_coinbase_daily(product, start, end)
        except Exception as exc:
            print(f"Coinbase fetch failed for {sym}: {exc}. Falling back to CoinGecko.")
            prices = fetch_coingecko_daily(coin, start, end)
        # run backtest
        # realistic simulation parameters (identical for all participants)
        config = {
            'short_period': 5,
            'long_period': 20,
            'trade_amount': 50.0,
            # transaction fee (0.001 = 0.1%)
            'fee_pct': 0.001,
            # slippage (0.0005 = 0.05%)
            'slippage_pct': 0.0005,
            # execution delay in days/ticks
            'exec_delay_days': 1,
        }
        summary, trade_log, pv = run_backtest(prices, strategy_cls, config, starting_cash=10000.0)
        reports.append((sym, summary, trade_log, pv))

    # Write a combined markdown
    report_path = os.path.join(ROOT, 'reports', 'backtest_report.md')
    lines = []
    lines.append('# Official Backtest Report — MA Crossover')
    lines.append('\n')
    for sym, summary, trade_log, pv in reports:
        lines.append(f'## Symbol: {sym}')
        lines.append(f"**Final portfolio value:** ${summary['final_value']:.2f}")
        lines.append(f"**Net PnL:** ${summary['pnl']:.2f}")
        lines.append(f"**Sharpe ratio (annualised):** {summary['sharpe']:.3f}")
        lines.append(f"**Max drawdown:** {summary['max_drawdown_pct']:.2f}%")
        lines.append(f"**Total trades executed:** {summary['total_trades']} (buys: {summary['buys']}, sells: {summary['sells']})")
        lines.append('\n')

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print('Official backtests complete. Report written to', report_path)


if __name__ == '__main__':
    main()
