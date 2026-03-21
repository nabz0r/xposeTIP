# CLAUDE.md — Project context for Claude Code

## What is xpose

Identity Threat Intelligence platform. Bridges deep OSINT tools (SpiderFoot, Maltego)
with consumer-grade UX (Aura, NordProtect). Users see exactly what the internet knows
about them: identity graph, exposure score, breach history, account enumeration,
tracking exposure, data broker presence — with actionable remediation.

Think "personal SOC for your privacy." Every finding is an Identity IOC.

Reference document: XPOSE_VISION_PRD.md contains full product vision, personas,
user stories, UX flows, monetization, legal, and roadmap.

## Developer

- **Name**: Nabil (nabz0r), network/security engineer, 20+ years
- **Background**: Master Mathematics (Sorbonne), CCNA, NSE 1-4, JNCIA
- **Day job**: ThreatConnect cybersecurity support, EMEA region
- **Style**: French, casual, very direct, zero bullshit, heavy abbreviations
- **OS**: macOS — GitHub: nabz0r
- **Related**: HexWGuard (SOC dashboard), HexGuard (honeypot), SS7 Guardian
- **OSINT toolkit**: GHunt (custom DroidGuard patch), Holehe, Maigret, h8mail,
  Mosint, Blackbird, Sherlock — all operational on macOS

## Global scope

xpose is NOT Luxembourg-only. The product works worldwide with varying depth:
- **US targets**: Maximum data. Voter rolls, court records, property records, Spokeo,
  WhitePages, BeenVerified, ThatsThem, PeopleFinder — all public, no legal barrier.
  US has no federal privacy law equivalent to GDPR. Gold mine for exposure auditing.
- **EU targets**: GDPR applies but we're showing exposure that already exists publicly.
  We don't create data, we reveal it. Lawful basis = consent (user scans themselves)
  or legitimate interest (consultant with DPA).
- **Rest of world**: Varies. Most countries have less protection than EU.
  Our module system adapts — region-specific modules can be enabled/disabled.

The exposure score for a US target will naturally be higher (more public data available)
than for an EU target (GDPR reduces public exposure). That's a feature, not a bug —
it proves the point about digital exposure varying by jurisdiction.

## Current version: v0.22.0

Sprint 23 complete. 25 scanners (17 implemented + 8 placeholder), 43 scrapers
across 7 categories (social, breach, metadata, people_search, identity, archive,
gaming), 5 intelligence analyzers, digital fingerprint (8-axis radar), persona
clustering engine, dual score (exposure/threat), identity estimation
(gender/age/nationality), per-field confidence, IdentityCard + PersonaCard,
real-time log viewer with Redis ring buffer, plans (Free/Consultant/Enterprise)
with enforcement, open registration, admin panel (users/workspaces management),
quick scan from targets list, multi-workspace, RBAC, organizations, source
scoring, Google/Microsoft OAuth framework, DB-driven name blacklist system,
reworked targets list (avatar, dual score, timestamp), scan metadata with
log download, target exposure leaderboard on dashboard.

## Tech stack (locked)

- **Backend**: FastAPI + SQLAlchemy 2.0 (async, mapped_column) + Alembic
- **Queue**: Celery + Redis broker
- **Database**: PostgreSQL 16 + pgvector
- **Frontend**: React 18 + Vite + Tailwind CSS 4
- **Auth**: JWT (PyJWT + bcrypt) — SSO and MFA planned for later phases
- **UI**: Dark cyber theme. Inter font (UI), JetBrains Mono (data). Neon green accent #00ff88.
- **Charts**: Recharts (bar, donut)
- **Graph**: D3.js force-directed (identity graph) + D3 geo (world heatmap)
- **Map**: SVG world map with Mercator projection (replaced Leaflet in v0.5.0)
- **Reports**: WeasyPrint (HTML→PDF) — planned
- **OSINT**: Holehe, Sherlock (Python wrappers), plus 15 custom scanners + 43 data-driven scrapers
- **Identity**: Genderize.io, Agify.io, Nationalize.io (free, no auth)
- **Archive**: Wayback Machine CDX API (free, no auth)
- **Breach**: HIBP API ($3.50/mo) + XposedOrNot (free)
- **Geolocation**: ip-api.com (free) + MaxMind GeoLite2 (free, local DB)
- **Encryption**: Fernet (AES-256) for API keys at rest
- **Containers**: Docker Compose (5 services)
- **Notifications**: Toast system (ToastProvider context, auto-dismiss 4s, stackable)

