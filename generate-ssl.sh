#!/bin/bash

echo "🔐 Generating SSL certificates for TorWAR"

mkdir -p ssl

# Generate self-signed certificate for development/testing
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=BH/ST=Bahrain/L=Manama/O=TorWAR/CN=localhost"

chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem

echo "✅ SSL certificates generated in ./ssl/"
echo "⚠️  For production, replace with proper certificates"
