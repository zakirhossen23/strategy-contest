Trading Strategy Contest – Build the Most Profitable Bot

$1,500 Total Prize Pool
Winner: $1,000 USD | Runner-ups: 2nd Place: $300 USD, 3rd Place: $200 USD

Please note that each participant is allowed a maximum of three submissions. Any additional entries will result in disqualification.

Contest Overview

We are launching the first official trading strategy contest for our SaaS trading platform.
Your mission is simple: build a profitable trading strategy using our enterprise-grade infrastructure.
We provide the complete bot framework – you develop the logic.

Goal: Achieve the highest Profit & Loss (PnL) after backtesting.
Testing Data: BTC-USD and ETH-USD historical data (Jan–Jun 2024).
Starting Capital: $10,000 virtual for all participants.
Evaluation Metric: Final portfolio value (highest PnL wins).

What We Provide

Base Infrastructure (provided):

```markdown
Trading Strategy Contest – Build the Most Profitable Bot

$1,500 Total Prize Pool
Winner: $1,000 USD | Runner-ups: 2nd Place: $300 USD, 3rd Place: $200 USD

Please note that each participant is allowed a maximum of three submissions. Any additional entries will result in disqualification.

Contest Overview

We are launching the first official trading strategy contest for our SaaS trading platform.
Your mission is simple: build a profitable trading strategy using our enterprise-grade infrastructure.
We provide the complete bot framework – you develop the logic.

Goal: Achieve the highest Profit & Loss (PnL) after backtesting.
Testing Data: BTC-USD and ETH-USD historical data (Jan–Jun 2024).
Starting Capital: $10,000 virtual for all participants.
Evaluation Metric: Final portfolio value (highest PnL wins).

What We Provide

Base Infrastructure (provided):

base-bot-template/ – universal trading bot framework
strategy_interface.py – defines BaseStrategy and Signal classes
exchange_interface.py – handles market data and execution simulation
http_endpoints.py – dashboard and monitoring integration
enhanced_logging.py – enterprise-level structured logging
integrations.py – database and callback support

Reference Implementation (for study):

dca-bot-template/ – a fully working reference strategy
Demonstrates how to inherit and implement strategy logic
Includes startup files, Dockerfile, and configuration examples

You’ll build your own vol-momentum/ following the same structure.


Your Task

Create a new strategy template that inherits from the BaseStrategy interface.

Deliverables:

1. Folder: vol-momentum/
Must include exactly these files:

vol-momentum/
├─ vol-momentum.py
├─ startup.py
├─ Dockerfile
├─ requirements.txt
└─ README.md

2. Folder: reports/
Must include:
reports/
├─ backtest_runner.py
├─ backtest_report pdf or markdown

Six-month backtest report (PnL, Sharpe ratio, drawdown)

3. File: trade_logic_explanation.py
Clear explanation of your trading logic

⚠️ Anything else will cause disqualification.

When you submit pdf with trade logic, In your message, include the GitHub account link



Evaluation Criteria

Highest total PnL wins
Maximum drawdown < 50%
At least 10 executed trades
Identical starting balance and fees for all participants
Realistic simulation with execution delay and transaction costs

Prizes

1st Place (Highest PnL):

$1,000 USD cash prize
Strategy integration into our production platform
Professional portfolio showcase with verified metrics

2nd & 3rd Place:

2nd Place: $300 USD, 3rd Place: $200 USD
Portfolio addition with verified backtest performance
Recognition in our strategy showcase section

Total Prize Pool: $1,500 USD

Contest Timeline

Registration Opens: Tonight
Submission Deadline: 3 weeks from launch
Backtesting Period: 1 week (automated)
Winner Announcement: 4 weeks from launch


Ideal Participants

Quantitative traders familiar with Python
Algorithmic trading developers
Data scientists with financial knowledge
Experienced programmers interested in market strategy design

Getting Started

Download the base-bot-template (provided upon registration).
Review the dca-bot-template example to understand the structure.
Build your own vol-momentum/ with custom trading logic.
Test locally using the provided backtesting tools.
Submit your complete strategy package before the deadline.

Fair Play & Verification

All strategies will be re-executed in a controlled backtesting environment.
Hardcoded data or manipulation of test results will lead to disqualification.
By submitting, you agree that winning strategies may be integrated into our SaaS platform.

Why Join

Clear and simple objective: highest PnL wins
Identical testing for all participants
Fully transparent evaluation process
Real infrastructure, not a toy example
Cash prizes only – no revenue-sharing or complex terms

This first-round contest aims to discover and reward talented algorithmic traders who can deliver profitable, production-ready strategies.

``` 
