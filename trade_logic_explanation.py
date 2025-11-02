"""Trade logic explanation for the MA Crossover strategy.

This module contains a concise, human-readable explanation of the
trading logic used by `ma_crossover/ma_crossover.py`.
"""

def explanation() -> str:
    """Return a clear explanation of the trading logic.

    Contract:
    - Inputs: historical prices and current market price
    - Outputs: a trading signal (buy, sell, hold) and size
    - Error modes: returns 'hold' when insufficient data or insufficient cash
    """
    return (
        "MA Crossover Strategy: This strategy computes a short-period and a long-period "
        "simple moving average (SMA) on the available price history. When the short SMA "
        "crosses above the long SMA, the strategy issues a BUY signal to spend a fixed USD "
        "amount (trade_amount). The buy size is calculated as notional / current_price. "
        "When the short SMA crosses below the long SMA and there is an existing position, "
        "the strategy issues a SELL signal for the entire held quantity. The strategy "
        "returns 'hold' if history is insufficient, price is invalid, or no action is warranted."
    )


if __name__ == '__main__':
    print(explanation())
