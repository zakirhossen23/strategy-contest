````markdown
# Submission: Volatility-targeted Momentum (vol-momentum)

Author: zakirhossen23
GitHub: https://github.com/zakirhossen23

This folder contains the exact files required by the contest submission (renamed
from `example_strategy/` to `vol-momentum/`).

Files:
- `example_strategy.py` — main strategy logic (keeps filename for compatibility)
- `vol_momentum.py` — implementation copy and registration for `vol-momentum`
- `startup.py` — entrypoint for the bot
- `Dockerfile` — container definition example
- `requirements.txt` — Python dependencies
- `README.md` — this file

Quick start (run locally):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r base-bot-template/requirements.txt
pip install -r vol-momentum/requirements.txt

# Run the submission (paper exchange)
export BOT_STRATEGY=vol-momentum
export BOT_EXCHANGE=paper
export BOT_SYMBOL=BTC-USD
export BOT_STARTING_CASH=10000
python vol-momentum/startup.py
```

Backtest

This submission includes a backtest run in `reports/backtest_report.md` produced with the official Jan–Jun 2024 data.

Simulation assumptions used for the official backtest (identical for all participants):

- Starting capital: $10,000
- Transaction fee: 0.1% per trade (fee_pct = 0.001)
- Slippage: 0.05% per trade (slippage_pct = 0.0005)
- Execution delay: 1 day (exec_delay_days = 1)

These parameters are applied in `reports/backtest_runner.py` and were used to generate the official `reports/backtest_report.md` included in the `submissions/` folder.

Packaging and submission
------------------------
- The submission zip is at: `submissions/zakirhossen23/vol-momentum.zip`. It contains only the `vol-momentum/` folder and the five required files. This is the artifact to upload to the contest.

````