## Architecture concepts

### Multi-tenant from day 1
Everything belongs to a `workspace`. Phase 1 = one workspace (admin).
Phase 2 = one per consultant client. Phase 3 = one per consumer.
PostgreSQL Row-Level Security (RLS) enforces isolation at DB level.

### RBAC
Five roles: superadmin, admin, consultant, client, user.
Stored per-workspace via user_workspaces junction table.
Phase 1 only uses superadmin. Others activate in later phases.

### Plugin architecture
Every scanner inherits BaseScanner, implements scan() and health_check().
Phase 2+: community modules via Python entry_points (pip install, restart, done).

### 4 Layers
- Layer 1: Passive recon (email → accounts, breaches, Google metadata, reputation)
- Layer 2: Public databases (geoloc, WHOIS, DNS security, data brokers, pastes)
- Layer 3: Voluntary audit (OAuth account linking, app trackers, browser)
- Layer 4: Intelligence engine (score, graph, profile aggregation, remediation)

## Scanner registry (api/tasks/module_tasks.py)

Complete SCANNER_REGISTRY with all 17 implemented scanners:

```python
SCANNER_REGISTRY = {
    # Layer 1 — Passive Recon (12 scanners)
    "email_validator": "api.services.layer1.email_validator:EmailValidatorScanner",
    "holehe":          "api.services.layer1.holehe_scanner:HoleheScanner",
    "hibp":            "api.services.layer1.hibp_scanner:HIBPScanner",
    "sherlock":        "api.services.layer1.sherlock_scanner:SherlockScanner",
    "gravatar":        "api.services.layer1.gravatar_scanner:GravatarScanner",
    "social_enricher": "api.services.layer1.social_enricher:SocialEnricherScanner",
    "google_profile":  "api.services.layer1.google_scanner:GoogleScanner",
    "emailrep":        "api.services.layer1.emailrep_scanner:EmailRepScanner",
    "epieos":          "api.services.layer1.epieos_scanner:EpieosScanner",
    "fullcontact":     "api.services.layer1.fullcontact_scanner:FullContactScanner",
    "github_deep":     "api.services.layer1.github_scanner:GitHubDeepScanner",
    "username_hunter": "api.services.layer1.username_scanner:UsernameScannerPlugin",
    # Layer 2 — Public Databases (5 scanners)
    "whois_lookup":    "api.services.layer2.whois_scanner:WhoisScanner",
    "maxmind_geo":     "api.services.layer2.maxmind_scanner:MaxmindScanner",
    "geoip":           "api.services.layer2.geoip_scanner:GeoIPScanner",
    "leaked_domains":  "api.services.layer2.leaked_scanner:LeakedScanner",
    "dns_deep":        "api.services.layer2.dns_scanner:DNSDeepScanner",
}
```

Seeded modules (25 total in `scripts/seed_modules.py`): 17 implemented + 8 placeholder
(maigret, ghunt, h8mail, databroker_check, paste_monitor, google_auditor, exodus_tracker, browser_auditor).

Lazy-loaded via `importlib` — missing deps don't crash the worker.
Modules without a registered scanner are marked `implemented: false` in the API response
and silently excluded from scan dispatch.

Additionally, the scraper engine (`scraper_engine` module) executes 43 data-driven scrapers
defined in `scripts/seed_scrapers.py` and stored in the `scrapers` DB table. These are
editable via the Scrapers UI page without code changes.

## Scraper registry (scripts/seed_scrapers.py)

43 scrapers across 7 categories, all editable via UI:

| Category | Count | Scrapers |
|----------|-------|----------|
| social | 21 | Reddit, GitHub, Steam, Keybase, Medium, HackerNews, Dev.to, GitLab, About.me, Imgur, Mastodon, StackOverflow, Pinterest, Linktree, Disqus, Twitch, Telegram, Letterboxd, BuyMeACoffee, Pastebin User, Docker Hub |
| breach | 3 | XposedOrNot, LeakCheck, Pastebin Dumps |
| metadata | 4 | Gravatar, crt.sh subdomains, SecurityTrails, Disposable Email |
| identity | 3 | Genderize (gender), Agify (age), Nationalize (nationality) |
| archive | 3 | Wayback Domain History, Wayback Snapshot Count, Wayback Profile Archive |
| gaming | 7 | Steam (expanded), Xbox Gamertag, PSN Profile, Epic Games, Riot Games, Chess.com, Lichess |
| music | 2 | Mixcloud, Duolingo |

