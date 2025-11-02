# Trading Strategy Contest – Build the Most Profitable Bot

## 🏆 Prize Pool: $1,500 USD
- **Winner:** $1,000 USD
- **2nd Place:** $300 USD
- **3rd Place:** $200 USD

## 📋 Contest Overview

We are launching the first official trading strategy contest for our SaaS trading platform.
Your mission is simple: **build a profitable trading strategy** using our enterprise-grade infrastructure.
We provide the complete bot framework – you develop the logic.

### 🎯 Contest Goal
- **Objective:** Achieve the highest Profit & Loss (PnL) after backtesting
- **Testing Data:** BTC-USD and ETH-USD historical data (Jan–Jun 2024)
- **Starting Capital:** $10,000 virtual for all participants
- **Evaluation Metric:** Final portfolio value (highest PnL wins)

## 📦 What We Provide

### Base Infrastructure (provided):
```
base-bot-template/              # Universal trading bot framework
├── strategy_interface.py       # BaseStrategy and Signal classes
├── exchange_interface.py       # Market data and execution simulation
├── http_endpoints.py          # Dashboard and monitoring integration
├── enhanced_logging.py        # Enterprise-level structured logging
├── integrations.py            # Database and callback support
└── universal_bot.py           # Core orchestration
```

### Reference Implementation (for study):
```
dca-bot-template/              # Fully working reference strategy
├── dca_strategy.py           # Strategy implementation example
├── startup.py                # Bot entry point example
├── Dockerfile                # Container definition example
└── README.md                 # Documentation example
```

**You'll build your own `your-strategy-template/` following the same structure.**


## 🎯 Your Task

Create a new strategy template that inherits from the BaseStrategy interface.

### 📋 Deliverables:

1. **your-strategy-template/ folder containing:**
   - `your_strategy.py` – main strategy logic
   - `startup.py` – bot entry point
   - `Dockerfile` – container definition
   - `requirements.txt` – dependencies
   - `README.md` – documentation and parameter explanation

2. **Six-month backtest report** (PnL, Sharpe ratio, drawdown)

3. **Clear explanation** of your trading logic

All submissions will be backtested in our automated environment under identical conditions.

## 📊 Evaluation Criteria

- ✅ **Highest total PnL wins**
- ✅ Maximum drawdown < 50%
- ✅ At least 10 executed trades
- ✅ Identical starting balance and fees for all participants
- ✅ Realistic simulation with execution delay and transaction costs

## 🏅 Prizes

### 🥇 1st Place (Highest PnL):
- **$1,000 USD** cash prize
- Strategy integration into our production platform
- Professional portfolio showcase with verified metrics

### 🥈🥉 2nd & 3rd Place:
- **2nd Place:** $300 USD
- **3rd Place:** $200 USD
- Portfolio addition with verified backtest performance
- Recognition in our strategy showcase section

**Total Prize Pool: $1,500 USD**

## 📅 Contest Timeline

- **Registration Opens:** Tonight
- **Submission Deadline:** 3 weeks from launch
- **Backtesting Period:** 1 week (automated)
- **Winner Announcement:** 4 weeks from launch

## 👥 Ideal Participants

- Quantitative traders familiar with Python
- Algorithmic trading developers
- Data scientists with financial knowledge
- Experienced programmers interested in market strategy design

## 🚀 Getting Started

1. **Clone this repository:**
   ```bash
   git clone https://github.com/msolomos/strategy-contest.git
   cd strategy-contest
   ```

2. **Study the infrastructure:**
   - Review `base-bot-template/` to understand the framework
   - Examine `dca-bot-template/` to see implementation patterns

3. **Create your strategy:**
   - Copy `dca-bot-template/` as starting point
   - Implement your trading logic in the strategy file
   - Test locally using the provided tools

4. **Submit your strategy:**
   - Upload your complete `your-strategy-template/` folder
   - Include all required deliverables

## ⚖️ Fair Play & Verification

- All strategies will be re-executed in a controlled backtesting environment
- Hardcoded data or manipulation of test results will lead to disqualification
- By submitting, you agree that winning strategies may be integrated into our SaaS platform

## 💡 Why Join This Contest

- ✅ **Clear objective:** Highest PnL wins (no subjective judging)
- ✅ **Identical testing:** All participants use same data and conditions
- ✅ **Transparent evaluation:** Fully automated and fair process
- ✅ **Real infrastructure:** Production-grade framework, not a toy example
- ✅ **Cash prizes only:** No revenue-sharing or complex terms

**This first-round contest aims to discover and reward talented algorithmic traders who can deliver profitable, production-ready strategies.**

---

**Good luck building the most profitable strategy! 🚀** 