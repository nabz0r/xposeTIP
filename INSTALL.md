# Installation Guide

## Prerequisites

- **Docker** + **Docker Compose** (v2+)
- **Node.js** 18+ and **npm** (for frontend dev)
- **Git**

## 1. Clone and configure

```bash
git clone https://github.com/nabz0r/xposeTIP.git
cd xposeTIP
cp .env.example .env
```

Edit `.env`:

```bash
# REQUIRED — change this to a random string
SECRET_KEY=your-random-secret-key-here

# OPTIONAL — paid APIs (configure later via Settings UI)
HIBP_API_KEY=           # HaveIBeenPwned $3.50/mo
MAXMIND_LICENSE=        # MaxMind GeoLite2 (free tier)

# These defaults work with Docker Compose — don't change unless custom setup
DATABASE_URL=postgresql+asyncpg://xpose:xpose@postgres:5432/xpose
DATABASE_URL_SYNC=postgresql://xpose:xpose@postgres:5432/xpose
REDIS_URL=redis://redis:6379/0
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 2. Build and start services

```bash
docker compose up -d --build
```

This starts 5 containers:
- `xpose-postgres` — PostgreSQL 16 + pgvector
- `xpose-redis` — Redis 7
- `xpose-api` — FastAPI on port 8000
- `xpose-worker` — Celery worker (4 concurrent tasks)
- `xpose-beat` — Celery beat scheduler

Wait for all containers to be healthy:

```bash
docker compose ps
```

## 3. Initialize database

```bash
# Run migrations
docker compose exec api alembic upgrade head

# Seed scanner modules (25 modules, 17 with implementations)
docker compose exec api python scripts/seed_modules.py
```

## 4. Register admin account

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"your-password-here"}'
```

## 5. Start frontend

```bash
cd dashboard
npm install
npm run dev
```

Open http://localhost:5173

## 6. First scan

1. Go to **Targets** tab, click **Add Target**
2. Enter an email address
3. Click on the target, then **New Scan**
4. Default modules are pre-selected (7 free scanners)
5. Click **Scan** and watch results come in

## Optional: API keys

Some modules need API keys. Configure them in **Settings > API Keys**:

| Key | Module | Cost | How to get |
|-----|--------|------|-----------|
| `HIBP_API_KEY` | Have I Been Pwned | $3.50/mo | https://haveibeenpwned.com/API/Key |
| `FULLCONTACT_API_KEY` | FullContact | Free tier | https://www.fullcontact.com/developer/ |
| `MAXMIND_LICENSE` | MaxMind GeoIP | Free | https://www.maxmind.com/en/geolite2/signup |

Keys are encrypted at rest with Fernet (AES-256) and stored in workspace settings.

---

## Troubleshooting

### Docker build fails with credential errors

```bash
# If you see "failed to solve: error getting credentials"
docker logout
docker compose build --no-cache
```

### PYTHONPATH errors in worker/api

The `docker-compose.yml` sets `PYTHONPATH=/app`. If running outside Docker:

```bash
export PYTHONPATH=/path/to/xposeTIP
```

### npm peer dependency warnings

React 18 with some packages triggers peer dep warnings. Safe to ignore:

```bash
npm install --legacy-peer-deps
```

### Alembic "target database is not up to date"

```bash
docker compose exec api alembic upgrade head
```

### Celery worker not processing tasks

Check that Redis is healthy and the worker is connected:

```bash
docker compose logs worker --tail=50
docker compose exec redis redis-cli ping
```

### Scanners return 0 findings

1. Make sure modules are seeded: `docker compose exec api python scripts/seed_modules.py`
2. Check worker logs: `docker compose logs worker --tail=100`
3. Verify module health in **Settings > Modules > Run Health Checks**

### EmailRep rate limited from Docker

emailrep.io may rate-limit Docker/cloud IPs more aggressively. This is normal — results may be limited when running from a server. Works better from residential IPs.

### Database connection refused

PostgreSQL needs a few seconds to start. Docker healthcheck handles this, but if running manually:

```bash
docker compose up -d postgres redis
sleep 5
docker compose up -d api worker beat
```

---

## Development without Docker

```bash
# Start Postgres + Redis manually or via Docker
docker compose up -d postgres redis

# Backend
pip install -r requirements.txt
export DATABASE_URL=postgresql+asyncpg://xpose:xpose@localhost:5432/xpose
export DATABASE_URL_SYNC=postgresql://xpose:xpose@localhost:5432/xpose
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=dev-secret
export PYTHONPATH=.

alembic upgrade head
python scripts/seed_modules.py
uvicorn api.main:app --reload --port 8000

# Worker (separate terminal)
celery -A api.tasks worker -l info -c 4 -Q celery,scans,modules

# Frontend (separate terminal)
cd dashboard
npm install
npm run dev
```
