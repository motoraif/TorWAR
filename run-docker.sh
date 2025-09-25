#!/bin/bash

echo "🚀 Starting TorWAR Multi-Container Setup..."
echo "📦 Services: Application + PostgreSQL + Redis"

# Build and run with docker-compose
docker-compose up --build -d

echo ""
echo "✅ TorWAR is running at http://localhost:5000"
echo "🗄️  PostgreSQL database running on port 5432"
echo "🔴 Redis cache running on port 6379"
echo ""
echo "📊 View logs: docker-compose logs -f torwar"
echo "🔍 Check status: docker-compose ps"
echo "🛑 Stop all: docker-compose down"
echo "🗑️  Clean up: docker-compose down -v (removes data volumes)"
