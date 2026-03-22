# CLAUDE.md — Project context for Claude Code

## What is xpose

Identity Threat Intelligence platform. Scans an email address across 71+ sources,
builds an identity graph, runs PageRank/Markov chain confidence propagation,
clusters digital personas, generates a 32x32 pixel art identity avatar, and
produces an actionable remediation plan.

Think "Have I Been Pwned × Maltego × CryptoPunks" — consumer-grade UX on
enterprise-grade OSINT intelligence.

## Developer

- **Name**: Nabil (nabz0r), network/security engineer, 20+ years
- **Background**: Master Mathematics (Sorbonne), CCNA, NSE 1-4, JNCIA
- **Day job**: ThreatConnect cybersecurity support, EMEA region
- **Style**: French, casual, very direct, heavy abbreviations
- **OS**: macOS — GitHub: nabz0r
- **Event**: Nexus 2026 — June 10-11, Luxexpo, Luxembourg

## Current version: v0.42.0

42 sprints. 71 scrapers, 25 scanners, 5 intelligence analyzers.
PageRank confidence propagation, Markov chain transition matrix,
graph-based persona clustering, 32x32 pixel art avatars (5.4B combinations),
freemium quick scan, 3 plans (Free/Consultant/Enterprise).

## Tech stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, Celery, PostgreSQL 16, Redis
- **Frontend**: React 18, Vite, Tailwind CSS 4, D3.js, Recharts
- **Infra**: Docker Compose (api, worker, beat, postgres, redis)
- **Auth**: JWT (access + refresh tokens)

## Architecture

### Intelligence Pipeline (finalize_scan order)

1. Cross-verify findings (boosts confidence)
2. Build identity graph (nodes + weighted edges)
3. PageRank confidence propagation (20 iterations, damping=0.85)
4. Build graph_context (node_scores, node_map, transition_matrix, clusters)
5. Compute score (exposure + threat, weighted by graph confidence)
6. Aggregate profile (names, avatar, bio — ranked by graph + source reliability)
7. Force bio cleanup (reject Telegram slogans, platform descriptions)
8. Force display_name blacklist validation
9. Identity enrichment (re-query Genderize/Agify/Nationalize with discovered name)
10. Cluster personas (graph-based with SequenceMatcher fallback)
11. Intelligence pipeline (5 analyzers: risk, breach, domain, behavioral, network)
12. Compute fingerprint (8-axis radar, eigenvalues, avatar_seed, timeline_events)
13. Store life_timeline in profile_data
14. Publish SSE events (disabled for stability)

### Markov Chain / graph_context

Computed once after PageRank, passed to ALL downstream services:
- `node_scores`: {identity_id: confidence} — PageRank results
- `node_map`: {value: {type, confidence, platform, id}} — quick lookups
- `transition_matrix`: {node_id: {dest_id: probability}} — Markov transitions
- `clusters`: [{nodes, confidence, density, dominant_type}] — connected components

Services receive `graph_context=None` parameter. If present → enhanced behavior.
If absent → graceful fallback to pre-Markov behavior. Zero regression guarantee.

Clustering uses ONLY strong edges (registered_with, identified_as, same_person,
exposed_in). Weak edges (associated_with, located_in) are used for PageRank but
excluded from clustering BFS.

### Name Resolution

Composite score: `graph_confidence × 0.5 + source_reliability × 0.3 + source_count × 0.1`
Higher reliability sources (GitHub 0.85, LinkedIn 0.80) beat lower ones (scraper 0.60).
Names in the top PageRank cluster get a +0.15 boost.
Single-letter initials ("J.", "Steffen H.") are rejected.

### Email Age Inference

Extracts earliest timestamp from ALL findings:
- `BreachDate`, `created_at`, `joined`, `member_since`, `first_seen`, etc.
- Skips domain-level modules (dns_deep, whois_lookup)
- Skips findings with "domain reputation" in title
- Caps by domain launch date (Gmail 2004, Outlook 2012, etc.)
- 30-year sanity cap

### Score Engine

