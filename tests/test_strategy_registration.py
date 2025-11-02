import importlib.util
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
STRAT_PATH = os.path.join(ROOT, 'ma_crossover', 'ma_crossover.py')


class StrategyRegistrationTest(unittest.TestCase):
    def test_ma_crossover_registered(self):
        # Import the strategy module dynamically
        spec = importlib.util.spec_from_file_location('user_strategy', STRAT_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore

        # After importing, load base template modules and inspect registered strategies
        base_path = os.path.join(ROOT, '..', 'base-bot-template')
        if not os.path.exists(base_path):
            base_path = os.path.join(ROOT, 'base-bot-template')
        sys.path.insert(0, base_path)

        from strategy_interface import available_strategies

        # available_strategies returns a sorted list
        names = available_strategies()
        self.assertIn('ma-crossover', names, msg=f"Registered strategies: {names}")


if __name__ == '__main__':
    unittest.main()
