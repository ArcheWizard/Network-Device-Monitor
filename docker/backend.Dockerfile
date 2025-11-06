FROM python:3.11-slim
WORKDIR /app

# Install system dependencies including ping
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements/ /app/requirements/
RUN pip install --no-cache-dir -r /app/requirements/dev.txt
COPY backend /app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]