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

## Tech stack (locked)

- **Backend**: FastAPI + SQLAlchemy 2.0 (async, mapped_column) + Alembic
- **Queue**: Celery + Redis broker
- **Database**: PostgreSQL 16 + pgvector
- **Frontend**: React 18 + Vite + Tailwind CSS
- **Auth**: Phase 1 = JWT (PyJWT + bcrypt). Phase 2 = +SSO (Authlib). Phase 3 = +MFA (pyotp)
- **UI**: Dark cyber theme. Inter font (UI), JetBrains Mono (data). Neon green accent.
- **Charts**: Recharts
- **Graph**: D3.js force-directed
- **Reports**: WeasyPrint (HTML→PDF)
- **OSINT**: Holehe, Maigret, GHunt, Sherlock, h8mail (Python wrappers)
- **Breach**: HIBP API ($3.50/mo)
- **Geolocation**: MaxMind GeoLite2 (free, local DB)
- **App trackers**: Exodus Privacy DB (CC-BY-SA)
- **Containers**: Docker Compose
- **Reverse proxy**: Caddy (auto HTTPS in prod)

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
- Layer 1: Passive recon (email → accounts, breaches, Google metadata)
- Layer 2: Public databases (geoloc, WHOIS, data brokers, pastes, DNS history)
- Layer 3: Voluntary audit (OAuth account linking, app trackers, browser)
- Layer 4: Intelligence engine (score, graph, patterns, remediation)

## Database schema

All tables: UUID PKs (gen_random_uuid), created_at/updated_at TIMESTAMPTZ.
All queries scoped to workspace_id.

### workspaces
```sql
id              UUID PK
name            VARCHAR(100) NOT NULL
slug            VARCHAR(100) UNIQUE NOT NULL
owner_id        UUID FK → users.id
plan            VARCHAR(20) DEFAULT 'free'  -- free|pro|consultant|enterprise
settings        JSONB DEFAULT '{}'
created_at      TIMESTAMPTZ DEFAULT NOW()
updated_at      TIMESTAMPTZ DEFAULT NOW()
```

### users
```sql
id              UUID PK
email           VARCHAR(255) UNIQUE NOT NULL
password_hash   VARCHAR(255)          -- NULL if OAuth-only
display_name    VARCHAR(255)
avatar_url      VARCHAR(1024)
auth_provider   VARCHAR(20) DEFAULT 'local'  -- local|google|microsoft|github
auth_provider_id VARCHAR(255)
mfa_secret      TEXT                  -- encrypted, NULL if not enabled
mfa_enabled     BOOLEAN DEFAULT false
is_active       BOOLEAN DEFAULT true
last_login      TIMESTAMPTZ
created_at      TIMESTAMPTZ DEFAULT NOW()
updated_at      TIMESTAMPTZ DEFAULT NOW()
```

### user_workspaces
```sql
user_id         UUID FK → users.id ON DELETE CASCADE
workspace_id    UUID FK → workspaces.id ON DELETE CASCADE
role            VARCHAR(20) NOT NULL  -- superadmin|admin|consultant|client|user
joined_at       TIMESTAMPTZ DEFAULT NOW()
PRIMARY KEY (user_id, workspace_id)
```

### targets
```sql
id              UUID PK
workspace_id    UUID FK → workspaces.id ON DELETE CASCADE
email           VARCHAR(255) NOT NULL
display_name    VARCHAR(255)
avatar_url      VARCHAR(1024)
country_code    VARCHAR(2)            -- ISO 3166-1 alpha-2, for region-specific modules
status          VARCHAR(20) DEFAULT 'pending'
                -- pending|scanning|completed|error
exposure_score  INTEGER               -- 0-100
score_breakdown JSONB                 -- {breach:30, social:20, tracking:15, geo:10, ...}
first_scanned   TIMESTAMPTZ
last_scanned    TIMESTAMPTZ
tags            TEXT[]
notes           TEXT
created_at      TIMESTAMPTZ DEFAULT NOW()
updated_at      TIMESTAMPTZ DEFAULT NOW()

UNIQUE(workspace_id, email)
INDEX idx_targets_workspace ON targets(workspace_id)
INDEX idx_targets_score ON targets(exposure_score DESC)
```

