# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=5000 \
    DATA_DIR=/app/data \
    LOG_DIR=/app/logs \
    HOME=/home/torwar

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create torwar user and home directory
RUN groupadd -g 1000 torwar && \
    useradd -u 1000 -g 1000 -m -d /home/torwar -s /bin/bash torwar && \
    mkdir -p /home/torwar/.aws

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/data/reports /app/data/workloads /app/logs && \
    chmod +x docker-entrypoint.sh && \
    chown -R torwar:torwar /app /home/torwar

# Switch to torwar user
USER torwar

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Use entrypoint script
ENTRYPOINT ["./docker-entrypoint.sh"]
