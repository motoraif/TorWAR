#!/bin/bash

echo "🚀 Starting TorWAR Production Server"
echo "===================================="

# Fix AWS credentials permissions
if [ -d "/home/torwar/.aws" ]; then
    echo "🔧 Fixing AWS credentials permissions..."
    # Copy credentials to writable location if needed
    if [ ! -r "/home/torwar/.aws/credentials" ]; then
        echo "⚠️  AWS credentials not readable by torwar user"
    fi
fi

# Wait for database
echo "⏳ Waiting for database..."
until pg_isready -h db -p 5432 -U torwar; do
  sleep 2
done
echo "✅ Database ready"

# Initialize database if needed
python3 -c "
from database_config import create_app, init_database
app, db, migrate = create_app()
with app.app_context():
    init_database()
"

# Start with Gunicorn for production
echo "🌐 Starting production server..."
exec gunicorn \
    --bind 0.0.0.0:5001 \
    --workers 2 \
    --threads 4 \
    --timeout 30 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    app_with_auth:app