### scans
```sql
id              UUID PK
workspace_id    UUID FK → workspaces.id ON DELETE CASCADE
target_id       UUID FK → targets.id ON DELETE CASCADE
status          VARCHAR(20) DEFAULT 'queued'
                -- queued|running|completed|partial|failed|cancelled
layer           INTEGER DEFAULT 1
modules         JSONB                 -- ["holehe","maigret","hibp"]
module_progress JSONB                 -- {"holehe":"completed","maigret":"running"}
started_at      TIMESTAMPTZ
completed_at    TIMESTAMPTZ
duration_ms     INTEGER
findings_count  INTEGER DEFAULT 0
new_findings    INTEGER DEFAULT 0     -- findings not in previous scan
error_log       TEXT
celery_task_id  VARCHAR(255)
created_at      TIMESTAMPTZ DEFAULT NOW()

INDEX idx_scans_workspace ON scans(workspace_id)
INDEX idx_scans_target ON scans(target_id)
```

### findings
```sql
id              UUID PK
workspace_id    UUID FK → workspaces.id ON DELETE CASCADE
scan_id         UUID FK → scans.id ON DELETE CASCADE
target_id       UUID FK → targets.id ON DELETE CASCADE
module          VARCHAR(50) NOT NULL
layer           INTEGER NOT NULL
category        VARCHAR(30) NOT NULL
                -- social_account|breach|credential|metadata|tracking|
                -- geolocation|device|data_broker|paste|app_permission|
                -- dns_record|domain_registration|browser_data|public_record
severity        VARCHAR(10) NOT NULL  -- info|low|medium|high|critical
title           VARCHAR(255) NOT NULL
description     TEXT
data            JSONB                 -- raw module output (forensic archive, never delete)
url             VARCHAR(1024)
indicator_value VARCHAR(500)
indicator_type  VARCHAR(30)           -- email|username|ip|phone|domain|device_id|address
verified        BOOLEAN DEFAULT false
status          VARCHAR(20) DEFAULT 'active'
                -- active|resolved|false_positive|monitoring
first_seen      TIMESTAMPTZ DEFAULT NOW()
last_seen       TIMESTAMPTZ DEFAULT NOW()
created_at      TIMESTAMPTZ DEFAULT NOW()

-- Partition by workspace_id for large-scale deployments
INDEX idx_findings_workspace ON findings(workspace_id)
INDEX idx_findings_target ON findings(target_id)
INDEX idx_findings_module ON findings(module)
INDEX idx_findings_severity ON findings(severity)
INDEX idx_findings_category ON findings(category)
INDEX idx_findings_indicator ON findings(indicator_value)
```

### identities
```sql
id              UUID PK
workspace_id    UUID FK → workspaces.id ON DELETE CASCADE
target_id       UUID FK → targets.id ON DELETE CASCADE
type            VARCHAR(20) NOT NULL
                -- email|username|phone|full_name|ip|domain|
                -- device_id|social_url|avatar_hash|address
value           VARCHAR(500) NOT NULL
platform        VARCHAR(100)
source_module   VARCHAR(50)
source_finding  UUID FK → findings.id
confidence      FLOAT DEFAULT 1.0
metadata        JSONB
created_at      TIMESTAMPTZ DEFAULT NOW()

UNIQUE(workspace_id, target_id, type, value)
```

### identity_links
```sql
id              UUID PK
workspace_id    UUID FK → workspaces.id ON DELETE CASCADE
source_id       UUID FK → identities.id ON DELETE CASCADE
dest_id         UUID FK → identities.id ON DELETE CASCADE
link_type       VARCHAR(30) NOT NULL
                -- same_person|registered_with|mentioned_together|
                -- resolves_to|logged_from|linked_account|shares_password_hash
confidence      FLOAT DEFAULT 1.0
source_module   VARCHAR(50)
evidence        JSONB
created_at      TIMESTAMPTZ DEFAULT NOW()

UNIQUE(workspace_id, source_id, dest_id, link_type)
```

### modules
```sql
id              VARCHAR(50) PK
display_name    VARCHAR(100) NOT NULL
description     TEXT
layer           INTEGER NOT NULL
category        VARCHAR(50)
enabled         BOOLEAN DEFAULT true
requires_auth   BOOLEAN DEFAULT false
auth_config     JSONB                 -- {"api_key_env":"HIBP_API_KEY"}
rate_limit      JSONB                 -- {"rpm":30,"cooldown_sec":2}
supported_regions JSONB               -- ["US","EU","*"] — "*" = global
version         VARCHAR(20)
health_status   VARCHAR(20) DEFAULT 'unknown'
last_health     TIMESTAMPTZ
```

