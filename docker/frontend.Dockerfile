# Minimal frontend (PyQt) image placeholder
# Note: GUI apps in containers require extra setup; keep as placeholder for now.
FROM python:3.11-slim
WORKDIR /app

# Install system libraries required by PyQt / Qt (provides libGL.so.1)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libx11-6 \
    libxcb1 \
    libxrender1 \
    libxrandr2 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY frontend/pyqt/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt || true
COPY frontend/pyqt /app
CMD ["python", "src/app.py"]
