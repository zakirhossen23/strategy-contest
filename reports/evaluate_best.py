#!/usr/bin/env python3
"""Run a deterministic evaluation using the best params saved by the randomized search.

This imports the combined_backtest module and calls run_combined with the saved config.
"""
from __future__ import annotations
import os
import json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
BEST_PATH = os.path.join(ROOT, 'reports', 'best_params.json')
CB_PATH = os.path.join(ROOT, 'reports', 'combined_backtest.py')
OUT_MD = os.path.join(ROOT, 'reports', 'combined_backtest_report_best.md')

# load best params
with open(BEST_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
best_cfg = data.get('best_vol_config')
if best_cfg is None:
    raise RuntimeError('no best_vol_config in best_params.json')

# import combined_backtest as module
import importlib.util
spec = importlib.util.spec_from_file_location('combined_backtest_eval', CB_PATH)
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)  # type: ignore

# set up same environment as in combined_backtest.main
start = datetime(2024, 1, 1)
end = datetime(2024, 6, 30)
symbols = ['BTC-USD', 'ETH-USD']
base_sim = {'fee_pct': 0.001, 'slippage_pct': 0.0005, 'exec_delay_days': 1}

# pre-fetch series exactly as the main script does
series = {}
for s in symbols:
    ps = cb.get_prices(s, start, end)
    daily = {d.replace(tzinfo=cb.timezone.utc): p for (d, p) in ps} if hasattr(cb, 'timezone') else {d: p for (d, p) in ps}
    cur = datetime(start.year, start.month, start.day).replace(tzinfo=cb.timezone.utc)
    out = []
    last = None
    while cur <= end.replace(tzinfo=cb.timezone.utc):
        if cur in daily:
            last = daily[cur]
        last_price = float(last) if last is not None else 0.0
        out.append((cur, last_price))
        from datetime import timedelta
        cur = cur + timedelta(days=1)
    series[s] = out

# build dates
dates = [d for (d, _) in series[symbols[0]]]

# run deterministic combined backtest with the best vol config
summary, trades, pv = cb.run_combined(symbols, [os.path.join(ROOT, 'vol-momentum', 'vol_momentum.py')], [best_cfg], start, end, base_sim, series=series, dates=dates)

# write a human-readable report using the existing write_report helper
cb.write_report(OUT_MD, summary, trades, pv, start, end)

print('Wrote deterministic best-config report to', OUT_MD)
print('Summary:')
print(json.dumps(summary, indent=2))
