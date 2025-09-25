# 🐳 TorWAR Multi-Container Deployment

## Architecture

- **Application**: TorWAR Flask app (Port 5000)
- **Database**: PostgreSQL 15 (Port 5432)
- **Cache**: Redis 7 (Port 6379)

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/motoraif/TorWAR.git
   cd TorWAR
   ```

2. **Run multi-container setup:**
   ```bash
   ./run-docker.sh
   ```

3. **Access the application:**
   - Open http://localhost:5000 in your browser

## Manual Docker Commands

**Build and run all services:**
```bash
docker-compose up --build -d
```

**View logs:**
```bash
docker-compose logs -f torwar    # Application logs
docker-compose logs -f db        # Database logs
docker-compose logs -f redis     # Redis logs
```

**Check service status:**
```bash
docker-compose ps
```

**Stop all services:**
```bash
docker-compose down
```

**Clean up (removes data volumes):**
```bash
docker-compose down -v
```

## Services

### Application (torwar)
- **Port**: 5000
- **Environment**: Production-ready Flask app
- **Dependencies**: PostgreSQL + Redis

### Database (db)
- **Image**: PostgreSQL 15 Alpine
- **Port**: 5432 (internal)
- **Database**: torwar
- **User**: torwar
- **Persistent**: Data stored in `postgres_data` volume

### Cache (redis)
- **Image**: Redis 7 Alpine
- **Port**: 6379 (internal)
- **Persistent**: Data stored in `redis_data` volume

## Data Persistence

- **Application data**: `./data` directory (mounted as volume)
- **Application logs**: `./logs` directory (mounted as volume)
- **Database data**: `postgres_data` Docker volume
- **Redis data**: `redis_data` Docker volume
- **AWS credentials**: `~/.aws/` (mounted read-only)

## Configuration

Environment variables can be customized in `docker-compose.yml`:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Flask secret key

## Fresh Installation

The multi-container setup provides:
- ✅ Clean, isolated environment
- ✅ Persistent data storage
- ✅ Scalable architecture
- ✅ Production-ready configuration
