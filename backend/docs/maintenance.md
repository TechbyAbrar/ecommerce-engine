# Maintenance Guide

This document contains the common operational commands and recovery procedures for the **Ecommerce Engine** project.

---

# Table of Contents

* Starting the application
* Stopping the application
* Restarting services
* Viewing logs
* Accessing containers
* Health checks
* Database migrations
* Rebuilding containers
* Updating the application
* Cleaning Docker resources
* Troubleshooting
* Emergency recovery

---

# Starting the Application

Start all services in detached mode.

```bash
docker compose up -d
```

Start and rebuild images.

```bash
docker compose up -d --build
```

Start a specific service.

```bash
docker compose up -d api
```

---

# Stopping the Application

Stop all containers.

```bash
docker compose down
```

Stop and remove volumes.

> Warning: This deletes Docker volumes, including Redis data.

```bash
docker compose down -v
```

Stop a single service.

```bash
docker compose stop api
```

---

# Restarting Services

Restart everything.

```bash
docker compose restart
```

Restart only the API.

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

# Viewing Logs

View logs from all services.

```bash
docker compose logs
```

Follow logs in real time.

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

Show the last 100 log lines.

```bash
docker compose logs --tail=100 api
```

---

# Accessing Containers

Open a shell inside the API container.

```bash
docker compose exec api bash
```

If Bash is unavailable:

```bash
docker compose exec api sh
```

Worker container.

```bash
docker compose exec worker bash
```

Redis CLI.

```bash
docker compose exec redis redis-cli
```

---

# Container Status

List running containers.

```bash
docker compose ps
```

List all Docker containers.

```bash
docker ps -a
```

---

# Health Checks

Check Docker container health.

```bash
docker inspect ecommerce-api
```

Check application endpoint.

```bash
curl http://localhost:8000/health
```

---

# Database Migrations

Run migrations.

```bash
docker compose run --rm api ./docker/migrate-entrypoint.sh
```

Create a migration.

```bash
docker compose exec api uv run alembic revision --autogenerate -m "description"
```

---

# Rebuilding Containers

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

---

# Updating the Application

Pull the latest source code.

```bash
git pull origin main
```

Rebuild the project.

```bash
docker compose down
docker compose build
docker compose up -d
```

Verify containers.

```bash
docker compose ps
```

---

# Cleaning Docker Resources

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

Clean everything unused.

> Use carefully.

```bash
docker system prune -a
```

---

# Troubleshooting

## API container won't start

Check logs.

```bash
docker compose logs api
```

Common causes:

* Missing `.env`
* Invalid environment variables
* Syntax errors
* Dependency installation failure

---

## Worker is not processing tasks

Check worker logs.

```bash
docker compose logs worker
```

Verify Redis.

```bash
docker compose exec redis redis-cli ping
```

Expected response:

```
PONG
```

---

## Redis is unavailable

Restart Redis.

```bash
docker compose restart redis
```

Check logs.

```bash
docker compose logs redis
```

---

## Port already in use

Find the process.

Linux:

```bash
sudo lsof -i :8000
```

Windows:

```powershell
netstat -ano | findstr :8000
```

Stop the conflicting process or change the exposed port.

---

## Health check failed

Check application logs.

```bash
docker compose logs api
```

Verify the health endpoint.

```bash
curl http://localhost:8000/health
```

Ensure the application has finished starting.

---

## Containers keep restarting

Inspect the restart reason.

```bash
docker compose ps
docker compose logs api
docker compose logs worker
```

Typical causes:

* Missing environment variables
* Database connection errors
* Redis unavailable
* Unhandled startup exception

---

# Emergency Recovery

Stop all services.

```bash
docker compose down
```

Remove containers and volumes.

> Warning: This removes persistent Docker volumes.

```bash
docker compose down -v
```

Rebuild everything.

```bash
docker compose build --no-cache
```

Start services again.

```bash
docker compose up -d
```

Verify status.

```bash
docker compose ps
```

Check logs.

```bash
docker compose logs -f
```

---

# Useful Docker Commands

List images.

```bash
docker images
```

List volumes.

```bash
docker volume ls
```

List networks.

```bash
docker network ls
```

List running containers.

```bash
docker ps
```

Remove stopped containers.

```bash
docker container prune
```

---

# Deployment Checklist

Before deploying:

* Pull the latest code.
* Verify the `.env` configuration.
* Build Docker images.
* Run database migrations.
* Start all services.
* Verify container health.
* Check API logs.
* Test the `/health` endpoint.
* Verify Redis connectivity.
* Monitor logs after deployment.

---

# Notes

* Never use `docker compose down -v` on a production server unless you intentionally want to remove Docker volumes.
* Always review logs before restarting services.
* Prefer rebuilding containers after dependency or Dockerfile changes.
* Run database migrations before deploying application changes that modify the database schema.
