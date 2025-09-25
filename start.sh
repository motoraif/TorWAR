#!/bin/bash

echo "🚀 Starting TorWAR with Database Initialization"
echo "=============================================="

# Wait for database to be ready
echo "⏳ Waiting for database..."
until pg_isready -h db -p 5432 -U torwar; do
  echo "Database not ready, waiting..."
  sleep 2
done

echo "✅ Database is ready"

# Start the application (it will initialize the database)
echo "🌐 Starting TorWAR application..."
python3 app_with_auth.py
