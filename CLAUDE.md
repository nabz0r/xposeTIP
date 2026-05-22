# CLAUDE.md — Project context for Claude Code

## What is xposeTIP

Identity Threat Intelligence platform. Scans email → builds identity graph →
PageRank/Markov confidence → clusters personas → pixel art avatar → remediation plan.

## Current version: v1.3.4

163+ sprints. 127 scrapers (110 active, 17 disabled placeholders), 27 scanners, 9 intelligence analyzers, 11-axis fingerprint (S145 formal_records + S147 network_signature).
DB-persisted similarity engine (post-S131): target_similarities table, 11-axis cosine, name-aware combined score (S146 — cosine × name_sim Jaccard), threshold 0.70, audit-grade first_detected preserved across recomputes.
Cascade state machine (post-S134): scans.cascade_state column tracks gathering → computing → similarity → done (failed terminal).
Scanners: 26 registered (SCANNER_REGISTRY) + 9 analyzers. 5 disabled placeholders (maigret, h8mail, ghunt, paste_monitor, databroker_check).
Two-phase pipeline: Phase A (gather: cross-verify → A1.5 phone/crypto extraction → A1.6 secondary enrichment → Pass 1.5 → early profile → Pass 2 → A3.5 sequential name_scraper_engine dispatch post-name-resolution)
→ Phase B (compute: graph → PageRank → score → profile → personas → intelligence → fingerprint).
Deep Scan triggers cascade (discovered emails/usernames/domains → chain-scanned, depth=1, max=5).
Per-scraper module attribution (Sprint 89). 429 exponential backoff on all scrapers.
PDF identity report export (ReportLab, dark theme, tiered by plan).
Phase C (web discovery, operator-triggered): fingerprint-driven Google dorking → trafilatura
page fetch → 6 extractors (rel_me/jsonld/social_link/email/meta_tag/username) → quality gate
→ discovery_leads DB. Budget: 20 queries, 50 pages, 60s default.

## Recent sprints

