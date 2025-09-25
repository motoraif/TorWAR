# 🛡️ TorWAR - Containerized AWS Well-Architected Review Tool

A production-ready containerized application for conducting AWS Well-Architected Framework reviews with enterprise security and performance optimizations.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- AWS CLI configured with appropriate permissions
- Git

### Deployment

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd TorWAR
   cp .env.example .env
   # Edit .env with your secure values
   ```

2. **Development deployment:**
   ```bash
   ./run-docker-new.sh
   # Access: http://localhost:5001
   ```

3. **Production deployment:**
   ```bash
   ./deploy-prod.sh
   # Access: https://localhost (with SSL)
   ```

## 🏗️ Architecture

- **Application**: Flask with Gunicorn WSGI server
- **Database**: PostgreSQL 15 with performance tuning
- **Cache**: Redis with memory optimization
- **Proxy**: Nginx with SSL termination and security headers
- **Security**: Non-root execution, rate limiting, HTTPS enforcement

## 📊 Features

- ✅ AWS Well-Architected Framework reviews
- ✅ Multi-account AWS support
- ✅ User authentication and session management
- ✅ Report generation and comparison
- ✅ Trusted Advisor integration
- ✅ Production-ready containerization
- ✅ SSL/TLS encryption
- ✅ Health monitoring endpoints

## 🔧 Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:
- `DB_PASSWORD`: Secure database password
- `SECRET_KEY`: Application secret key (32+ characters)

### AWS Credentials
Mount your AWS credentials directory:
- Development: `~/.aws` mounted read-only
- Production: Ensure proper IAM permissions for Well-Architected Tool access

## 📋 Management Commands

```bash
# Development
docker-compose -f docker-compose.new.yml logs -f
docker-compose -f docker-compose.new.yml ps
docker-compose -f docker-compose.new.yml down

# Production
docker-compose -f docker-compose.prod.yml logs -f
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml down
```

## 🔐 Security Features

- Multi-stage Docker builds for minimal attack surface
- Non-root container execution
- SSL/TLS termination with modern cipher suites
- Security headers (HSTS, XSS protection, etc.)
- Rate limiting and request throttling
- Secrets management via environment variables

## ⚡ Performance Optimizations

- Gunicorn with optimized worker configuration
- PostgreSQL performance tuning
- Redis caching with memory limits
- Nginx compression and HTTP/2
- Resource limits and health checks

## 📖 Documentation

- `PRODUCTION-SETUP.md`: Production deployment guide
- `CONTAINERIZATION-SUCCESS.md`: Containerization details
- `.env.example`: Environment configuration template

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Created by Mohamed Toraif** | **Production-Ready Containerization**
