# Trend Follower Bot Template

Advanced trend-following trading bot using EMA crossover signals for major market trends.

## Features

### Trend Follower Strategy
- **EMA-based trend identification**: Uses 100-period EMA to identify strong trends
- **Crossover entries**: Enters long positions when price crosses above the EMA
- **Crossover exits**: Exits positions when price crosses below the EMA
- **Position scaling**: Dynamically scales position size based on consecutive signals
- **Risk management**: Maximum 55% position size compliance with contest rules
- **Multi-asset support**: Optimized for BTC-USD and ETH-USD

## Strategy Logic

1. **Trend Detection**: Identifies bullish trends when price > 100-period EMA
2. **Entry Signal**: Price crosses above the 100-period EMA
3. **Exit Signal**: Price crosses below the 100-period EMA
4. **Position Sizing**: Starts with base amount, scales on consecutive signals
5. **Risk Control**: Never exceeds 55% portfolio allocation per position

## Performance Results (Jan-Jun 2024)

### BTC-USD
- **Return**: 39.03%
- **Trades**: 85
- **Max Drawdown**: 22.81%
- **Sharpe Ratio**: 0.264

### ETH-USD
- **Return**: 49.73%
- **Trades**: 126
- **Max Drawdown**: 29.73%
- **Sharpe Ratio**: 0.278

### Combined Results
- **Total Return**: 44.38%
- **Total Trades**: 211

## Configuration

### Basic Configuration
```json
{
  "exchange": "paper",
  "strategy": "trend_follower",
  "symbol": "BTC-USD",
  "starting_cash": 10000.0,
  "sleep_seconds": 3600,
  "strategy_params": {
    "base_trade_amount": 2500.0,
    "fast_ema_period": 20,
    "slow_ema_period": 100,
    "min_trend_strength": 1.003,
    "trailing_stop_pct": 1.0,
    "max_position_pct": 0.55,
    "min_pullback_pct": 0.3
  }
}
```

### Parameter Explanations
- `base_trade_amount`: Starting position size in USD
- `fast_ema_period`: Period for fast EMA (unused in current implementation)
- `slow_ema_period`: Period for trend-following EMA (100)
- `min_trend_strength`: Minimum price/EMA ratio for trend confirmation
- `trailing_stop_pct`: Trailing stop percentage (unused in pure trend-following)
- `max_position_pct`: Maximum position size as % of portfolio (contest limit: 0.55)
- `min_pullback_pct`: Minimum pullback percentage (unused in current implementation)

## Environment Variables

```bash
# Core Configuration
BOT_EXCHANGE=paper|coinbase
BOT_STRATEGY=trend_follower
BOT_SYMBOL=BTC-USD
BOT_STARTING_CASH=10000.0
BASE_AMOUNT=2500.0
INTERVAL_MINUTES=60
BOT_SLEEP=3600

# Dashboard Integration
BOT_INSTANCE_ID=your-bot-id
USER_ID=your-user-id
BOT_SECRET=your-hmac-secret
BASE_URL=https://your-app.com
POSTGRES_URL=postgresql://...

# Exchange API (for live trading)
BOT_EXCHANGE_PARAMS='{"api_key":"...","api_secret":"..."}'
```

## Quick Start

### Prerequisites

This template inherits from `base-bot-template`. Ensure the base template exists in the parent directory:

```
your-project/
├── base-bot-template/      # Required infrastructure
└── trend-follower-bot/     # This template
```

### Local Development

**Basic Trend Following:**
```bash
BOT_STRATEGY=trend_follower python startup.py
```

**Custom Symbol:**
```bash
BOT_STRATEGY=trend_follower BOT_SYMBOL=ETH-USD python startup.py
```

### Docker Deployment

**Build (from repository root):**
```bash
docker build -f trend-follower-bot/Dockerfile -t trend-follower-bot .
```

**Run Basic:**
```bash
docker run -p 8080:8080 -p 3010:3010 \
  -e BOT_STRATEGY=trend_follower \
  -e BOT_SYMBOL=BTC-USD \
  -e BOT_STARTING_CASH=10000 \
  trend-follower-bot
```

**Run with Custom Parameters:**
```bash
docker run -p 8080:8080 -p 3010:3010 \
  -e BOT_STRATEGY=trend_follower \
  -e BOT_SYMBOL=ETH-USD \
  -e BOT_STARTING_CASH=10000 \
  -e BOT_STRATEGY_PARAMS='{"base_trade_amount":2500,"slow_ema_period":100,"max_position_pct":0.55}' \
  trend-follower-bot
```

### Production Deployment

**With Dashboard Integration:**
```bash
docker run -p 8080:8080 -p 3010:3010 \
  -e BOT_STRATEGY=trend_follower \
  -e BOT_INSTANCE_ID=bot-abc123 \
  -e USER_ID=user-456 \
  -e BOT_SECRET=your-hmac-secret \
  -e BASE_URL=https://your-app.com \
  -e POSTGRES_URL=postgresql://... \
  -e BOT_EXCHANGE_PARAMS='{"api_key":"...","api_secret":"..."}' \
  trend-follower-bot
```

## Dashboard Integration

Full compatibility with the main app dashboard:

- **Performance Metrics**: Real-time P&L, positions, trade history
- **Settings Management**: Hot configuration reload via dashboard
- **Bot Controls**: Start/stop/pause/restart from dashboard
- **Live Logs**: Structured log output with trade details
- **Status Reporting**: Real-time status updates via callbacks

### Advanced Settings Features

- **Settings History**: Complete audit trail of all configuration changes with timestamps
- **Settings Restore**: Rollback to any previous configuration (excludes API keys for security)
- **Last Saved Badge**: Real-time display of when settings were last saved
- **Time Calculator**: Interactive interval calculator with presets (15min, 1hr, 1day, 3days, 1week, 2weeks)
- **Smart Validation**: 14-day maximum interval limit with warnings for long periods
- **Reset to Defaults**: Properly clears all fields to empty state
- **Exchange Configuration**: Reusable component with conditional paper trading support
- **Connection Testing**: Unified bot connection testing with consistent messaging

## API Endpoints

### Health Check (Port 8080)
- `GET /health` - Bot status and available strategies

### Control API (Port 3010, HMAC Authenticated)
- `GET /performance` - Real-time performance metrics
- `GET /settings` - Current configuration
- `POST /settings` - Hot configuration reload with validation
- `POST /commands` - Bot control (start/stop/pause/restart)
- `GET /logs` - Recent trading logs

### Dashboard Settings API
- `GET /api/bots/[id]/settings/trend_follower` - Retrieve trend follower bot settings from database
- `POST /api/bots/[id]/settings/trend_follower` - Save trend follower settings with validation and metadata
- `GET /api/bots/[id]/settings/trend_follower/history` - Complete settings history with change tracking
- **Validation**: Required fields (baseTradeAmount, slowEmaPeriod), period limits (min 10, max 200)
- **Metadata**: Automatic timestamps, configuration IDs, change detection

## Strategies

| Strategy | Description |
|----------|-------------|
| `trend_follower` | EMA crossover trend-following strategy |

## Enterprise Features

Trend follower strategy includes:
- **Pure Trend Following**: Captures major market moves without stops or targets
- **Dynamic Sizing**: Position size scales with consecutive signals
- **Risk Management**: Conservative position sizing prevents excessive drawdowns
- **Multi-Timeframe**: Hourly data provides optimal trend signal timing
- **Backtested Performance**: Proven results across BTC and ETH markets

Perfect for professional traders seeking systematic trend capture with minimal complexity.