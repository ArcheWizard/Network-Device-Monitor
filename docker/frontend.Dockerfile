# syntax=docker/dockerfile:1.6
# Minimal frontend (PyQt) image placeholder
# Note: GUI apps in containers require extra setup; keep as placeholder for now.
FROM python:3.11-slim
WORKDIR /app

# Install Qt/X11 runtime deps (and cache apt metadata with BuildKit)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libegl1 \
    libgles2 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxrandr2 \
    libxcb1 \
    libxcb-xinerama0 \
    libxcb-util1 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxi6 \
    libsm6 \
    libice6 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libdbus-1-3 \
    libfontconfig1 \
    libfreetype6 \
    libglib2.0-0 \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements first (better caching)
COPY frontend/pyqt/requirements.txt /app/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r /app/requirements.txt || true

# Copy application code last (changes most frequently)
COPY frontend/pyqt /app

CMD ["python", "src/app.py"]