Dual score: Exposure (how much is public) + Threat (how dangerous it is).
Each finding: `severity × confidence × source_reliability × graph_node_confidence`.
Graph weighting: `0.5 + node_conf × 0.5` (50% at zero confidence → 100% at full).

### Digital Fingerprint

8-axis radar: accounts, platforms, username_reuse, breaches, geo_spread,
data_leaked, email_age, security.
Eigenvalue computation from identity graph adjacency matrix.
Avatar seed: deterministic params for GenerativeAvatar.
Fingerprint hash: SHA256 of sorted axis values.

### GenerativeAvatar (32x32 Pixel Art)

CryptoPunk-style pixel face generated from `avatar_seed.email_hash`.
~5.4 billion combinations (face shape, skin, hair, eyes, mouth, accessories, clothing).
Score-reactive: expression changes, background shifts green→red, glitch pixels at high score.
Located next to fingerprint radar as "identity glyph".

## Scrapers: 71 total

| Category | Count | Examples |
|----------|-------|---------|
| Social | 29 | Reddit, GitHub, GitLab, Telegram, Medium, Bluesky, Mastodon, Flickr, Replit, SoundCloud |
| Breach | 5 | LeakCheck, XposedOrNot, Pastebin Dump, IntelX Public, BreachDirectory |
| Metadata | 4 | Gravatar, GitHub Search, Snapchat |
| Identity | 3 | Genderize, Agify, Nationalize |
| Archive | 8 | Wayback (profile, domain, Facebook, LinkedIn, Twitter, Instagram), Domain History |
| Gaming | 8 | Steam, Chess.com, Lichess, MyAnimeList, CodeWars, RuneScape, AniList, Speedrun.com |
| People Search | 5 | WebMii, Google Scholar, Gravatar Email, NPM Maintainer, PyPI |
| Dev | 4 | Codeberg, Hashnode |
| Music | 2 | Discogs, SoundCloud |

## Scanners: 25 modules

| Layer | Modules |
|-------|---------|
| L1 (basic) | email_validator, holehe, hibp, sherlock, gravatar, social_enricher, google_profile, emailrep, epieos, fullcontact, github_deep, username_hunter |
| L2 (deep) | whois_lookup, maxmind_geo, geoip, leaked_domains, dns_deep |
| L3 (audit) | google_auditor, exodus_tracker, browser_auditor, databroker_check, paste_monitor |
| L4 (intel) | intelligence (5 analyzers), maigret, ghunt, h8mail |

Seeded modules: 25 total (17 implemented + 8 placeholder).
Lazy-loaded via `importlib` — missing deps don't crash the worker.

## Plans

| | Free | Consultant (€49/mo) | Enterprise (€199/mo) |
|--|------|---------------------|---------------------|
| Targets | 1 | 25 | Unlimited |
| Scans/mo | 5 | 100 | Unlimited |
| Scrapers | Basic | All 71 | All 71 |
| Personas | No | Yes | Yes |
| Identity | No | Yes | Yes |
| PDF Export | No | Yes | Yes |

superadmin bypasses ALL limits always. First registered user = superadmin + enterprise workspace.

## Key files

### Backend
- `api/tasks/scan_orchestrator.py` — finalize_scan pipeline, graph_context builder
- `api/services/layer4/graph_builder.py` — identity graph construction
- `api/services/layer4/confidence_propagator.py` — PageRank (damping=0.85, 20 iterations)
- `api/services/layer4/profile_aggregator.py` — name/avatar/bio resolution with blacklist
- `api/services/layer4/score_engine.py` — dual exposure/threat score
- `api/services/layer4/persona_engine.py` — graph cluster + SequenceMatcher personas
- `api/services/layer4/fingerprint_engine.py` — 8-axis radar, eigenvalues, avatar_seed, timeline
- `api/services/layer4/analysis_pipeline.py` — 5 intelligence analyzers
- `api/services/layer4/identity_enricher.py` — re-query with discovered name
- `api/services/layer4/source_scoring.py` — source reliability weights, cross-verification
- `api/services/plan_config.py` — plan definitions, feature gates
- `api/services/scraper_engine.py` — URL template + regex/JSONPath extraction
- `api/routers/targets.py` — CRUD + profile + fingerprint + move
- `api/routers/scans.py` — scan CRUD + quick scan endpoints
- `api/main.py` — quick scan public endpoint
- `api/models/name_blacklist.py` — DB-driven name/bio blacklist
- `scripts/seed_scrapers.py` — 71 scraper definitions
- `scripts/seed_blacklist.py` — 65+ blacklist entries