- **S165** — BFP invariance diagnostic: NEW `scripts/bfp_invariance_diag.py` (read-only). Measures per-axis stability across `fingerprint_history` snapshots for all 206 targets with ≥2 snapshots (avg 6.98 snaps/target, max 47). Output: `docs/diag/invariance_<date>.{md,json}`. Reports BOTH intra-target stability (mean_abs_delta + CV + range) AND inter-target discrimination (across-pop stdev + unique buckets) — a canonical-hash-worthy axis needs both. Top stable+discriminating axes: `public_exposure` (delta 0.003, 18 buckets), `geo_spread` (delta 0.021, 36 buckets), `data_leaked` (delta 0.030, 45 buckets). `security` is most stable per-target (delta=0) but only 4 unique buckets across population — high stability, low discrimination. `network_signature` (delta 0.008, 9 buckets, N=143 post-S147) is excellent on both axes. CLI flags: `--workspace` / `--limit` / `--output-dir` / `--date` (date override for host-vs-container UTC mismatch). Substrate for S166 canonical hash axis selection
- **S164** — BFP pre-implementation audit — autonomous forensic baseline before BFP Phase 1 work. 7-section report at `docs/qa/bfp_pre_impl_audit_2026-05-23.md` covering repo state, platform inventory (127 scrapers / 27 scanners / 9 analyzers / 11 axes), data corpus (15 workspaces / 223 targets / 206 with ≥2 fingerprint snapshots / 6.52 avg snapshots — strong invariance substrate), Phase 1 entry point identified (`fingerprint_engine.py:385` `FingerprintEngine.compute()`), and 22-row gap matrix between BFP page promises (S160-S163) and code reality (15 hard gaps, 5 partial gaps adaptable, 2 already-existing). Recommends sprint sequencing: S165 invariance diag → S166 canonical hash MVP (MinHash/SHA-3-256 + Alembic 017) → S167 claim log scaffolding (`bfp_claims` table) → S168 `findings.verified` formalization → PRE-S169 PQC library eval spike → S169 Merkle root computation. Zero code changes, zero DB writes
- **S163** — BFP page Status section + Hero Inversion visual — NEW `BFPStatus.jsx` (6-stat reference impl snapshot: Version v1.3.4 / Sprints 163+ / Active scrapers 110 of 127 / Fingerprint axes 11 / License AGPL-3.0 / Crypto suite NIST 2024 PQC, with pulse-dot live indicator "xposeTIP — May 2026" + GitHub link at bottom) + NEW `BFPInversionVisual.jsx` (single-composite 280×220 SVG injected above Hero h1: subject 4×4 teal hash grid centered, BFP ring around it, 6 gray actor circles at outer ring, 6 dashed gray inward extraction arrows + 6 solid teal outward vision arrows with arrowheads). Page now 8 sections (Hero → Foundation → Architecture → Cryptography → Subject Layer → Ethics → Status → Roadmap). **BFP public page complete.** Next sprint pivots to implementation (S163-diag = invariance measurement across 11 axes for Phase 1 canonical hash design)
- **S162** — BFP page Subject Layer + Ethics sections — NEW `BFPSubjectLayer.jsx` (4 service tiers: Level I Read free / Level II Guidance free / Level III Monitoring Play 3a paid / Level IV Managed Remediation Play 3b paid; Takedown rendered as separate purple-accented card with circular ⏻ icon = legal safety valve, not a product tier) + NEW `BFPEthics.jsx` (italic thesis with `border-l-2 border-[#00ff88]` accent + cypherpunk/Brin/Right-to-Read lineage; 3-principle grid: Asymmetry is the harm, Empowerment over paternalism, Auditable by design; 2-card commitments grid: Takedown protocol + Auditable methodology). Page now 7 sections total (Hero → Foundation → Architecture → Cryptography → Subject Layer → Ethics → Roadmap)
- **S161** — BFP page Architecture + Cryptography sections — NEW `BFPArchitecture.jsx` (2-layer split: xposeTIP cloud vs BFP local binary, 4 infrastructure parallels DNS/CT/MISP/BFP, Trust + Threat model cards) + NEW `BFPCryptography.jsx` (PQC stack: MinHash over SHA-3-256, SPHINCS+ / SLH-DSA, ML-DSA / Dilithium, ML-KEM / Kyber, Merkle tree — all NIST FIPS 203/204/205 since August 2024). `BFP.jsx` updated to interleave the new sections between Foundation and Roadmap with alternating `[#0a0a0f]`/`[#0d0d14]` backgrounds
- **S160** — BFP public page MVP — NEW `/bfp` route + `dashboard/src/pages/BFP.jsx` wrapper, 3 components (`BFPHero` / `BFPFoundation` / `BFPRoadmap`) under `dashboard/src/components/bfp/`. Hero: "The internet knows who you are… Except you." Inversion statement + 4 attribute pills (Protocol / Subject / Post-quantum / Local-first). Foundation: 4 pillar cards (Identity is a layer / Protocol not product / Subject as first-class / Post-quantum local-first green). Roadmap: 4 buckets (Shipped / Active / Next / Long-term) with color-coded dots + sprint IDs. PublicNav adds `/bfp` between Architecture and Compare. Architecture / Cryptography / Subject Layer / Ethics / Status sections deferred to S161-S163 (56a3783→TBD)
- **S159b** — Cosmetic chip fixes post-S159. UsernameTab.jsx: `getPlatformColor()` normalize regex changed to strip separators entirely (`/[.\-\s_]/g → ''`) so `dev.to` matches `devto` key; `extractPlatform()` generalized to accept both Finding (`.module`/`.data.platform`) and graph node (`.source_module`/`.platform`); graph-node loop now stores canonical platform name. PlatformIcon.jsx (used by OverviewTab): added `npm`/`pypi`/`kaggle` to PLATFORMS map (previously fell to grey default), NEW `PLATFORM_ALIASES` map (`npmmaintainer → npm`, `waybacklinkedinuser → linkedin`, etc.), extracted shared `resolveKey()` helper used by `getPlatformInfo`/`getRemediationLink`/`PlatformIcon` default export (56a3783)
- **S159** — Username taxonomy correction — backend writer fix + DB backfill + frontend defense. Audit confirmed 15 scrapers wrote `indicator_type='username'` while producing domains or emails (root cause: ZERO scrapers had explicit `identity_type`, all fell back to `"username"` via `scraper_scanner.py`). Backend: `scraper_scanner.py` fallback changed to `identity_type or input_type` (was `or "username"`), writer guard skips empty-value findings; `seed_scrapers.py` adds explicit `identity_type` to 6 domain + 9 email scrapers. Migration 016: UPDATE relabel + DELETE 2245 empty-value rows + UPDATE `data.platform='name_synthesis'` for 1684 intelligence-module rows. Frontend `UsernameTab.jsx`: PLATFORM_COLORS rewritten as allow-list, NEW `MODULE_PLATFORM_MAP` for verbose→canonical, NEW `extractPlatform`/`isJunkUsernameValue` helpers applied at findings + graph-node loops. Post-deploy: `recompute_fingerprints.py` recalibrated 113/175 fingerprinted targets (sample drops: 30→17, 23→14, 21→7) (80acd69 → 56a3783)
- **S158** — `module_progress` dict-vs-string defensive handling. NEW `dashboard/src/lib/moduleProgress.js` with `normalizeModuleStatus` (worst-case prioritization: failed>running>completed>skipped>mixed) + `formatModuleStatus` ("N completed / M failed" summary). Fixed 4 sites: ScansTab.jsx:88 crash on dict-shape `scraper_engine_attempts`, TargetDetail.jsx:139 (scraperProgress poll engagement), :339 (Object.values filter for pct calc), :386 (sub-progress detail row gate). Exposed by S157 QA smoke (3a13640 → 282424f verify)
- **S157** — TargetDetail tab consolidation 13 → 5 with sub-pill nav. NEW `FindingsHubTab` / `GraphHubTab` / `SourcesHubTab` wrappers — composition only, 9 inner tab files reused as-is. Compat shim `setActiveTabCompat` maps OverviewTab's pre-S157 `setActiveTab('breaches'|...)` calls to new `{top, sub}` structure without modifying OverviewTab. Connected-accounts useEffect re-wired from `activeTab==='accounts'` (top-tab gone) to `activeTab==='sources'`. Sub-pill design language mirrors S120 preset chips (3e57517 → cb4d1e1 verify)
- **S156** — Doc closure sweep S142-S154 + v1.3.0 stamp (964b3a8)
- **S155** — Synthetic test for S150 `_create_pe_graph_edges` idempotency: NEW `tests/test_create_pe_graph_edges.py` with 3 integration tests against throwaway `_s155_smoke` workspace. Closes S152 smoke validation gap (a7c308b)
- **S154** — Workspace-aware refresh bundle + Redis close + system_stats scoping. Three small P2s: Settings.jsx + Scrapers.jsx `useEffect` deps gain `refreshKey` so workspace switch refetches (mirrors S152 System tabs bundle). `scraper_progress` endpoint now closes its Redis client in `finally`. `/system/stats` table counts now workspace-scoped for targets/scans/findings/identities + users via UserWorkspace; modules stay global (1f7ade4)
- **S153** — Cancel race condition fix — chord child task revoke + finalize_scan guard. Pre-fix: cancel only revoked the parent `launch_scan` task; chord's N child `run_module` tasks kept running and fired finalize_scan callback which overwrote `status='cancelled'` back to `'completed'`. Layer A: `if scan.status == "cancelled": return` early in finalize_scan. Layer B: NEW `api/tasks/utils.py` helpers `stash_scan_child_tasks` + `revoke_scan_tasks`, child IDs stashed in Redis at chord dispatch with 24h TTL, both cancel endpoints iterate+revoke before status flip. Smoke (S152) exposed the bug; e2befba ships the fix. Layer B killed the chord before Layer A ever fired in validation — strongest possible signal Layer B works (e2befba)
- **S152** — Live Scans cross-orgs admin tab + System stale-data fix bundle. NEW `GET /system/scans/live` (superadmin) returns all in-flight scans across all workspaces joined with target+workspace; NEW `POST /system/scans/{id}/cancel` (superadmin, unscoped). NEW `SystemLiveScansTab.jsx` polls 3s, displays workspace name + target email + status + cascade badge + progress bar + age + cancel button (SSE remains disabled platform-wide via `useSSE.js` no-op stub). Bundle fix: 6 System tabs (`Dashboard/Health/Modules/NameRules/Users/Workspaces`) `useEffect` deps gain `refreshKey` so workspace switch refetches (ed6d269)
- **S150** — uq_identity rollback on rescan — get-or-create in `_create_pe_graph_edges`. Pre-fix: rescan with prior media exposure tried to INSERT `Identity` rows with `(workspace_id, target_id, type, value)` tuples already existing → `IntegrityError` on `uq_identity` → silent `PendingRollbackError`, masked by `_set_cascade_state`'s S134 rollback → Pass 2 Findings + graph edges + `cascade_state='computing'` rolled back. Net = silent data loss on rescan (no DB smoking gun, scan reaches `cascade='done'` clean). Fix: get-or-create both `Identity` and `IdentityLink` (uq_identity + uq_identity_link), `session.rollback()` in every `except` around flush. New observability log: `"PASS2: X new graph edges created, Y reused (idempotent rescan)"` (6112faf)
- **S149** — Polling cascade orphelin — unify in-progress predicate. `TargetDetail.jsx` polling `useEffect` filtered scans on narrow `(status === 'running' || 'queued')` while the live progress UI block used the wider predicate including cascade-active completed scans. Result: when scan flipped `running → completed` mid-cascade, useEffect re-ran with narrow filter → empty → `clearInterval` → cascade UI froze. Extracted shared `isScanInProgress` helper used at all 3 call sites (polling + 2 display). CC Playwright live-validation captured a 4-min cascade window with continuous polling and clean stepper transitions (4ae31ff)
- **S148** — Lost-task fragility — `acks_late=True` + `reject_on_worker_lost=True` on `launch_scan` + Celery beat watchdog. Redis broker `visibility_timeout=7200s` gives long cascade scans headroom before broker redelivers. NEW `api/tasks/watchdog.py` with `sweep_orphan_scans` running every 5min via `beat_schedule`. Marks failed: queued >30min, running with no progress >20min, running >240min hard cap. Exposed by orphan scan `c48712fc` (nabz0r@gmail.com, lost 2026-05-20 during sprint-night worker restart storm). First watchdog tick swept it cleanly via hard_timeout branch (dc0475a)
- **S147** — `network_signature` 11th fingerprint axis — spectral entropy of identity-graph eigenvalues. Per-person discriminative measure derived from the top-5 eigenvalues already computed by the engine, never previously surfaced. Closes the same-name homonym failure mode that S146 cannot address — two real John Smiths have `name_sim ≈ 1.0` but distinct identity-graph topologies and therefore distinct `network_signature` values. AXIS_MAX 1.0 (Shannon entropy normalized), SCORE_WEIGHTS rebalanced: data_leaked 0.18 → 0.13 (semantic overlap with breaches at 0.22), network_signature 0.05 (af81c14)
- **S146** — Name-aware similarity engine — `combined = cosine × name_sim`. NEW migration 015 adds `name_similarity` + `cosine_similarity` columns to `target_similarities`. Token-set Jaccard with Unicode normalization (stdlib `unicodedata`, no fuzzy match library). `target_similarities` 3586 → 0 rows on first recompute (FP cleanup — proves name-aware filter eliminates cross-domain noise). Empty post-S146 is by design until a TP case appears (7b4d907)
- **S145** — `formal_records` 10th fingerprint axis — routes Courtlistener (US federal) + BODACC (FR procédures collectives) + UK Gazette findings via `indicator_type='legal_record'`. `FingerprintRadar.jsx` refactored to consume dynamic `ALL_AXIS_LABELS` from backend instead of hardcoded 9-axis list. AXIS_MAX=5 (1 record = 0.2 score, 5+ saturates). Most targets at 0 — works as expected for a discriminative low-prevalence signal (b9a21cd)
- **S144** — Data-driven AXIS_MAX recalibration + fingerprint recompute. After S143 diagnostic across 12 workspaces showed 5/9 axes saturating: `accounts` 15→60, `platforms` 10→50, `username_reuse` 5→10, `data_leaked` 8→25, `email_age_years` 15→40. NEW `scripts/recompute_fingerprints.py` (idempotent, `--dry-run`/`--limit`/`--workspace`, `S144_recalibration` history reason). 172 targets recomputed. Sim table 56 → 3586 backfill. Cross-domain FP discrimination fixed; same-domain (BGL/KPMG/ING) still requires BFP per-person axes (validates S145+S147 direction) (1a57162)
- **S143** — Fingerprint calibration diagnostic — pre-BFP audit. NEW `scripts/diag_fingerprint_calibration.py` runs per-workspace measurement across 12 workspaces (159 fingerprints, 1968 pairs), writes paired MD+JSON snapshots to `docs/diag/`. Proved 9-axis saturates 5/9 axes + 3 axes are workspace-constants → cosine 0.88-1.00 intra-corpus. Empirical baseline that justified S144 axis recalibration and S145+S147 per-person axis additions (87b1ce5 + 7 chore commits)
- **S142** — Doc closure post-S141 — markdown reflects reality. Sprint count badge updated, `/changelog` page noted in README, footer dashboard count reconciled (035192b)
- **S141** — `/changelog` public page parsed from git log: build-time `dashboard/scripts/generate-changelog.mjs` runs `git log` at repo root, writes `dashboard/src/data/changelog.json`. `predev`/`prebuild` hooks regenerate on every dev start / production build. Page renders all 210 commits, filterable by type + sprint + keyword + sha, grouped by month, with GitHub commit links per row
- **S140** — Architecture page full sexy refresh: 3 new stages (`StageCascade` / `StageSimilarity` / `StageDiscovery`) with SVG diagrams, hero stat banner (127·9·5.4B·11·0), `TechStackSection.jsx` (Backend/Storage/Frontend/Output groups), `ScraperBreakdown` active/disabled split (110/17), RoadmapSection v1 backfilled with S130+ achievements, `CollectDiagram` counts realigned (9 wedges summing to 127)
- **S139** — Pricing: dropped `price` field from Starter/Team/Enterprise in `AUDIENCES`. Free keeps "€0 forever". `PricingSection.jsx` conditionally renders the price `<p>` only when present. CTAs (Join waitlist ×2, Contact sales) carry the message
- **S138** — Public nav + footer unification: NEW `PublicNav.jsx` + `PublicFooter.jsx` shared across Landing/Architecture/Manifesto/Compare. Active state via `useLocation()`. Deleted `LandingFooter.jsx` + `ArchFooter.jsx`. `ArchCTA` extracted to its own file. `/changelog` link pre-added (404 until S141 by design)
- **S137** — Cleanup combo: centralized `fallbackSeed` to `dashboard/src/lib/avatar.js` (single source of truth, all 4 consumers import — `ProfileHeader`/`Dashboard`/`Targets`/`UserPreview`). NEW `docs/qa/SMOKE_PROTOCOL.md` documenting the skip-if-recent ≤60min rule + multi-layer evidence pattern (DB + worker logs + API + UI screenshots)
- **S136** — Glyph in header dual-avatar pattern: `ProfileHeader` renders an 80px Snapchat photo with a 32px pixel-art glyph badge bottom-right (rounded-md cutout border). Solo 80px glyph when no photo. Fingerprint Evolution gets right/left fade gradients + "← drag to scroll →" hint + scroll-snap on 20-snapshot timeline
- **S135** — UI polish 4-pack: backend `_target_dict` always returns non-null `fingerprint_avatar_seed` + `fingerprint_axes` (Fix A/B no-render-flip); `TargetDetail.setTimeout(2000)` post-`done` re-fetch kills cascade race (Fix C); `fallbackSeed` aligned across 4 consumers (Fix D — later centralized in S137)
- **S134** — R4 cleanup combo: `_clean_name_value` regex extended to reject lowercase short multi-word phrases ("about me" etc) + 7 entries seed_blacklist. Courtlistener `_coerce_to_str` helper for list-vs-string defensive parse. NEW `scans.cascade_state` column (Alembic 014, values: `gathering` / `computing` / `similarity` / `done` / `failed`). `finalize_scan` instrumented with 4 transitions + failure path. TargetDetail polling extended + cascade stepper UI (Gather → Compute → Similarity, percentage override 75/85/95)
- **S133** — Geomap polish — TopoJSON 110m + heatmap + zoom/pan: world-atlas TopoJSON (~50KB gzipped) bundled in `dashboard/public/`, D3 Natural Earth projection. NEW `dashboard/src/lib/geo.js` with `useWorldData` hook (module-level cache, ISO_ALPHA2_TO_NUMERIC bridge — 52 codes) and `useZoom` (1-8× clamp). `WorkspaceGeoMap` becomes a country-density heatmap. `LocationMap` ground-truth in gold tint. Added `topojson-client` dep
- **S132** — Landing refresh + Compare page: `HeroSection` nav adds Architecture+Compare. `FeaturesSection` extends 3→6 stat cards (phone, crypto, legal). `TrustBar` swapped table-stakes for "US·FR·UK Legal records" + "Verified Provenance". `MockPreview` Risk Signals teaser. NEW `TwoWaysSection.jsx` (Play 1 purple / Play 2 green). NEW `/compare` route + `Compare.jsx` (tri-segment matrix + SVG quadrant + dual CTA)

