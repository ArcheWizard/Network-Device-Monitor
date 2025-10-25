# Minimal frontend (PyQt) image placeholder
# Note: GUI apps in containers require extra setup; keep as placeholder for now.
FROM python:3.11-slim
WORKDIR /app
COPY frontend/pyqt/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt || true
COPY frontend/pyqt /app
CMD ["python", "src/app.py"]
