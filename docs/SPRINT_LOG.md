# Sprint Log — xposeTIP v1.2.0

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
| 107-110 | Discovery UX polish chain (v1.1.1-v1.1.4): event trail + zombie guard + junk filter + EmailRep API key + avatar fix + PivotStrategy engine + multi-round pivot execution |
| 111-112 | Auto-ingest + Phase A.5 targeted rescan (v1.1.5) + stability hotfixes (v1.1.6: graph dedup, discovery timeout, junk filter) |
| 113-114 | Comprehensive hotfix (v1.1.7: timeouts, UI, email_age, tabs) + module cleanup (v1.1.8: 9 phantoms removed/disabled) |
| 115-117 | Secondary identifier pipeline (v1.1.9: finalize_scan A1.5/A1.6 steps) + Phone + crypto scrapers (v1.1.10: 6 sources seeded disabled, key-based JSONB extraction) + OSS readiness (v1.1.11: LICENSE flip to AGPL-3.0, CLA infra, gitleaks audit clean) |
| 118 | 4-tier SaaS alignment (v1.1.12): consultant→starter plan rename, new Team tier, Alembic migration 012, frontend planColors shared module |
| 119 | Courtlistener (v1.1.13): US federal court scraper MVP, RECAP archive via REST API v4, token auth, legal_record indicator_type |
| 120 | EU legal scrapers (v1.1.14): BODACC (FR procédures collectives) + UK Gazette (London/Edinburgh/Belfast) |
| S119-S120 | Risk Signals UI block on Overview (v1.1.15) + Findings tab preset filter chips with shared `lib/findingFilters.js` (v1.1.16) |
| S121 + S121b | Doc drift closure post-S116→S120: stale landing JSX refs, DEMO_SCRIPT pricing table aligned with S113 4-tier |
| S122 chain (S122a → S122e-holdover) | Per-scraper attempt logging in `attempt_log` JSONB, `name_scraper_engine` factored out, aggregator tie-break (Gravatar email-verified beats heuristic), emoji regex extended to U+2600 block, 2 Gravatar duplicates disabled, pastebin_user HTML extraction fixed, low-confidence severity for placeholder name-scrapers |
| S123 | Holdover rollback + courtlistener defensive: PASS2 int→str coerce for indicator_value, courtlistener RECAP shape variant parse |
| S124-S126 | Verified provenance UI per finding (tier badges + cross-verif + first_seen/last_seen timeline) + Recalculate Profiles retro-rebuild + match_confidence row in ProvenanceCard |
| S127-S129 | name_scraper_engine sequential dispatch post-A3 + telemetry rectification (scraper_engine returns (found, reason), no_data classification for explicit_not_found/blocked_403) + Pass 1 username dispatch gated by is_valid_username (HN-style 400 fix) |
| S130 | Doc closure + v1.2.0 stamp: scripts/seed_scrapers.py audit (127/110/17/11 cats), SPRINT_LOG backfill S121-S130, DEMO_SCRIPT archived as Nexus v1 + rewritten dual Play 1/Play 2 narrative |
| S131 | DB-persisted similarity engine: Alembic 013 (`target_similarities` table), 9-axis cosine threshold 0.70, `first_detected` preserved across recomputes, Celery task post scan.completed, `GET /targets/{id}/similar`, `SimilarityBlock.jsx` on Overview tab |
| S132 | Landing refresh + Compare page: 6-card FeaturesSection, TwoWaysSection (Play 1 purple / Play 2 green), `/compare` route + Compare.jsx (tri-segment matrix + SVG quadrant) |
| S133 | TopoJSON geomap: world-atlas 110m, D3 Natural Earth, country-density heatmap, zoom/pan 1-8×, `lib/geo.js` (useWorldData/useZoom), `topojson-client` dep |
| S134 | R4 cleanup combo: `_clean_name_value` regex tightening + Courtlistener defensive cast + NEW `scans.cascade_state` (Alembic 014, gathering/computing/similarity/done/failed) + cascade stepper UI |
| S135 | UI polish 4-pack: backend always-non-null fingerprint_avatar_seed/axes, `TargetDetail` post-`done` re-fetch kills cascade race, fallbackSeed aligned across 4 consumers |
| S136 | Glyph in header dual-avatar (80px photo + 32px glyph badge) + Fingerprint Evolution scroll cue (right/left fades + drag hint + scroll-snap) |
| S137 | Cleanup combo: centralized `fallbackSeed` → `dashboard/src/lib/avatar.js`, NEW `docs/qa/SMOKE_PROTOCOL.md` |
| S138 | Public nav + footer unification: NEW `PublicNav.jsx` + `PublicFooter.jsx` shared across 4 public pages, active state via `useLocation()`, deleted `LandingFooter.jsx` + `ArchFooter.jsx`, `ArchCTA` extracted, `/changelog` link pre-added |
| S139 | Pricing tweaks: dropped `price` field from Starter/Team/Enterprise, Free keeps "€0 forever", `PricingSection` conditional render |
| S140 | Architecture full sexy refresh: 3 new stages (Cascade/Similarity/Discovery) + diagrams, hero stat banner 127·9·5.4B·11·0, NEW TechStackSection.jsx, ScraperBreakdown active/disabled split (110/17), RoadmapSection v1 backfill, CollectDiagram counts realigned (127) |
| S141 | `/changelog` public page parsed from git log: build-time `generate-changelog.mjs` via predev/prebuild hooks, 210 commits in JSON, filterable timeline grouped by month |

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

