# Multi-stage Docker build for NASDAQ-100 Screener
# Stage 1: Python dependencies builder
FROM python:3.12-slim AS python-builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Node.js dependencies builder
FROM node:20-alpine AS node-builder

WORKDIR /app
COPY package.json ./
RUN npm install --only=production --no-audit --no-fund

# Stage 3: Runtime image (minimal)
FROM python:3.12-slim

LABEL maintainer="NASDAQ-100 Screener"
LABEL description="Production container for NASDAQ-100 Stock Screener"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production

# Logging Configuration (can be overridden at runtime)
# LOG_LEVEL: Set to DEBUG, INFO, WARNING, ERROR, or CRITICAL
# Default: INFO (suitable for production)
ENV LOG_LEVEL=INFO

WORKDIR /app

# Install Node.js runtime (for any JS dependencies)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nodejs \
        npm \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder (cached layer)
COPY --from=python-builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy Node.js modules from builder (cached layer)
COPY --from=node-builder /app/node_modules ./node_modules

# Copy dependency files FIRST (for venv installation - cached when deps don't change)
COPY requirements.txt .

# Create virtual environment and install dependencies (CACHED LAYER)
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# Copy project source code LAST (changes here don't invalidate dependency layers)
COPY . .

# Create cache directory for SQLite database (volume mount point)
VOLUME ["/app/cache"]

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command: run tests first, then start server
CMD ["python", "-u", "server/app.py"]
