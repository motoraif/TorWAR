# 🐳 TorWAR Docker Deployment Guide

## Quick Start

### 1. Build and Start
```bash
./docker-manage.sh build
./docker-manage.sh start
```

### 2. Access Application
Open your browser: **http://localhost:5000**

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- AWS credentials configured (`~/.aws/credentials`)

## Installation

### Option 1: Using Management Script (Recommended)

```bash
# Build the image
./docker-manage.sh build

# Start the container
./docker-manage.sh start

# View logs
./docker-manage.sh logs

# Check status
./docker-manage.sh status

# Stop the container
./docker-manage.sh stop

# Restart
./docker-manage.sh restart

# Access container shell
./docker-manage.sh shell

# Clean up everything
./docker-manage.sh clean
```

### Option 2: Using Docker Compose Directly

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build
```

### Option 3: Using Docker CLI

```bash
# Build image
docker build -t torwar:latest .

# Run container
docker run -d \
  --name torwar \
  -p 5000:5000 \
  -v ~/.aws:/root/.aws:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -e AWS_DEFAULT_REGION=us-east-1 \
  torwar:latest

# View logs
docker logs -f torwar

# Stop and remove
docker stop torwar && docker rm torwar
```

## Configuration

### Environment Variables

Create a `.env` file (copy from `.env.docker`):

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
DEBUG=False
PORT=5000

# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
AWS_PROFILE=default

# Application Settings
AUTO_SAVE_INTERVAL=300
MAX_REPORTS_PER_WORKLOAD=10
```

### AWS Credentials

The container mounts your AWS credentials from `~/.aws/`:

```bash
# Ensure your credentials are configured
aws configure

# Or use a specific profile
export AWS_PROFILE=your-profile-name
```

## Volume Mounts

The container uses the following volumes:

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./data` | `/app/data` | Reports and workload data |
| `./logs` | `/app/logs` | Application logs |
| `~/.aws` | `/root/.aws` | AWS credentials (read-only) |

## Networking

- **Port 5000**: Web application interface
- **Network**: `torwar-network` (bridge)

## Health Checks

The container includes automatic health checks:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' torwar-app

# Manual health check
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "TorWAR",
  "timestamp": "2026-02-02T12:00:00Z"
}
```

## Production Deployment

### Using Gunicorn (Default)

The container runs with Gunicorn by default:
- 4 workers
- 120s timeout
- Binds to 0.0.0.0:5000

### Custom Configuration

Override the CMD in `docker-compose.yml`:

```yaml
services:
  torwar:
    command: gunicorn --bind 0.0.0.0:5000 --workers 8 --timeout 300 app:app
```

### Behind a Reverse Proxy

#### Nginx Example

```nginx
server {
    listen 80;
    server_name torwar.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Traefik Example

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.torwar.rule=Host(`torwar.example.com`)"
  - "traefik.http.services.torwar.loadbalancer.server.port=5000"
```

## Troubleshooting

### Container won't start

```bash
# Check logs
./docker-manage.sh logs

# Check Docker status
docker ps -a

# Rebuild from scratch
./docker-manage.sh clean
./docker-manage.sh build
./docker-manage.sh start
```

### AWS credentials not working

```bash
# Verify credentials are mounted
docker exec torwar-app ls -la /root/.aws

# Test AWS connection
docker exec torwar-app aws sts get-caller-identity

# Check environment variables
docker exec torwar-app env | grep AWS
```

### Permission issues

```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/ logs/

# Recreate directories
mkdir -p data/reports/metadata data/reports/workloads data/workloads logs
```

### Port already in use

```bash
# Find what's using port 5000
sudo lsof -i :5000

# Change port in docker-compose.yml
ports:
  - "8080:5000"  # Use port 8080 instead
```

## Monitoring

### View Logs

```bash
# Real-time logs
./docker-manage.sh logs

# Last 100 lines
docker-compose logs --tail=100

# Specific service logs
docker logs torwar-app
```

### Resource Usage

```bash
# Container stats
docker stats torwar-app

# Detailed info
docker inspect torwar-app
```

## Backup and Restore

### Backup Data

```bash
# Backup reports and workloads
tar -czf torwar-backup-$(date +%Y%m%d).tar.gz data/

# Backup to S3
aws s3 cp torwar-backup-*.tar.gz s3://your-bucket/backups/
```

### Restore Data

```bash
# Extract backup
tar -xzf torwar-backup-20260202.tar.gz

# Restart container
./docker-manage.sh restart
```

## Scaling

### Multiple Instances

```bash
# Scale to 3 instances
docker-compose up -d --scale torwar=3

# Use a load balancer (nginx, traefik, etc.)
```

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  torwar:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Security Best Practices

1. **Change the secret key** in production
2. **Use read-only AWS credentials** when possible
3. **Run behind HTTPS** with a reverse proxy
4. **Limit container resources** to prevent DoS
5. **Regular updates**: Rebuild images with latest dependencies
6. **Scan for vulnerabilities**:
   ```bash
   docker scan torwar:latest
   ```

## Updates

### Update Application

```bash
# Pull latest code
git pull origin containerization

# Rebuild and restart
./docker-manage.sh stop
./docker-manage.sh build
./docker-manage.sh start
```

### Update Dependencies

```bash
# Update requirements.txt
# Then rebuild
./docker-manage.sh build
```

## Development Mode

For development with hot-reload:

```yaml
# docker-compose.dev.yml
services:
  torwar:
    build: .
    volumes:
      - .:/app
    environment:
      - FLASK_ENV=development
      - DEBUG=True
    command: flask run --host=0.0.0.0 --port=5000 --reload
```

Run with:
```bash
docker-compose -f docker-compose.dev.yml up
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/motoraif/TorWAR/issues
- Documentation: See README.md

---

**Created by Mohamed Toraif**
