# Submission: MA Crossover (your-strategy-template)

Author: zakirhossen23
GitHub: https://github.com/zakirhossen23

This folder contains the exact files required by the contest submission.

Files:
- `your_strategy.py` — main strategy logic (MA Crossover)
- `startup.py` — entrypoint for the bot
- `Dockerfile` — container definition example
- `requirements.txt` — Python dependencies
- `README.md` — this file

Quick start (run locally):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r base-bot-template/requirements.txt
pip install -r your-strategy-template/requirements.txt

# Run the submission (paper exchange)
export BOT_STRATEGY=ma-crossover
export BOT_EXCHANGE=paper
export BOT_SYMBOL=BTC-USD
export BOT_STARTING_CASH=10000
python your-strategy-template/startup.py
```

Backtest

This submission includes a backtest run in `reports/backtest_report.md` produced with the official Jan–Jun 2024 data.
