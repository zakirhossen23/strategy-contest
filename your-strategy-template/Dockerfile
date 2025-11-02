FROM python:3.11-slim
WORKDIR /app

# Copy base infra and this template
COPY ../base-bot-template/ /app/base-bot-template/
COPY . /app/your-strategy-template/

RUN pip install --no-cache-dir -r /app/base-bot-template/requirements.txt || true
RUN pip install --no-cache-dir -r /app/your-strategy-template/requirements.txt || true

CMD ["python", "your-strategy-template/startup.py"]
