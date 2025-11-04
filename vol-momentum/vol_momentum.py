#!/usr/bin/env python3
"""Volatility-targeted momentum strategy (submission copy).

This is a direct copy of the strategy implementation so the `vol-momentum/`
folder contains both the implementation and the registered submission file.
"""
from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime
import os

import sys
base_path = os.path.join(os.path.dirname(__file__), '..', 'base-bot-template')
if not os.path.exists(base_path):
    base_path = '/app/base'
sys.path.insert(0, base_path)

from strategy_interface import BaseStrategy, Signal
from exchange_interface import MarketSnapshot


def _sma(values: List[float], period: int) -> float | None:
    if not values or period <= 0 or len(values) < period:
        return None
    return sum(values[-period:]) / float(period)


def _std_returns(values: List[float], window: int) -> float:
    if len(values) < 2 or window <= 0:
        return 0.0
    import math
    rets = []
    for i in range(1, len(values)):
        prev = values[i-1]
        cur = values[i]
        if prev and prev > 0:
            rets.append((cur - prev) / prev)
    if not rets:
        return 0.0
    w = rets[-window:]
    mean = sum(w) / len(w)
    var = sum((r - mean) ** 2 for r in w) / (len(w) - 1) if len(w) > 1 else 0.0
    return math.sqrt(var) if var > 0 else 0.0


class VolMomentumStrategy(BaseStrategy):
    def __init__(self, config: Dict[str, Any], exchange):
        super().__init__(config=config, exchange=exchange)
        self.short_period = int(config.get("short_period", 5))
        self.long_period = int(config.get("long_period", 20))
        self.vol_window = int(config.get("vol_window", 14))
        # target annual vol (e.g., 0.30 = 30% annual)
        self.target_annual_vol = float(config.get("target_annual_vol", 0.30))
        # cap max fraction of portfolio to deploy in a single asset
        self.max_exposure = float(config.get("max_exposure", 0.5))
        # small base trade amount to ensure multiple executions (contest requires >=10 trades)
        self.trade_amount = float(config.get("trade_amount", 100.0))
        self._last_signal: str | None = None

    def prepare(self) -> None:
        pass

    def generate_signal(self, market: MarketSnapshot, portfolio) -> Signal:
        prices = market.history
        if not prices or len(prices) < max(self.short_period, self.long_period, self.vol_window):
            return Signal("hold", reason="insufficient_history")

        short = _sma(prices, self.short_period)
        long = _sma(prices, self.long_period)
        if short is None or long is None:
            return Signal("hold", reason="insufficient_ma")

        # compute realized daily volatility (std of returns)
        sigma_daily = _std_returns(prices, self.vol_window)
        # convert target annual vol to daily
        import math
        target_daily = self.target_annual_vol / math.sqrt(252.0)

        # position fraction according to volatility targeting
        pos_frac = 0.0
        if sigma_daily > 0:
            pos_frac = target_daily / sigma_daily
        # clamp
        if pos_frac > self.max_exposure:
            pos_frac = self.max_exposure
        if pos_frac < 0.0:
            pos_frac = 0.0

        portfolio_value_est = float(getattr(portfolio, 'cash', 0.0))
        # We don't have per-symbol holdings value in the proxy, so we only use cash as a conservative estimate
        # If there is some cash and we are allowed to buy, compute dollar allocation
        if short > long and portfolio_value_est > 0 and getattr(portfolio, 'cash', 0.0) > 1e-8:
            # cap the dollar allocation per trade to a small trade_amount so we get more trades
            dollar_size = min(portfolio_value_est * pos_frac, float(self.trade_amount), float(getattr(portfolio, 'cash', 0.0)))
            size = dollar_size / market.current_price if market.current_price > 0 else 0.0
            if size <= 0:
                return Signal("hold", reason="zero_size_or_price")
            # allow repeated buys (small increments) while the MA condition holds to accumulate position
            self._last_signal = "buy"
            return Signal("buy", size=size, reason=f"vol_target_buy frac={pos_frac:.3f}")

        if short < long and getattr(portfolio, 'quantity', 0.0) > 0:
            if self._last_signal == "sell":
                return Signal("hold", reason="already_in_sell_state")
            self._last_signal = "sell"
            return Signal("sell", size=portfolio.quantity, reason="vol_target_sell")

        return Signal("hold", reason="no_cross")

    def on_trade(self, signal: Signal, execution_price: float, execution_size: float, timestamp: datetime) -> None:
        return


def _factory(config: Dict[str, Any], exchange):
    return VolMomentumStrategy(config=config, exchange=exchange)


try:
    from strategy_interface import register_strategy
    register_strategy("vol-momentum", _factory)
except Exception:
    # running in combined_backtest loader path may not need registry
    pass
