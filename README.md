# SocialPulse - Instagram Follower Monitoring

FastAPI-based system for monitoring Instagram follower counts with automated milestone alerts via Telegram. Uses Clean Architecture with async PostgreSQL, Celery background tasks, and comprehensive analytics.

## Architecture

**Core Stack:**
- FastAPI with async/await throughout
- PostgreSQL 15+ with asyncpg driver
- Redis for Celery broker and caching
- Celery for background monitoring tasks
- aiograpi for Instagram API integration
- Telegram Bot API for notifications

**Service Architecture:**
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   FastAPI   │    │    Celery    │    │ PostgreSQL  │
│     App     │◄──►│   Workers    │◄──►│  Database   │
└─────────────┘    └──────────────┘    └─────────────┘
       │                   │                   
       ▼                   ▼                   
┌─────────────┐    ┌──────────────┐            
│    Redis    │    │  Instagram   │            
│   Broker    │    │     API      │            
└─────────────┘    └──────────────┘            
```

**Layer Structure:**
- **API Layer**: FastAPI routes, schemas, dependencies
- **Service Layer**: Business logic, analytics, monitoring
- **Infrastructure**: Database repositories, external APIs
- **Core**: Entities, interfaces, exceptions

## Setup

**Prerequisites:**
- Docker and Docker Compose
- Instagram account credentials
- Telegram bot token (from @BotFather)

**Environment Configuration:**
```bash
cp env.example .env
# Edit .env with your credentials
```

**Production Deployment:**
```bash
docker compose up -d
```

**Development Setup:**
```bash
docker compose -f docker-compose.dev.yml up -d
# Includes hot-reload, debugging ports, and dev tools
```

**Development Tools (Optional):**
```bash
docker compose -f docker-compose.dev.yml --profile tools up -d
# Adds pgAdmin (localhost:5050) and Redis Commander (localhost:8081)
```

## Configuration

**Required Environment Variables:**
```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/socialpulse
SECRET_KEY=your-jwt-secret-key-32-chars-minimum
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

**Service Endpoints:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## API Usage

**Authentication:**
```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'
```

**Profile Management:**
```bash
# Add Instagram profile
curl -X POST http://localhost:8000/profiles/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"instagram_username","display_name":"My Profile"}'

# List profiles
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/profiles/
```

**Analytics:**
```bash
# User dashboard
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/insights/dashboard

# Profile growth analysis
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/insights/profiles/username/growth?days=30"

# Top changes
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/insights/my-top-changes?period=7d"
```

**Alerts:**
```bash
# Create milestone alert
curl -X POST http://localhost:8000/api/alerts/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profile_username":"username","threshold":1000,"message":"Reached 1K!"}'
```

## Development

**Local Development:**
```bash
# Start development environment
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.dev.yml logs -f app

# Run tests
docker compose -f docker-compose.dev.yml exec app python -m pytest

# Database migrations
docker compose -f docker-compose.dev.yml exec app alembic upgrade head
```

**Code Structure:**
```
app/
├── api/           # FastAPI routes and schemas
├── core/          # Domain entities and interfaces
├── services/      # Business logic layer
└── infrastructure/ # Database and external APIs
```

**Testing:**
```bash
# Analytics system test
python test_analytics.py

# Create sample data
python test_analytics.py --create-data
```

## Deployment

**Production Checklist:**
- [ ] Set strong SECRET_KEY (32+ characters)
- [ ] Configure Instagram credentials
- [ ] Set up Telegram bot
- [ ] Review resource limits in docker-compose.yml
- [ ] Set up log aggregation
- [ ] Configure backup strategy for PostgreSQL
- [ ] Set up monitoring and alerting

**Scaling Considerations:**
- Increase Celery worker concurrency for higher throughput
- Add Redis Cluster for high availability
- Use PostgreSQL read replicas for analytics queries
- Implement rate limiting for Instagram API calls

**Health Monitoring:**
```bash
# Check service health
curl http://localhost:8000/health

# Monitor Celery workers
docker compose exec worker celery -A app.infrastructure.background_tasks.celery_app inspect active

# Database connection test
docker compose exec db pg_isready -U postgres
```

## Monitoring

**Service Health Checks:**
- FastAPI: `/health` endpoint
- PostgreSQL: `pg_isready` command
- Redis: `redis-cli ping`
- Celery: Built-in worker monitoring

**Key Metrics:**
- Instagram API rate limits and response times
- Celery task queue length and processing time
- Database connection pool usage
- Memory and CPU usage per service

**Logs:**
```bash
# Application logs
docker compose logs -f app

# Worker logs
docker compose logs -f worker

# All services
docker compose logs -f
```

## Troubleshooting

**Common Issues:**

*Instagram Authentication Fails:*
- Verify credentials in .env file
- Check for 2FA requirements
- Review Instagram API rate limits

*Celery Tasks Not Processing:*
- Verify Redis connection
- Check worker logs for errors
- Ensure database connectivity

*Database Connection Issues:*
- Verify DATABASE_URL format
- Check PostgreSQL service health
- Review connection pool settings

*Telegram Notifications Not Sent:*
- Verify bot token validity
- Check user has started conversation with bot
- Review Telegram API rate limits

**Performance Issues:**
- Monitor Instagram API response times
- Check database query performance
- Review Celery worker concurrency settings
- Analyze memory usage patterns

## Dependencies

**Core:**
- FastAPI 0.104+
- SQLAlchemy 2.0+ with asyncpg
- Celery 5.3+ with Redis
- aiograpi for Instagram API
- python-telegram-bot for notifications

**Infrastructure:**
- PostgreSQL 15+
- Redis 7+
- Python 3.12+

## Security

- JWT token authentication
- Non-root container execution
- Environment variable configuration
- Network isolation via Docker networks
- Input validation and sanitization
- Rate limiting on API endpoints