## Developer

Nabil (nabz0r). Solo founder. Network/security engineer 20+ years.
Master Mathematics (Sorbonne), CCNA, NSE 1-4, JNCIA.

## Tech stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, Celery, PostgreSQL 16 (service=postgres, user=xpose), Redis
- **Frontend**: React 18, Vite, Tailwind CSS 4, D3.js, Recharts
- **Infra**: Docker Compose (api, worker, beat, postgres, redis)
- **Auth**: JWT (access + refresh tokens)
- **DB**: All datetime columns use `TIMESTAMP(timezone=True)`

## Critical rules

1. graph_context is OPTIONAL — all services MUST work without it (graceful fallback)
2. NEVER show platform names as display names
3. NEVER count domain registration as email age
4. NEVER use GeoIP for user location (mail server IP only)
5. Clustering BFS excludes weak edges (associated_with, located_in)
6. superadmin bypasses ALL plan limits
7. Public workspace ("public" slug) for quick scan — transferred on register
8. OSINT tools in Celery worker (`-Q celery,scans,modules`), NEVER in API process
9. API keys AES-256 encrypted at rest (Fernet)
10. Every DB query scoped to workspace_id
11. SCANNER_REGISTRY IDs must match scripts/seed_modules.py
12. wayback_domain and wayback_count are domain-age modules — excluded from identity timeline
13. Discovery leads are NOT findings — separate table (discovery_leads), separate workflow
14. Phase C queries MUST be disambiguated with email domain for name-based searches (homonyme prevention)

