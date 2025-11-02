#!/usr/bin/env python3
"""Submission startup for contest (placed in `your-strategy-template/`)."""

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
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    os.environ.setdefault('BOT_STRATEGY', 'ma-crossover')
    bot = UniversalBot(config_path)
    print("🤖 Submission: MA Crossover")
    bot.run()


if __name__ == '__main__':
    main()
