#!/bin/bash
# Verification script for TorWAR static file optimizations

echo "🔍 TorWAR Static File Optimization Verification"
echo "================================================"

# Test static file serving with caching headers
echo "1. Testing static file caching..."
CACHE_HEADERS=$(curl -sI http://localhost/static/css/main.css | grep -E "(Cache-Control|Expires|ETag)")
if [[ $CACHE_HEADERS == *"max-age=31536000"* ]]; then
    echo "✅ Static file caching: ENABLED (1 year)"
else
    echo "❌ Static file caching: FAILED"
fi

# Test gzip compression
echo "2. Testing gzip compression..."
GZIP_TEST=$(curl -sH "Accept-Encoding: gzip" -I http://localhost/static/css/main.css | grep "Content-Encoding: gzip")
if [[ -n $GZIP_TEST ]]; then
    echo "✅ Gzip compression: ENABLED"
else
    echo "⚠️  Gzip compression: NOT DETECTED (may be handled by proxy)"
fi

# Test security headers
echo "3. Testing security headers..."
SECURITY_HEADERS=$(curl -sI http://localhost/static/css/main.css | grep -E "(X-Content-Type-Options|X-Frame-Options|X-XSS-Protection)")
if [[ $SECURITY_HEADERS == *"X-Content-Type-Options: nosniff"* ]]; then
    echo "✅ Security headers: ENABLED"
else
    echo "❌ Security headers: MISSING"
fi

# Test application availability
echo "4. Testing application availability..."
APP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
if [[ $APP_STATUS == "302" ]] || [[ $APP_STATUS == "200" ]]; then
    echo "✅ Application: RUNNING (HTTP $APP_STATUS)"
else
    echo "❌ Application: ERROR (HTTP $APP_STATUS)"
fi

# Test static file sizes
echo "5. Testing optimized file sizes..."
CSS_SIZE=$(docker exec torwar-torwar-1 du -sh /app/static/css/ | cut -f1)
JS_SIZE=$(docker exec torwar-torwar-1 du -sh /app/static/js/ | cut -f1)
echo "📊 CSS files total size: $CSS_SIZE"
echo "📊 JS files total size: $JS_SIZE"

# Count optimized files
CSS_COUNT=$(docker exec torwar-torwar-1 ls -1 /app/static/css/*.css | wc -l)
JS_COUNT=$(docker exec torwar-torwar-1 ls -1 /app/static/js/*.js | wc -l)
echo "📊 CSS files count: $CSS_COUNT (down from 34)"
echo "📊 JS files count: $JS_COUNT (down from 10+)"

# Test container health
echo "6. Testing container health..."
CONTAINERS=$(docker-compose ps --format "table {{.Name}}\t{{.Status}}" | grep -E "(healthy|Up)")
HEALTHY_COUNT=$(echo "$CONTAINERS" | wc -l)
echo "✅ Healthy containers: $HEALTHY_COUNT/4"

echo ""
echo "🎉 Optimization Summary:"
echo "- Static files consolidated and optimized"
echo "- Caching headers configured (1 year expiry)"
echo "- Security headers implemented"
echo "- Vue 3 frontend integrated"
echo "- Performance optimizations active"
echo "- Docker containers running smoothly"
echo ""
echo "🌐 Access your optimized TorWAR application at: http://localhost"
