# Sprint Log — xposeTIP v0.74.0

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
| 44-50 | 85 scrapers, corporate scrapers, public exposure axis (9th), enhanced fingerprint |
| 51-60 | 100 scrapers, scanner expansion (35 modules), L5 premium tier, Pass 2 name enrichment |
| 61-70 | 117 scrapers, Pass 1.5 username expansion, 3-pass pipeline, identity-first narrative |
| 71 | Component extraction: Landing.jsx and Architecture.jsx split into focused sub-components |
| 72 | Narrative rewrite: identity-first landing + architecture ("From IOCs to identities") |
| 73 | Bug Fix Blitz: pre-flush truncation, import alias fix, WHOIS JSON safety, scan pagination, table scroll, geo map pins, username validator |
| 73b | Username filter: is_valid_username() applied in username_expander + profile_aggregator |
| 73c | Avatar quality ranking (_score_avatar), always-sync to target.avatar_url |
| 73d | CLAUDE.md split into 4 files, version bump to v0.73.0 |
| 74 | PDF identity report export (ReportLab, dark theme, 5-page Pro tier, tiered by plan) |

## Known issues

- Quick scan timeout (300s) may not be enough for slow Celery
- Some scraper timestamps not parsed (field names vary per API)
- Life timeline sparse (most findings don't include timestamps)
- Fingerprint evolution avatars identical when score stable (by design)
- BUG 4 (deferred to Sprint 74): Add exponential backoff with 1 retry on HTTP 429 for Roblox, Agify, Nationalize scrapers

## Roadmap

### v1.0 — Nexus 2026 (June)
- [x] 117 scrapers, 35 scanners
- [x] PageRank / Markov chain confidence propagation
- [x] 32x32 pixel art identity avatars
- [x] Freemium quick scan (zero friction)
- [x] Plans (Free/Consultant/Enterprise)
- [x] 3-pass pipeline (email → username → name)
- [x] 9-axis digital fingerprint
- [x] Identity-first narrative rewrite
- [x] PDF report export
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
