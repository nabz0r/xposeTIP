# xpose — Product Vision & Requirements Document

**Version**: 0.1 (Draft)
**Author**: Nabil Sontini (nabz0r) — PM + Lead Dev
**Date**: March 2026
**Status**: Pre-development — Vision lock

---

## 1. Executive summary

xpose is an **Identity Threat Intelligence platform** that bridges two worlds that don't talk to each other: deep OSINT tools (SpiderFoot, Maltego) that only experts can use, and consumer identity protection services (Aura, NordProtect) that hide everything behind a "trust us" curtain.

Our bet: people want to **see** what the internet knows about them — not just be told "we're monitoring." They want the transparency of SpiderFoot with the usability of Aura. They want an identity graph they can interact with, an exposure score they understand, and an action plan they can execute.

The product serves three audiences in three phases: power users (self-audit), security consultants (client audits), and eventually the general public (SaaS).

---

## 2. Market landscape & positioning

### 2.1 What exists today

**OSINT tools (expert-only)**
SpiderFoot, Maltego, Recon-ng, Sherlock, Maigret — powerful, 200+ data sources, graph visualization. But they require CLI knowledge, manual configuration, API key management, and interpretation skills. No consumer would ever use these on themselves.

**Consumer identity protection ($10-30/mo)**
Aura, NordProtect, LifeLock, Identity Guard — beautiful apps, credit monitoring, dark web scanning, insurance up to $5M. But they're black boxes. You never see your identity graph, never understand *how* your data is connected, never get deep technical insight. They sell peace of mind, not transparency.

**Data removal services ($8-15/mo)**
Incogni, DeleteMe, Optery — they do one thing well: find your data on broker sites and request removal. Incogni covers 420+ brokers. But they don't audit your full digital footprint, don't show connections, and don't help with account hygiene.

**Security posture tools (niche)**
Guardio (browser extension, proactive blocking), Surfshark Alert (dark web monitor). They touch adjacent problems but don't map your full identity.

### 2.2 The gap

Nobody combines:
- The **depth** of OSINT reconnaissance (account enumeration, breach correlation, Google metadata, username tracking across 2000+ sites)
- With a **consumer-grade UX** (dashboard, identity graph, exposure score, guided remediation)
- And **user agency** (you see everything, you control what gets scanned, you decide what to do)

That's the blue ocean. xpose lives there.

### 2.3 Competitive moat

1. **Transparency by design** — You see every finding, every data source, every connection. Not "we found 3 issues" but "here's the graph of how your email links to 47 accounts, 3 breaches, and 2 data brokers, with evidence."
2. **Plugin architecture** — Extensible module system. Community can add scanners. This is how SpiderFoot scaled to 200+ modules without building them all in-house.
3. **IOC model** — Every finding is a typed, scored, timestamped indicator. Security pros recognize this immediately. Normal users learn the language of their own exposure.
4. **Self-hosted option** — Privacy purists won't send their data to a SaaS. Day 1, xpose runs on your own infra. SaaS comes later for convenience.

---

## 3. Personas & phased rollout

### Phase 1 — "Operator" (v0.1 to v0.5)

**Persona: Nabil**
Network/security engineer, 20+ years. Already runs OSINT tools from CLI. Wants a unified dashboard to audit his own exposure and test the product. Has the technical background to install Docker, configure API keys, and understand raw findings.

**What he needs:**
- Admin portal where he adds emails and launches scans
- All Layer 1 engines (Holehe, Maigret, GHunt, HIBP, Sherlock, h8mail)
- Raw findings with full evidence (JSONB data)
- Identity graph showing how his identities link together
- Exposure score he can track over time
- Self-hosted, zero cloud dependency

**Success metric:** Nabil uses xpose weekly to audit his own exposure and finds it more useful than running tools individually from CLI.

### Phase 2 — "Consultant" (v0.6 to v0.8)

