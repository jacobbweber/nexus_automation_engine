# syntax=docker/dockerfile:1

# --- Stage 1: build the frontend ------------------------------------------------------------
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: backend runtime ---------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Rootless, OpenShift-SCC-friendly: run as an arbitrary non-root UID.
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NEXUS_STATIC_DIR=/app/static \
    NEXUS_DATABASE_URL=sqlite:////data/nexus.db

WORKDIR /app
COPY backend/pyproject.toml ./backend/
COPY backend/app ./backend/app
RUN pip install ./backend

# Built SPA served by the API at "/".
COPY --from=frontend /app/frontend/dist /app/static

# Writable state dir for the SQLite database (works with random OpenShift UIDs).
RUN mkdir -p /data && chgrp -R 0 /data /app && chmod -R g=u /data /app
USER 1001

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