### Frontend
- `dashboard/src/pages/Landing.jsx` — fear-driven landing, quick scan, pixel avatar grid
- `dashboard/src/pages/TargetDetail.jsx` — full target view (Overview/Findings/Graph/Timeline/Accounts/Locations/Scans)
- `dashboard/src/pages/Architecture.jsx` — technical whitepaper (Collect/Graph/Propagate/Score/Identify)
- `dashboard/src/pages/System.jsx` — admin panel (users/workspaces/logs)
- `dashboard/src/components/GenerativeAvatar.jsx` — 32x32 pixel art from fingerprint
- `dashboard/src/components/IdentityGraph.jsx` — D3 force-directed graph with PageRank sizing
- `dashboard/src/components/FingerprintRadar.jsx` — 8-axis radar chart
- `dashboard/src/components/LifeTimeline.jsx` — vertical timeline from timestamps
- `dashboard/src/components/WorldHeatmap.jsx` — D3 geographic exposure map

## Deploy sequence

```bash
killall -9 node && sleep 2
git fetch origin && git reset --hard origin/claude/sprint-1-operator-mvp-0sq70
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_modules.py
docker compose exec api python scripts/seed_scrapers.py
docker compose exec api python scripts/seed_blacklist.py
pkill -f vite
cd dashboard && npm install --legacy-peer-deps && npm run dev &
```

After deploy: System → Recalculate Fingerprints → Recalculate Profiles

## Name blacklist

DB-driven (model: NameBlacklist). Types: exact, contains, regex. 65+ entries:
platform names, services, Telegram slogans, browsers, password managers.
Bio blacklist: Telegram slogans, Linktree descriptions.
Avatar URL blacklist: Telegram CDN, default platform avatars.
Single-letter initial rejection: "Steffen H." → rejected (first or last part).

## Graph edge types

| Type | Meaning | Used for clustering? |
|------|---------|---------------------|
| registered_with | Email registered on platform | Yes |
| identified_as | Username identified as name | Yes |
| same_person | Email linked to username | Yes |
| exposed_in | Email exposed in breach | Yes |
| associated_with | Catch-all orphan link to email anchor | No (PageRank only) |
| located_in | Identity linked to location | No (PageRank only) |

## SSE (disabled)

useSSE hook is a no-op. Was causing API saturation (all workers blocked by SSE
connections). Re-enable after: dedicated SSE server, or WebSocket, or long-polling
with connection limit.

## Known issues