### Post-trilogy expansion — Identity layer + UI (May 2026)

- [x] S115 — Doc drift closure post-trilogy: CLAUDE.md, README changelog backfill v1.1.1–v1.1.11, SPRINT_LOG sync, CONTRIBUTING duplication resolved (docs/CONTRIBUTING.md → docs/ADDING_A_SCANNER.md), PRD status bump
- [x] S116a — Backend plan config 4-tier alignment: free/consultant/enterprise → free/starter/team/enterprise. Scan limits 25/250/2000/unlimited. New max_seats + feature flags (custom_scrapers, sso, audit_log, multi_tenant). Alembic 012 data migration consultant→starter on workspaces.plan. pdf_generator tier gate updated. Role 'consultant' UNTOUCHED (memberships.role) (v1.1.12)
- [x] S116b — Frontend plan rename + Team tier UI: new dashboard/src/lib/planColors.js (single source of truth), 4 inline duplicate maps removed, Layout/Organization/SystemUsersTab/SystemWorkspacesTab synced, UserPreview upgrade copy "Consultant"→"Starter", new team color #aa66ff (purple), plan cards grid md:grid-cols-3 → lg:grid-cols-4
- [x] S117 — Courtlistener legal scraper (MVP, collection only): US federal court records via Courtlistener REST API v4 (RECAP archive). Token auth, 401 Redis disable flag, 429 retry, conservative name confidence (0.70). PASS2 dispatch block 5b after Interpol. indicator_type=legal_record (does NOT match _PE_EDGE_TYPES — axis math untouched). courtlistener_api_key registered. Source scoring 0.85 (v1.1.13)
- [x] S118 — EU legal scrapers BODACC (FR) + UK Gazette: BODACC via Opendatasoft public dataset (procédures collectives, ventes/cessions, radiations), no auth. UK Gazette via official JSON feed (personal insolvency, bankruptcy, probate, deceased estates), no auth, 10s crawl delay per robots.txt, requires ≥2 name tokens. Pivot from Judilibre (pseudonymized at publication) and UK Insolvency Register (no public API) documented in commit (v1.1.14)
- [x] S119 — Risk Signals UI block on Overview tab: dashboard/src/components/RiskSignalsBlock.jsx, three-column grid (phone #3388ff / crypto #aa66ff / legal #ff8800), self-hides when all empty. Per-column accents match plan colors. Filter logic: data.scraper IN PHONE_SCRAPERS/CRYPTO_SCRAPERS, indicator_type='legal_record'. Closes deferred S108 plan (v1.1.15)
- [x] S120 — Findings tab preset filter chips: dashboard/src/lib/findingFilters.js (shared classifier, single source of truth), RiskSignalsBlock refactored to import from shared lib (no inline arrays). presetFilter state in TargetDetail, handleRiskSignalViewAll resets sev/mod/status + switches tab. FindingsTab renders self-hiding chip row (All / Phone / Crypto / Legal) above existing filter bar. Closes S119 navigation loop (v1.1.16)

### v1.2 stability chain — Doc closure + S122 chain + provenance + telemetry (May 2026)

- [x] S121 — Doc drift closure post-S116→S120: README badges, CLAUDE.md sprint list, SCANNERS.md count reconciliation, landing components stale refs swept (commit 64b57aa)
- [x] S121b — Sweep of remaining drift: DEMO_SCRIPT.md pricing table aligned with S113 4-tier, stale JSX landing references, follow-up to S121 (commit 984c129)
- [x] S122a — QA quick-fixes: sync_avatars script idempotent guard, /targets paginated cap tightened, error renderer fallback, version bump (commit e994b2f)
- [x] S122b — Pre-truncate `result.indicator_value` before SELECT/Identity insert: prevents PostgreSQL VARCHAR overflow on long extraction output (commit 514e4d4)
- [x] S122c — Diagnostic logging + UI banner for failed name resolution: `name_resolution_debug` JSONB on scan, surfaced in TargetDetail banner when aggregator produces no primary_name (commit 1758466)
- [x] S122-clean — Disable 2 Gravatar duplicates (`gravatar_scraper` + `gravatar_json` shadow `gravatar_profile_v2`), fix `pastebin_user` HTML extraction regex (commit 350f173)
- [x] S122-obs — Per-scraper `attempt_log` JSONB on Scan: every scraper dispatch logged with (started_at, ended_at, status, reason), name-resolution diag enrichment (commit 0c8c2d9)
- [x] S122-hk — Move QA reports to `docs/qa/`, add `.gitignore` entries for transient scan artifacts (commit 2cd5f44)
- [x] S122-name — Aggregator tie-break: when 2 sources propose competing names with equal weight, Gravatar email-verified beats heuristic. Emoji regex extends to U+2600 block (misc symbols) for cleanup (commit 0893acc)
- [x] S122e — `name_scraper_engine` module factored out: name-input scrapers (OpenSanctions, Interpol, OpenCorporates, Courtlistener, BODACC, UK Gazette) dispatched via dedicated path with per-scraper timeout + dedup (commit 6544804)
- [x] S122e-holdover — Low-confidence severity + manual-check title for 5 placeholder name-scrapers (preserved as scaffolding pending future activation) (commit 4fb647f)
- [x] Forensic round 2 — Pipeline health validation + scraper inventory snapshot post-S122 chain (commit d2bb4ee, `docs/qa/forensic_round_2_*.md`)
- [x] S123 — Holdover rollback + R1 + R2: R1 = PASS2 finding creation `int → str` coerce for `indicator_value` (NumVerify/Veriphone numeric IDs broke FK), R2 = `courtlistener_search` defensive parse on RECAP shape variants, rollback of 4 placeholder name-scrapers from S122e-holdover (low-signal verdict) (commit 51c5663)
- [x] S124 — Verified provenance UI per finding: `ProvenanceCard.jsx` displays tier badge (verified / cross-verified / unverified), cross-verif source list, first_seen/last_seen timeline. Closes provenance audit gap (commit 705eb3f)
- [x] S125 — Recalculate Profiles retro-rebuilds confidence: System Settings → Recalculate Profiles button now reruns `recalc_finding_confidence` + cross-verif boost over all existing findings, not just future scans (commit 0f30272)
- [x] S126 — `data.match_confidence` as separate ProvenanceCard row: distinct from finding-level confidence — exposes per-source name match score (e.g., OpenSanctions partial vs exact) (commit d7894df)
- [x] S127 — `name_scraper_engine` sequential dispatch post-A3: name-input scrapers fire AFTER A3 name resolution completes (not parallel with Pass 1.5). Fixes no_name_input regression on first scan of unknown identities (commit 9226a37)
- [x] Forensic round 3 — Full S122 → S127 chain validation: 3 Friends targets scanned (Ksontinisarah/abed.belaid/booking.lxb), 7 health checks PASS, all 12 sprints' fixes hold (commit fb394be, `docs/qa/forensic_round_3_*.md`)
- [x] S128 — Telemetry rectification: `scraper_engine._check_found()` returns `tuple[bool, str]` with reasons (`success | explicit_not_found | blocked_403 | implicit_not_found | not_2xx`). `scraper_scanner` classifier reclassifies `explicit_not_found | blocked_403 | implicit_not_found` as `no_data` instead of `error_4xx`. 4 scrapers flipped from error to no_data per scan (bluesky/crunchbase/discogs/wayback). Honest classification surfaced real HN bug → fixed in S129 (commit 77b08f5)
- [x] S129 — Pass 1 dispatch validation symmetry: `is_valid_username()` now gates Pass 1 username dispatch in `scraper_scanner.scan()` (matching Pass 1.5 validation in `username_expander._select_usernames`). Eliminates HN-style 400 errors on multi-dot emails. Broken bucket 12→2 on T2 control (83% reduction). Accepted gap: 1-dot emails still pass through (observe round 4 before tightening) (commit 3c383da)
- [x] S130 — Documentation closure + v1.2.0 stamp: all scraper counts reconciled to authoritative 127 (110 active / 17 disabled), sprint count 114+ → 129+, version v1.1.16 → v1.2.0 across README/CLAUDE/SCANNERS/PRD/footers, DEMO_SCRIPT.md archived (Nexus narrative dead) and rewritten for Play 1 + Play 2 framing, ScraperBreakdown.jsx category table reconciled with new Financial row + Public Exposure recount, SPRINT_LOG backfill S121-S129

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