All scrapers use the ScraperEngine: URL template + regex/JSONPath extraction.
Input types: email, username, domain, first_name.
Transforms: email_to_username, email_to_domain, email_to_first_name, email_to_fullname, url_encode.

### Adding a new scanner

1. Create scanner class inheriting `BaseScanner` (in `api/services/layerN/`)
2. Add entry to `SCANNER_REGISTRY` in `api/tasks/module_tasks.py`
3. Add module row to `MODULES` list in `scripts/seed_modules.py`
4. If scanner needs an API key, add to `run_module()` key loading block
5. Re-seed: `python scripts/seed_modules.py`

## Layer 4 services

### Exposure score engine (api/services/layer4/score_engine.py)

Called automatically in `finalize_scan` after every scan completion.
Updates `target.exposure_score` (0-100) and `target.score_breakdown` (JSONB).

```python
SCORE_WEIGHTS = {
    "breach": 0.25, "social_account": 0.20, "tracking": 0.15,
    "geolocation": 0.12, "data_broker": 0.10, "metadata": 0.08,
    "domain_registration": 0.05, "paste": 0.05,
}
SEVERITY_MULTIPLIER = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
```

Per-category: sum(severity_multiplier per finding), capped at 100.
Total = weighted sum across categories.

### Identity graph builder (api/services/layer4/graph_builder.py)

Called automatically in `finalize_scan` after score computation.
Extracts identity nodes and links from findings:
- Social account → `Identity(type="social_url")` + `IdentityLink(type="registered_with")`
- Breach → `Identity(type="breach")` + `IdentityLink(type="exposed_in")`
- Username → `IdentityLink(type="same_person")` back to email

### Profile aggregator (api/services/layer4/profile_aggregator.py)

Called automatically in `finalize_scan` after graph building.
Merges all findings into a unified profile stored in `target.profile_data` (JSONB).
Extracts: name, location, social profiles, breach count, credential status, reputation.

**Important**: Excludes `geoip`/`maxmind_geo` modules from location extraction — those
are mail server locations, not user locations.

### Identity estimation (via profile aggregator)

Extracted from Genderize/Agify/Nationalize scraper findings during profile aggregation.
Stored in `target.profile_data.identity_estimation`:
- `gender` + `gender_probability` (from Genderize.io)
- `age` + `age_sample_count` (from Agify.io)
- `nationalities[]` with `country_code` + `probability` (from Nationalize.io, top 3)

### Persona clustering engine (api/services/layer4/persona_engine.py)

Identifies distinct digital personas from identity graph nodes.
Clusters social accounts by shared usernames, profile names, avatars.
Each persona gets: name, confidence score, associated accounts, risk assessment.
Stored in `target.profile_data.personas` (JSONB array).
Feature-gated: requires Consultant or Enterprise plan (or superadmin).

### Dual score engine

Two scores computed in `finalize_scan`:
- **Exposure score** (0-100): How much data is publicly visible. Weighted by category.
- **Threat score** (0-100): Active risk level. Weighted by breach recency, credential leaks, active tracking.
Both stored on `target` model. UI shows both with color-coded indicators.

## Plans & Monetization (api/services/plan_config.py)

Three-tier plan system enforced at API level:

| Plan | Price | Targets | Scans/mo | Layers | Features |
|------|-------|---------|----------|--------|----------|
| Free | €0 | 1 | 5 | L1 only | Basic exposure scan |
| Consultant | €49/mo | 25 | 100 | L1+L2 | Persona clustering, multi-workspace, PDF reports |
| Enterprise | €199/mo | Unlimited | Unlimited | All | Intelligence pipeline, API access, priority support |

Enforcement points:
- `check_target_limit()` — blocks target creation over plan quota
- `check_scan_limit()` — blocks scan creation over monthly quota
- `filter_modules_by_plan()` — strips modules from layers not included in plan
- `check_feature()` — gates features like persona clustering, intelligence pipeline
- **superadmin bypasses ALL limits** — `is_superadmin()` check in every function
- Plan lives on `Workspace`, not on `User`
- First registered user = superadmin + enterprise; subsequent = user + free

## API design

