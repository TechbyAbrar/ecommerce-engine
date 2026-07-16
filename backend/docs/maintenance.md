# Ecommerce Engine - Production Maintenance Guide

This document contains operational commands, deployment procedures, troubleshooting steps, and recovery procedures for the **Ecommerce Engine** production environment.

---

## Table of Contents

- Starting the application
- Stopping the application
- Restarting services
- Viewing logs
- Container management
- Health checks
- Database migrations
- Rebuilding containers
- Deployment workflow
- Rollback procedure
- Cleaning Docker resources
- Backup and recovery
- Troubleshooting
- Emergency recovery
- Production checklist

---

## Starting the Application

Start all services in detached mode.

```bash
docker compose up -d
```

Start services and rebuild images.

```bash
docker compose up -d --build
```

Start a specific service.

```bash
docker compose up -d api
```

Start services and remove orphan containers.

```bash
docker compose up -d --remove-orphans
```

---

## Stopping the Application

Stop all services.

```bash
docker compose down
```

Stop containers and remove orphan containers.

```bash
docker compose down --remove-orphans
```

Remove containers and volumes.

> Warning: This removes persistent data such as Redis/database volumes.

```bash
docker compose down -v
```

Stop a specific service.

```bash
docker compose stop api
```

---

## Restarting Services

Restart all services.

```bash
docker compose restart
```

Restart API service.

```bash
docker compose restart api
```

Restart Celery worker.

```bash
docker compose restart worker
```

Restart Redis.

```bash
docker compose restart redis
```

---

## Viewing Logs

View all service logs.

```bash
docker compose logs
```

Follow logs continuously.

```bash
docker compose logs -f
```

API logs.

```bash
docker compose logs -f api
```

Worker logs.

```bash
docker compose logs -f worker
```

Redis logs.

```bash
docker compose logs -f redis
```

Show recent logs.

```bash
docker compose logs --tail=100 api
```

---

## Container Management

Check running services.

```bash
docker compose ps
```

Check all containers.

```bash
docker ps -a
```

View container resource usage.

```bash
docker stats
```

Open API container shell.

```bash
docker compose exec api bash
```

Fallback shell:

```bash
docker compose exec api sh
```

Access worker container.

```bash
docker compose exec worker bash
```

Access Redis CLI.

```bash
docker compose exec redis redis-cli
```

---

## Health Checks

Check container health.

```bash
docker inspect ecommerce-api
```

Check API health endpoint.

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy"
}
```

Verify Redis connection.

```bash
docker compose exec redis redis-cli ping
```

Expected:

```text
PONG
```

---

## Database Migrations

Run database migrations.

```bash
docker compose run --rm api ./docker/migrate-entrypoint.sh
```

Create a migration.

```bash
docker compose exec api uv run alembic revision --autogenerate -m "migration description"
```

Apply migrations manually.

```bash
docker compose exec api uv run alembic upgrade head
```

Check migration status.

```bash
docker compose exec api uv run alembic current
```

---

## Rebuilding Containers

Rebuild images.

```bash
docker compose build
```

Rebuild without cache.

```bash
docker compose build --no-cache
```

Recreate containers.

```bash
docker compose up -d --force-recreate
```

Full rebuild:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## Deployment Workflow

Recommended production deployment sequence:

### 1. Pull latest code

```bash
git pull origin main
```

### 2. Check environment configuration

```bash
cat .env
```

Verify:

- Database credentials
- Redis URL
- Secret keys
- API configuration

### 3. Run migrations

```bash
docker compose run --rm api ./docker/migrate-entrypoint.sh
```

### 4. Rebuild application

```bash
docker compose build
```

### 5. Restart services

```bash
docker compose up -d
```

### 6. Verify deployment

```bash
docker compose ps
```

Check logs:

```bash
docker compose logs -f api
```

---

## Rollback Procedure

If deployment fails:

Stop services.

```bash
docker compose down
```

Checkout previous stable version.

```bash
git checkout <previous-commit>
```

Rebuild containers.

```bash
docker compose build
```

Start services.

```bash
docker compose up -d
```

Verify health.

```bash
curl http://localhost:8000/health
```

---

## Cleaning Docker Resources

Remove unused images.

```bash
docker image prune -a
```

Remove unused volumes.

```bash
docker volume prune
```

Remove unused networks.

```bash
docker network prune
```

Remove unused Docker resources.

> Use carefully in production.

```bash
docker system prune -a
```

---

## Troubleshooting

### API container is not starting

Check logs:

```bash
docker compose logs api
```

Common causes:

- Missing `.env`
- Invalid configuration
- Database unavailable
- Dependency installation failure
- Application startup exception

### Worker is not processing tasks

Check worker logs:

```bash
docker compose logs worker
```

Verify Redis:

```bash
docker compose exec redis redis-cli ping
```

Expected:

```text
PONG
```

### Redis unavailable

Restart Redis:

```bash
docker compose restart redis
```

Check logs:

```bash
docker compose logs redis
```

### Port already in use

Linux:

```bash
sudo lsof -i :8000
```

Windows:

```powershell
netstat -ano | findstr :8000
```

### Containers continuously restarting

Check status:

```bash
docker compose ps
```

Check logs:

```bash
docker compose logs api
docker compose logs worker
```

Common reasons:

- Missing environment variables
- Database connection failure
- Redis failure
- Invalid startup command

---

## Emergency Recovery

Stop everything:

```bash
docker compose down
```

Rebuild images:

```bash
docker compose build --no-cache
```

Start services:

```bash
docker compose up -d
```

Verify:

```bash
docker compose ps
```

Monitor logs:

```bash
docker compose logs -f
```

---

## Backup and Recovery

Before major deployments:

- Backup database.
- Backup environment configuration.
- Record current git commit.
- Verify Docker volumes.

Database backup example:

```bash
pg_dump database_name > backup.sql
```

Restore example:

```bash
psql database_name < backup.sql
```

---

## Production Checklist

Before deployment:

- [ ] Pull latest code
- [ ] Review changes
- [ ] Verify `.env`
- [ ] Backup database
- [ ] Run migrations
- [ ] Build Docker images
- [ ] Restart services
- [ ] Check container health
- [ ] Verify API endpoint
- [ ] Verify Redis
- [ ] Monitor logs

---

## Important Notes

- Never run `docker compose down -v` on production unless you intentionally want to delete volumes.
- Always check logs before restarting services.
- Run migrations before deploying schema changes.
- Keep `.env` files secure.
- Do not expose internal services publicly.
- Monitor CPU, memory, disk usage, and container health regularly.
