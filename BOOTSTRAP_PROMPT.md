# Bootstrap prompt — paste this into Claude Code

Read CLAUDE.md for full context. Read XPOSE_VISION_PRD.md for product vision.
Then execute Sprint 1 to build the v0.1.0 MVP. Every decision here traces back to the PRD.

## Sprint 1 — Operator MVP (v0.1.0)

### 1. Docker Compose (`docker-compose.yml`)

```yaml
services:
  postgres:  # PostgreSQL 16 + pgvector, port 5432, volume, healthcheck pg_isready
  redis:     # Redis 7, port 6379, healthcheck redis-cli ping
  api:       # FastAPI, port 8000, hot reload, depends on postgres+redis
  worker:    # Celery worker, same image as api, celery -A api.tasks worker -l info -c 4
  beat:      # Celery beat, same image, celery -A api.tasks beat -l info
```

Shared network `xpose-net`. `.env` file for config. All services healthchecked.

### 2. Python project setup

`requirements.txt`:
```
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
asyncpg
alembic
celery[redis]
redis
pydantic>=2.0
pydantic-settings
python-dotenv
python-multipart
pyjwt
bcrypt
httpx
holehe
maigret
```

`.env.example`:
```
DATABASE_URL=postgresql+asyncpg://xpose:xpose@postgres:5432/xpose
DATABASE_URL_SYNC=postgresql://xpose:xpose@postgres:5432/xpose
REDIS_URL=redis://redis:6379/0
SECRET_KEY=change-me-please-use-a-real-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=7
HIBP_API_KEY=
MAXMIND_LICENSE=
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

`api/config.py` — Pydantic BaseSettings class loading from .env.
`api/main.py` — FastAPI app with:
- CORS middleware (CORS_ORIGINS from config)
- Lifespan for DB engine setup/teardown
- `/health` endpoint (returns DB + Redis status)
- Include all routers with /api/v1 prefix
- Exception handlers for common errors

### 3. Database models (`api/models/`)

Use SQLAlchemy 2.0 `Mapped`, `mapped_column`, `relationship` style.
UUIDs via `uuid.uuid4` default. Timestamps via `func.now()`.

Create ALL tables from CLAUDE.md schema — the full set:
- `api/models/workspace.py` — workspaces table
- `api/models/user.py` — users table + user_workspaces junction
- `api/models/target.py` — targets table
- `api/models/scan.py` — scans table
- `api/models/finding.py` — findings table (with all indexes)
- `api/models/identity.py` — identities + identity_links tables
- `api/models/module.py` — modules table
- `api/models/account.py` — accounts table (Layer 3, empty for now)
- `api/models/alert.py` — alerts table (Phase 2, empty for now)
- `api/models/report.py` — reports table (Phase 2, empty for now)
- `api/models/audit_log.py` — audit_log table
- `api/models/__init__.py` — imports all, exposes Base

Even though Phase 1 only uses a subset, ALL tables exist from day 1.
This prevents migration hell when Phase 2/3 features come online.

### 4. Alembic

- `alembic init alembic`
- Configure async engine in `alembic/env.py`
- First migration: `CREATE EXTENSION IF NOT EXISTS "pgcrypto"` + all tables
- Verify migration applies cleanly: `alembic upgrade head`

### 5. Auth system (`api/auth/`)

Phase 1 auth = local JWT only. But architecture supports SSO/MFA later.

- `api/auth/security.py`:
  - `hash_password(plain)` → bcrypt hash
  - `verify_password(plain, hashed)` → bool
  - `create_access_token(user_id, workspace_id, role)` → JWT string
  - `create_refresh_token(user_id)` → JWT string
  - `decode_token(token)` → payload dict

- `api/auth/dependencies.py`:
  - `get_current_user` → FastAPI Depends, extracts user from JWT
  - `get_current_workspace` → extracts workspace_id from JWT claims
  - `require_role(roles)` → dependency factory for RBAC

- `api/routers/auth.py`:
  - `POST /api/v1/auth/register` — create first user (only works if no users exist = setup wizard)
    Body: {email, password, display_name}
    Creates user + default workspace + superadmin role
    Returns JWT pair
  - `POST /api/v1/auth/login` — email + password → JWT pair
  - `POST /api/v1/auth/refresh` — refresh token → new access + refresh
  - `GET /api/v1/auth/me` — current user with workspaces and roles

### 6. Seed modules (`scripts/seed_modules.py`)

Async script that upserts all modules from CLAUDE.md into the modules table.
Run via: `docker compose exec api python scripts/seed_modules.py`

Layer 1 (enabled):
- email_validator, holehe, maigret, sherlock, ghunt, hibp, h8mail

Layer 2 (disabled):
- maxmind_geo, whois_lookup, databroker_check, paste_monitor

Layer 3 (disabled):
- google_auditor, exodus_tracker, browser_auditor

Set supported_regions: most are ["*"], databroker_check is ["US","UK","CA","AU"].

### 7. Base scanner + Holehe wrapper

`api/services/base.py`:
- ScanResult dataclass + BaseScanner abstract class (exactly as in CLAUDE.md)

`api/services/layer1/__init__.py`
`api/services/layer1/holehe_scanner.py`:
- Inherits BaseScanner
- MODULE_ID = "holehe", LAYER = 1, CATEGORY = "social"
- `async def scan(email)`:
  - Import and run holehe against the email
  - For each site where account IS found:
    - Create ScanResult with category="social_account", severity="medium" if major site (Google, Facebook, Twitter, Instagram, LinkedIn) else "low"
    - indicator_value = email, indicator_type = "email"
    - url = site URL
    - verified = True (holehe confirms existence)
  - Return list of ScanResults
- `async def health_check()`: Try one known-good email, return True if holehe runs
- Rate limit: 1 request per second between sites

`api/services/layer1/email_validator.py`:
- Simple email validation: regex check, MX record lookup via DNS, detect disposable providers
- Returns ScanResult with category="metadata", severity="info"

### 8. Scan orchestrator (`api/tasks/`)

`api/tasks/__init__.py`:
- Celery app configuration with Redis broker
- Task serializer = json
- Result backend = redis
- Task routes for priority queues

`api/tasks/scan_orchestrator.py`:
- `launch_scan(scan_id)` Celery task:
  1. Load scan from DB, update status to "running"
  2. Load target email
  3. For each module in scan.modules:
     a. Check if module is enabled
     b. Dispatch `run_module.delay(scan_id, module_id, email)`
     c. Update module_progress: {module: "queued"}
  4. Use Celery chord: all module tasks → finalize_scan callback
  5. `finalize_scan(scan_id)`:
     - Count total findings, count new findings (not in previous scans)
     - Update scan: status=completed, completed_at, duration_ms, findings_count, new_findings
     - Update target: status=completed, last_scanned
     - Trigger score computation (placeholder for v0.3)

`api/tasks/module_tasks.py`:
- `run_module(scan_id, module_id, email)` Celery task:
  1. Instantiate the right scanner class based on module_id
  2. Update module_progress: {module: "running"}
  3. Call scanner.scan(email)
  4. For each ScanResult:
     a. Check for duplicates (same module + indicator_value + title for this target)
     b. If new: create Finding record. If existing: update last_seen.
     c. Extract identity nodes (email, username from URL patterns)
     d. Create/update Identity records
  5. Update module_progress: {module: "completed"} or {module: "failed"}
  6. Handle exceptions: log error, mark module as failed, continue

### 9. API routers

`api/routers/targets.py`:
- POST /api/v1/targets — validate email format, check uniqueness per workspace, create target
- GET /api/v1/targets — paginated list, search by email, filter by status/tags, order by score
- GET /api/v1/targets/{id} — detail with last scan summary, score, findings count by severity
- PATCH /api/v1/targets/{id} — update tags, notes, country_code
- DELETE /api/v1/targets/{id} — cascade delete (confirm with ?confirm=true query param)

`api/routers/scans.py`:
- POST /api/v1/scans — {target_id, modules: ["holehe","email_validator"]}
  Validate target exists in workspace, validate modules exist and are enabled
  Create Scan record, dispatch launch_scan.delay(scan_id)
  Return scan with status=queued
- GET /api/v1/scans — list, filter by target_id and status
- GET /api/v1/scans/{id} — detail with module_progress
- POST /api/v1/scans/{id}/cancel — revoke Celery task, update status=cancelled

`api/routers/findings.py`:
- GET /api/v1/findings — paginated, filter by target_id, module, severity, category, status
- GET /api/v1/findings/{id} — full detail including raw data JSONB
- PATCH /api/v1/findings/{id} — update status only (resolved, false_positive, monitoring)
- GET /api/v1/findings/stats — grouped counts: by severity, by category, by module

`api/routers/modules.py`:
- GET /api/v1/modules — list all modules with health status
- PATCH /api/v1/modules/{id} — enable/disable only (config changes = later)

Wire everything in main.py with proper tags for OpenAPI docs.

### 10. React dashboard (`dashboard/`)

`npx create-vite@latest dashboard -- --template react`
Install: tailwindcss, @tailwindcss/vite, react-router-dom, lucide-react

**tailwind.config.js**: extend theme with xpose dark colors from CLAUDE.md.

**Global styles**: Import JetBrains Mono + Inter from Google Fonts.

**Layout** (`src/components/Layout.jsx`):
- Sidebar: dark (#0a0a0f), logo "xpose" in neon green, nav items with lucide icons
  - Dashboard (LayoutDashboard)
  - Targets (Crosshair)
  - Scans (Radar) — maybe later
  - Settings (Settings)
- Main content area: #0f0f14 background
- Top bar: workspace name (hardcoded "Default" for Phase 1), user avatar, logout

**Auth flow**:
- `/login` page: email + password form, dark themed
- On success: store JWT in memory (not localStorage for security), refresh in httpOnly cookie if possible, else memory
- Protected route wrapper: redirect to /login if no token
- First visit with no users: redirect to `/setup` (register form)

**Pages**:

a. **Dashboard** (`src/pages/Dashboard.jsx`):
- 4 stat cards: Total targets, Active scans, Total findings, Critical findings
  Style: dark card (#12121a), border (#1e1e2e), big number in white, label in gray
- Recent scans table (last 10): target email, status badge, modules, duration, findings
- Quick action: email input + "Scan" button → creates target + launches default scan
- Empty state: "Welcome to xpose. Add your first target to start."

b. **Targets** (`src/pages/Targets.jsx`):
- Table: email, country flag (emoji from country_code), status badge, exposure score (colored 0-100), last scanned (relative time), findings count, actions (view, delete)
- Search bar (debounced, filters by email)
- "Add Target" button → modal: email input, country_code dropdown (optional), tags input
- Click row → navigate to target detail

c. **Target Detail** (`src/pages/TargetDetail.jsx`):
- Header: email (monospace, large), score donut (colored by severity bracket), status, last scanned
- Action bar: "New Scan" button (opens module selector popover with checkboxes), "Export" button
- Findings table: severity badge (pill), module name, category, title, URL (clickable), status, first_seen
  Filterable by severity, category, module. Sortable by severity, date.
  Click row → expand with description + raw data (collapsible JSON viewer)
- Scan history: list at bottom, each with status, modules, duration, findings count

d. **Settings** (`src/pages/Settings.jsx`):
- Modules section: list of all modules, toggle switch (enabled/disabled), health dot (green/red/gray), layer badge, requires_auth indicator
- Profile section: email, display name, change password form

**API client** (`src/lib/api.js`):
- Base URL from env (VITE_API_URL=http://localhost:8000/api/v1)
- Wrapper around fetch with JWT injection, error handling, auto-refresh on 401
- Functions: login(), register(), getMe(), getTargets(), createTarget(), getTarget(), deleteTarget(), createScan(), getScans(), getScan(), getFindings(), getFindingsStats(), getModules(), patchModule()

**Polling**: Target detail page polls GET /api/v1/scans/{id} every 2 seconds while any scan has status=running. Show animated progress per module.

### 11. Dockerfile

Single Dockerfile for api + worker + beat:
- Python 3.12 slim base
- Copy requirements.txt, pip install
- Copy api/ and scripts/
- Default CMD: uvicorn api.main:app
- Override in docker-compose for worker and beat

### 12. Commit

```bash
git add -A
git commit -m "feat: v0.1.0 — xpose MVP, Identity Threat Intelligence platform

- Docker Compose (PG16 + Redis + API + Worker + Beat)
- Full 4-layer DB schema (12 tables, all indexes)
- JWT auth with workspace scoping + RBAC foundation
- Target CRUD with workspace isolation
- Holehe + email validator scan modules
- Celery scan orchestrator with per-module progress tracking
- Findings API with filtering and stats
- Dark cyber React dashboard (targets, scans, findings)
- Module registry with health monitoring
- Audit logging foundation

PRD: XPOSE_VISION_PRD.md | Arch: CLAUDE.md"

git tag -a v0.1.0 -m "v0.1.0: xpose Identity Threat Intelligence MVP"
```

Start with docker-compose.yml. Go!