### accounts
```sql
id              UUID PK
workspace_id    UUID FK → workspaces.id ON DELETE CASCADE
target_id       UUID FK → targets.id ON DELETE CASCADE
provider        VARCHAR(30) NOT NULL  -- google|apple|facebook|github
provider_uid    VARCHAR(255)
email           VARCHAR(255)
display_name    VARCHAR(255)
access_token    TEXT                  -- AES-256 encrypted (Fernet)
refresh_token   TEXT                  -- AES-256 encrypted (Fernet)
token_expires   TIMESTAMPTZ
scopes          Text[]
last_audited    TIMESTAMPTZ
audit_summary   JSONB
created_at      TIMESTAMPTZ DEFAULT NOW()
updated_at      TIMESTAMPTZ DEFAULT NOW()
```

### alerts
```sql
id              UUID PK
workspace_id    UUID FK → workspaces.id ON DELETE CASCADE
target_id       UUID FK → targets.id ON DELETE CASCADE
type            VARCHAR(30) NOT NULL
                -- new_breach|score_change|new_paste|new_account|
                -- data_broker_found|scheduled_rescan
config          JSONB
last_triggered  TIMESTAMPTZ
trigger_count   INTEGER DEFAULT 0
enabled         BOOLEAN DEFAULT true
created_at      TIMESTAMPTZ DEFAULT NOW()
```

### reports
```sql
id              UUID PK
workspace_id    UUID FK → workspaces.id ON DELETE CASCADE
target_id       UUID FK → targets.id ON DELETE CASCADE
type            VARCHAR(20) DEFAULT 'standard'  -- standard|whitelabel
file_path       VARCHAR(500)
file_size       INTEGER
sections        JSONB                 -- which sections to include
generated_at    TIMESTAMPTZ DEFAULT NOW()
```

### audit_log
```sql
id              UUID PK
workspace_id    UUID FK → workspaces.id
user_id         UUID FK → users.id
action          VARCHAR(50) NOT NULL  -- target.create|scan.launch|finding.resolve|...
resource_type   VARCHAR(30)
resource_id     UUID
metadata        JSONB
ip_address      VARCHAR(45)
created_at      TIMESTAMPTZ DEFAULT NOW()

-- Append-only, never deleted
INDEX idx_audit_workspace ON audit_log(workspace_id, created_at DESC)
```

## API design

All endpoints prefixed with `/api/v1/`. All require auth (JWT Bearer) except health.
All scoped to workspace via middleware (extracts workspace_id from JWT claims).

### Auth
```
POST /api/v1/auth/register        -- Phase 1: admin setup. Phase 3: public signup
POST /api/v1/auth/login           -- email + password → JWT pair
POST /api/v1/auth/refresh         -- refresh token → new access token
POST /api/v1/auth/logout          -- blacklist refresh token
GET  /api/v1/auth/me              -- current user + workspaces + roles
POST /api/v1/auth/oauth/{provider} -- Phase 2: SSO initiation
GET  /api/v1/auth/oauth/callback  -- SSO callback
POST /api/v1/auth/mfa/setup       -- Phase 3: generate TOTP secret + QR
POST /api/v1/auth/mfa/verify      -- verify TOTP code
```

### Targets
```
GET    /api/v1/targets                    -- list (paginated, ?search, ?status, ?min_score, ?tags)
POST   /api/v1/targets                    -- create {email, country_code?, tags?, notes?}
GET    /api/v1/targets/{id}               -- detail + latest scan + score
PATCH  /api/v1/targets/{id}               -- update tags, notes, country_code
DELETE /api/v1/targets/{id}               -- cascade delete all data (GDPR)
GET    /api/v1/targets/{id}/graph         -- identity graph nodes + edges
GET    /api/v1/targets/{id}/timeline      -- findings timeline
GET    /api/v1/targets/{id}/export        -- full data export (JSON)
```

### Scans
```
POST   /api/v1/scans                      -- launch {target_id, modules[]}
GET    /api/v1/scans                      -- list (?target_id, ?status)
GET    /api/v1/scans/{id}                 -- detail + module_progress
POST   /api/v1/scans/{id}/cancel          -- revoke celery task
WS     /api/v1/scans/{id}/ws             -- WebSocket for live progress
```

### Findings
```
GET    /api/v1/findings                   -- list (?target_id, ?module, ?severity, ?category, ?status)
GET    /api/v1/findings/{id}              -- detail + raw data
PATCH  /api/v1/findings/{id}              -- update status (resolved, false_positive)
GET    /api/v1/findings/stats             -- aggregates (by severity, category, module)
```

