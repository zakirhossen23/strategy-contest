#!/usr/bin/env python3
"""MA Crossover strategy template (example).

Implements a simple moving-average crossover that
buys a fixed dollar amount when the short MA crosses
above the long MA and sells the full position when the
short MA crosses below the long MA.

This file is a drop-in strategy template that registers
itself under the name "ma-crossover".
"""

from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime

import os

# Import base infra (handles relative paths when run inside container)
import sys
base_path = os.path.join(os.path.dirname(__file__), '..', 'base-bot-template')
if not os.path.exists(base_path):
    base_path = '/app/base'
sys.path.insert(0, base_path)

from strategy_interface import BaseStrategy, Signal, register_strategy
from exchange_interface import MarketSnapshot


def _sma(values: List[float], period: int) -> float | None:
    if not values or period <= 0 or len(values) < period:
        return None
    return sum(values[-period:]) / float(period)


class MaCrossoverStrategy(BaseStrategy):
    """Simple moving-average crossover strategy.

    Config keys (via config dict or ENV mapping):
    - short_period: int (default 5)
    - long_period: int (default 20)
    - trade_amount: float (USD to spend per buy, default 50.0)
    """

    def __init__(self, config: Dict[str, Any], exchange):
        super().__init__(config=config, exchange=exchange)
        self.short_period = int(config.get("short_period", int(os.getenv("SHORT_PERIOD", 5))))
        self.long_period = int(config.get("long_period", int(os.getenv("LONG_PERIOD", 20))))
        self.trade_amount = float(config.get("trade_amount", float(os.getenv("TRADE_AMOUNT", 50.0))))
        self._last_signal: str | None = None

    def prepare(self) -> None:
        # No warm-up required for this simple strategy
        pass

    def generate_signal(self, market: MarketSnapshot, portfolio) -> Signal:
        prices = market.history
        if not prices or len(prices) < max(self.short_period, self.long_period):
            return Signal("hold", reason="insufficient_history")

        short = _sma(prices, self.short_period)
        long = _sma(prices, self.long_period)
        if short is None or long is None:
            return Signal("hold", reason="insufficient_history")

        # Buy if short MA crosses above long MA and we have cash
        if short > long and portfolio.cash > 0:
            # compute notional USD to spend
            notional = min(self.trade_amount, portfolio.cash)
            size = notional / market.current_price if market.current_price > 0 else 0.0
            if size <= 0:
                return Signal("hold", reason="zero_size_or_price")
            # avoid placing duplicate buys if already signalled
            if self._last_signal == "buy":
                return Signal("hold", reason="already_in_buy_state")
            self._last_signal = "buy"
            return Signal("buy", size=size, reason="ma_crossover_buy", target_price=None)

        # Sell if short MA crosses below long MA and we hold position
        if short < long and portfolio.quantity > 0:
            if self._last_signal == "sell":
                return Signal("hold", reason="already_in_sell_state")
            self._last_signal = "sell"
            return Signal("sell", size=portfolio.quantity, reason="ma_crossover_sell")

        return Signal("hold", reason="no_cross")

    def on_trade(self, signal: Signal, execution_price: float, execution_size: float, timestamp: datetime) -> None:
        # The base loop keeps portfolio state; this hook can be used to track trade history.
        return


def _factory(config: Dict[str, Any], exchange):
    return MaCrossoverStrategy(config=config, exchange=exchange)


# Register strategy under a stable name
register_strategy("ma-crossover", _factory)
