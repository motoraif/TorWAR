#!/bin/bash

echo "🚀 Starting TorWAR Database Application with Docker"
echo "=================================================="
echo "📦 Services: TorWAR App + PostgreSQL + Redis"

# Build and run with docker-compose
docker compose up --build -d

echo ""
echo "✅ TorWAR is running at http://localhost:5001"
echo "🗄️  PostgreSQL database running on port 5432"
echo "🔴 Redis cache running on port 6379"
echo ""
echo "🔐 Features enabled:"
echo "   - User Authentication (Login/Signup)"
echo "   - PostgreSQL Database Storage"
echo "   - Redis Caching"
echo "   - AWS Data Synchronization"
echo ""
echo "📊 View logs: docker compose logs -f torwar"
echo "🔍 Check status: docker compose ps"
echo "🛑 Stop all: docker compose down"
echo "🗑️  Clean up: docker compose down -v (removes data volumes)"
