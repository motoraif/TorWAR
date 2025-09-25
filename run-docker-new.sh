#!/bin/bash

echo "🚀 Starting TorWAR with Database Authentication"
echo "=============================================="

# Stop any existing containers
docker-compose -f docker-compose.new.yml down

# Build and start services
docker-compose -f docker-compose.new.yml up --build -d

echo ""
echo "✅ TorWAR is running at:"
echo "   - http://localhost:5001"
echo "   - http://172.23.40.210:5001"
echo ""
echo "🔐 Features enabled:"
echo "   - User Authentication (Login/Signup)"
echo "   - PostgreSQL Database Storage"
echo "   - Redis Caching"
echo "   - AWS Data Synchronization"
echo ""
echo "📊 View logs: docker-compose -f docker-compose.new.yml logs -f torwar"
echo "🔍 Check status: docker-compose -f docker-compose.new.yml ps"
echo "🛑 Stop all: docker-compose -f docker-compose.new.yml down"