All endpoints prefixed with `/api/v1/`. All require auth (JWT Bearer) except health.
All scoped to workspace via middleware (extracts workspace_id from JWT claims).

### Auth
```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
PATCH /api/v1/auth/profile      -- update display_name
```

### Targets
```
GET    /api/v1/targets
POST   /api/v1/targets
GET    /api/v1/targets/{id}
PATCH  /api/v1/targets/{id}
DELETE /api/v1/targets/{id}
GET    /api/v1/targets/{id}/profile   -- aggregated profile data
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
PATCH  /api/v1/findings/{id}          -- update status (resolved, false_positive)
GET    /api/v1/findings/stats
```

### Graph
```
GET    /api/v1/graph/{target_id}      -- identity graph nodes + edges + stats
```

### Modules
```
GET    /api/v1/modules                -- list all + health + implemented flag
PATCH  /api/v1/modules/{id}           -- enable/disable
POST   /api/v1/modules/{id}/health    -- single health check
POST   /api/v1/modules/health-all     -- bulk health check
```

### Settings
```
GET    /api/v1/settings/apikeys       -- list configured API keys (masked)
POST   /api/v1/settings/apikeys       -- save API key (Fernet encrypted)
POST   /api/v1/settings/apikeys/custom -- save custom key
POST   /api/v1/settings/apikeys/{key_name}/validate
DELETE /api/v1/settings/apikeys/{key_name}
GET    /api/v1/settings/defaults      -- scan default modules
PUT    /api/v1/settings/defaults      -- update scan defaults
```

### Workspaces
```
GET    /api/v1/workspaces             -- list user workspaces
POST   /api/v1/workspaces             -- create workspace
PATCH  /api/v1/workspaces/{id}        -- update workspace
DELETE /api/v1/workspaces/{id}        -- delete workspace
GET    /api/v1/workspaces/{id}/members
POST   /api/v1/workspaces/{id}/invite -- invite member by email
PATCH  /api/v1/workspaces/{id}/members/{user_id}
DELETE /api/v1/workspaces/{id}/members/{user_id}
GET    /api/v1/workspaces/plans       -- list available plans
GET    /api/v1/workspaces/{id}/usage  -- target count, scans this month, limits
PATCH  /api/v1/workspaces/{id}/plan   -- change workspace plan (superadmin)
```

### System (superadmin only)
```
GET    /api/v1/system/stats           -- platform statistics
GET    /api/v1/system/users           -- all users with workspace memberships
PATCH  /api/v1/system/users/{id}      -- activate/deactivate user
GET    /api/v1/system/workspaces      -- all workspaces with member/target/scan counts
GET    /api/v1/system/logs            -- structured logs from Redis ring buffer
DELETE /api/v1/system/logs            -- clear logs
POST   /api/v1/system/recalculate-scores
```

## Database schema

All tables: UUID PKs (gen_random_uuid), created_at/updated_at TIMESTAMPTZ.
All queries scoped to workspace_id. Key tables:

- **workspaces** — multi-tenant isolation, plan (free/consultant/enterprise), settings JSONB (stores encrypted API keys)
- **users** — auth, display_name, avatar
- **user_workspaces** — RBAC junction (role per workspace)
- **targets** — email, exposure_score, score_breakdown, profile_data (JSONB)
- **scans** — status, modules JSONB, module_progress JSONB, celery_task_id
- **findings** — the big table. module, layer, category, severity, data JSONB (forensic archive)
- **identities** — identity nodes (email, username, social_url, etc.)
- **identity_links** — edges between identity nodes
- **modules** — scanner metadata, health_status, auth_config
- **name_blacklist** — name validation rules (exact/contains/regex), manageable from System UI

Notable column added in v0.5.0: `targets.profile_data` (JSONB) — aggregated profile.
Migration: `alembic/versions/002_add_profile_data.py`.

## Frontend pages

### Dashboard (/)
Stats cards: total targets, active scans, total findings, HIGH count, most exposed target.
Recharts severity bar chart + module donut chart. Quick scan form with 7 default modules.

### Targets (/targets)
Table: email, country, status, fingerprint radar, score, last scanned.
Search + filter. "Add target" modal. Bulk import (CSV/paste). Quick scan button per row.
Click row → detail.

