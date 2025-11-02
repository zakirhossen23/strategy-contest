# MA Crossover Strategy Template

This template implements a simple moving-average crossover strategy as an example submission for the contest.

Files included:

- `ma_crossover.py` — strategy implementation (registers as `ma-crossover`)
- `startup.py` — entrypoint that boots the `UniversalBot`
- `requirements.txt` — minimal dependencies
- `Dockerfile` — container definition (simple example)

Quick start

1. Create and activate a virtualenv, then install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r base-bot-template/requirements.txt
pip install -r ma_crossover/requirements.txt
```

2. Run the template locally (uses environment variables or an optional config file):

```bash
export BOT_STRATEGY=ma-crossover
export BOT_SYMBOL=BTC-USD
export BOT_EXCHANGE=paper
export BOT_STARTING_CASH=10000

# Run the strategy
python ma_crossover/startup.py
```

Notes

- The strategy registers itself as `ma-crossover`. Use `BOT_STRATEGY=ma-crossover` to run it.
- Tune the strategy by setting env vars or passing a config file to `startup.py`.

Configuration keys supported (via config file or env vars):

- `short_period` / `SHORT_PERIOD` (int, default 5)
- `long_period` / `LONG_PERIOD` (int, default 20)
- `trade_amount` / `TRADE_AMOUNT` (float USD per buy, default 50.0)

How to submit

Follow the contest README. Place this folder under `submissions/<your-github-username>/ma-crossover/` and open a PR.
