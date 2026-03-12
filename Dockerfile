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

WORKDIR /app

# Install Node.js runtime (for any JS dependencies)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nodejs \
        npm \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=python-builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy Node.js modules from builder
COPY --from=node-builder /app/node_modules ./node_modules

# Copy project source code
COPY . .

# Create virtual environment and install dependencies fresh
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# Create cache directory for SQLite database (volume mount point)
VOLUME ["/app/cache"]

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command: run tests first, then start server
CMD ["./test.sh"]
