FROM python:3.11-slim
WORKDIR /app

# Copy only the template and the base framework necessary to run the bot
COPY base-bot-template/ base-bot-template/
COPY ma_crossover/ ma_crossover/

# Install minimal deps
RUN pip install --no-cache-dir -r base-bot-template/requirements.txt || true
RUN pip install --no-cache-dir -r ma_crossover/requirements.txt || true

# Run the template startup by default
CMD ["python", "ma_crossover/startup.py"]
