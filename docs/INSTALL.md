# Installation Guide

## Prerequisites

- Docker & Docker Compose v2+
- Git
- (Optional) Node.js 18+ for local frontend dev
- (Optional) Python 3.11+ for local backend dev

## Quick Start (Docker)

```bash
git clone https://github.com/nabz0r/xposeTIP.git
cd xposeTIP
cp .env.example .env
docker compose up -d
docker compose exec api python scripts/seed_modules.py
```

Open http://localhost:5173 (dashboard) or http://localhost:8000/docs (API).

## Environment Variables

Create a `.env` file in the project root:

```env
# Required
SECRET_KEY=your-secret-key-min-32-chars
DATABASE_URL=postgresql+asyncpg://xpose:xpose@postgres:5432/xpose
DATABASE_URL_SYNC=postgresql://xpose:xpose@postgres:5432/xpose
REDIS_URL=redis://redis:6379/0

# Optional API keys (enable more scanners)
HIBP_API_KEY=           # haveibeenpwned.com — $3.50/mo
MAXMIND_LICENSE=        # maxmind.com — free GeoLite2
FULLCONTACT_API_KEY=    # fullcontact.com
VIRUSTOTAL_API_KEY=     # virustotal.com — free tier
SHODAN_API_KEY=         # shodan.io
INTELX_API_KEY=         # intelx.io
HUNTER_API_KEY=         # hunter.io
DEHASHED_API_KEY=       # dehashed.com
PIMEYES_API_KEY=        # pimeyes.com

# Google OAuth (Layer 3 self-audit)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Microsoft OAuth (Layer 3 self-audit)
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=

# Frontend
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| `api` | 8000 | FastAPI backend |
| `worker` | — | Celery worker (4 concurrent) |
| `beat` | — | Celery beat scheduler |
| `postgres` | 5432 | PostgreSQL 16 + pgvector |
| `redis` | 6379 | Redis 7 (broker + cache) |

The frontend dev server runs on port 5173 (Vite).

## Local Development (without Docker)

### Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

### Worker

```bash
celery -A api.tasks worker -l info -c 4 -Q celery,scans,modules
```

### Frontend

```bash
cd dashboard
npm install
npm run dev
```

## Database Migrations

```bash
# Create migration
docker compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec api alembic upgrade head

# Seed modules
docker compose exec api python scripts/seed_modules.py
```

## Troubleshooting

### Containers won't start
```bash
docker compose down -v   # reset volumes
docker compose up -d --build
```

### Scanner module not appearing
Re-seed after adding new modules:
```bash
docker compose exec api python scripts/seed_modules.py
```

### emailrep.io rate limiting
Cloud/Docker IPs get rate-limited aggressively. Works better from residential IPs.

### Sherlock IP ban
Aggressive rate limiting is configured (5 rpm). Shared IPs may still get banned.

### WorldHeatmap blank
The D3 heatmap fetches TopoJSON from jsdelivr CDN. If CDN is unreachable, it silently fails. The SVG world map (Locations tab) works offline.

### Health check
```bash
curl http://localhost:8000/health           # quick check
curl http://localhost:8000/health/detailed  # full infrastructure status
```