### Target detail (/targets/:id)
ProfileHeader: social profiles strip, credentials leaked status, email security badge,
reputation indicator, data sources count, category-labeled score breakdown.
IdentityCard: photo strip (up to 6 avatars from multiple sources), gender with confidence
bar, age estimation, nationality flags with probability bars. Only renders when identity
data exists.
Tabs: Overview | Findings | Graph | Timeline | Locations | Scans.
- Overview: critical alerts, breach cards, social accounts, mail server locations
- Findings: filterable table (severity/module/status), expandable rows with FindingDataCard
  (enriched cards per scanner type: breach, social, emailrep, github, dns, geo)
- Graph: D3 force-directed identity map
- Timeline: IOC timeline grouped by date
- Locations: SVG world map with Mercator projection, animated pulse rings, labels
- Scans: scan history with module progress badges
Module selector: grouped by layer, "Select all Layer N", lock icon for auth-required, scan time estimates.
Toast notifications on scan completion.

### Settings (/settings)
Tabs: Plan & Billing (usage bars, feature matrix, plan comparison) | Modules (toggle + health) |
API Keys (add/validate/delete, Fernet encrypted) | Scan Defaults | Profile (display_name edit).

### Organization (/organization)
Multi-workspace management. Create/switch workspaces. Plan badge per workspace.
Member management: invite by email, role assignment, remove.
Usage bars (targets, scans/month) with plan limits. Superadmin: inline plan change dropdown.

### System (/system) — superadmin only
Tabs: Stats | Logs | Users | Workspaces.
- Stats: platform-wide metrics, recalculate scores
- Logs: real-time structured logs from Redis ring buffer (LogViewer component)
- Users: all users with workspace memberships, active/inactive toggle, email search
- Workspaces: all workspaces with member/target/scan counts, inline plan dropdown

### Login (/login)
Login/Register toggle. Open registration — first user = superadmin + enterprise,
subsequent = user + free. Invited users (pre-created, no last_login) register with own password.

## Frontend components

- `ProfileHeader.jsx` — uses `/profile` API, shows social strip + stats + category-labeled breakdown
- `IdentityCard.jsx` — photo strip + gender/age/nationality estimation display
- `PersonaCard.jsx` — clustered digital persona display with confidence scores
- `IdentityGraph.jsx` — D3 force-directed with zoom, drag, hover highlight
- `IOCTimeline.jsx` — vertical timeline grouped by date
- `LifeTimeline.jsx` — chronological life events extracted from OSINT data
- `LocationMap.jsx` — pure SVG world map (Mercator projection, animated dots)
- `WorldHeatmap.jsx` — D3 geo choropleth (dashboard)
- `FingerprintRadar.jsx` — 8-axis radar chart (digital fingerprint visualization)
- `LogViewer.jsx` — real-time structured log viewer from Redis ring buffer
- `TargetQuickView.jsx` — slide-out quick preview panel for target details
- `Toast.jsx` — ToastProvider context, auto-dismiss 4s, stackable, top-right
- `Layout.jsx` — sidebar nav, workspace switcher, plan badge, refreshKey pattern

## UI rules

- Background: #0a0a0f. Cards: #12121a, border #1e1e2e
- Accent: #00ff88 (green), #ff2244 (critical), #ff8800 (high), #ffcc00 (medium), #3388ff (low), #666688 (info)
- Monospace (JetBrains Mono) for all data values. Sans-serif (Inter) for UI.
- Cards with subtle glow on hover (box-shadow with accent at 0.1 opacity)
- Severity badge: pill-shaped, colored bg at 0.15 opacity, text full color
- Tables: dark rows, sticky header, zebra #ffffff05 alternate

## Celery worker

Worker command: `celery -A api.tasks worker -l info -c 4 -Q celery,scans,modules`
- Chord-based scan orchestration: launch_scan → [run_module × N] → finalize_scan
- finalize_scan pipeline: count findings → update target → compute score → build graph → aggregate profile
- API keys loaded per-module in run_module (hibp, maxmind_geo, fullcontact)

## Default scan modules

Backend fallback (when workspace has no custom defaults):
`["email_validator", "holehe", "emailrep", "gravatar", "epieos", "github_deep", "dns_deep"]`

Frontend pre-selects: all enabled+implemented L1 + recommended L2 (dns_deep, leaked_domains, geoip).

## Sprint history

