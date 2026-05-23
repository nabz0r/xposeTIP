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
| S142 | Doc closure post-S141 — markdown reflects reality, sprint count badge updated, `/changelog` page noted, footer dashboard count reconciled (commit 035192b) |
| S143 | Fingerprint calibration diagnostic — pre-BFP audit. NEW `scripts/diag_fingerprint_calibration.py` ran 12 workspaces (159 FPs, 1968 pairs), proved 9-axis saturates 5/9 axes + 3 workspace-constants → cosine 0.88-1.00 intra-corpus. Justified S144 + S145+S147 (commit 87b1ce5 + 7 chore commits) |
| S144 | Data-driven AXIS_MAX recalibration + fingerprint recompute. `accounts` 15→60, `platforms` 10→50, `username_reuse` 5→10, `data_leaked` 8→25, `email_age_years` 15→40. NEW `scripts/recompute_fingerprints.py` (idempotent, `--dry-run`/`--limit`/`--workspace`). 172 targets recomputed, sim table 56→3586 backfill (commit 1a57162) |
| S145 | `formal_records` 10th fingerprint axis — routes Courtlistener/BODACC/UK Gazette via `indicator_type='legal_record'`, `FingerprintRadar.jsx` consumes dynamic `ALL_AXIS_LABELS` from backend, AXIS_MAX=5 (commit b9a21cd) |
| S146 | Name-aware similarity engine — `combined = cosine × name_sim`. NEW migration 015 (`name_similarity` + `cosine_similarity` cols), Unicode token-set Jaccard via stdlib `unicodedata`. `target_similarities` 3586→0 on first recompute (FP cleanup) (commit 7b4d907) |
| S147 | `network_signature` 11th fingerprint axis — spectral entropy of identity-graph eigenvalues. AXIS_MAX 1.0, SCORE_WEIGHTS rebalanced (data_leaked 0.18→0.13, network_signature 0.05). Closes same-name homonym failure mode (commit af81c14) |
| S148 | Lost-task fragility — `acks_late=True` + `reject_on_worker_lost=True` on `launch_scan`, Redis broker `visibility_timeout=7200`. NEW `api/tasks/watchdog.py` `sweep_orphan_scans` every 5min via `beat_schedule` (queued>30min, no-progress>20min, hard-cap>240min). Exposed by orphan scan `c48712fc` (nabz0r@gmail.com, May 20 worker restart storm) — first watchdog tick swept it via hard_timeout branch (commit dc0475a) |
| S149 | Polling cascade orphelin — `TargetDetail.jsx` polling guard now uses shared `isScanInProgress` predicate matching the wider display predicate (covers `status='completed' AND cascade_state ∈ {gathering,computing,similarity}`). Playwright validated 4-min cascade window with continuous polling (commit 4ae31ff) |
| S150 | uq_identity rollback on rescan — get-or-create both `Identity` and `IdentityLink` in `_create_pe_graph_edges`, `session.rollback()` in every except around flush. Re-classified P0→P2 (silent data loss, not crash — `_set_cascade_state` S134 rollback masked `PendingRollbackError`, lost Pass 2 Findings + graph edges) (commit 6112faf) |
| S151 | Investigated, no repro found (fingerprint_history "absent on some profiles" — 215/215 targets had populated history, likely backfilled by S144 recompute). Skipped, no code change |
| S152 | Live Scans cross-orgs admin tab + System stale-data bundle fix. NEW `GET /system/scans/live` + `POST /system/scans/{id}/cancel` (superadmin), NEW `SystemLiveScansTab.jsx` (polls 3s). Bundle fix: 6 System tabs `useEffect` deps gain `refreshKey` (commit ed6d269) |
| Smoke S148-S152 | Multi-layer Playwright validation on 3 targets across 2 workspaces. Verdict: PASS WITH NOTES. Surfaced S153 cancel race bug, S150 validation gap, /system/stats counter inconsistency. Evidence + report in `docs/qa/smoke_2026-05-22_s148_s149_s150_s152.md` (commit 05299a1) |
| S153 | Cancel race condition fix — chord child task revoke + finalize_scan guard. NEW `api/tasks/utils.py` helpers `stash_scan_child_tasks` + `revoke_scan_tasks`, Redis SADD `scan:{id}:child_tasks` TTL 24h at dispatch, both cancel endpoints iterate+revoke before status flip. Layer B killed chord callback before Layer A's early-return ever fired in validation (commit e2befba) |
| S154 | Workspace-aware refresh bundle + Redis close + system_stats scoping. Settings.jsx + Scrapers.jsx `useEffect` deps gain `refreshKey`, `scraper_progress` Redis client closed in `finally`, `/system/stats` table counts now workspace-scoped (targets/scans/findings/identities + users via UserWorkspace; modules stay global) (commit 1f7ade4) |
| S155 | Synthetic test for S150 `_create_pe_graph_edges` idempotency. NEW `tests/test_create_pe_graph_edges.py` — 3 integration tests against throwaway `_s155_smoke` workspace (fixture-managed cleanup): reuses existing Identity on duplicate value, second call doesn't duplicate link, new value still creates new Identity+link. All 3 PASS. Closes S152 smoke validation gap (commit a7c308b) |
| S156 | Doc closure sweep S142-S154 + v1.3.0 stamp. 9-axis → 11-axis across CLAUDE.md/README/DEMO_SCRIPT, 26 scanners → 27, sprints 141+ → 154+, version 1.2.0 → 1.3.0 (commit 964b3a8) |
| S157 | TargetDetail tab consolidation 13 → 5 with sub-pill nav. NEW FindingsHubTab/GraphHubTab/SourcesHubTab wrappers, compat shim `setActiveTabCompat`, connected-accounts useEffect re-wired to `activeTab==='sources'`. Sub-pills mirror S120 preset chip style (commits 3e57517 + cb4d1e1 verify) |
| S158 | `module_progress` dict-vs-string defensive handling. NEW `dashboard/src/lib/moduleProgress.js` (normalizeModuleStatus + formatModuleStatus). Fixed 4 sites: ScansTab crash + 3 silent correctness sites in TargetDetail (commits 3a13640 + 282424f verify) |
| S159 | Username taxonomy correction. Backend writer fix (`scraper_scanner.py` fallback + empty-value guard) + seed_scrapers explicit `identity_type` on 15 scrapers (6 domain + 9 email) + alembic 016 (relabel 936 + delete 2245 empty + tag 1684 intelligence rows as `platform='name_synthesis'`) + frontend allow-list defense in `UsernameTab.jsx` + recompute_fingerprints recalibrated 113/175 targets (commit 80acd69 + 804b33f verify) |
| S159b | Cosmetic chip fixes post-S159 verify. UsernameTab normalize regex strip separators; extractPlatform accepts both findings and graph nodes; PlatformIcon adds npm/pypi/kaggle + PLATFORM_ALIASES + shared resolveKey helper (commit 56a3783) |
| S160 | BFP public page MVP — NEW `/bfp` public route + `BFP.jsx` wrapper + 3 components (BFPHero / BFPFoundation / BFPRoadmap). Hero: Inversion statement + 4 attribute pills. Foundation: 4 pillar cards. Roadmap: 4 buckets (Shipped / Active / Next / Long-term) with color-coded dots. PublicNav adds `/bfp` link. Architecture / Cryptography / Subject Layer / Ethics / Status deferred to S161-S163. Version bumped v1.3.0 → v1.3.1 |
| S161 | BFP page Architecture + Cryptography sections — NEW `BFPArchitecture.jsx` (2-layer split xposeTIP cloud vs BFP local binary + 4 infrastructure parallels DNS/CT/MISP/BFP + Trust + Threat model cards) + NEW `BFPCryptography.jsx` (5-row PQC stack: MinHash/SHA-3-256, SPHINCS+/SLH-DSA, ML-DSA/Dilithium, ML-KEM/Kyber, Merkle — all NIST FIPS 203/204/205 since August 2024). `BFP.jsx` interleaves the new sections between Foundation and Roadmap with alternating `[#0a0a0f]`/`[#0d0d14]` backgrounds. Subject Layer / Ethics deferred to S162; Status section + hero visual swap to S163. Version bumped v1.3.1 → v1.3.2 |
| S162 | BFP page Subject Layer + Ethics sections — NEW `BFPSubjectLayer.jsx` (4-tier service grid Level I-IV with Free/Paid pill + Play 3a/3b badges on paid tiers; Takedown rendered as separate full-width purple-accented card with circular ⏻ icon, framed as legal safety valve not a product tier) + NEW `BFPEthics.jsx` (italic thesis block with `border-l-2 border-[#00ff88]` accent + cypherpunk/Brin/Right-to-Read lineage; 3-principle grid: Asymmetry is the harm / Empowerment over paternalism / Auditable by design; 2-card commitments grid: Takedown protocol + Auditable methodology). Page now 7 sections (Hero → Foundation → Architecture → Cryptography → Subject Layer → Ethics → Roadmap). Status section + hero visual swap deferred to S163. Version bumped v1.3.2 → v1.3.3 |
| S163 | BFP page Status section + Hero Inversion visual — NEW `BFPStatus.jsx` (6-stat reference impl snapshot: Version v1.3.4 / Sprints 163+ / Active scrapers 110/127 / Fingerprint axes 11 / License AGPL-3.0 / Crypto suite NIST 2024 PQC, pulse-dot live indicator + GitHub link) + NEW `BFPInversionVisual.jsx` (single-composite 280×220 SVG: subject 4×4 hash grid centered + BFP ring + 6 actor circles + dashed-in extraction + teal-out vision arrows with markerEnd arrowheads — injected into Hero between badge and h1). `BFP.jsx` inserts Status between Ethics and Roadmap with bg flip on Roadmap. Page now 8 sections (Hero → Foundation → Architecture → Cryptography → Subject Layer → Ethics → Status → Roadmap). **BFP public page complete.** Version bumped v1.3.3 → v1.3.4 |
| S170 | `docs/BFP_SPEC_v0.md` committed — v0.2.0 public working draft, Apache-2.0. **Doc-only sprint** (zero code, zero migrations, zero behavior change). Session 1 of spec rewrite covers the trust layer formalization: **§2.3 entropy-honesty framing** (~28 bits Shannon → clustering primitive, not unique identifier; unique identity via composition with subject binding signature + network signals); **§15 Cross-Verification** (8 sub-sections: definition, source identity, subject- vs population-scoped, self-exclusion, idempotence, snapshot semantics, sources ordering, conformance); **§16 Claim Log** (9 sub-sections: 9-field claim structure + 4 reserved, JSON canonical encoding with sort_keys + `(",", ":")` separators, SHA-3-256 hash function, emission rule `cross_verification_count ≥ 1`, UNIQUE dedup, append-only, evidence-evolution deferral, conformance); **§17 Merkle Anchor** (12 sub-sections: per-trust-boundary scope, canonical leaf ordering `emitted_at` ASC + `claim_hash` tiebreaker, RFC 6962 leaf `SHA3-256(0x00 \|\| raw)` / internal `SHA3-256(0x01 \|\| left \|\| right)`, odd-leaf promotion with CVE-2012-2459 callout, empty-tree no-sentinel, anchor snapshot 5-field record, rebuild frequency unspecified, MUST provide independent verification means, conformance, explicit out-of-scope: inclusion proofs / consistency proofs / STH / gossip). Existing §15/§16 renamed to `Appendix A` / `Appendix B`. Closing marker `*End of BFP v0.2.0 public working draft.*`. Final file 877 lines (+338 vs prior internal v0.1.0). Non-normative notes reference the xposeTIP reference impl at v1.6.0 (`findings.cross_verification_count` 48.0%, 1,107 claims across 15 workspaces, 6 claim types). Closes the gap where the `/bfp` public page committed to a protocol with no published specification (the substrate from S166 + S168 + S167 + S169 is now publicly formalized). Sessions 2–3 deferred (§5 axes status flags, §9.2 MinHash spec, §11 conformance trust-layer extension, §13 PQC stack, §3 terminology, §4 2-layer diagram, §12 subject-rights tiers, §14 versioning ties, Appendix B refresh). PRE-S169 PQC eval spike now blocks Session 2 §13. Version v1.6.0 → v1.6.1 (patch — doc-only) |
| S169 | Merkle root over `bfp_claims` → tamper-evident trust log. Completes Phase 1 substrate. NEW `bfp_merkle_roots` table (Alembic 020): append-only per-workspace root snapshots (workspace_id/root_hash/num_leaves/root_version/computed_at; latest = MAX(computed_at)). NEW `api/services/bfp/merkle_builder.py`: **RFC 6962** binary Merkle tree, **SHA-3-256**, **`0x00 \|\| leaf` / `0x01 \|\| left \|\| right` domain separation** (defeats second-preimage at level boundaries), **odd-leaf promotion** (NOT duplication — CVE-2012-2459 antipattern). Canonical leaf order: `bfp_claims ORDER BY emitted_at ASC, claim_hash ASC` (deterministic, append-friendly). Populates `bfp_claims.merkle_position` (0-indexed, dense per workspace). NEW `scripts/build_bfp_merkle.py` (idempotent, `--workspace`/`--dry-run`); NEW `scripts/verify_bfp_merkle.py` (independent re-derivation from raw `claim_hash`, exit 1 on mismatch). **No app-code changes to existing write paths** (only `api/models/__init__.py` +2 lines registering the new model; `persist_scanner_results` untouched). Live: **15 workspaces, 1,107 claims → 15 roots** (sizes 6–297 leaves); `verify_bfp_merkle.py` 15/15 OK; second rebuild produces identical roots (stability proven); **tamper smoke: corrupted 1 hash → verify reports 14/15, exit 1; restored → 15/15, exit 0**. `bfp_claims.parent_hash` left NULL (reserved for inclusion-proof storage in a later sprint). Batch-only in MVP (no Celery beat hook yet, no API endpoint, no UI surface). Version v1.5.0 → v1.6.0 |
| S167 | `bfp_claims` append-only trust log — **first BFP protocol structure in the repo**. NEW `bfp_claims` table (Alembic 019, 16 columns incl. 4 reserved for S169/Phase 3) with UNIQUE `(target_id, claim_type, claim_value)`, content-addressable via SHA-3-256 `claim_hash` over canonical JSON (sort_keys + sorted sources + `claim_hash_version:1`). **Locked emission rule:** finding must have `cross_verification_count >= 1` AND non-null `indicator_type`+`indicator_value`. NEW `api/services/bfp/claim_emitter.py` (sole writer, `pg_insert.on_conflict_do_nothing` for idempotency). NEW `api/models/bfp_claim.py` (registered in `__init__`). NEW `scripts/backfill_bfp_claims.py` (idempotent). `persist_scanner_results` emits live alongside S168 cross-verif recompute, same transaction. Live: **1,107 claims emitted** from 8,012 cross-verified findings (ip 352 · username 301 · email 223 · domain 223 · first_name 6 · social_url 2). All 1,107 SHA-3-256 hashes valid 64-hex; recompute-from-stored verified deterministic. All 4 reserved columns NULL on every row. Append-only = convention only at MVP. Version v1.4.1 → v1.5.0 |
| S168 | Cross-verification formalization — BFP trust layer seed signal moved from read-time computation (`api/routers/findings.py:54-68` + `:154-167` S124-S126 lineage) to persisted columns. NEW `findings.cross_verification_count` (int) + `findings.cross_verification_sources` (jsonb) + `idx_findings_cross_verification_count` (Alembic 018). `persist_scanner_results` recomputes for all `(target_id, indicator_value)` tuples in each batch within the same transaction. `_finding_dict` reads from columns; response keys `cross_verified_count`/`cross_verified_by` preserved unchanged. NEW `scripts/backfill_cross_verification.py` (idempotent). Live: 223 targets / 16704 findings / 8012 backfilled updates (48% cross-verified), 1007/1007 consistency, dashboard unchanged. Trust-layer foundation for S167 `bfp_claims`. Version v1.4.0 → v1.4.1 |
| S166 | `bfp_behavioral_hash_v1` MVP — **first BFP-protocol code in repo**. NEW `FingerprintEngine._compute_behavioral_hash_v1()` (MinHash 128 perms seed=42, 20 buckets/axis, over `public_exposure`/`geo_spread`/`data_leaked` per S165 ranking). NEW `targets.bfp_behavioral_hash_v1` column + index (Alembic 017). NEW `scripts/recompute_bfp_behavioral_hash.py` (backfill + `--compare A B` Jaccard utility). Orchestrator persists from happy + Deep Scan paths. NEW `datasketch>=1.6,<2.0` dep. Wording: "Canonical identity hash" → "Canonical behavioral hash" with composition caveat (BFPArchitecture + BFPCryptography). Backfill: 223/223 targets (100%), 80 distinct hashes (143 collisions — expected at K=3 ≈ 6.68 bits entropy). Smoke: self-compare=1.0, distinct pairs 0.0–0.21. **Clustering primitive, not unique identifier.** Version v1.3.4 → v1.4.0 |
| S165 | BFP invariance diagnostic — NEW `scripts/bfp_invariance_diag.py` (read-only). Measures per-axis stability across `fingerprint_history` snapshots for 206 targets (avg 6.98 snaps/target). Outputs `docs/diag/invariance_2026-05-23.{md,json}`. Reports BOTH intra-target stability (mean_abs_delta, CV, range) AND inter-target discrimination (across-pop stdev, unique buckets) — canonical hash needs both. Recommendation: `public_exposure` / `geo_spread` / `data_leaked` are stable+discriminating. `security` is perfectly stable per-target but only 4 unique buckets across population. `network_signature` (S147) excellent on both, N=143. CLI: `--workspace` / `--limit` / `--output-dir` / `--date`. Substrate for S166 canonical hash axis selection |
| S164 | BFP pre-implementation audit — autonomous read/analysis sweep before BFP Phase 1 work. 7-section report at `docs/qa/bfp_pre_impl_audit_2026-05-23.md`: repo state (HEAD b529cd6, v1.3.4, 245-line sprint log) · platform inventory (127 scrapers / 27 scanners / 9 L4 analyzers / 11 axes + AXIS_MAX dump) · data corpus (15 workspaces / 223 targets / 16704 findings / 6113 identities; **206/223 targets have ≥2 fingerprint snapshots, avg 6.52 snapshots — strong invariance substrate**) · current fingerprint computation entry points (`fingerprint_engine.py:385` `FingerprintEngine.compute()` is the canonical insertion point; existing `_compute_hash` / `_compute_enhanced_hash` / `_compute_avatar_seed` are UI-only and don't block) · **22-row gap matrix BFP page promises vs code reality (15 hard gaps including MinHash/PQC/Merkle/subject portal/takedown, 5 partial gaps adaptable from `findings.verified` cross-verification infra at 41.8% coverage, 2 already-existing)** · tech debt (17 alembic migrations, 0 FIXMEs in fp/intelligence paths, 17 disabled scrapers, untracked BFP_SPEC stubs) · recommended Phase 1 sequencing (S165 invariance diag → S166 canonical hash MVP MinHash/SHA-3-256 + Alembic 017 → S167 claim log scaffolding `bfp_claims` + Alembic 018 → S168 `findings.verified` formalization Alembic 019 → PRE-S169 PQC liboqs-python eval spike → S169 Merkle root). Zero code changes, zero DB writes, no version bump |

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
- [x] 11-axis digital fingerprint (9 axes at v1.0, +formal_records S145, +network_signature S147)
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
