# Simplified Docker build for NASDAQ-100 Screener
FROM python:3.12-slim

LABEL maintainer="smoki99 <nasdaq-screener@github.com>"
LABEL version="1.0.0"
LABEL description="NASDAQ-100 Stock Screener - Multi-factor analysis tool with Novy-Marx methodology"
LABEL org.opencontainers.image.source="https://github.com/smoki99/value_screener"
LABEL org.opencontainers.image.description="Production container for NASDAQ-100 Stock Screener with Flask API and web interface"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production

# Logging Configuration (can be overridden at runtime)
# LOG_LEVEL: Set to DEBUG, INFO, WARNING, ERROR, or CRITICAL
# Default: INFO (suitable for production)
ENV LOG_LEVEL=INFO

WORKDIR /app

# Install Node.js runtime and curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nodejs \
        npm \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files FIRST (cached when deps don't change)
COPY requirements.txt .

# Create virtual environment and install dependencies (CACHED LAYER)
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy project source code LAST (changes here don't invalidate dependency layers)
COPY . .

# Create cache directory for SQLite database (volume mount point)
VOLUME ["/app/cache"]

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command: activate venv and run server
CMD ["bash", "-c", ". venv/bin/activate && python -u server/app.py"]
