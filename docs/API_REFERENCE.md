# API Reference — xposeTIP v0.90.0

All endpoints prefixed with `/api/v1/`. All require auth (JWT Bearer) except health.
All scoped to workspace via middleware (extracts workspace_id from JWT claims).

## Auth
```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
PATCH /api/v1/auth/profile
```

## Targets
```
GET    /api/v1/targets              — paginated, returns geo_locations + user_locations
POST   /api/v1/targets
GET    /api/v1/targets/{id}
PATCH  /api/v1/targets/{id}
DELETE /api/v1/targets/{id}
GET    /api/v1/targets/{id}/profile
POST   /api/v1/targets/{id}/scan-username  — Deep scan a single username (202 Accepted)
GET    /api/v1/targets/{id}/remediation    — Prioritized remediation actions
POST   /api/v1/targets/{id}/scan-indicator — Deep scan any indicator type (202 Accepted)
  Body: {"type": "username|email|domain|name|fullname", "value": "..."}
  Notes: Triggers cascade (cross-type discovery, depth=1, max=5)
```

## Scans
```
POST   /api/v1/scans                — returns {items, total, page, per_page}
GET    /api/v1/scans
GET    /api/v1/scans/{id}
POST   /api/v1/scans/{id}/cancel
```

## Findings
```
GET    /api/v1/findings
GET    /api/v1/findings/{id}
PATCH  /api/v1/findings/{id}
GET    /api/v1/findings/stats
```

## Graph
```
GET    /api/v1/graph/{target_id}
```

## Modules
```
GET    /api/v1/modules
PATCH  /api/v1/modules/{id}
POST   /api/v1/modules/{id}/health
POST   /api/v1/modules/health-all
```

## Settings
```
GET    /api/v1/settings/apikeys
POST   /api/v1/settings/apikeys
DELETE /api/v1/settings/apikeys/{key_name}
GET    /api/v1/settings/defaults
PUT    /api/v1/settings/defaults
```

## Workspaces
```
GET    /api/v1/workspaces
POST   /api/v1/workspaces
PATCH  /api/v1/workspaces/{id}
DELETE /api/v1/workspaces/{id}
GET    /api/v1/workspaces/{id}/members
POST   /api/v1/workspaces/{id}/invite
PATCH  /api/v1/workspaces/{id}/plan
```

## System (superadmin)
```
GET    /api/v1/system/stats
GET    /api/v1/system/users
PATCH  /api/v1/system/users/{id}
GET    /api/v1/system/workspaces
GET    /api/v1/system/logs
POST   /api/v1/system/recalculate-scores
```

## Plans

| | Free | Consultant (€49/mo) | Enterprise (€199/mo) |
|--|------|---------------------|---------------------|
| Targets | 1 | 25 | Unlimited |
| Scans/mo | 5 | 100 | Unlimited |
| Scrapers | Basic | All 117 | All 117 |
| Personas | No | Yes | Yes |
| Identity | No | Yes | Yes |
| PDF Export | No | Yes | Yes |

superadmin bypasses ALL limits. First registered user = superadmin + enterprise workspace.

## Global scope

xposeTIP works worldwide with varying depth:
- **US targets**: Maximum data. Voter rolls, court records, public records — all public.
- **EU targets**: GDPR applies but we reveal existing public exposure. Lawful basis = consent.
- **Rest of world**: Varies. Module system adapts — region-specific modules can be enabled/disabled.