## Product Principles (Manifesto)

### Ethical OSINT
- Consent-first: scan yourself or with DPA authorization
- Transparency: every finding shows source, every score explains reasoning
- Purpose limitation: expose to protect, not to exploit
- Right to delete: full purge on request, not soft delete
- No dark patterns: honest scores, no scare-tactic upsells

### Green Intelligence
- Maximum insight per watt — Amiga 500 philosophy
- Data-driven scrapers (JSON config, not code per source)
- Single PostgreSQL, no distributed clusters
- Pixel art avatars: 5.4B combos, zero GPU, zero API
- Every architecture decision: "is this the lightest way?"

### Education First
- Every finding explains WHY it's a risk in plain language
- Remediation actions are actionable, not generic
- The goal is to make users NOT need xpose anymore
- Scores are explainable, not black-box

## Deploy sequence

```bash
killall -9 node && sleep 2
git fetch origin && git reset --hard origin/main
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_modules.py
docker compose exec api python scripts/seed_scrapers.py
docker compose exec api python scripts/seed_blacklist.py
docker compose exec api python scripts/sync_avatars.py
pkill -f vite
cd dashboard && npm install --legacy-peer-deps && npm run dev &
```

After deploy: System → Recalculate Fingerprints → Recalculate Profiles

## Key files

