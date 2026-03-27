# CLAUDE.md — Project context for Claude Code

## What is xposeTIP

Identity Threat Intelligence platform. Scans email → builds identity graph →
PageRank/Markov confidence → clusters personas → pixel art avatar → remediation plan.

## Current version: v0.74.0

80 sprints. 120 scrapers, 35 scanners, 7 intelligence analyzers, 9-axis fingerprint.
3-pass pipeline (email → username expansion → name-based enrichment).
PDF identity report export (ReportLab, dark theme, tiered by plan).

## Developer

Nabil (nabz0r). Solo founder. Network/security engineer 20+ years.
Master Mathematics (Sorbonne), CCNA, NSE 1-4, JNCIA.
Nexus 2026 — June 10-11, Luxexpo, Luxembourg (€50 cybersecurity category, submitted).

## Tech stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, Celery, PostgreSQL 16 (service=postgres, user=xpose), Redis
- **Frontend**: React 18, Vite, Tailwind CSS 4, D3.js, Recharts
- **Infra**: Docker Compose (api, worker, beat, postgres, redis)
- **Auth**: JWT (access + refresh tokens)
- **DB**: All datetime columns use `TIMESTAMP(timezone=True)`

## Critical rules

1. graph_context is OPTIONAL — all services MUST work without it (graceful fallback)
2. NEVER show platform names as display names
3. NEVER count domain registration as email age
4. NEVER use GeoIP for user location (mail server IP only)
5. Clustering BFS excludes weak edges (associated_with, located_in)
6. superadmin bypasses ALL plan limits
7. Public workspace ("public" slug) for quick scan — transferred on register
8. OSINT tools in Celery worker (`-Q celery,scans,modules`), NEVER in API process
9. API keys AES-256 encrypted at rest (Fernet)
10. Every DB query scoped to workspace_id
11. SCANNER_REGISTRY IDs must match scripts/seed_modules.py

## Deploy sequence

```bash
killall -9 node && sleep 2
git fetch origin && git reset --hard origin/claude/sprint-1-operator-mvp-0sq70
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_modules.py
docker compose exec api python scripts/seed_scrapers.py
docker compose exec api python scripts/seed_blacklist.py
docker compose exec api python scripts/sync_avatars.py
pkill -f vite
cd dashboard && npm install --legacy-peer-deps && npm run dev &
```

After deploy: System → Recalculate Fingerprints → Recalculate Profiles

## Key files

### Backend
- `api/tasks/scan_orchestrator.py` — 3-pass pipeline, finalize_scan, graph_context
- `api/tasks/module_tasks.py` — module execution, pre-flush truncation
- `api/services/layer4/graph_builder.py` — identity graph construction
- `api/services/layer4/confidence_propagator.py` — PageRank (damping=0.85, 20 iter)
- `api/services/layer4/profile_aggregator.py` — name/avatar/bio resolution, avatar quality ranking
- `api/services/layer4/score_engine.py` — dual exposure/threat score
- `api/services/layer4/persona_engine.py` — graph cluster + SequenceMatcher personas
- `api/services/layer4/fingerprint_engine.py` — 9-axis radar, eigenvalues, avatar_seed
- `api/services/layer4/analysis_pipeline.py` — 5 intelligence analyzers
- `api/services/layer4/username_expander.py` — Pass 1.5 username expansion
- `api/services/layer4/username_validator.py` — is_valid_username() junk filter
- `api/services/layer4/source_scoring.py` — source reliability weights
- `api/services/plan_config.py` — plan definitions, feature gates
- `api/services/scraper_engine.py` — URL template + regex/JSONPath extraction
- `api/routers/targets.py` — CRUD + profile + fingerprint + geo_locations
- `api/routers/scans.py` — scan CRUD + quick scan + paginated total
- `api/services/report/pdf_generator.py` — PDF identity report (ReportLab)
- `scripts/seed_scrapers.py` — 120 scraper definitions
- `scripts/seed_modules.py` — 35 scanner modules

### Frontend
- `dashboard/src/pages/Landing.jsx` — landing page (composed from components/landing/)
- `dashboard/src/pages/TargetDetail.jsx` — full target view (7 tabs)
- `dashboard/src/pages/Architecture.jsx` — technical whitepaper
- `dashboard/src/components/GenerativeAvatar.jsx` — 32x32 pixel art
- `dashboard/src/components/IdentityGraph.jsx` — D3 force-directed graph
- `dashboard/src/components/FingerprintRadar.jsx` — 9-axis radar chart
- `dashboard/src/components/WorkspaceGeoMap.jsx` — D3 geographic heatmap

## Details

See `docs/ARCHITECTURE.md`, `docs/API_REFERENCE.md`, `docs/SPRINT_LOG.md`.
