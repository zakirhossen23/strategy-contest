#!/usr/bin/env python3
"""Contest-compliant backtest runner for vol-momentum strategy using Yahoo Finance data."""

import sys
import os
import argparse
import json
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'vol-momentum'))

# Import strategy
import trend_follower_strategy

def download_data(symbol, start_date, end_date):
    """Download historical data from Yahoo Finance."""
    print(f"Downloading {symbol} data from Yahoo Finance...")
    print(f"Period: {start_date} to {end_date}")
    
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval='1h')
    
    if df.empty:
        raise ValueError(f"No data found for {symbol}")
    
    print(f"✓ Loaded {len(df)} candles from Yahoo Finance")
    return df

def simulate_trading(df, config, starting_capital=10000.0):
    """Simulate trading with the strategy."""
    cash = starting_capital
    position = 0.0
    trades = []
    portfolio_values = []
    
    # Strategy instance
    from trend_follower_strategy import TrendFollowerStrategy
    from exchange_interface import PaperExchange
    
    exchange = PaperExchange()
    strategy = TrendFollowerStrategy(config, exchange)
    
    for i, (date, row) in enumerate(df.iterrows()):
        price = row['Close']
        
        # Create market snapshot
        from exchange_interface import MarketSnapshot
        snapshot = MarketSnapshot(
            symbol=config.get('symbol', 'BTC-USD'),
            prices=[price],  # Simple list with current price
            current_price=price,
            timestamp=date.to_pydatetime()
        )
        
        # Create portfolio mock
        class MockPortfolio:
            def __init__(self, cash, position):
                self.cash = cash
                self._position = position
            
            def get_position(self, symbol):
                class MockPosition:
                    def __init__(self, size):
                        self.size = size
                return MockPosition(self._position)
        
        portfolio = MockPortfolio(cash, position)
        
        # Get signal
        signal = strategy.generate_signal(snapshot, portfolio)
        
        # Execute trade
        if signal.action == 'buy' and cash >= signal.size * price:
            # Apply fees (0.1% + 0.05% slippage)
            fee = signal.size * price * 0.001
            slippage = signal.size * price * 0.0005
            total_cost = signal.size * price + fee + slippage
            
            if cash >= total_cost:
                cash -= total_cost
                position += signal.size
                trades.append({
                    'date': date,
                    'action': 'buy',
                    'size': signal.size,
                    'price': price,
                    'fee': fee,
                    'reason': signal.reason
                })
        
        elif signal.action == 'sell' and position >= signal.size:
            # Apply fees
            fee = signal.size * price * 0.001
            slippage = signal.size * price * 0.0005
            total_received = signal.size * price - fee - slippage
            
            cash += total_received
            position -= signal.size
            trades.append({
                'date': date,
                'action': 'sell',
                'size': signal.size,
                'price': price,
                'fee': fee,
                'reason': signal.reason
            })
        
        # Track portfolio value
        portfolio_value = cash + position * price
        portfolio_values.append(portfolio_value)
    
    return cash, position, trades, portfolio_values

def calculate_metrics(trades, portfolio_values, starting_capital):
    """Calculate performance metrics."""
    if not trades:
        return {
            'final_value': starting_capital,
            'pnl': 0,
            'return_pct': 0,
            'total_trades': 0,
            'max_drawdown': 0,
            'sharpe': 0
        }
    
    final_value = portfolio_values[-1] if portfolio_values else starting_capital
    pnl = final_value - starting_capital
    return_pct = (pnl / starting_capital) * 100
    
    # Max drawdown
    peak = starting_capital
    max_dd = 0
    for val in portfolio_values:
        if val > peak:
            peak = val
        dd = (peak - val) / peak
        max_dd = max(max_dd, dd)
    
    # Sharpe ratio (simplified)
    returns = np.diff(portfolio_values) / portfolio_values[:-1]
    if len(returns) > 1:
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
    else:
        sharpe = 0
    
    return {
        'final_value': final_value,
        'pnl': pnl,
        'return_pct': return_pct,
        'total_trades': len(trades),
        'max_drawdown': max_dd * 100,
        'sharpe': sharpe
    }

def main():
    parser = argparse.ArgumentParser(description='Backtest trend follower strategy')
    parser.add_argument('--symbol', default='BTC-USD', help='Trading symbol')
    parser.add_argument('--start', default='2024-01-01', help='Start date')
    parser.add_argument('--end', default='2024-06-30', help='End date')
    parser.add_argument('--capital', type=float, default=10000.0, help='Starting capital')
    parser.add_argument('--output', default='backtest_results.json', help='Output file')
    
    args = parser.parse_args()
    
    # Strategy config
    config = {
        'base_trade_amount': 2500.0,
        'fast_ema_period': 20,
        'slow_ema_period': 100,
        'min_trend_strength': 1.003,
        'trailing_stop_pct': 1.0,
        'max_position_pct': 0.55,
        'min_pullback_pct': 0.3,
        'symbol': args.symbol
    }
    
    # Download data
    df = download_data(args.symbol, args.start, args.end)
    
    # Run simulation
    cash, position, trades, portfolio_values = simulate_trading(df, config, args.capital)
    
    # Calculate metrics
    metrics = calculate_metrics(trades, portfolio_values, args.capital)
    
    # Print results
    print(f"\nBacktest Results for {args.symbol}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Starting Capital: ${args.capital}")
    print(f"Ending Capital: ${metrics['final_value']:.2f}")
    print(f"PnL: ${metrics['pnl']:.2f}")
    print(f"Return: {metrics['return_pct']:.2f}%")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"Sharpe Ratio: {metrics['sharpe']:.3f}")
    print(f"Total Trades: {metrics['total_trades']}")
    
    # Save results
    results = {
        'config': config,
        'metrics': metrics,
        'trades': trades,
        'portfolio_values': portfolio_values
    }
    
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to {args.output}")

if __name__ == '__main__':
    main()