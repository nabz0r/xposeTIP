# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: http://localhost:8000/docs (Swagger UI)

All endpoints require JWT Bearer auth unless noted otherwise.

## Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, returns access + refresh tokens |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Invalidate refresh token |
| GET | `/auth/me` | Current user info |
| PATCH | `/auth/profile` | Update display_name |

## Targets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/targets` | List targets in workspace |
| POST | `/targets` | Create target (email required) |
| GET | `/targets/{id}` | Get target details |
| PATCH | `/targets/{id}` | Update target |
| DELETE | `/targets/{id}` | Delete target and findings |
| GET | `/targets/{id}/profile` | Aggregated profile data |

## Scans

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/scans` | Launch scan (target_id, modules[]) |
| GET | `/scans` | List scans in workspace |
| GET | `/scans/{id}` | Scan status + module progress |
| POST | `/scans/{id}/cancel` | Cancel running scan |

### Quick Scan (No Auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/scan/quick` | Quick scan — 3 fast modules, rate limited (5/email/hour) |

Request body:
```json
{ "email": "user@example.com" }
```

## Findings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/findings` | List findings (filter: severity, module, status) |
| GET | `/findings/{id}` | Finding detail with raw data |
| PATCH | `/findings/{id}` | Update status (resolved, false_positive) |
| GET | `/findings/stats` | Severity/module/category aggregations |

## Graph

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/graph/{target_id}` | Identity graph — nodes, edges, stats |

## Modules

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/modules` | List all modules + health + implemented flag |
| PATCH | `/modules/{id}` | Enable/disable module |
| POST | `/modules/{id}/health` | Run health check for one module |
| POST | `/modules/health-all` | Bulk health check all modules |

## Connected Accounts (OAuth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/accounts` | List connected accounts (optional ?target_id=) |
| POST | `/accounts/oauth/start` | Get OAuth authorization URL |
| POST | `/accounts/oauth/callback` | Exchange auth code for tokens |
| POST | `/accounts/{id}/audit` | Trigger account audit |
| DELETE | `/accounts/{id}` | Disconnect account |

## Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/settings/apikeys` | List configured API keys (masked) |
| POST | `/settings/apikeys` | Save API key (Fernet encrypted) |
| POST | `/settings/apikeys/custom` | Save custom key |
| POST | `/settings/apikeys/{name}/validate` | Validate API key |
| DELETE | `/settings/apikeys/{name}` | Delete API key |
| GET | `/settings/defaults` | Get default scan modules |
| PUT | `/settings/defaults` | Update default scan modules |

## System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Quick health check (no auth) |
| GET | `/health/detailed` | Full infrastructure status (no auth) |
| GET | `/system/stats` | Admin dashboard stats (superadmin/admin) |
| POST | `/system/recalculate-scores` | Re-run score engine for all targets |

## Common Response Patterns

### Pagination
Most list endpoints support `?skip=0&limit=50`.

### Error Format
```json
{
  "detail": "Error message"
}
```

### Finding Severity Levels
`critical` | `high` | `medium` | `low` | `info`

### Scan Statuses
`pending` | `running` | `completed` | `failed` | `cancelled`
