# 🔍 xpose

**Identity Threat Intelligence for humans.**

Your digital identity is scattered across thousands of services, breaches, data brokers, and tracking networks. Enterprises have CrowdStrike and ThreatConnect to monitor their threat surface. You have nothing.

**xpose** changes that. It maps, scores, and monitors your digital exposure — treating every leaked email, every exposed account, every tracking cookie as an Identity IOC.

Deep OSINT reconnaissance. Consumer-grade UX. Full transparency.

---

## How it works

**Enter an email → see everything the internet knows.**

| Layer | What it does | Depth |
|-------|-------------|-------|
| **Passive recon** | Account enumeration, breach history, Google footprint, username hunt | 2000+ sites checked |
| **Public databases** | IP geolocation, WHOIS, data brokers, paste sites, DNS history | US targets = maximum depth |
| **Account audit** | Google/Apple OAuth audit, app tracker analysis, browser hygiene | Voluntary, full consent |
| **Intelligence** | Identity graph, exposure score (0-100), pattern detection, remediation | Actionable output |

Every finding is an **Identity IOC** — typed, scored, timestamped, linked to your identity graph.

---

## Identity graph

Your email connects to usernames. Usernames connect to accounts. Accounts leak to breaches. Breaches expose passwords reused across services. xpose maps all of it in an interactive D3 force-directed graph.

---

## Global coverage

| Region | Data depth | Why |
|--------|-----------|-----|
| 🇺🇸 US | Maximum | No federal privacy law. Voter rolls, court records, property records, people-search engines — all public. |
| 🇪🇺 EU | Moderate | GDPR limits public data. But breaches, social accounts, and username enumeration still work. |
| 🌍 Rest | Varies | Most countries have less protection than EU. Module system adapts per region. |

A US target will score higher than an EU target. That's not a bug — it proves the point about digital exposure.

---

## Tech stack

FastAPI · PostgreSQL + pgvector · Redis · Celery · React · D3.js · Docker Compose

OSINT engines: Holehe · Maigret · GHunt · Sherlock · h8mail · HIBP

---

## Quick start

```bash
git clone https://github.com/nabz0r/xpose.git
cd xpose
cp .env.example .env
docker compose up -d
docker compose exec api python scripts/seed_modules.py
open http://localhost:3000
```

---

## Roadmap

| Version | Milestone |
|---------|-----------|
| **v0.1** | Admin portal + Holehe scan + dark dashboard |
| **v0.2** | HIBP + Maigret + findings filtering |
| **v0.3** | GHunt + identity graph + exposure score |
| **v0.4** | MaxMind geoloc + WHOIS + data brokers |
| **v0.5** | PDF reports + scan diffing |
| **v0.6** | Multi-tenant + SSO + consultant workspaces |
| **v0.7** | Module marketplace + community plugins |
| **v0.8** | Pattern detection + remediation playbook |
| **v0.9** | Consumer self-service + MFA |
| **v1.0** | Public SaaS beta + Stripe billing |

---

## Plugin system

Every scanner is a Python class with two methods: `scan()` and `health_check()`. Community modules install via pip and register via entry_points. No Docker rebuild needed.

```python
class MyScanner(BaseScanner):
    MODULE_ID = "my_scanner"
    LAYER = 2

    async def scan(self, email, **kwargs) -> list[ScanResult]:
        # Your logic here
        ...
```

---

## Legal

xpose is a **defensive** privacy audit tool. We don't create data — we reveal what's already public.

- ✅ Self-audit · Security assessments with consent · Privacy consulting · Research
- ❌ Stalking · Unauthorized surveillance · Doxing

GDPR-compliant. Right to erasure. Data export. Consent-first.

---

## License

MIT

---

*"Privacy is not about having something to hide. Privacy is about having something to protect."*