* Quick scan timeout (300s) may not be enough for slow Celery
* Some scraper timestamps not parsed (field names vary per API)
* Life timeline sparse (most findings don't include timestamps)
* PDF export never implemented
* Fingerprint evolution avatars identical when score stable (by design)

## Critical rules

1. NEVER show platform names as display names
2. NEVER count domain registration as email age
3. graph_context is OPTIONAL — all services must work without it
4. Clustering excludes weak edges (associated_with, located_in)
5. superadmin bypasses ALL plan limits
6. Public workspace ("public" slug) for quick scan targets — transferred on register
7. OSINT tools in Celery workers, NEVER in API process
8. API keys AES-256 encrypted at rest (Fernet)
9. Every DB query scoped to workspace_id
10. US targets = more data available = higher scores. This is correct.

## Roadmap

### v1.0 — Nexus 2026 (June)
- [x] 71 scrapers, 25 scanners
- [x] PageRank / Markov chain confidence propagation
- [x] 32x32 pixel art identity avatars
- [x] Freemium quick scan (zero friction)
- [x] Plans (Free/Consultant/Enterprise)
- [ ] PDF report export
- [ ] SSE real-time (stable)
- [ ] Graph zoom/pan improvement

### v1.1 — Post-Nexus (July-August)
- [ ] Corporate/LDAP scrapers (O365 enumeration, Azure AD tenant, GitHub org)
- [ ] Domain-wide scan (all employees of company)
- [ ] API public (for integrations)
- [ ] Webhook notifications
- [ ] On-premise deployment guide

### v1.2 — Enterprise (Q4 2026)
- [ ] OAuth audit (Google/Microsoft third-party app access)
- [ ] Dark web monitoring (Tor paste sites)
- [ ] Scheduled recurring scans
- [ ] Compliance reports (NIS2, DORA)
- [ ] Multi-language (FR, DE, LU)

### v2.0 — Platform (2027)
- [ ] Marketplace (community scrapers)
- [ ] Plugin API (custom analyzers)
- [ ] Team collaboration (shared investigations)
- [ ] Mobile app

## Global scope

xpose is NOT Luxembourg-only. The product works worldwide with varying depth:
- **US targets**: Maximum data. Voter rolls, court records, Spokeo, WhitePages — all public.
- **EU targets**: GDPR applies but we reveal existing public exposure. Lawful basis = consent.
- **Rest of world**: Varies. Module system adapts — region-specific modules can be enabled/disabled.

## API design

All endpoints prefixed with `/api/v1/`. All require auth (JWT Bearer) except health.
All scoped to workspace via middleware (extracts workspace_id from JWT claims).

### Auth
```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
PATCH /api/v1/auth/profile
```

### Targets
```
GET    /api/v1/targets
POST   /api/v1/targets
GET    /api/v1/targets/{id}
PATCH  /api/v1/targets/{id}
DELETE /api/v1/targets/{id}
GET    /api/v1/targets/{id}/profile
```

### Scans
```
POST   /api/v1/scans
GET    /api/v1/scans
GET    /api/v1/scans/{id}
POST   /api/v1/scans/{id}/cancel
```

### Findings
```
GET    /api/v1/findings
GET    /api/v1/findings/{id}
PATCH  /api/v1/findings/{id}
GET    /api/v1/findings/stats
```

### Graph
```
GET    /api/v1/graph/{target_id}
```

### Modules
```
GET    /api/v1/modules
PATCH  /api/v1/modules/{id}
POST   /api/v1/modules/{id}/health
POST   /api/v1/modules/health-all
```

### Settings
```
GET    /api/v1/settings/apikeys
POST   /api/v1/settings/apikeys
DELETE /api/v1/settings/apikeys/{key_name}
GET    /api/v1/settings/defaults
PUT    /api/v1/settings/defaults
```

### Workspaces
```
GET    /api/v1/workspaces
POST   /api/v1/workspaces
PATCH  /api/v1/workspaces/{id}
DELETE /api/v1/workspaces/{id}
GET    /api/v1/workspaces/{id}/members
POST   /api/v1/workspaces/{id}/invite
PATCH  /api/v1/workspaces/{id}/plan
```

### System (superadmin)
```
GET    /api/v1/system/stats
GET    /api/v1/system/users
PATCH  /api/v1/system/users/{id}
GET    /api/v1/system/workspaces
GET    /api/v1/system/logs
POST   /api/v1/system/recalculate-scores
```

## Sprint history

| Sprint | Key deliverables |
|--------|-----------------|
| 1-5 | Core: Docker, auth, Holehe, HIBP, Sherlock, score engine, graph, timeline, settings |
| 6-10 | Premium scanners, OAuth framework, intelligence engine, fingerprint, scraper engine |
| 11-15 | Identity estimation, persona clustering, dual score, real-time logs, multi-workspace |
| 16-20 | OAuth accounts, 43 scrapers, scraper UI, plans, registration |
| 21-25 | Admin panel, name blacklist, DNS blocklist, executive summary, CSV export |
| 26-30 | 51 scrapers, PageRank, eigenvalue fingerprint, generative avatar, landing page, SSE |
| 31-35 | 71 scrapers, pixel art avatar, quick scan, landing redesign |
| 36-40 | Markov chain, graph_context, name resolution, email age fix, graph connectivity |
| 41-42 | Clustering fix, persona platform, bio cleanup, accounts tab, graph readability |
| 43 | CLAUDE.md rewrite, architecture whitepaper, roadmap |
