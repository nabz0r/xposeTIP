# Architecture

## System Overview

```mermaid
graph TB
    subgraph Frontend
        React[React 18 + Vite]
        TW[Tailwind CSS 4]
        D3[D3.js Graphs]
        RC[Recharts]
    end

    subgraph API Layer
        FastAPI[FastAPI]
        JWT[JWT Auth]
        MW[Workspace Middleware]
    end

    subgraph Task Layer
        Celery[Celery Workers]
        Beat[Celery Beat]
        Redis[(Redis 7)]
    end

    subgraph Storage
        PG[(PostgreSQL 16)]
        Fernet[Fernet AES-256]
    end

    subgraph Scanners
        L1[Layer 1: Passive Recon]
        L2[Layer 2: Public DBs]
        L3[Layer 3: OAuth Audit]
        L4[Layer 4: Intelligence]
    end

    React --> FastAPI
    FastAPI --> JWT
    FastAPI --> MW
    FastAPI --> PG
    FastAPI --> Redis
    FastAPI --> Celery
    Celery --> L1 & L2 & L3 & L4
    L4 --> PG
    Celery --> Redis
    Beat --> Redis
    Fernet -.-> PG
```

## Scan Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant C as Celery
    participant S as Scanners
    participant DB as PostgreSQL

    U->>API: POST /scans (target_id, modules)
    API->>DB: Create Scan record
    API->>C: launch_scan.delay(scan_id)
    C->>C: chord([run_module x N], finalize_scan)
    par For each module
        C->>S: scanner.scan(target_email)
        S-->>C: ScanResult(findings)
        C->>DB: Insert findings
    end
    C->>C: finalize_scan
    C->>DB: Count findings, update target
    C->>C: compute_score()
    C->>C: build_graph()
    C->>C: aggregate_profile()
    C->>C: analysis_pipeline.run()
    C->>DB: Store score, graph, profile, intelligence
```

## Database Schema

```mermaid
erDiagram
    workspaces ||--o{ users : "user_workspaces"
    workspaces ||--o{ targets : contains
    workspaces ||--o{ scans : contains
    targets ||--o{ scans : has
    targets ||--o{ findings : has
    targets ||--o{ identities : has
    scans ||--o{ findings : produces
    identities ||--o{ identity_links : source
    identities ||--o{ identity_links : target

    workspaces {
        uuid id PK
        string name
        jsonb settings
    }
    targets {
        uuid id PK
        uuid workspace_id FK
        string email
        int exposure_score
        jsonb score_breakdown
        jsonb profile_data
    }
    scans {
        uuid id PK
        uuid target_id FK
        string status
        jsonb modules
        jsonb module_progress
        int findings_count
    }
    findings {
        uuid id PK
        uuid scan_id FK
        uuid target_id FK
        string module
        int layer
        string category
        string severity
        string title
        jsonb data
        float confidence
    }
    identities {
        uuid id PK
        uuid target_id FK
        string type
        string value
        string source_module
    }
    identity_links {
        uuid id PK
        uuid source_id FK
        uuid target_id FK
        string link_type
    }
    modules {
        string id PK
        string display_name
        int layer
        bool enabled
        string health_status
    }
```

## Multi-Tenant Design

Everything is scoped to a `workspace_id`:
- JWT tokens carry workspace_id in claims
- Middleware extracts workspace_id for every request
- All DB queries filter by workspace_id
- PostgreSQL Row-Level Security (RLS) planned for Phase 2

### RBAC Roles
`superadmin` > `admin` > `consultant` > `client` > `user`

Phase 1 uses superadmin only. Others activate in later phases.

## Score Engine

```
Exposure Score = Σ (category_weight × min(Σ severity_multiplier, 100))

Weights: breach=0.25, social=0.20, tracking=0.15, geo=0.12,
         data_broker=0.10, metadata=0.08, domain=0.05, paste=0.05

Severity: critical=5, high=4, medium=3, low=2, info=1
```

## Intelligence Pipeline

Runs automatically after each scan in `finalize_scan`:

1. **IP Analyzer** — ASN lookup, reverse DNS, infrastructure mapping
2. **Domain Analyzer** — Subdomain discovery (crt.sh), security headers, SSL check
3. **Username Correlator** — Cross-platform username reuse detection
4. **Breach Correlator** — Password reuse risk, exposure timeline
5. **Risk Assessor** — Overall risk level + prioritized remediation actions

Intelligence findings are stored as `layer=4, module="intelligence"`.

## Encryption

- API keys encrypted at rest using **Fernet** (AES-256-CBC + HMAC-SHA256)
- Encryption key derived from `SECRET_KEY`
- Stored in workspace `settings` JSONB column
- Decrypted only when passed to scanner at scan time
