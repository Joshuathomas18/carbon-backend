# Deployment Guide

## Quick Start: Docker Compose (Production)

```bash
# Clone repo
git clone https://github.com/Joshuathomas18/carbon-backend.git
cd carbon-backend

# Create .env file
cp .env.example .env

# Edit .env with production values
nano .env

# Start services
docker-compose -f docker-compose.prod.yml up -d

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## GCP Cloud Run Deployment

### Prerequisites
- GCP project with Cloud Run enabled
- Docker artifact registry
- Service account for GEE

### Steps

```bash
# 1. Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT/carbon-backend

# 2. Deploy to Cloud Run
gcloud run deploy carbon-backend \
  --image gcr.io/YOUR_PROJECT/carbon-backend \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=postgresql+asyncpg://user:pass@cloudsql_proxy:5432/carbon_db \
  --set-env-vars SARVAM_API_KEY=your_key \
  --set-env-vars GEE_PROJECT_ID=your_project \
  --memory 2Gi \
  --cpu 2 \
  --timeout 60 \
  --allow-unauthenticated

# 3. View logs
gcloud run logs read carbon-backend --limit 50
```

## AWS Lambda Deployment

### Using Serverless Framework

```bash
# Install serverless
npm install -g serverless

# Create serverless config
cat > serverless.yml << 'EOF'
service: carbon-backend
provider:
  name: aws
  runtime: python3.10
  region: ap-south-1
  environment:
    DATABASE_URL: ${ssm:/carbon-backend/db-url}
    SARVAM_API_KEY: ${ssm:/carbon-backend/sarvam-key}

functions:
  api:
    handler: app.main.app
    events:
      - http:
          path: /{proxy+}
          method: ANY
    layers:
      - arn:aws:lambda:ap-south-1:123456789:layer:python-deps
EOF

# Deploy
serverless deploy
```

## Manual VPS Deployment (Ubuntu 22.04)

```bash
# 1. Install dependencies
sudo apt update && sudo apt install -y python3.10 postgresql postgresql-contrib redis-server

# 2. Clone repo
git clone https://github.com/Joshuathomas18/carbon-backend.git
cd carbon-backend

# 3. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your values
nano .env

# 5. Setup database
psql -U postgres -c "CREATE DATABASE carbon_db;"
alembic upgrade head

# 6. Start with supervisor
cat > /etc/supervisor/conf.d/carbon-backend.conf << 'EOF'
[program:carbon-backend]
directory=/home/ubuntu/carbon-backend
command=/home/ubuntu/carbon-backend/venv/bin/gunicorn app.main:app --bind 0.0.0.0:8000 --workers 4
autostart=true
autorestart=true
user=ubuntu
environment=PATH="/home/ubuntu/carbon-backend/venv/bin",DATABASE_URL=postgresql://...
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start carbon-backend

# 7. Setup nginx reverse proxy
cat > /etc/nginx/sites-available/carbon-backend << 'EOF'
server {
    listen 80;
    server_name api.carbon-backend.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/carbon-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL/TLS Setup

### Using Let's Encrypt (Certbot)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.carbon-backend.example.com
```

## Monitoring & Logs

### Sentry for Error Tracking
```python
# Already configured in app/main.py
# Set SENTRY_DSN in .env
SENTRY_DSN=https://key@sentry.io/project_id
```

### Logs Location
```bash
# Docker compose
docker-compose logs -f fastapi

# File logs
tail -f /var/log/carbon-backend/app.log
```

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Performance Tuning

### Database Connection Pool
```python
# app/config.py
DATABASE_URL = "postgresql+asyncpg://user:pass@host/db?pool_size=20&max_overflow=40"
```

### Cache Configuration
```python
FEATURE_CACHE_TTL = 604800  # 7 days
GEE_CACHE_DAYS = 7
```

### Worker Configuration
```bash
# Production: 4 workers for 2 CPU machine
gunicorn app.main:app --workers 4 --threads 4 --worker-class uvicorn.workers.UvicornWorker
```

## Health Checks & Monitoring

```bash
# Health check
curl http://localhost:8000/health

# API Documentation
curl http://localhost:8000/docs

# Check database connection
psql -U carbon_user -d carbon_db -c "SELECT 1;"
```

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U carbon_user -h localhost -d carbon_db
```

### Port Already in Use
```bash
# Kill process on port 8000
sudo lsof -i :8000
sudo kill -9 PID
```

### High Memory Usage
```bash
# Reduce worker count
gunicorn app.main:app --workers 2

# Check Redis memory
redis-cli info memory
```

## Backup Strategy

```bash
# Database backup
pg_dump carbon_db > backup_$(date +%Y%m%d).sql

# Restore from backup
psql carbon_db < backup_20260415.sql

# Automated daily backup (cron)
0 2 * * * pg_dump carbon_db | gzip > /backups/carbon_db_$(date +\%Y\%m\%d).sql.gz
```

## Security Checklist

- [ ] Change default database password
- [ ] Set strong SARVAM_API_KEY
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly (restrict origins)
- [ ] Set DEBUG=false in production
- [ ] Use environment variables for secrets
- [ ] Enable database backups
- [ ] Setup log aggregation
- [ ] Monitor API rate limits
- [ ] Regular security updates
