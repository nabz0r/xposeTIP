# xpose

**Identity Threat Intelligence for humans.**

Your digital identity is scattered across thousands of services, breaches, data brokers, and tracking networks. Enterprises have CrowdStrike and ThreatConnect. You have nothing.

**xpose** maps, scores, and monitors your digital exposure — treating every leaked email, every exposed account, every tracking cookie as an Identity IOC.

Deep OSINT reconnaissance. Consumer-grade UX. Full transparency.

---

## How it works

**Enter an email. See everything the internet knows.**

| Layer | What it does | Depth |
|-------|-------------|-------|
| **L1 — Passive recon** | Account enumeration, breach history, reputation, Google footprint, username hunt | 2000+ sites |
| **L2 — Public databases** | IP geolocation, WHOIS, DNS security, data brokers, paste sites | US = max depth |
| **L3 — Account audit** | Google/Apple OAuth audit, app trackers, browser hygiene | Voluntary, consent |
| **L4 — Intelligence** | Identity graph, exposure score 0-100, profile aggregation, remediation | Actionable output |

Every finding is an **Identity IOC** — typed, scored, timestamped, linked to your identity graph.

---

## Scanners (17 implemented)

### Layer 1 — Passive Recon

| Module ID | Name | Free? | What it finds |
|-----------|------|-------|---------------|
| `email_validator` | Email Validator | Yes | Format validation, MX records, disposable provider detection |
| `holehe` | Holehe | Yes | Account enumeration across 120+ services from email |
| `hibp` | Have I Been Pwned | $3.50/mo | Full breach history, paste exposure, data classes leaked |
| `sherlock` | Sherlock | Yes | Username search across 400+ social networks |
| `gravatar` | Gravatar | Yes | Avatar, profile data, linked social accounts via email hash |
| `social_enricher` | Social Enricher | Yes | GitHub profile — name, bio, location, repos, followers |
| `google_profile` | Google Profile | Yes | Gmail/Workspace detection, YouTube presence |
| `emailrep` | Email Reputation | Yes | Reputation score, breach status, social profiles, domain security |
| `epieos` | Epieos Google | Yes | Google account discovery — ID, name, profile photo |
| `fullcontact` | FullContact | API key | Person enrichment — name, age, gender, social profiles |
| `github_deep` | GitHub Deep | Yes | Full GitHub profile, events, gists, alternate emails from commits |
| `username_hunter` | Username Hunter | Yes | Username permutations checked on Reddit, Steam, Keybase, GitLab, Medium, HN, Dev.to |

### Layer 2 — Public Databases

| Module ID | Name | Free? | What it finds |
|-----------|------|-------|---------------|
| `geoip` | Free GeoIP | Yes | Mail server IP geolocation via ip-api.com |
| `maxmind_geo` | MaxMind GeoIP | Free tier | IP geolocation via local GeoLite2 database |
| `whois_lookup` | WHOIS Lookup | Yes | Domain registration, ownership, registrant email match |
| `leaked_domains` | Leaked Domains | Yes | Breach check via XposedOrNot — breach history, exposed data types |
| `dns_deep` | DNS Intelligence | Yes | SPF, DMARC, DKIM, MX, NS analysis — email security posture |

### Not yet implemented (seeded, ready for future sprints)

`maigret`, `ghunt`, `h8mail`, `databroker_check`, `paste_monitor`, `google_auditor`, `exodus_tracker`, `browser_auditor`

---

## Screenshots

<!-- TODO: Add screenshots -->

### Dashboard
<!-- ![Dashboard](docs/screenshots/dashboard.png) -->

### Target Detail — Overview
<!-- ![Target Detail](docs/screenshots/target-detail.png) -->

### Identity Graph
<!-- ![Identity Graph](docs/screenshots/identity-graph.png) -->

### SVG World Map
<!-- ![World Map](docs/screenshots/world-map.png) -->

---

## Quick start

```bash
git clone https://github.com/nabz0r/xposeTIP.git
cd xposeTIP
cp .env.example .env
# Edit .env — set SECRET_KEY, optionally add HIBP_API_KEY

docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_modules.py

# Register admin
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme123"}'

# Start frontend
cd dashboard && npm install && npm run dev
# Open http://localhost:5173
```

See [INSTALL.md](INSTALL.md) for detailed setup instructions and troubleshooting.

---

## Tech stack

FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL 16 + pgvector + Redis + Celery + React 18 + Vite + Tailwind CSS 4 + D3.js + Recharts + Docker Compose

---

## Roadmap

| Version | Milestone | Status |
|---------|-----------|--------|
| **v0.1.0** | Docker, DB models, JWT auth, Holehe + email_validator, Celery orchestrator, React dashboard | Done |
| **v0.2.0** | HIBP, Sherlock, WHOIS, MaxMind GeoIP, score engine, identity graph, IOC timeline, world heatmap, scanner registry | Done |
| **v0.3.0** | Gravatar, Social Enricher, Google Profile, Free GeoIP, admin polish, settings UI, API key management | Done |
| **v0.4.0** | Dynamic API keys (Fernet encrypted), key validation, custom keys, location mapping, scan defaults | Done |
| **v0.5.0** | 7 new scanners (EmailRep, Epieos, FullContact, GitHub Deep, Username Hunter, Leaked Domains, DNS Intel), profile aggregation, health checks, SVG world map, toast system | Done |
| **v0.6** | GHunt integration, Maigret deep scan, PDF reports, data broker detection | Next |
| **v0.7** | Multi-tenant workspaces, SSO (Authlib), consultant mode | |
| **v0.8** | Pattern detection, remediation playbook, alert system | |
| **v0.9** | Consumer self-service, MFA (pyotp), Stripe billing | |
| **v1.0** | Public SaaS beta | |

---

## Plugin system

Every scanner is a Python class with two methods: `scan()` and `health_check()`.

```python
class MyScanner(BaseScanner):
    MODULE_ID = "my_scanner"
    LAYER = 2
    CATEGORY = "metadata"

    async def scan(self, email, **kwargs) -> list[ScanResult]:
        # Your logic here
        ...

    async def health_check(self) -> bool:
        return True
```

Add to `SCANNER_REGISTRY` in `api/tasks/module_tasks.py`, seed the module row, done.

---

## Legal

xpose is a **defensive** privacy audit tool. We don't create data — we reveal what's already public.

- Self-audit, security assessments with consent, privacy consulting, research
- Not for: stalking, unauthorized surveillance, doxing

GDPR-compliant. Right to erasure. Data export. Consent-first.

---

## License

MIT

---

*"Privacy is not about having something to hide. Privacy is about having something to protect."*
