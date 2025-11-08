# Trend Follower Bot Template - Dockerfile
FROM python:3.11-slim

LABEL description="Trend Follower Trading Bot with Dashboard Integration"
LABEL strategies="trend_follower"
LABEL tier="basic"

# Set working directory
WORKDIR /app

# Copy base bot infrastructure
COPY base-bot-template/ /app/base/

# Copy trend follower-specific files
COPY trend-follower/ /app/

# Install dependencies
RUN pip install --no-cache-dir -r /app/base/requirements.txt

# Make startup script executable
RUN chmod +x /app/startup.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Expose ports
EXPOSE 8080 3010

# Default environment
ENV BOT_EXCHANGE=paper
ENV BOT_STRATEGY=trend_follower
ENV BOT_SYMBOL=BTC-USD
ENV BOT_STARTING_CASH=10000.0
ENV BOT_SLEEP=3600

# Start the trend follower bot
CMD ["python", "/app/startup.py"]