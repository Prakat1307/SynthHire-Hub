FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY backend/shared /tmp/shared
RUN pip install --no-cache-dir /tmp/shared && rm -rf /tmp/shared

COPY ml /app/ml
RUN cd /app/ml && pip install --default-timeout=1000 -e .

COPY backend/services/assessment-engine/requirements.txt .
RUN sed -i '/shared/d' requirements.txt
RUN sed -i '/ml/d' requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/services/assessment-engine/app /app/app

EXPOSE 8006

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
