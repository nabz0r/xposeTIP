# CLAUDE.md — Project context for Claude Code

## What is xposeTIP

Identity Threat Intelligence platform. Scans email → builds identity graph →
PageRank/Markov confidence → clusters personas → pixel art avatar → remediation plan.

## Current version: v1.1.10

110 sprints. 126 scrapers, 26 scanners, 9 intelligence analyzers, 9-axis fingerprint.
Scanners: 26 registered (SCANNER_REGISTRY) + 9 analyzers. 5 disabled placeholders (maigret, h8mail, ghunt, paste_monitor, databroker_check).
Two-phase pipeline: Phase A (gather: cross-verify → A1.5 phone/crypto extraction → A1.6 secondary enrichment → Pass 1.5 → early profile → Pass 2)
→ Phase B (compute: graph → PageRank → score → profile → personas → intelligence → fingerprint).
Deep Scan triggers cascade (discovered emails/usernames/domains → chain-scanned, depth=1, max=5).
Per-scraper module attribution (Sprint 89). 429 exponential backoff on all scrapers.
PDF identity report export (ReportLab, dark theme, tiered by plan).
Phase C (web discovery, operator-triggered): fingerprint-driven Google dorking → trafilatura
page fetch → 6 extractors (rel_me/jsonld/social_link/email/meta_tag/username) → quality gate
→ discovery_leads DB. Budget: 20 queries, 50 pages, 60s default.

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
12. wayback_domain and wayback_count are domain-age modules — excluded from identity timeline
13. Discovery leads are NOT findings — separate table (discovery_leads), separate workflow
14. Phase C queries MUST be disambiguated with email domain for name-based searches (homonyme prevention)

## Product Principles (Manifesto)

### Ethical OSINT
- Consent-first: scan yourself or with DPA authorization
- Transparency: every finding shows source, every score explains reasoning
- Purpose limitation: expose to protect, not to exploit
- Right to delete: full purge on request, not soft delete
- No dark patterns: honest scores, no scare-tactic upsells

### Green Intelligence
- Maximum insight per watt — Amiga 500 philosophy
- Data-driven scrapers (JSON config, not code per source)
- Single PostgreSQL, no distributed clusters
- Pixel art avatars: 5.4B combos, zero GPU, zero API
- Every architecture decision: "is this the lightest way?"

### Education First
- Every finding explains WHY it's a risk in plain language
- Remediation actions are actionable, not generic
- The goal is to make users NOT need xpose anymore
- Scores are explainable, not black-box

## Deploy sequence

```bash
killall -9 node && sleep 2
git fetch origin && git reset --hard origin/main
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
- `api/tasks/scan_orchestrator.py` — two-phase pipeline (gather→compute), finalize_scan, graph_context, _full_refinalize (15-step Deep Scan pipeline), _extract_cascade_indicators
- `api/tasks/module_tasks.py` — module execution, pre-flush truncation
- `api/services/layer4/graph_builder.py` — identity graph construction
- `api/services/layer4/confidence_propagator.py` — PageRank (damping=0.85, 20 iter)
- `api/services/layer4/profile_aggregator.py` — name/avatar/bio resolution, avatar quality ranking
- `api/services/layer4/score_engine.py` — dual exposure/threat score
- `api/services/layer4/persona_engine.py` — graph cluster + SequenceMatcher personas
- `api/services/layer4/fingerprint_engine.py` — 9-axis radar, eigenvalues, avatar_seed
- `api/services/layer4/analysis_pipeline.py` — 9 intelligence analyzers
- `api/services/layer4/analyzers/code_leak_analyzer.py` — GitHub/paste code leak detection
- `api/services/layer4/analyzers/behavioral_profiler.py` — 5 archetypes behavioral classification
- `api/services/layer4/analyzers/geo_consistency.py` — 6-signal geographic consistency analysis
- `api/services/layer4/analyzers/timezone_analyzer.py` — timezone inference from activity timestamps
- `api/services/layer4/username_expander.py` — Pass 1.5 username expansion, scan_single_indicator (generic deep scan)
- `api/services/layer4/username_validator.py` — is_valid_username() junk filter
- `api/services/layer4/source_scoring.py` — source reliability weights
- `api/services/plan_config.py` — plan definitions, feature gates
- `api/services/scraper_engine.py` — URL template + regex/JSONPath extraction
- `api/routers/targets.py` — CRUD + profile + fingerprint + geo_locations + discovery endpoints
- `api/routers/scans.py` — scan CRUD + quick scan + paginated total
- `api/services/report/pdf_generator.py` — PDF identity report (ReportLab)
- `api/discovery/pipeline.py` — Phase C Web Discovery orchestrator
- `api/discovery/extractors/` — 6 lead extractors (rel_me, jsonld, social_link, email, meta_tag, username)
- `api/discovery/quality_gate.py` — dedup discovery leads vs existing findings
- `api/discovery/query_generator.py` — fingerprint-driven search query composition
- `api/tasks/web_discovery.py` — Celery task for Phase C
- `scripts/seed_scrapers.py` — 126 scraper definitions
- `scripts/seed_modules.py` — 32 scanner modules (26 active + 5 disabled + 1 virtual)

### Frontend
- `dashboard/src/pages/Landing.jsx` — landing page (composed from components/landing/)
- `dashboard/src/pages/TargetDetail.jsx` — full target view (7 tabs)
- `dashboard/src/pages/Architecture.jsx` — technical whitepaper
- `dashboard/src/components/GenerativeAvatar.jsx` — 32x32 pixel art
- `dashboard/src/components/IdentityGraph.jsx` — D3 force-directed graph
- `dashboard/src/components/FingerprintRadar.jsx` — 9-axis radar chart
- `dashboard/src/components/WorkspaceGeoMap.jsx` — D3 geographic heatmap
- `dashboard/src/pages/UserPreview.jsx` — consumer dashboard preview (/user-preview)
- `dashboard/src/pages/tabs/DiscoveredTab.jsx` — Phase C discovery UI (launch, leads, dismiss)

## Details

See `docs/ARCHITECTURE.md`, `docs/API_REFERENCE.md`, `docs/SPRINT_LOG.md`.
