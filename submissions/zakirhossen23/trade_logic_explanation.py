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
        "Volatility-targeted momentum: Uses MA crossover for entries/exits, but sizes positions "
        "by realized volatility. It computes recent daily volatility, converts a target annual "
        "volatility to a daily target, and sets pos_frac = target_daily / sigma_daily (clamped by max_exposure). "
        "On buy signals the strategy deploys up to min(portfolio_cash * pos_frac, trade_amount) dollars in small increments; "
        "on sell signals it fully liquidates. Simulation params: starting cash $10k, fee_pct=0.001, slippage_pct=0.0005, exec_delay_days=1."
    )


if __name__ == '__main__':
    print(explanation())