**Persona: Nicolas**
Big 4 auditor (KPMG Luxembourg), interested in NIS2/DORA compliance. Wants to offer "digital hygiene audits" as a service to financial sector clients. Needs multi-client management, professional reports, and a clean interface he can show to a CISO.

**What he needs:**
- Multi-tenant: each client is a separate workspace
- Client invitation flow (email invite, OAuth onboarding)
- White-label PDF reports (consultant's branding)
- Role-based access: consultant sees all clients, client sees only their own data
- Layer 2 modules (data broker check, geolocation, WHOIS) for deeper audits
- Scheduled monitoring with alerts
- SSO (Google Workspace, Microsoft Entra) for enterprise clients
- Audit trail: who scanned what, when

**Success metric:** Nicolas closes 3 paying clients in Luxembourg's financial sector using xpose-generated reports.

### Phase 3 — "Consumer" (v0.9 to v1.0+)

**Persona: Marie**
33, marketing manager in Luxembourg. Tech-savvy but not a security person. Heard about data breaches on the news, worried about her digital footprint. Wants something she can sign up for in 2 minutes and understand in 5.

**What she needs:**
- Self-service signup (email + OAuth)
- Guided onboarding: "Let's see what the internet knows about you"
- Simplified dashboard: exposure score front and center, top 5 urgent actions
- No jargon: "Your email was found in a LinkedIn data breach" not "IOC type=breach, severity=high"
- Account linking (Google OAuth) for deeper voluntary audit
- App tracker check (which of her phone apps track her)
- One-click remediation where possible (link to delete account, enable 2FA)
- Freemium model: basic scan free, monitoring + deep audit = paid

**Success metric:** 1000 signups in first 3 months, 10% conversion to paid.

---

## 4. User stories (by phase)

### Phase 1 — Operator

```
US-101: As an operator, I can add an email address as a scan target
        so that I can audit its digital exposure.

US-102: As an operator, I can select which scan modules to run
        so that I control the depth and speed of the audit.

US-103: As an operator, I can see scan progress in real-time
        so that I know which modules are running, completed, or failed.

US-104: As an operator, I can view all findings for a target
        grouped by category and sorted by severity
        so that I prioritize the most critical exposures.

US-105: As an operator, I can see raw evidence (JSON) for any finding
        so that I can verify and investigate further.

US-106: As an operator, I can see an identity graph
        showing how my emails, usernames, and accounts connect
        so that I understand my digital footprint visually.

US-107: As an operator, I can see an exposure score (0-100)
        with a breakdown by category
        so that I have a single metric to track over time.

US-108: As an operator, I can mark findings as resolved or false positive
        so that my score reflects my actual exposure.

US-109: As an operator, I can re-scan a target
        and see new findings highlighted vs previous scans
        so that I track changes over time.

US-110: As an operator, I can enable/disable individual scan modules
        and configure their API keys
        so that I control which external services are used.
```

### Phase 2 — Consultant

```
US-201: As a consultant, I can create client workspaces
        each with their own targets and findings
        so that client data is isolated.

US-202: As a consultant, I can invite a client via email
        to view their own audit results
        so that they have self-service access.

US-203: As a consultant, I can generate a branded PDF report
        for a client's target
        so that I deliver professional audit deliverables.

US-204: As a consultant, I can set up scheduled re-scans
        with email alerts on new findings
        so that clients get continuous monitoring.

US-205: As a consultant, I can see an audit log
        of all scans, access, and changes
        so that I maintain compliance records.

US-206: As a consultant, I can sign in via SSO (Google/Microsoft)
        so that enterprise clients can use their existing auth.

US-207: As a consultant, I can run Layer 2 scans
        (data broker, WHOIS, geolocation, paste monitoring)
        so that I offer deeper audits than basic email recon.
```

### Phase 3 — Consumer

```
US-301: As a consumer, I can sign up with my email or Google account
        in under 2 minutes
        so that I start auditing my exposure immediately.

US-302: As a consumer, I can see a guided onboarding
        that scans my email and explains each finding
        in plain language
        so that I understand without security expertise.

US-303: As a consumer, I can link my Google account (OAuth read-only)
        to audit connected apps, security settings, and location sharing
        so that I get a deeper voluntary audit.

US-304: As a consumer, I can see which of my phone apps contain trackers
        (via Exodus Privacy database)
        so that I make informed choices about my apps.

US-305: As a consumer, I can get a prioritized action plan
        ("Delete this account", "Enable 2FA here", "Opt out there")
        with direct links
        so that I take concrete steps to reduce my exposure.

US-306: As a consumer, I can use a free tier (basic email scan)
        and upgrade to paid ($9.99/mo) for monitoring + deep audit
        so that I try before I buy.

US-307: As a consumer, I can delete all my data from xpose at any time
        with one click
        so that I maintain control over my information.
```

---

## 5. UX flows

### 5.1 Onboarding — Phase 1 (Operator)

```
[Deploy docker compose] → [Open localhost:3000]
         ↓
[Setup wizard: create admin account (email + password)]
         ↓
[Configure modules: enter API keys (HIBP, MaxMind, etc.)]
         ↓
[Dashboard: empty state → "Add your first target"]
         ↓
[Enter email → select modules → Launch scan]
         ↓
[Live scan progress → findings appear in real-time]
         ↓
[Results: exposure score + findings table + identity graph]
```

### 5.2 Onboarding — Phase 3 (Consumer)

```
[Landing page: "Know what the internet knows about you"]
         ↓
[Enter email + "Start free scan" (no signup yet)]
         ↓
[Teaser results: "We found X accounts, Y breaches" (blurred details)]
         ↓
[Create account to see full results (email or Google OAuth)]
         ↓
[Full dashboard: exposure score + top 5 actions]
         ↓
[Upsell: "Link your Google account for a deeper audit" (free)]
         ↓
[Upsell: "Enable monitoring for $9.99/mo"]
```

### 5.3 Core loop — Scan & Review

```
[Target detail page]
    ↓
[Click "New scan" → module selector with smart defaults]
    ↓
[Scan runs → progress bar per module → findings stream in]
    ↓
[Results grouped by category tabs:
   Accounts | Breaches | Tracking | Geolocation | Metadata]
    ↓
[Click any finding → detail panel: evidence + explanation + action]
    ↓
[Mark as "resolved" after taking action → score updates]
```

### 5.4 Identity graph interaction

```
[Target detail → "Graph" tab]
    ↓
[D3 force-directed graph loads:
   center = target email
   linked nodes = usernames, phone, other emails, IPs, accounts]
    ↓
[Click any node → panel shows:
   how it was discovered, which module found it, confidence level]
    ↓
[Click edge → shows the link type:
   "same_person", "registered_with", "mentioned_together"]
    ↓
[Hover cluster → highlight all connected nodes]
```

---

## 6. Monetization model

### Pricing tiers

| Tier | Price | Targets | Scans | Layers | Monitoring | Reports |
|------|-------|---------|-------|--------|------------|---------|
| **Free** | $0 | 1 email | 1 scan/week | L1 (basic: validation + Holehe) | No | No |
| **Pro** | $9.99/mo | 5 emails | Unlimited | L1 full + L2 | Weekly re-scan + alerts | PDF |
| **Consultant** | $29.99/mo | 50 emails, 10 workspaces | Unlimited | L1 + L2 + L3 | Daily + custom alerts | White-label PDF |
| **Enterprise** | Custom | Unlimited | Unlimited | All | Real-time | Custom + API |

### Revenue model

Phase 1: No revenue (self-hosted, open source core)
Phase 2: Consultant tier ($29.99 x clients)
Phase 3: SaaS freemium (targeting 10% free-to-paid conversion)

### What stays free forever

- Self-hosted deployment (full features, you run it)
- Open source core engine + all Layer 1 modules
- Community module development & marketplace

### What's paid (SaaS only)

- Managed hosting (we run it for you)
- Monitoring & alerting
- Premium modules (some Layer 2/3 with API costs we absorb)
- White-label reports
- SSO + multi-tenant
- Priority support

---

## 7. Legal & compliance (GDPR critical)

### 7.1 Why this matters

xpose processes personal data (email addresses, breach records, account lists, geolocation). Operating from Luxembourg = full GDPR jurisdiction. This is not optional.

### 7.2 Key requirements

**Lawful basis for processing:**
- Self-audit: Consent (user scans their own data) — clear and unambiguous
- Client audit (consultant): Legitimate interest + data processing agreement (DPA) between consultant and client
- Consumer SaaS: Consent via Terms of Service

**Data minimization:**
- Store only what's needed for the audit
- Raw findings in JSONB: kept for forensic value, deletable on request
- Never store plaintext passwords from breach data — store breach names, dates, and password hash prefixes only
- OAuth tokens: encrypted at rest (AES-256 via Fernet), scoped to minimum required permissions

**Right to erasure (Article 17):**
- One-click "Delete all my data" in user settings
- Cascade delete: target → scans → findings → identities → identity_links → accounts → alerts
- Hard delete, not soft delete. When it's gone, it's gone.
- Audit log entry retained: "[user] requested data deletion on [date]" (no PII in the log)

**Data portability (Article 20):**
- Export all findings as JSON/CSV
- Export identity graph as structured data
- Machine-readable format, delivered within 30 days (but we target instant)

**Data Processing Agreement (DPA):**
- Required for consultant tier (they process client data through our platform)
- Template DPA provided, Luxembourg law governing

**Cookie policy:**
- SaaS frontend: essential cookies only, no analytics trackers
- No third-party tracking pixels, no Google Analytics
- If we add analytics later: privacy-focused (Plausible, Umami), no PII

**HIBP API compliance:**
- HIBP prohibits storing breach details beyond what's needed
- We store: breach name, date, data classes affected, user's email hash
- We don't store: full breach dumps, plaintext credentials

### 7.3 Scanning ethics

**Self-audit:** No restrictions. You can scan yourself.

**Third-party scanning:** Requires either (a) the target person's explicit written consent, or (b) a legitimate security assessment engagement with documented scope. The platform should surface a consent confirmation dialog before scanning third-party emails in the consumer tier.

**Rate limiting:** All modules are rate-limited to respect external service ToS. We don't scrape aggressively. We follow robots.txt. We use APIs when available.

---

## 8. Architecture

### 8.1 High-level system design

```
                     ┌───────────────────────────────────────┐
                     │        CDN / Reverse Proxy             │
                     │           (Caddy / Nginx)              │
                     └───────────────┬───────────────────────┘
                                     │
                     ┌───────────────▼───────────────────────┐
                     │         React SPA (Vite)              │
                     │                                       │
                     │  Phase 1: Admin dashboard              │
                     │  Phase 2: + Consultant workspace       │
                     │  Phase 3: + Consumer onboarding        │
                     └───────────────┬───────────────────────┘
                                     │ REST + WebSocket
                     ┌───────────────▼───────────────────────┐
                     │         FastAPI Backend                │
                     │                                       │
                     │  Auth (JWT → SSO → MFA)               │
                     │  RBAC (admin, consultant, client, user)│
                     │  API versioning (/api/v1/)             │
                     │  WebSocket for scan progress           │
                     │  Rate limiting (per-user, per-module)  │
                     └──┬──────────┬──────────┬──────────────┘
                        │          │          │
                 ┌──────▼──┐ ┌────▼────┐ ┌───▼──────┐
                 │ Celery  │ │ Postgres│ │ Redis    │
                 │ Workers │ │ 16     │ │          │
                 │         │ │+pgvector│ │ Broker   │
                 │ Scanner │ │         │ │ Cache    │
                 │ modules │ │ Tables: │ │ Sessions │
                 │         │ │ (below) │ │ PubSub   │
                 └─────────┘ └─────────┘ └──────────┘
```

### 8.2 Authentication & authorization roadmap

| Phase | Auth method | Details |
|-------|-----------|---------|
| 1 | Local JWT | Single admin account, bcrypt password, JWT access + refresh tokens, 15min/7d expiry |
| 2 | + SSO (OAuth2) | Google Workspace, Microsoft Entra, GitHub. Via Authlib. Consultant invites clients via email → OAuth onboarding |
| 3 | + MFA (TOTP) | Optional TOTP via pyotp. Recovery codes. Enforced for consultant tier. |

**RBAC model:**

| Role | Can do |
|------|--------|
| `superadmin` | Everything. Module config, system settings, user management. |
| `admin` | Manage targets, scans, modules in their workspace. Invite users. |
| `consultant` | Create workspaces, manage client targets, generate reports. |
| `client` | View their own targets, findings, reports. Read-only scan launch (consultant approves). |
| `user` | Self-service. Manage their own identity, launch scans, see results. (Phase 3) |

**Workspace isolation:**
Every query is scoped to `workspace_id`. A consultant's workspace contains their clients. A consumer's workspace contains only themselves. PostgreSQL Row-Level Security (RLS) enforces this at the DB level — even if the app has a bug, data doesn't leak across workspaces.

### 8.3 Data model (product-oriented)

The database serves the product, not the other way around. Here's why each table exists and what product feature it powers.

**workspaces** — Multi-tenant isolation unit. Every target, scan, finding belongs to a workspace. Phase 1 = one workspace. Phase 2 = one per consultant client. Phase 3 = one per consumer user.

**users** — Auth + profile. Links to workspace(s) via a junction table. Stores hashed password, OAuth provider info, MFA secret (encrypted), role.

**user_workspaces** — Junction table. A user can belong to multiple workspaces (consultant belongs to all their client workspaces). Role is per-workspace, not global.

**targets** — The core entity: an email address to audit. Has exposure_score (computed), score_breakdown (per-category JSONB), status, tags. Belongs to a workspace.

**scans** — A scan job. Tracks which modules were run, per-module progress, duration, findings count. Links to target and workspace. Has celery_task_id for cancellation.

**findings** — Individual IOCs. This is the biggest table — will grow to millions of rows. Partitioned by workspace_id for query performance. Each finding has: module, layer, category, severity, title, description, raw evidence (JSONB), indicator_value, indicator_type, status (active/resolved/false_positive), first_seen/last_seen.

**identities** — Nodes in the identity graph. Each is an identifier (email, username, phone, full_name, ip, domain, device_id, social_url) linked to a target. Source traced back to the finding that discovered it.

**identity_links** — Edges in the identity graph. Source identity → target identity with a link_type (same_person, registered_with, mentioned_together, resolves_to, logged_from, linked_account) and confidence score. This is the secret sauce — the graph only works because of this table.

**modules** — Registry of scan engines. Layer, category, enabled flag, auth requirements, rate limit config, health status. Seeded at deploy, updated by admin.

**accounts** — OAuth-linked accounts for Layer 3 voluntary audit. Provider, tokens (encrypted), scopes, last audit date. Phase 3 only.

**alerts** — Monitoring rules. "Alert me when a new breach is found for this target." Type, config (JSONB), last triggered, enabled. Phase 2+.

**reports** — Generated PDF reports. Metadata + file path (or S3 key). Phase 2+.

**audit_log** — Who did what, when. Critical for consultant compliance. Action, actor, workspace, timestamp, metadata. Append-only, never deleted.

### 8.4 Module / plugin architecture

This is the extensibility play. A module is a Python class that:
1. Inherits from `BaseScanner`
2. Declares its `MODULE_ID`, `LAYER`, `CATEGORY`
3. Implements `async def scan(email, **kwargs) -> list[ScanResult]`
4. Implements `async def health_check() -> bool`
5. Declares its `rate_limit` config and `requires_auth` flag

**Built-in modules (shipped with core):**

| ID | Layer | Category | Engine | Auth needed |
|----|-------|----------|--------|-------------|
| `email_validator` | 1 | validation | DNS/MX/SMTP | No |
| `holehe` | 1 | social | Holehe | No |
| `maigret` | 1 | social | Maigret | No |
| `sherlock` | 1 | social | Sherlock | No |
| `ghunt` | 1 | metadata | GHunt | Yes (cookies) |
| `hibp` | 1 | breach | HIBP API | Yes ($3.50/mo) |
| `h8mail` | 1 | breach | h8mail | Optional |
| `maxmind_geo` | 2 | geolocation | GeoLite2 | Yes (free key) |
| `whois_lookup` | 2 | metadata | WHOIS/RDAP | No |
| `databroker_check` | 2 | data_broker | Custom scrapers | No |
| `paste_monitor` | 2 | paste | IntelX API | Yes |
| `google_auditor` | 3 | audit | Google OAuth | Yes (OAuth) |
| `exodus_tracker` | 3 | tracking | Exodus Privacy DB | No |
| `browser_auditor` | 3 | audit | Extension/export | No |

**Community module spec (Phase 2+):**

A community module is a pip-installable package that registers itself:

```python
# pyproject.toml
[project.entry-points."xpose.modules"]
my_scanner = "my_package:MyScanner"
```

The xpose module loader discovers it via `importlib.metadata.entry_points()`. Zero configuration, zero Docker rebuilds. Install the package, restart the worker, the module appears in the dashboard.

**Module marketplace (Phase 3+):**

A curated registry (think: PyPI for xpose modules). Verified modules get a badge. Users install from the Settings page. Revenue share possible for premium modules.

### 8.5 Scalability considerations

**Findings table partitioning:**
- Partition by `workspace_id` (list partitioning) for workspace isolation
- Within each partition, index on `target_id`, `severity`, `category`, `module`
- Estimated volume: 100 findings per target per full scan x 50 targets per workspace = 5000 rows per workspace per scan cycle. At 1000 workspaces: 5M rows. PostgreSQL handles this fine with proper indexing + partitioning.

**Redis usage:**
- Celery broker (scan task queue)
- Scan progress pub/sub (WebSocket pushes)
- Rate limit counters per module (sliding window)
- Session store (JWT blacklist for logout)
- Cache: recent findings for dashboard (TTL 5 min)

**Celery worker scaling:**
- Layer 1 modules are I/O bound (HTTP requests to external services) → async workers, high concurrency
- Layer 3 modules may be CPU bound (parsing large exports) → separate worker pool
- Rate limiting per module prevents external service abuse
- Celery priority queues: high (user-triggered scan) > medium (scheduled) > low (monitoring)

**File storage:**
- PDF reports: local filesystem in Phase 1, S3-compatible (MinIO) in Phase 2+
- MaxMind GeoLite2 DB: local file, refreshed weekly via cron
- Exodus tracker DB: local JSON, refreshed weekly

### 8.6 Security model

**At rest:**
- OAuth tokens: AES-256 encrypted via Fernet (key in env var, never in DB)
- User passwords: bcrypt with cost factor 12
- Findings data: plaintext in DB (it's derived from public sources), but DB disk encrypted
- No plaintext passwords from breaches. Ever.

**In transit:**
- HTTPS everywhere (Caddy auto-cert in production)
- WebSocket over WSS
- API tokens in Authorization header, never in URL params

**Application security:**
- CORS: strict origin whitelist
- CSRF: SameSite cookies + double-submit token
- Input validation: Pydantic models on every endpoint
- SQL injection: SQLAlchemy parameterized queries (no raw SQL)
- Rate limiting: per-user (100 req/min), per-module (varies), per-IP (1000 req/min)
- Content Security Policy headers on frontend

---

## 9. Tech stack (final)

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Backend | FastAPI + SQLAlchemy 2.0 (async) + Alembic | Async, typed, fast. SQLAlchemy 2.0 for modern mapped_column style. |
| Queue | Celery + Redis | Battle-tested. Priority queues, task revocation, beat scheduler. |
| Database | PostgreSQL 16 + pgvector | RLS for multi-tenant, pgvector for future similarity search on findings, PostGIS if we add geolocation maps. |
| Cache/PubSub | Redis | Broker + cache + session + rate limit counters + scan progress pub/sub. |
| Frontend | React 18 + Vite + Tailwind CSS | Fast dev cycle, dark theme easy, component-based. |
| Identity graph | D3.js force-directed | Interactive, handles 500+ nodes, runs client-side. |
| Charts | Recharts | React-native, simple API, dark theme support. |
| Auth | Authlib (OAuth2) + PyJWT + pyotp (TOTP) | Phase 1: JWT. Phase 2: +SSO. Phase 3: +MFA. |
| Reports | WeasyPrint | HTML-to-PDF, supports CSS, no headless browser needed. |
| OSINT engines | Holehe, Maigret, GHunt, Sherlock, h8mail | Python-native, already proven on macOS. |
| Breach data | HIBP API ($3.50/mo) | Official, reliable, legal. |
| Geolocation | MaxMind GeoLite2 (free) | Local DB file, no API calls, privacy-friendly. |
| App trackers | Exodus Privacy DB (CC-BY-SA) | Open data, can be bundled, community-maintained. |
| Containers | Docker Compose | Phase 1: local. Phase 2+: Kubernetes-ready with Helm chart. |
| Reverse proxy | Caddy | Auto HTTPS, simple config, production-ready. |
| File storage | Local → MinIO (S3-compatible) | Self-hosted S3 for reports and exports. |

---

## 10. UI/UX design principles

### Visual language

- **Dark theme by default.** This is a security tool, not a marketing site. Blacks (#0a0a0f), dark grays (#12121a), subtle borders (#1e1e2e).
- **Accent: neon green (#00ff88)** for positive/success, red (#ff2244) for critical, amber (#ffcc00) for warnings, blue (#3388ff) for info.
- **Typography:** Inter for UI, JetBrains Mono for data (IPs, emails, hashes, scores).
- **Data-dense.** Show information, not decoration. Every pixel serves the user.
- **Severity color-coding everywhere.** Critical=red, high=orange, medium=yellow, low=blue, info=gray. Consistent across all views.

### Key UX patterns

- **Progressive disclosure.** Dashboard shows the score. Click for categories. Click for findings. Click for evidence. Never overwhelm.
- **Zero state guidance.** Empty dashboard = "Add your first target" with a quick start tutorial. Not a blank page.
- **Real-time feedback.** Scan progress streams via WebSocket. Findings appear as they're discovered, not all at once at the end.
- **Action-oriented findings.** Every finding has a "What to do" section. "You have an account on X → here's the delete link." Not just "we found something."
- **Graph-first exploration.** The identity graph is the main way to explore connections. Click a node, see what it connects to, understand your exposure visually.

### Responsive behavior

- Desktop-first (this is a dashboard tool)
- Tablet: sidebar collapses to icons
- Mobile: simplified view — score + top actions only. Full findings table not great on mobile.

---

## 11. Roadmap

### Phase 1 — Operator MVP (v0.1 to v0.5) — Target: 8 weeks

```
v0.1.0 — Foundation
  Docker Compose + DB schema + Alembic + seed modules
  JWT auth (single admin)
  Target CRUD + basic dark dashboard
  Holehe scanner + scan orchestrator + results viewer

v0.2.0 — Layer 1 complete
  HIBP breach check
  Maigret username enumeration
  Email validation module
  Findings filtering, search, export (CSV)

v0.3.0 — Intelligence
  GHunt Google footprint scanner
  Exposure score engine (weighted composite)
  Identity graph (D3 force-directed)
  IOC timeline view

v0.4.0 — Layer 2 starts
  MaxMind IP geolocation
  WHOIS domain lookup
  Paste monitoring (IntelX)

v0.5.0 — Polish
  Data broker checker
  Findings diff between scans (new vs known)
  PDF report generation (WeasyPrint)
  Dark theme refinement + UX polish
```

### Phase 2 — Consultant (v0.6 to v0.8) — Target: 12 weeks

```
v0.6.0 — Multi-tenant
  Workspace model + RLS
  SSO (Google, Microsoft) via Authlib
  RBAC (admin, consultant, client)
  Workspace invitation flow

v0.7.0 — Professional features
  White-label PDF reports
  Scheduled re-scans (Celery Beat)
  Alert rules + email notifications
  Audit log

v0.8.0 — Module ecosystem
  Community module loader (entry_points)
  Module health dashboard
  Module configuration UI
  Documentation + SDK for module developers
```

### Phase 3 — Consumer SaaS (v0.9 to v1.0) — Target: 16 weeks

```
v0.9.0 — Self-service onboarding
  Public signup (email + Google OAuth)
  Guided first scan experience
  Simplified dashboard (score-first)
  Plain language finding explanations
  MFA (TOTP) for all users

v0.10.0 — Layer 3
  Google account audit (OAuth read-only)
  Exodus tracker integration (app audit)
  Browser audit via export/extension
  Account linking management page

v1.0.0 — Public beta
  Freemium billing (Stripe integration)
  Landing page + marketing site
  One-click data deletion (GDPR)
  Data export (JSON/CSV)
  Performance optimization + load testing
  Security audit
```

---

## 12. Key risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| External services change their API/block us | Modules break | Health check system + graceful degradation. Module shows "degraded" not "error." Community can fix fast via plugin system. |
| GDPR complaint (processing without consent) | Legal | Consent flow baked into every scan. DPA template for consultants. Right to erasure is day-1 feature. |
| Rate limiting by external services (IP ban) | Scans fail | Per-module rate limits in config. Proxy rotation for heavy modules. Respectful scanning defaults. |
| Competition copies the concept | Market share | Open source core = community moat. Plugin ecosystem = network effect. First-mover with transparency angle. |
| Data breach of xpose itself | Reputation | Encrypt tokens at rest, minimize stored PII, security audit at v1.0, bug bounty program. |
| Over-engineering before product-market fit | Never ships | Phase 1 is deliberately simple. Ship to ourselves first. Dog-food ruthlessly. Add complexity only when the user (us) demands it. |

---

## 13. Success metrics

### Phase 1 (Operator)
- Nabil uses xpose weekly instead of CLI tools
- Full Layer 1 scan completes in under 5 minutes
- Identity graph displays 50+ nodes without performance issues
- Zero data leaks in self-hosted deployment

### Phase 2 (Consultant)
- 3 paying consultant clients in Luxembourg financial sector
- Reports generated in under 30 seconds
- Client onboarding (invite to first scan) under 10 minutes
- Zero cross-workspace data leakage

### Phase 3 (Consumer)
- 1000 signups in first 3 months
- 10% free-to-paid conversion
- Median time to first scan: under 2 minutes
- NPS above 40
- GDPR compliance validated by external audit

---

## 14. Open questions (to resolve before v0.3)

1. **Naming**: Is "xpose" final? Check trademark availability in EU/US. Alternative: ExposureMap, DigitalMirror, Footprint, Recon.me.
2. **GHunt DroidGuard patch**: Can we ship this in the Docker image or does it need user-side setup? License implications?
3. **HIBP commercial use**: Does the $3.50/mo API key cover SaaS resale in Phase 3? Need to check Troy Hunt's terms.
4. **Module marketplace revenue share**: If community modules become a thing, what's the split? 70/30 like app stores?
5. **Luxembourg legal review**: Should we get a formal legal opinion on the platform before Phase 2? Me Homo at DSM could advise.
6. **Brand identity**: Need logo, color palette finalization, landing page design before Phase 3.

---

*"The best way to predict the future is to build it — but only after you've understood what you're building and why."*

**Next step**: Lock this document, create the repo, generate CLAUDE.md + BOOTSTRAP_PROMPT.md from this vision, and start Sprint 1.
