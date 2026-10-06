FROM python:3.12-slim

WORKDIR /home/ubuntu/trendguard

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY panel/requirements.txt ./panel/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r panel/requirements.txt

COPY bot.py config.py indicators.py strategy.py notifier.py ./
COPY panel/ ./panel/

ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Berlin

# Sin CMD por defecto — cada contenedor lo define en docker-compose.yml
