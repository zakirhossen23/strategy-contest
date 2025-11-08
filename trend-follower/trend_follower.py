#!/usr/bin/env python3
"""Trend Following Strategy with Pullback Entries."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any, Dict, Optional, List, Deque
from collections import deque
import logging

# Import base infrastructure from base-bot-template
import sys
import os

# Handle both local development and Docker container paths
base_path = os.path.join(os.path.dirname(__file__), '..', 'base-bot-template')
if not os.path.exists(base_path):
    # In Docker container, base template is at /app/base/
    base_path = '/app/base'

sys.path.insert(0, base_path)

from strategy_interface import BaseStrategy, Signal, register_strategy
from exchange_interface import MarketSnapshot


class TrendFollowerStrategy(BaseStrategy):
    """Trend Following Strategy with Pullback Entries."""
    
    def __init__(self, config: Dict[str, Any], exchange):
        super().__init__(config=config, exchange=exchange)
        
        # Trading parameters
        self.base_trade_amount = float(config.get("base_trade_amount", 1000.0))
        self.fast_ema_period = int(config.get("fast_ema_period", 50))
        self.slow_ema_period = int(config.get("slow_ema_period", 200))
        self.min_trend_strength = float(config.get("min_trend_strength", 1.02))
        self.trailing_stop_pct = float(config.get("trailing_stop_pct", 5.0))
        self.max_position_pct = float(config.get("max_position_pct", 0.55))
        self.min_pullback_pct = float(config.get("min_pullback_pct", 2.0))
        
        # State tracking
        self.fast_ema = deque(maxlen=self.fast_ema_period)
        self.slow_ema = deque(maxlen=self.slow_ema_period)
        self.price_history = deque(maxlen=max(self.fast_ema_period, self.slow_ema_period) * 2)
        
        self.in_position = False
        self.entry_price = 0.0
        self.position_size = 0.0
        self.trailing_stop = 0.0
        self.consecutive_signals = 0
        
        # For pullback detection
        self.last_high = 0.0
        self.pullback_detected = False
        
        # For crossover detection
        self.was_bullish = False
        
        self.logger = logging.getLogger("strategy.trend_follower")

    def prepare(self) -> None:
        """Initialize strategy - no historical data needed."""
        self.logger.info(f"Trend Follower strategy initialized for {self.exchange.name}")

    def _update_emas(self) -> None:
        """Update EMA values with current price history."""
        if len(self.price_history) < self.slow_ema_period:
            return
            
        # Calculate EMAs
        prices = list(self.price_history)
        
        # Fast EMA
        if len(self.fast_ema) == 0:
            self.fast_ema.extend(prices[-self.fast_ema_period:])
        else:
            multiplier = 2 / (self.fast_ema_period + 1)
            current_fast = self._get_fast_ema()
            new_fast = (prices[-1] - current_fast) * multiplier + current_fast
            self.fast_ema.append(new_fast)
        
        # Slow EMA  
        if len(self.slow_ema) == 0:
            self.slow_ema.extend(prices[-self.slow_ema_period:])
        else:
            multiplier = 2 / (self.slow_ema_period + 1)
            current_slow = self._get_slow_ema()
            new_slow = (prices[-1] - current_slow) * multiplier + current_slow
            self.slow_ema.append(new_slow)

    def _get_fast_ema(self) -> float:
        """Get current fast EMA value."""
        return self.fast_ema[-1] if self.fast_ema else 0.0
        
    def _get_slow_ema(self) -> float:
        """Get current slow EMA value."""
        return self.slow_ema[-1] if self.slow_ema else 0.0

    def generate_signal(self, market, portfolio) -> Signal:
        """Generate trading signal based on trend following."""
        current_price = market.current_price
        self.price_history.append(current_price)
        self._update_emas()
        
        fast_ema = self._get_fast_ema()
        slow_ema = self._get_slow_ema()
        
        if fast_ema == 0.0 or slow_ema == 0.0:
            return Signal(action="hold", reason="Insufficient data for EMA calculation")
        
        # Simple trend following: buy when crossing above slow EMA, sell when crossing below
        in_bullish_trend = current_price > slow_ema
        
        if in_bullish_trend and not self.in_position and not self.was_bullish:
            # Enter position on crossover
            position_value = min(self.base_trade_amount, portfolio.cash * self.max_position_pct)
            size = position_value / current_price
            self.was_bullish = True
            return Signal(
                action="buy",
                size=size,
                reason=f"Bullish crossover: price {current_price:.2f} crossed above slow EMA {slow_ema:.2f}",
                target_price=current_price * 1.1,
                stop_loss=current_price * 0.9
            )
        
        elif not in_bullish_trend and self.in_position and self.was_bullish:
            # Exit position on crossover
            self.was_bullish = False
            return Signal(
                action="sell",
                size=self.position_size,
                reason=f"Bearish crossover: price {current_price:.2f} crossed below slow EMA {slow_ema:.2f}",
                entry_price=self.entry_price
            )
        
        # Update bullish state
        self.was_bullish = in_bullish_trend
        
        return Signal(action="hold", reason="No trade conditions met")

    def on_trade(self, signal: Signal, execution_price: float, execution_size: float, timestamp: datetime) -> None:
        """Update strategy state after trade execution."""
        if signal.action == "buy":
            self.in_position = True
            self.entry_price = execution_price
            self.position_size = execution_size
            self.logger.info(f"Entered position at {execution_price:.2f}")
            
        elif signal.action == "sell":
            self.in_position = False
            self.logger.info(f"Exited position at {execution_price:.2f}, entry was {self.entry_price:.2f}, P&L: {(execution_price - self.entry_price) * self.position_size:.2f}")


# Register the strategy
register_strategy("trend_follower", lambda config, exchange: TrendFollowerStrategy(config, exchange))
