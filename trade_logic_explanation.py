"""Trade logic explanation for the vol-momentum strategy.

This module contains a concise, human-readable explanation of the
volatility-targeted momentum strategy implemented in the submission.
"""

def explanation() -> str:
    """Return a clear explanation of the trading logic.

    Contract:
    - Inputs: historical prices and current market price
    - Outputs: a trading signal (buy, sell, hold) and size
    - Error modes: returns 'hold' when insufficient data or insufficient cash
    """
    return (
        "Volatility-targeted momentum (vol-momentum): The strategy uses a short and "
        "long simple moving average (SMA) to generate entry/exit signals (classic MA "
        "crossover). It sizes positions using a volatility-targeting rule: convert the "
        "configured target annual volatility to a daily target and divide by the asset's "
        "realized daily volatility to compute a position fraction of the portfolio. That "
        "dollar exposure is capped by a configurable max_exposure and per-trade trade_amount. "
        "Buys are executed in small increments while the short SMA > long SMA; sells close the "
        "position when short SMA < long SMA. The strategy returns 'hold' when history is "
        "insufficient or size would be zero."
    )


if __name__ == '__main__':
    print(explanation())
