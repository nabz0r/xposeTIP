# Sprint Log — xposeTIP v0.80.0

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
| 75 | Avatar quality gate: _score_avatar >= 2 for avatar_url, GenerativeAvatar fallback, PhotosTab quality badges, Dashboard Quick Scan removed |
| 76 | Deep Username Scan: POST /targets/{id}/scan-username, scan_single_username (300s/80 scrapers), Celery task + lightweight refinalize, UI button with polling + DEEP badge |
| 77 | Bug Fix Blitz: photos confidence %, timeline DNS date filter, username validator strengthened, UsernameTab sort real>intelligence, severity-based analyzer confidence |
| 78 | User Dashboard Preview (/user-preview): score hero + GenerativeAvatar 160px, evolution chart (Recharts), remediation checklist, GET /targets/{id}/remediation endpoint |
| 79 | Code Leak & Paste Monitoring: 3 new scrapers (GitHub Code Search email+username, GitHub Gists), psbdmp re-enabled, CodeLeakAnalyzer (10 sensitive patterns), code_leak category |
| 80 | Account Depth Profiling: enriched extraction on 5 scrapers (+19 fields), BehavioralProfiler analyzer (5 archetypes + longevity + high-activity detection) |

## Known issues

- Quick scan timeout (300s) may not be enough for slow Celery
- Some scraper timestamps not parsed (field names vary per API)
- Life timeline sparse (most findings don't include timestamps)
- Fingerprint evolution avatars identical when score stable (by design)
- BUG 4 (deferred): Add exponential backoff with 1 retry on HTTP 429 for Roblox, Agify, Nationalize scrapers
- Intelligence analyzer confidence now severity-based (0.40-0.85), fixed in Sprint 77
- Code leak scrapers require GitHub API rate limit awareness (5 req/min unauth)

## Roadmap

### v1.0 — Nexus 2026 (June)
- [x] 120 scrapers, 35 scanners, 7 intelligence analyzers
- [x] PageRank / Markov chain confidence propagation
- [x] 32x32 pixel art identity avatars with quality gate
- [x] Freemium quick scan (zero friction)
- [x] Plans (Free/Consultant/Enterprise)
- [x] 3-pass pipeline (email → username → name)
- [x] 9-axis digital fingerprint
- [x] Identity-first narrative rewrite
- [x] PDF report export (ReportLab, dark theme, plan-tiered)
- [x] Deep username scan (operator-triggered)
- [x] Code leak monitoring (GitHub Code Search, Gists, Pastebin dumps)
- [x] Behavioral profiling (Developer, Gamer, Creative, Influencer, Privacy-conscious)
- [x] Consumer dashboard preview (/user-preview)
- [x] Remediation engine (prioritized action plan)
- [x] Avatar quality gate (reject identicons/defaults)
- [ ] Graph zoom/pan improvement
- [ ] Corporate intelligence via Hunter.io (domain → employees)

### v1.1 — Post-Nexus (July-August)
- [ ] Consumer auth flow (self-service scan + save)
- [ ] Score evolution tracking (before/after comparison)
- [ ] Reverse image search (TinEye, cross-platform photo matching)
- [ ] Corporate/LDAP scrapers (O365 enumeration, Azure AD tenant, GitHub org)
- [ ] Domain-wide scan (all employees of company)
- [ ] Public API — behavioral fingerprints as structured intelligence
- [ ] Webhook notifications
- [ ] On-premise deployment guide

### v1.2 — Enterprise (Q4 2026)
- [ ] OAuth audit (Google/Microsoft third-party app access)
- [ ] Dark web monitoring (Tor paste sites, .onion indexing)
- [ ] Scheduled recurring scans with delta reports
- [ ] Compliance reports (NIS2, DORA, AI Act)
- [ ] Multi-language (FR, DE, LU)
- [ ] Email alerts (new breach detected for monitored identities)

### v2.0 — Platform (2027)
- [ ] Marketplace (community scrapers and analyzers)
- [ ] Plugin API (custom analyzers, webhook integrations)
- [ ] Team collaboration (shared investigations, annotations)
- [ ] Mobile app (React Native)
- [ ] Real-time paste monitoring (streaming pastebin/GitHub events)