| Sprint | Version | Key deliverables |
|--------|---------|-----------------|
| 1 | v0.1.0 | Docker, DB models, JWT auth, Holehe, email_validator, Celery, React dashboard |
| 2 | v0.2.0 | HIBP, Sherlock, WHOIS, MaxMind, score engine, identity graph, IOC timeline, world heatmap |
| 3 | v0.3.0 | Gravatar, Social Enricher, Google Profile, Free GeoIP, settings UI |
| 4 | v0.4.0 | Dynamic API keys (Fernet), key validation, location mapping, scan defaults |
| 5 | v0.5.0 | 7 new scanners, profile aggregation, health checks, SVG world map, toast system |
| 6 | v0.6.0 | Source scoring, Premium scanners, SaaS connectors, OAuth framework |
| 7 | v0.7.0 | Intelligence engine (5 analyzers), Google OAuth audit, demo flow, scaling |
| 8 | v0.8.0 | Digital fingerprint (8-axis radar, hash, snapshots, evolution timeline) |
| 9 | v0.9.0 | Scraper engine: modular scrapers with editable regex in DB |
| 10 | v0.10.0 | Quality polish, dedup, profile name fix, finding details |
| 11 | v0.11.0 | 15 new scrapers: identity estimation, Wayback archive, social expansion (28 total) |
| 12 | v0.12.0 | IdentityCard, photo strip, profile aggregator fix, UX polish |
| 13 | v0.13.0 | Persona clustering engine, per-field confidence scoring, PersonaCard UI |
| 14 | v0.14.0 | Dual score (exposure + threat), score history, LifeTimeline component |
| 15 | v0.15.0 | Real-time log viewer (Redis ring buffer), structured logging, LogViewer UI |
| 16 | v0.16.0 | Multi-workspace support, workspace CRUD, member invite flow, Organization page |
| 17 | v0.17.0 | Connected accounts (OAuth framework), Google/Microsoft audit, Accounts UI |
| 18 | v0.18.0 | 7 gaming scrapers, 6 social scrapers, scraper import/export (43 total) |
| 19 | v0.19.0 | Scraper UI: test runner, toggle, YAML export/import, bulk operations |
| 20 | v0.20.0 | Plans (Free/Consultant/Enterprise), open registration, plan enforcement, billing UI |
| 21 | v0.21.0 | Admin panel (platform users/workspaces), quick scan, invite flow fix |
| 22 | v0.21.1 | Documentation update (v0.14.0 → v0.21.0) — zero code changes |
| 23 | v0.22.0 | Name blacklist system, targets rework, quality polish, scan metadata |

## Bugs fixed (v0.5.x)

- Scanner activation: DB needed re-seeding after adding new modules
- Leaflet black screen: replaced entirely with SVG world map (Mercator projection)
- GeoIP labeling: profile aggregator now excludes geoip/maxmind_geo from user location
- Health checks: added POST /modules/{id}/health and /modules/health-all endpoints
- Default modules: backend fallback updated from 3 to 7 free scanners

## Known issues

- **emailrep.io rate limiting from Docker**: Cloud/Docker IPs get rate-limited more aggressively.
  Works better from residential IPs. Not a code bug.
- **Sherlock IP ban risk**: Aggressive rate limiting configured (5 rpm). Still risky on shared IPs.
- **GHunt not implemented**: Needs DroidGuard patched credentials. Scanner class not yet built.
- **Maigret not implemented**: Pure Python but heavy dependencies. Planned for v0.6.
- **WorldHeatmap CDN dependency**: Fetches world-atlas TopoJSON from jsdelivr CDN at runtime.
  If CDN is unreachable, heatmap silently fails.
- **No WebSocket**: Scan progress uses 3s polling, not WebSocket. Good enough for now.

## Critical rules

- All OSINT tools in Celery workers, NEVER in API process
- Rate limit every external call — config in modules.rate_limit
- Raw tool output in findings.data JSONB forever
- NEVER store plaintext passwords — breach names + hash prefixes only
- API keys AES-256 encrypted at rest (Fernet, key derived from SECRET_KEY)
- Every DB query scoped to workspace_id (prepare for RLS in Phase 2)
- findings is the biggest table — design indexes and queries accordingly
- US targets = more data available = higher scores. This is correct.
- GHunt needs DroidGuard patch (already built by dev)
- HIBP API key $3.50/mo, required for breach depth
- Holehe = pure Python, zero external deps
- Sherlock needs aggressive rate limiting (IP ban risk)
- GeoIP findings = mail server location, NOT user location. Always label accordingly.
