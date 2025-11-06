# Minimal backend image (placeholder)
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements/ /app/requirements/
RUN pip install --no-cache-dir -r /app/requirements/dev.txt
COPY backend /app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
