#!/usr/bin/env python3
"""Startup entrypoint for the MA Crossover strategy template."""

from __future__ import annotations

import sys
import os

# Ensure base template is importable (works in dev and in container)
base_path = os.path.join(os.path.dirname(__file__), '..', 'base-bot-template')
if not os.path.exists(base_path):
    base_path = '/app/base'
sys.path.insert(0, base_path)

from universal_bot import UniversalBot


def main() -> None:
    # Allow passing a config path; otherwise use ENV. Default strategy for this template:
    config_path = sys.argv[1] if len(sys.argv) > 1 else None

    # Ensure this template runs the MA Crossover strategy by default
    os.environ.setdefault('BOT_STRATEGY', 'ma-crossover')

    bot = UniversalBot(config_path)

    print("🤖 MA Crossover Strategy")
    print(f"🆔 Bot ID: {bot.config.bot_instance_id}")
    print(f"📈 Strategy: {bot.config.strategy}")
    print(f"💰 Symbol: {bot.config.symbol}")
    print(f"💵 Starting Cash: ${bot.config.starting_cash}")
    print("----------------------------------------")

    bot.run()


if __name__ == "__main__":
    main()
