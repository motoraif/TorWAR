# TorWARTA - Well Architected Reviews & Trusted Advisor

A modern web application for conducting AWS Well-Architected Reviews and managing Trusted Advisor recommendations with AI-powered reporting.

## Features

### 1. Well Architected Reviews (WAR)
- 🔍 Interact with AWS Well-Architected Tool APIs
- 📝 Answer questions and generate comprehensive reports
- 💾 Store all data locally for offline access
- 📊 Track progress across multiple workloads

### 2. Trusted Advisor (TA) Management
- 🛡️ Fetch all TA recommendations automatically
- 🤖 AI-powered remediation plans using Amazon Bedrock
- 📋 Prioritize and track remediation efforts
- 📈 Monitor improvement over time

### 3. AI-Powered Reporting
- 🧠 Generate reports using Amazon Bedrock (cross-account)
- 📄 Executive summaries and detailed findings
- 🔄 Version control for report comparison
- 📊 Track improvements between assessments

### 4. Modern UI/UX
- 🎨 Modern design with Tailwind CSS
- 📱 Responsive design for all devices
- 🌙 Dark/light mode support
- ⚡ Real-time updates with Vue.js

## Quick Start

### Prerequisites
- Docker and Docker Compose
- AWS credentials configured
- Access to AWS Well-Architected Tool and Support APIs
- Amazon Bedrock access (for AI reporting)

### Deployment

1. **Clone and navigate to the project:**
   ```bash
   cd TorWAR
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials and settings
   ```

3. **Deploy with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   - Web Interface: http://localhost
   - API: http://localhost/api/
   - Default login: admin / password

## Architecture

### Services
- **TorWARTA App**: Flask application with Vue.js frontend
- **MongoDB**: Document database for storing reports and data
- **Redis**: Caching layer for performance
- **Nginx**: Reverse proxy with rate limiting and security headers

### Initialization Process
1. **Database Setup**: Creates indexes and collections
2. **Cache Initialization**: Configures Redis connections
3. **Admin User Creation**: Sets up default admin account
4. **Service Health Checks**: Ensures all components are ready

## API Endpoints

### Authentication
- `POST /login` - User authentication
- `GET /logout` - User logout

### Well Architected Reviews
- `GET /api/war/workloads` - List all workloads
- `GET /api/war/workload/<id>/answers` - Get workload answers
- `POST /api/war/answer` - Update workload answer

### Trusted Advisor
- `GET /api/ta/recommendations` - Get all TA recommendations
- `POST /api/ta/remediation-plan` - Create AI remediation plan

### Reports
- `POST /api/reports/generate` - Generate AI-powered report
- `GET /api/reports/versions` - List report versions
- `POST /api/reports/compare` - Compare two report versions

## Configuration

### Environment Variables
```bash
# Database
MONGODB_URI=mongodb://mongodb:27017/torwarta
REDIS_HOST=redis

# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Application
SECRET_KEY=your_secret_key
```

### AWS Permissions Required
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "wellarchitected:*",
                "support:DescribeTrustedAdvisorChecks",
                "support:DescribeTrustedAdvisorCheckResult",
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        }
    ]
}
```

## Data Storage

### Offline Access
- All WAR data stored in MongoDB
- TA recommendations cached locally
- Reports versioned for historical comparison
- Redis caching for performance

### Version Control
- Automatic versioning of all reports
- Compare reports across different time periods
- Track improvements and changes
- Export capabilities for external use

## Monitoring

### Health Checks
- Application health: `/health`
- Database connectivity monitoring
- Cache performance metrics
- API response time tracking

### Logging
- Application logs in `/app/logs`
- Access logs via Nginx
- Error tracking and alerting
- Performance monitoring

## Security

### Features
- Rate limiting on API endpoints
- Security headers (XSS, CSRF protection)
- Input validation and sanitization
- Secure session management

### Best Practices
- Regular security updates
- Encrypted data transmission
- Access control and authentication
- Audit logging

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run initialization
python init.py

# Start application
python app.py
```

### Testing
```bash
# Run health check
curl http://localhost/health

# Test API endpoints
curl -X GET http://localhost/api/war/workloads
```

## Support

For issues and questions:
1. Check the logs: `docker-compose logs torwarta`
2. Verify AWS credentials and permissions
3. Ensure all services are healthy: `docker-compose ps`

## License

MIT License - see LICENSE file for details.