### Backend
- `api/tasks/scan_orchestrator.py` — two-phase pipeline (gather→compute), finalize_scan, graph_context, _full_refinalize (15-step Deep Scan pipeline), _extract_cascade_indicators
- `api/tasks/module_tasks.py` — module execution, pre-flush truncation
- `api/services/layer4/graph_builder.py` — identity graph construction
- `api/services/layer4/confidence_propagator.py` — PageRank (damping=0.85, 20 iter)
- `api/services/layer4/profile_aggregator.py` — name/avatar/bio resolution, avatar quality ranking
- `api/services/layer4/score_engine.py` — dual exposure/threat score
- `api/services/layer4/persona_engine.py` — graph cluster + SequenceMatcher personas
- `api/services/layer4/fingerprint_engine.py` — 11-axis radar (S145 formal_records + S147 network_signature spectral entropy), eigenvalues, avatar_seed
- `api/services/layer4/analysis_pipeline.py` — 9 intelligence analyzers
- `api/services/layer4/analyzers/code_leak_analyzer.py` — GitHub/paste code leak detection
- `api/services/layer4/analyzers/behavioral_profiler.py` — 5 archetypes behavioral classification
- `api/services/layer4/analyzers/geo_consistency.py` — 6-signal geographic consistency analysis
- `api/services/layer4/analyzers/timezone_analyzer.py` — timezone inference from activity timestamps
- `api/services/layer4/username_expander.py` — Pass 1.5 username expansion, scan_single_indicator (generic deep scan)
- `api/services/layer4/username_validator.py` — is_valid_username() junk filter
- `api/services/layer4/source_scoring.py` — source reliability weights
- `api/services/plan_config.py` — plan definitions, feature gates
- `api/services/scraper_engine.py` — URL template + regex/JSONPath extraction
- `api/routers/targets.py` — CRUD + profile + fingerprint + geo_locations + discovery endpoints
- `api/routers/scans.py` — scan CRUD + quick scan + paginated total
- `api/services/report/pdf_generator.py` — PDF identity report (ReportLab)
- `api/discovery/pipeline.py` — Phase C Web Discovery orchestrator
- `api/discovery/extractors/` — 6 lead extractors (rel_me, jsonld, social_link, email, meta_tag, username)
- `api/discovery/quality_gate.py` — dedup discovery leads vs existing findings
- `api/discovery/query_generator.py` — fingerprint-driven search query composition
- `api/tasks/web_discovery.py` — Celery task for Phase C
- `scripts/seed_scrapers.py` — 127 scraper definitions (110 default-enabled, 17 disabled)
- `scripts/seed_modules.py` — 32 scanner modules (26 active + 5 disabled + 1 virtual)

### Frontend
- `dashboard/src/pages/Landing.jsx` — landing page (composed from components/landing/)
- `dashboard/src/pages/TargetDetail.jsx` — full target view (7 tabs)
- `dashboard/src/pages/Architecture.jsx` — technical whitepaper
- `dashboard/src/components/GenerativeAvatar.jsx` — 32x32 pixel art
- `dashboard/src/components/IdentityGraph.jsx` — D3 force-directed graph
- `dashboard/src/components/FingerprintRadar.jsx` — 11-axis radar chart (dynamic ALL_AXIS_LABELS from backend)
- `dashboard/src/components/WorkspaceGeoMap.jsx` — D3 geographic heatmap
- `dashboard/src/pages/UserPreview.jsx` — consumer dashboard preview (/user-preview)
- `dashboard/src/pages/tabs/DiscoveredTab.jsx` — Phase C discovery UI (launch, leads, dismiss)

## Details

See `docs/ARCHITECTURE.md`, `docs/API_REFERENCE.md`, `docs/SPRINT_LOG.md`.
