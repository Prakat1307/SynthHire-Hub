FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY backend/shared /tmp/shared
RUN pip install --no-cache-dir /tmp/shared && rm -rf /tmp/shared

COPY backend/services/emotion-analysis/requirements.txt .
RUN sed -i '/shared/d' requirements.txt
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

COPY ml /app/ml

COPY backend/services/emotion-analysis/app /app/app

EXPOSE 8007

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
