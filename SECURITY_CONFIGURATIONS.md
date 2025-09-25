# 🔧 TorWAR Security Configuration Examples

## 🚀 Quick Configuration Commands

```bash
# Show current configuration
python3 configure_security.py show

# Generate new secret keys
python3 configure_security.py secrets

# Validate configuration
python3 configure_security.py validate

# Configure for production
python3 configure_security.py production

# Configure for development
python3 configure_security.py development

# Create environment template
python3 configure_security.py template
```

## 🏠 Development Environment

```bash
# .env for development
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production
HTTPS_ENABLED=false
SECURE_COOKIES=false
DEBUG_SECURITY=true
RATE_LIMIT_GLOBAL=1000
RATE_LIMIT_AUTH=50
FAILED_LOGIN_THRESHOLD=20
```

## 🏢 Production Environment

```bash
# .env for production
SECRET_KEY=c4d89de983b5552970ad33594e7df5a29e38bd5a4712cad2727c1792a9295ecc
JWT_SECRET_KEY=4ff57e7891077c5305f45417eb9dba2a2a9d4d6e08ec537eb4f85779f2f6a8af
HTTPS_ENABLED=true
FORCE_HTTPS=true
SECURE_COOKIES=true
DEBUG_SECURITY=false
RATE_LIMIT_GLOBAL=100
RATE_LIMIT_AUTH=5
FAILED_LOGIN_THRESHOLD=5
IP_BLOCK_DURATION=600
REDIS_URL=redis://redis:6379/0
```

## 🧪 Testing Environment

```bash
# .env for testing
SECRET_KEY=test-secret-key-for-testing-only
JWT_SECRET_KEY=test-jwt-secret-for-testing-only
HTTPS_ENABLED=false
DISABLE_CSRF_IN_DEV=true
RATE_LIMIT_GLOBAL=10000
RATE_LIMIT_AUTH=1000
FAILED_LOGIN_THRESHOLD=100
DEBUG_SECURITY=true
```

## 🌐 High-Traffic Production

```bash
# .env for high-traffic production
SECRET_KEY=your-production-secret-key
JWT_SECRET_KEY=your-production-jwt-secret
HTTPS_ENABLED=true
FORCE_HTTPS=true
SECURE_COOKIES=true
RATE_LIMIT_GLOBAL=500
RATE_LIMIT_AUTH=20
RATE_LIMIT_API=200
FAILED_LOGIN_THRESHOLD=3
IP_BLOCK_DURATION=1800
REDIS_URL=redis://redis-cluster:6379/0
```

## 🔒 Maximum Security Environment

```bash
# .env for maximum security
SECRET_KEY=ultra-secure-secret-key-64-chars-minimum
JWT_SECRET_KEY=ultra-secure-jwt-secret-key-64-chars-minimum
JWT_EXPIRY_HOURS=1
SESSION_TIMEOUT=900
HTTPS_ENABLED=true
FORCE_HTTPS=true
SECURE_COOKIES=true
RATE_LIMIT_GLOBAL=50
RATE_LIMIT_AUTH=3
RATE_LIMIT_API=30
FAILED_LOGIN_THRESHOLD=3
IP_BLOCK_DURATION=3600
SUSPICIOUS_REQUEST_THRESHOLD=50
CSRF_TIME_LIMIT=1800
```

## 🐳 Docker Configuration

```yaml
# docker-compose.yml
version: '3.8'
services:
  torwar:
    build: .
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - HTTPS_ENABLED=true
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://torwar:${DB_PASSWORD}@db:5432/torwar
    depends_on:
      - redis
      - db
  
  redis:
    image: redis:alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
```

## ☁️ AWS Deployment Configuration

```bash
# .env for AWS deployment
SECRET_KEY=${AWS_SECRET_MANAGER_SECRET_KEY}
JWT_SECRET_KEY=${AWS_SECRET_MANAGER_JWT_KEY}
HTTPS_ENABLED=true
FORCE_HTTPS=true
SECURE_COOKIES=true
REDIS_URL=${AWS_ELASTICACHE_ENDPOINT}
DATABASE_URL=${AWS_RDS_ENDPOINT}
RATE_LIMIT_GLOBAL=200
SECURITY_LOG_FILE=/var/log/torwar/security.log
```

## 🔧 Runtime Configuration Changes

```python
# Programmatic configuration
from security_configurator import security_config

# Update rate limits
security_config.update_config('RATE_LIMIT_GLOBAL', 200)
security_config.update_config('RATE_LIMIT_AUTH', 10)

# Enable production mode
security_config.update_config('HTTPS_ENABLED', True)
security_config.update_config('SECURE_COOKIES', True)

# Validate changes
issues = security_config.validate_config()
if issues:
    print("Configuration issues:", issues)
```

## 📊 Configuration Monitoring

```bash
# Check configuration status
curl http://localhost:5000/api/security/stats

# Response example:
{
  "blocked_ips": 0,
  "active_request_signatures": 5,
  "monitored_ips": 3,
  "active_sessions": 2,
  "csrf_enabled": true,
  "rate_limiting_enabled": true
}
```

## 🔍 Configuration Validation

```bash
# Validate current configuration
python3 configure_security.py validate

# Check specific settings
python3 -c "
from security_configurator import security_config
config = security_config.config

print('Secret Key Length:', len(config['SECRET_KEY']))
print('HTTPS Enabled:', config['HTTPS_ENABLED'])
print('Rate Limits:', {
    'global': config['RATE_LIMIT_GLOBAL'],
    'auth': config['RATE_LIMIT_AUTH']
})
"
```

## 🚨 Security Alerts Configuration

```bash
# Configure security monitoring
SECURITY_LOG_LEVEL=WARNING
FAILED_LOGIN_THRESHOLD=5
IP_BLOCK_DURATION=600

# Log suspicious activities
SUSPICIOUS_REQUEST_THRESHOLD=100
SECURITY_LOG_FILE=logs/security.log
AUTH_LOG_FILE=logs/auth_failures.log
```

## 🔄 Configuration Hot Reload

```python
# Hot reload configuration without restart
from security_configurator import security_config

# Reload from environment
security_config._load_config()

# Apply new Flask config
app.config.update(security_config.get_flask_config())
```
