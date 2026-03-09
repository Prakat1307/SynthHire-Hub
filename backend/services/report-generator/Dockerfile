FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY backend/shared /tmp/shared
RUN pip install --no-cache-dir /tmp/shared && rm -rf /tmp/shared

COPY backend/services/report-generator/requirements.txt .
RUN sed -i '/shared/d' requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/services/report-generator/app /app/app

EXPOSE 8009

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8009"]
