FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional database and cache dependencies
RUN pip install --no-cache-dir psycopg2-binary redis

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/reports logs

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV SECRET_KEY=containerized-torwar-secret-key-change-in-production

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
