# syntax=docker/dockerfile:1.7

############################
# 1) Build Vue frontend
############################
FROM node:20-bookworm-slim AS frontend-build
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build-only


############################
# 2) Python runtime
############################
FROM python:3.11-slim-bookworm AS runtime
WORKDIR /app

# System deps:
# - ffmpeg: audio extraction + keyframes tooling
# - cairo/pango/gdk-pixbuf: weasyprint runtime deps
# - libgl1/libglib2.0-0: opencv runtime deps
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    tini \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    libgl1 \
    shared-mime-info \
    fonts-dejavu-core \
  && rm -rf /var/lib/apt/lists/*

# Python runtime env
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    XDG_CACHE_HOME=/app/.cache \
    HF_HOME=/app/.cache/huggingface

# Install Python deps first (better docker layer caching)
COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
  && pip install -r requirements.txt \
  && pip install gunicorn==22.0.0

# Copy backend code
COPY api/ ./api/
COPY src/ ./src/
COPY config.yaml ./config.yaml

# Copy built frontend dist into the location Flask expects
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Runtime dirs (can be bind-mounted/volumes in production)
RUN mkdir -p /app/data /app/output /app/.cache

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000

# Default: prefetch Whisper model on startup, then serve API+frontend via gunicorn.
ENTRYPOINT ["/usr/bin/tini","--","/entrypoint.sh"]
CMD ["gunicorn","-w","2","-b","0.0.0.0:5000","api.app:create_app()"]

