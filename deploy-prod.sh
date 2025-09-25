#!/bin/bash

echo "🚀 Deploying TorWAR Production Setup"
echo "===================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.prod .env
    echo "⚠️  Please update .env with secure values before deployment"
    exit 1
fi

# Generate SSL certificates if they don't exist
if [ ! -f ssl/cert.pem ]; then
    echo "🔐 Generating SSL certificates..."
    ./generate-ssl.sh
fi

# Deploy with production compose
echo "🐳 Starting production containers..."
docker-compose -f docker-compose.prod.yml up --build -d

echo ""
echo "✅ TorWAR Production deployed successfully!"
echo "🌐 Access: https://localhost"
echo "📊 Health: https://localhost/health"
echo ""
echo "📋 Management commands:"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop: docker-compose -f docker-compose.prod.yml down"
echo "  Scale: docker-compose -f docker-compose.prod.yml up --scale torwar=3 -d"
