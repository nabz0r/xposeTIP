# Sprint Log — xposeTIP v1.1.0

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
| 81 | Full docs & landing update to v0.80.0: CLAUDE.md, SPRINT_LOG.md, ARCHITECTURE.md, API_REFERENCE.md |
| 82 | Generic Deep Indicator Scan: POST /targets/{id}/scan-indicator (username/email/domain/name), Deep Scan button on all findings |
| 83 | The xpose Manifesto: /manifesto page, 3 pillars (Ethical OSINT, Green Intelligence, Education First), landing trust bar |
| 84 | CRITICAL FIX — Deep Scan Pipeline: _full_refinalize (15 steps replacing broken _lightweight_refinalize), cascade scan (cross-type indicator chaining), _store_result indicator_type fix |
| 85 | Docs, landing & version bump to v0.85.0 |
| 86 | Pipeline Reorder: two-phase Gather-then-Compute (Pass 1.5/2 before graph build, early profile bootstrap) |
| 87 | Bug Fix Blitz II: ratio-based risk levels, persona confidence rebalance, 429 exponential backoff retry |
| 88 | Graph username nodes fix (platform/username keys in _store_result), Deep Scan Activity panel in OverviewTab |
| 89 | CRITICAL — Scraper real module names (not scraper_engine), indicator_value fallback, dedup maps legacy findings |
| 90 | Docs, landing & architecture update to v0.90.0 |
| 91 | README rewrite: v0.90.0, two-phase pipeline, 120 scrapers, changelog |
| 92 | Manifesto v2: red lines, data commitment, B2B consent model, sourced green numbers |
| 93 | Extraction rules enrichment: 17 scrapers, ~68 new fields (bios, followers, dates, skills) |
| 94 | Geographic Intelligence: 132 countries, 123 cities, location normalization, url_last_segment transform |
| 95 | Timezone Intelligence: sleep window detection, UTC offset inference, 27 offset→region mappings |
| 96 | Geo Consistency Scoring: 6-signal cross-correlation (ground truth, self-reported, timezone, nationalize, language, geoip) |
| 97 | HOTFIX: Timeline wayback leak, profile perf (country_code param), email non-deliverable banner |
| 98 | Full documentation & landing alignment for Nexus (v0.98.0) |
| 98b | SCANNERS.md rewrite + architecture visual updates + demo script |
| 99 | Smarter Pass 2 queries (context from email domain + city) + photo quality tiers |
| 100 | v1.0.0: Persona confidence formula + tab labels + scan progress + MX lookup |
| 101 (A) | Discovery Engine: DB migration — 3 tables (discovery_sessions, discovery_leads, target_links) |
| 102 (B) | Discovery Engine: 6 extractors (rel_me 0.95, jsonld 0.95, social_link 0.85, email 0.90, meta_tag 0.80, username 0.60) |
| 103 (C) | Discovery Engine: Query generator (11 templates, 4 tiers) + variant engine + budget manager |
| 104 (D) | Discovery Engine: Fetch pipeline — SerpAPI → trafilatura → extractors → quality gate → DB |
| 104.5 | Discovery Engine: Relevance filter + nav/footer stripping |
| 104.6 | Discovery Engine: 8 quality fixes — LinkedIn penalty, geo, disambiguation, platform blocklist, dedup |
| 104.7 | Discovery Engine: Final quality — page relevance, common name blocklist, generic fallback removal |
| 105 (E) | Discovery Engine: Celery task + 3 API endpoints + 4 SSE event types |
| 106 (F) | Discovery Engine: Discovered tab — launch, lead cards, dismiss/undo, filter pills, chain view |

## Known issues

