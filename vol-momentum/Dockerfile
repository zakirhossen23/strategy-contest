FROM python:3.11-slim
WORKDIR /app

# Copy base infra and this template
COPY ../base-bot-template/ /app/base-bot-template/
COPY . /app/vol-momentum/

RUN pip install --no-cache-dir -r /app/base-bot-template/requirements.txt || true
RUN pip install --no-cache-dir -r /app/vol-momentum/requirements.txt || true

CMD ["python", "vol-momentum/startup.py"]
