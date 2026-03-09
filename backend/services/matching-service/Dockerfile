FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/app/backend

COPY backend/services/matching-service/requirements.txt .
RUN sed -i '/shared/d' requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/services/matching-service/app /app/app

EXPOSE 8015

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8015"]