### Modules
```
GET    /api/v1/modules                    -- list all + health
PATCH  /api/v1/modules/{id}               -- enable/disable, update config
POST   /api/v1/modules/{id}/health        -- trigger health check
```

### Workspaces (Phase 2)
```
GET    /api/v1/workspaces                 -- list user's workspaces
POST   /api/v1/workspaces                 -- create workspace
PATCH  /api/v1/workspaces/{id}            -- update settings
POST   /api/v1/workspaces/{id}/invite     -- invite user by email
```

### Reports (Phase 2)
```
POST   /api/v1/reports                    -- generate {target_id, type, sections[]}
GET    /api/v1/reports                    -- list
GET    /api/v1/reports/{id}/download       -- download PDF
```

### Alerts (Phase 2)
```
GET    /api/v1/alerts                     -- list
POST   /api/v1/alerts                     -- create rule
PATCH  /api/v1/alerts/{id}                -- update/toggle
DELETE /api/v1/alerts/{id}                -- remove
```

## Scanner interface

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ScanResult:
    module: str
    layer: int
    category: str
    severity: str          # info|low|medium|high|critical
    title: str
    description: str
    data: dict             # raw output — forensic archive
    url: Optional[str] = None
    indicator_value: Optional[str] = None
    indicator_type: Optional[str] = None
    verified: bool = False

class BaseScanner:
    MODULE_ID: str
    LAYER: int
    CATEGORY: str
    SUPPORTED_REGIONS: list[str] = ["*"]  # "*" = global

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        raise NotImplementedError

    async def health_check(self) -> bool:
        raise NotImplementedError
```

## Exposure score computation

```python
SCORE_WEIGHTS = {
    "breach":       0.25,
    "social":       0.20,
    "tracking":     0.15,
    "geo":          0.12,
    "data_broker":  0.10,
    "metadata":     0.08,
    "device":       0.05,
    "public_record": 0.05,
}

SEVERITY_MULTIPLIER = {
    "critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1
}
```

Per-category score = sum(findings × severity_multiplier), normalized 0-100.
Final score = weighted sum across categories.
US targets will naturally score higher (more public data) — that's correct behavior.

## Frontend pages

### Dashboard (/)
Stats cards: total targets, active scans, total findings, critical count.
Recent scans with status. Top 5 exposed targets. Module health. Quick scan form.

### Targets (/targets)
Table: email, country, status, score, last scanned, findings count.
Search + filter. "Add target" button → modal. Click row → detail.

### Target detail (/targets/:id)
Header: email, score donut, country flag, status.
Tabs: Findings | Graph | Timeline | Scans | Report.
Findings tab: filterable table with severity badges.
Graph tab: D3 force-directed identity map.
"Launch scan" button with module checkboxes.

### Settings (/settings)
Module toggles + health. API key config. Default modules. User profile.

## UI rules
- Background: #0a0a0f. Cards: #12121a, border #1e1e2e
- Accent: #00ff88 (green), #ff2244 (critical), #ff8800 (high), #ffcc00 (medium), #3388ff (low), #666688 (info)
- Monospace for all data values. Sans-serif for UI.
- Cards with subtle glow on hover (box-shadow with accent at 0.1 opacity)
- Severity badge: pill-shaped, colored bg at 0.15 opacity, text full color
- Tables: dark rows, sticky header, zebra #ffffff05 alternate

## Dev priority (Sprint 1 = v0.1.0)

1. Docker Compose
2. All DB models + Alembic (full schema, all tables)
3. JWT auth (register + login + me + middleware)
4. Seed modules
5. Target CRUD + workspace scoping
6. Holehe scanner wrapper
7. Scan orchestrator (Celery)
8. Findings API
9. React dashboard (dark theme, targets, scan, results)
10. Commit v0.1.0

## Critical rules

- All OSINT tools in Celery workers, NEVER in API process
- Rate limit every external call — config in modules.rate_limit
- Raw tool output in findings.data JSONB forever
- NEVER store plaintext passwords — breach names + hash prefixes only
- OAuth tokens AES-256 encrypted at rest (Fernet, key in env)
- Every DB query scoped to workspace_id (prepare for RLS in Phase 2)
- findings is the biggest table — design indexes and queries accordingly
- US targets = more data available = higher scores. This is correct.
- GHunt needs DroidGuard patch (already built by dev)
- HIBP API key $3.50/mo, required for breach depth
- Holehe + Maigret = pure Python, zero external deps
- Sherlock needs aggressive rate limiting (IP ban risk)