- Quick scan timeout (300s) may not be enough for slow Celery
- Some scraper timestamps not parsed (field names vary per API)
- Life timeline sparse (most findings don't include timestamps)
- Fingerprint evolution avatars identical when score stable (by design)
- ~~BUG 4 (deferred): 429 retry~~ — Fixed in Sprint 87 (exponential backoff on all scrapers)
- Intelligence analyzer confidence now severity-based (0.40-0.85), fixed in Sprint 77
- Code leak scrapers require GitHub API rate limit awareness (5 req/min unauth)
- BUG A: Timeline dates — DNS/archive dates may leak into timeline (shows 1999)
- BUG F: GitHub code search requires auth token for higher rate limits
- Graph label cleanup (_profile/_scraper suffix in node labels) — cosmetic
- Discovery: common first names need adding to COMMON_FIRST_NAMES blocklist
- Discovery: JSON-LD Article titles extracted as name leads (filter @type)
- Discovery: session stats show "0 queries" during running (updates on completion only)

## Roadmap

### v1.0 — Nexus 2026 (June)
- [x] 124 scrapers, 26 scanners, 9 intelligence analyzers
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
- [x] Product manifesto: Ethical OSINT + Green Intelligence + Education First
- [x] Generic deep indicator scan (any indicator type, not just username)
- [x] Cascade scan (cross-type indicator chaining after deep scan)
- [x] Two-phase pipeline (gather all findings before graph/score/profile)
- [x] Per-scraper module attribution (real scraper names in findings)
- [x] 429 exponential backoff retry on all scrapers
- [x] Ratio-based risk level thresholds
- [ ] Graph zoom/pan improvement
- [ ] Corporate intelligence via Hunter.io (domain → employees)

### Sprint 107 series — Phone + crypto identifiers + docs alignment (Apr–May 2026)

- [x] S107a — Phantom module cleanup: 9 phantoms removed/disabled, 4 undocumented live modules documented in CLAUDE.md (v1.1.8)
- [x] S107b — Secondary identifier infrastructure: `secondary_identifiers.py` + `secondary_identifier_enricher.py` services, `finalize_scan` A1.5/A1.6 steps, scraper engine `phone` and `crypto_wallet` input types (v1.1.9)
- [x] S107c — Phone + crypto scrapers: 6 new scrapers seeded disabled (numverify_phone, veriphone_phone, google_phone_dork, blockchain_info_btc, blockchair_wallet, chainabuse_check), key-based JSONB extraction (v1.1.10)
- [x] S107d — Docs sync (partial): 7 files aligned on count, did not catch all references — closure handled in S107e
- [x] S107e — Docs closure + `mastodon_search` dedupe: removed broken duplicate (invalid regex `"accounts":[{`), aligned all docs on 124 scrapers, PRD metadata refreshed, backfilled sprint log entries 107a-d
- [x] S108 — Secondary identifier extraction tests: 8 pytest characterization tests on `_extract_phones` and `_extract_wallets` covering key-based extraction, nested keys, module blacklist, dedupe across findings, BTC/ETH chain detection, and SECONDARY_INPUT_TYPES contract (no production code change)
- [x] S110 — Landing hero identity-layer rewrite: nav exposes Manifesto link, eyebrow reframed "Identity Layer · Free lookup", two intro paragraphs rewritten to identity-as-a-layer thesis (record→layer narrative), chip badges include "Identity layer · alpha", form caption rephrased
- [x] S111 — Manifesto identity-layer thesis section: hero reframed "Identity is a layer of the internet", new Foundation section (4 cards: thesis / what the layer looks like / why this matters now / what xposeTIP is and isn't), bridge intro to four operational pillars, version bumped v2→v3

### Trilogy C→B→A — Play 1 + Play 2 foundation (May 2026)

- [x] S112 — Identity Intelligence Report templates (Sprint C): consulting Markdown generator + client intake form for Play 1 delivery, internal infra only (no public surface), report tiers Quick Profile / Identity Assessment / Deep Investigation (v1.1.11)
- [x] S113 — Public positioning refresh (Sprint B): pricing 4-tier locked on landing (Free/Starter/Team/Enterprise), manifesto BFP-silent, Nexus 2026 references removed, contact@redbird.co.com surface
- [x] S114 — OSS readiness (Sprint A): LICENSE flip MIT→AGPL-3.0, CLA infra (cla-assistant.yml + .github/CLA.md), CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, NOTICE.md, .gitleaks.toml audit clean (0 history leaks)

### v1.1 — Post-Nexus (July-August)
- [x] Phase C Web Discovery (fingerprint-driven Google dorking)
- [x] 6 content extractors (rel=me, JSON-LD, social links, email, meta, username)
- [x] Quality gate (5-layer anti-noise: nav strip, relevance, LinkedIn penalty, geo, page relevance)
- [x] Discovery leads workflow (dismiss/undo, filter by status)
- [x] Discovered tab in UI with launch button + polling
- [ ] D3 discovery tree visualization (Sprint G)
- [ ] Ingest workflow: Enrich target / New linked target (Sprint H)
- [ ] Target links navigation (Sprint I)
- [ ] Consumer auth flow (self-service scan + save)
- [ ] Score evolution tracking (before/after comparison)
- [ ] Reverse image search (TinEye, cross-platform photo matching)
- [ ] Corporate/LDAP scrapers (O365 enumeration, Azure AD tenant, GitHub org)
- [ ] Domain-wide scan (all employees of company)
- [ ] Public API — behavioral fingerprints as structured intelligence
- [ ] Webhook notifications
- [ ] On-premise deployment guide
- [ ] Consent gate enforcement (scan authorization flow)
- [ ] Right-to-delete (full purge endpoint + UI)
- [ ] Finding explanations (plain-language "why this matters" per finding type)

### v1.2 — Enterprise (Q4 2026)
- [ ] OAuth audit (Google/Microsoft third-party app access)
- [ ] Dark web monitoring (Tor paste sites, .onion indexing)
- [ ] Scheduled recurring scans with delta reports
- [ ] Compliance reports (NIS2, DORA, AI Act)
- [ ] Multi-language (FR, DE, LU)
- [ ] Email alerts (new breach detected for monitored identities)
- [ ] Carbon footprint dashboard (scan cost in watts + CO2 vs industry average)
- [ ] Educational guides per finding category (interactive walkthroughs)
- [ ] Compliance: consent audit trail (who authorized which scan, when)

### v2.0 — Platform (2027)
- [ ] Marketplace (community scrapers and analyzers)
- [ ] Plugin API (custom analyzers, webhook integrations)
- [ ] Team collaboration (shared investigations, annotations)
- [ ] Mobile app (React Native)
- [ ] Real-time paste monitoring (streaming pastebin/GitHub events)
