#!/bin/bash

# TorWAR Database Application Startup Script

echo "🚀 Starting TorWAR with PostgreSQL Database"
echo "=========================================="

# Set environment variables
export DATABASE_URL='postgresql://torwar:torwar123@localhost/torwar_db'
export SECRET_KEY='torwar-production-secret-key-change-me'

# Check if PostgreSQL is running
if ! systemctl is-active --quiet postgresql; then
    echo "📊 Starting PostgreSQL service..."
    sudo systemctl start postgresql
fi

# Check if Redis is running (for caching)
if ! systemctl is-active --quiet redis-server; then
    echo "🔄 Starting Redis service..."
    sudo systemctl start redis-server
fi

echo "✅ Services started"
echo "🌐 Application will be available at:"
echo "   - http://localhost:5001"
echo "   - http://172.23.40.210:5001"
echo ""
echo "🔐 Features enabled:"
echo "   - User Authentication (Login/Signup)"
echo "   - PostgreSQL Database Storage"
echo "   - Redis Caching"
echo "   - AWS Data Synchronization"
echo ""
echo "📝 First time? Create an account at the signup page"
echo "🔄 Press Ctrl+C to stop the application"
echo ""

# Start the application
cd /home/toraif/TorWAR
python3 app_with_auth.py
