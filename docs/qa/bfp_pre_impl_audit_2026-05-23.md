# BFP pre-implementation audit — 2026-05-23

**Audit date:** 2026-05-23
**HEAD:** `b529cd6` (S163 — BFP page Status section + Hero Inversion visual)
**Auditor:** Claude Code (automated, per S164 spec)
**Methodology:** read/grep/SQL only. Zero code changes, zero DB writes. Every claim is backed by an inline command reference.

## Executive summary

- **Platform state:** v1.3.4, **163 sprints shipped** (sprint log = 245 lines), **127 scrapers** (110 enabled / 17 disabled), **27 scanners** in `SCANNER_REGISTRY`, **9 Layer-4 intelligence analyzers**, **11 fingerprint axes** declared in `AXIS_MAX` dict. Reference implementation healthy — zero FIXME/TODO/HACK markers in `api/services/layer4/` or `api/services/intelligence/`.
- **Corpus state:** **15 workspaces · 223 targets · 16,704 findings · 6,113 identities.** Crucially for invariance work: **206/223 (92%) of targets have ≥2 fingerprint snapshots**, **194/223 (87%) have ≥3 snapshots**, avg 6.52 snapshots per target — strong invariance corpus exists out-of-the-box.
- **BFP page promises vs reality:** **15 hard gaps** (canonical hash, PQC signatures, Merkle log, subject binding, MinHash, takedown protocol, subject portal, monitoring, managed remediation, API-driven Status, etc.). **1 partial gap** that's adaptable: `findings.verified` is `true` on 6,984/16,704 (42%) — the cross-verification signal S124-S126 produced is the **only buildable foundation** for the trust layer. Everything else is greenfield.
- **Phase 1 entry point identified:** `api/services/layer4/fingerprint_engine.py:385` — `FingerprintEngine.compute(...)`. Existing `_compute_hash` (line 905) + `_compute_enhanced_hash` (line 912) + `_compute_avatar_seed` (line 1003) are UI-only (pixel-avatar seed), NOT protocol-conformant. BFP canonical hash should sit adjacent or replace them. No existing logic blocks Phase 1.
- **Critical path:** S165 invariance diag (read existing 1,455+ snapshots, measure per-axis stability) → S166 canonical hash MVP (MinHash/SHA-3-256 over selected invariant axes, add `targets.bfp_canonical_hash` column) → S167 claim log scaffolding (new `bfp_claims` table with Merkle structure, dual-write from `findings`). **Phase 3 PQC work needs a pre-sprint** to evaluate `liboqs-python` / `pyspx` bindings before any signing code is committed (zero PQC libs currently in `requirements.txt`).

---

## 1. Repo state

| | |
|---|---|
| **HEAD sha** | `b529cd693a1f3e89422990d642bba1354e1e40cb` |
| **HEAD subject** | feat(S163): BFP page Status section + Hero Inversion visual |
| **git describe** | `v0.12.0-214-gb529cd6` (last semver tag = v0.12.0, 214 commits ago) |
| **Declared version (CLAUDE.md)** | `v1.3.4` |
| **Dashboard package.json** | `0.1.0` (decoupled from project semver) |
| **Sprint log length** | 245 lines (`docs/SPRINT_LOG.md`) |
| **Date of audit** | 2026-05-23 |

**Last 10 commits:**
```
b529cd6 feat(S163): BFP page Status section + Hero Inversion visual
9e37aaf feat(S162): BFP page Subject Layer + Ethics sections
873a093 feat(S161): BFP page Architecture + Cryptography sections
e7d0225 feat(S160): BFP public page MVP — foundation + roadmap
56a3783 fix(S159b): npm_maintainer + dev.to cosmetic chip fixes — UsernameTab + PlatformIcon
804b33f qa(S159): verify username taxonomy fix in UI — PASS
80acd69 feat(S159): username taxonomy correction — backend writer fix + DB backfill + frontend defense
282424f qa(S158): re-verify dict-vs-string fix — PASS
3a13640 fix(S158): module_progress dict-vs-string defensive handling
cb4d1e1 qa(S157): UX refonte smoke — PASS WITH NOTES
```

---

## 2. Platform inventory

| Component | Count | Source |
|---|---|---|
| Scrapers (total in DB) | **127** | `SELECT enabled, COUNT(*) FROM scrapers GROUP BY enabled;` |
| Scrapers (enabled) | **110** | same query |
| Scrapers (disabled) | **17** | same query |
| `api/scrapers/` dir files | 11 PE scrapers | `ls api/scrapers/` (gdelt/gnews/google_news/interpol/opensanctions/bodacc/courtlistener/uk_gazette/lbr/opencorporates + __pycache__) |
| Scanners (SCANNER_REGISTRY) | **27** | `grep -A 60 "SCANNER_REGISTRY = " api/tasks/module_tasks.py` |
| Intelligence analyzers (L4) | **9** | `ls api/services/layer4/analyzers/` |
| Fingerprint axes | **11** | `AXIS_MAX` dict in `fingerprint_engine.py` |
| Workspaces | **15** | `SELECT slug FROM workspaces;` |
| Targets | **223** | `SELECT COUNT(*) FROM targets;` |
| Findings | **16,704** | `SELECT COUNT(*) FROM findings;` |
| Identities | **6,113** | `SELECT COUNT(*) FROM identities;` |

**Scrapers by category (enabled only):**
| category | count |
|---|---|
| social | 50 |
| metadata | 12 |
| gaming | 9 |
| people_search | 9 |
| archive | 9 |
| breach | 6 |
| public_exposure | 5 |
| financial | 3 |
| identity | 3 |
| code_leak | 3 |
| social_account | 1 |

**Layer-4 analyzers** (`ls api/services/layer4/analyzers/`):
`behavioral_profiler` · `breach_correlator` · `code_leak_analyzer` · `domain_analyzer` · `geo_consistency` · `ip_analyzer` · `risk_assessor` · `timezone_analyzer` · `username_correlator`

**Fingerprint axes (`AXIS_MAX` dict at `fingerprint_engine.py:148`):**
1. `accounts` — max 60 (S144 recalibrated from 15)
2. `platforms` — max 50 (S144 from 10)
3. `username_reuse` — max 10 (S144 from 5)
4. `breaches` — max 5
5. `geo_spread` — max 5
6. `data_leaked` — max 25 (S144 from 8)
7. `email_age_years` — max 40 (S144 from 15)
8. `security_weak` — max 4
9. `public_exposure_raw` — max 1.0 (already normalized)
10. `formal_records_raw` — max 5 (NEW S145 — legal_record findings)
11. `network_signature_raw` — max 1.0 (NEW S147 — spectral entropy of identity-graph eigenvalues)

**Pipeline phases (observed in `api/tasks/scan_orchestrator.py` via `PIPELINE[%s]:` log lines):**
- `launch_scan` (line 162) → modules dispatch (chord)
- `finalize_scan` (line 249) — the cascade phases:
  - **Phase A (gather):** cross_verify → secondary_identifiers (A1.5) → secondary_enrichment (A1.6) → pass1.5 → early_profile → name_scrapers (A3.5) → pass2
  - **Phase B (compute):** graph_builder → pagerank → graph_context → score → profile_aggregator → personas → intelligence → fingerprint
- `_full_refinalize` (line 943) — Deep Scan re-pipeline

Pipeline matches declared shape from CLAUDE.md (`A1 → A1.5 → A1.6 → Pass 1.5 → early profile → Pass 2 → A3.5 → Phase B`). No deviation observed.

---

## 3. Data corpus state

### Workspaces (`SELECT slug, name, plan FROM workspaces`)

15 total. All enterprise plan except `public` (free, "Quick Scans" workspace for landing-page scans).

| slug | targets |
|---|---|
| bgl-bnp-paribas | 47 |
| friends | 35 |
| quentin | 30 |
| nexus-2026 | 21 |
| ferrero | 15 |
| default | 13 |
| threatconnect-cs | 12 |
| threatconnect | 12 |
| threatconnect-support | 9 |
| dataminr | 9 |
| maersk | 7 |
| threatconnect-devops | 4 |
| public | 3 |
| ing-luxembourg | 3 |
| kpmg | 3 |

**Total targets: 223**

### Fingerprint snapshots (critical for invariance work)

`fingerprint_history` is `jsonb` on `targets` (no separate snapshots table). One target row, many snapshots inside the JSONB array, truncated to last 50 entries at write time.

```
total_targets : 223
with_1plus    : 223  (100%)
with_2plus    : 206  (92.4%)
with_3plus    : 194  (87.0%)
avg snapshots : 6.52 per target
```

**Implication: invariance work has plenty of substrate** — 206 targets with multiple snapshots, avg 6+ snapshots each. The cap-at-50 means the upper bound is bounded but the lower bound is rich.

### Similarity corpus (`target_similarities`)

Schema (post-S146 + S150):
`id · workspace_id · target_a_id · target_b_id · similarity · axis_diffs(jsonb) · first_detected · last_computed · name_similarity · cosine_similarity`

```
total_pairs       : 2
cosine_above_0.7  : 2
avg_cosine        : 0.814
avg_name          : 1.000
```

**Note:** S159 recompute_fingerprints flushed the prior 56 → 3586 → 0 pair lineage; current 2 pairs are TPs from post-S146 name-aware filter. **Similarity corpus is essentially empty** — not a useful substrate for invariance work in its current state.

### Findings + cross-verification

`findings` schema (20 columns): `id · workspace_id · scan_id · target_id · module · layer · category · severity · title · description · data · url · indicator_value · indicator_type · verified · status · first_seen · last_seen · created_at · confidence`

```
total findings           : 16,704
verified=true            : 6,984  (41.8%)  ← cross-verification signal
data.cross_verified_by   : 0      (key not present)
data.cross_verification_count : 0  (key not present)
indicator_type IS NULL   : 471    (2.8% — post-S159 cleanup residual)
```

**Cross-verification surface:** the `findings.verified` boolean is the only persisted artifact of the S124-S126 cross-verification work. The "count" and "by" details that the UI shows (`ProvenanceCard` tier badges) appear to be computed at read-time, not stored. **42% of findings are flagged verified** — this is the foundation BFP can lean on for trust signalling.

---

## 4. Current fingerprint computation — Phase 1 entry point

| Item | Path:line | Notes |
|---|---|---|
| **Main compute entry** | `api/services/layer4/fingerprint_engine.py:385` | `FingerprintEngine.compute(findings, identities, profile_data, email, links, graph_context, country_code)` — returns full fingerprint dict |
| Raw values extraction | `api/services/layer4/fingerprint_engine.py:456` | `_extract_raw_values(...)` |
| Per-axis normalization | `api/services/layer4/fingerprint_engine.py:804` | `_normalize(raw)` — applies `AXIS_MAX` divisors |
| Score (0-100) computation | `api/services/layer4/fingerprint_engine.py:824` | `_compute_score(axes)` |
| Existing hash (legacy/UI) | `api/services/layer4/fingerprint_engine.py:905` | `_compute_hash(axes, raw, email)` — **NOT protocol-conformant** |
| Existing enhanced hash | `api/services/layer4/fingerprint_engine.py:912` | `_compute_enhanced_hash(axes, raw, email, eigenvalues)` |
| Graph signature (eigenvalues) | `api/services/layer4/fingerprint_engine.py:921` | `_compute_graph_signature(identities, links)` |
| Avatar seed (UI only) | `api/services/layer4/fingerprint_engine.py:1003` | `_compute_avatar_seed(axes, eigenvalues, email)` |
| Snapshot append (orchestrator path 1) | `api/tasks/scan_orchestrator.py:697` | `history.append(...); target.fingerprint_history = history[-50:]` |
| Snapshot append (orchestrator path 2) | `api/tasks/scan_orchestrator.py:1221` | Same pattern, used in `_full_refinalize` (Deep Scan) |
| Score persistence on target | `api/tasks/scan_orchestrator.py:485-497` (PIPELINE log lines) | Writes via `compute_score` (`api/services/layer4/score_engine.py:152`) |

**Frontend avatar derivation** (used as fallback when backend `fingerprint_avatar_seed` is null):
- `dashboard/src/lib/avatar.js:4` — comment explicitly notes "NOT a strict mirror of backend `_email_only_avatar_seed`"
- `dashboard/src/components/landing/constants.js:83` — `hashEmail(email)` (landing-page demo only)

**Phase 1 implication:**
- The BFP canonical hash should be **added next to `FingerprintEngine.compute()`** (line 385) — same call path, same data substrate (axes + raw + email + graph signature already computed).
- `_compute_hash` / `_compute_enhanced_hash` are deterministic over inputs but are **UI-derivation only** (consumed by `_compute_avatar_seed`). They are NOT designed as forgery-resistant canonical identity hashes.
- **No existing hash logic blocks BFP Phase 1.** A new method `_compute_canonical_hash_bfp(axes, raw, email)` can sit alongside and not interfere.

---

## 5. BFP page promises vs xposeTIP reality (critical)

`/bfp` page components: `BFPArchitecture · BFPCryptography · BFPEthics · BFPFoundation · BFPHero · BFPInversionVisual · BFPRoadmap · BFPStatus · BFPSubjectLayer` (9 files).

Each claim below is sourced to the JSX file that asserts it and checked against the codebase via grep/SQL.

| # | Page claim | Source (file) | Reality in code | Gap |
|---|---|---|---|---|
| 1 | "Canonical identity hash (locality-sensitive)" | BFPArchitecture.jsx | Not implemented. `_compute_hash` exists at `fingerprint_engine.py:905` but is UI-only avatar derivation, not LSH. | **HARD** — Phase 1 blocker |
| 2 | "MinHash over SHA-3-256" | BFPCryptography.jsx | No MinHash code anywhere. No SHA-3-256 either (existing hashing uses Python's `hashlib.sha256` per inspection of `_compute_hash`). | **HARD** — Phase 1 core |
| 3 | "Subject binding ceremony" | BFPArchitecture.jsx + BFPCryptography.jsx | Not implemented. No `binding` / `ceremony` / subject-proof code anywhere. | **HARD** — Phase 3 |
| 4 | "Subject + operator signatures (post-quantum)" | BFPArchitecture.jsx | No PQC signing code. No `liboqs` / `pyspx` / equivalent in `requirements.txt`. | **HARD** — Phase 3 blocker |
| 5 | "SPHINCS+ (SLH-DSA) subject attestations" | BFPCryptography.jsx | No code. NIST FIPS 205 reference exists only as page copy. | **HARD** — Phase 3 |
| 6 | "ML-DSA (Dilithium) scraper/operator signatures" | BFPCryptography.jsx | No code. Scrapers don't sign claims (only persist via `persist_scanner_results`). | **HARD** — Phase 3 |
| 7 | "ML-KEM (Kyber) key encapsulation" | BFPCryptography.jsx | No code. Subject-operator channel doesn't exist yet either. | **HARD** — Phase 3 (deferrable) |
| 8 | "Append-only claim log (Merkle-anchored)" | BFPArchitecture.jsx | `findings` table exists but is mutable (UPDATE/DELETE happen — see S159 migration 016). No Merkle tree, no append-only enforcement. | **HARD** — Phase 2 blocker |
| 9 | "Merkle tree, SHA-3-256 log integrity" | BFPCryptography.jsx | No Merkle constructs in code (`grep "merkle"` returns 0 hits in `api/`). | **HARD** — Phase 2 core |
| 10 | "Evidence-based consensus (≥N independent scrapers converge)" | BFPArchitecture.jsx | **PARTIAL** — `findings.verified=true` on 41.8% of rows. S124-S126 cross-verification logic exists but the count/by-list is computed at read-time, not stored. | **ADAPT** — formalize the existing signal |
| 11 | "Audit trail traceable to each source" | BFPArchitecture.jsx | `findings.module` + `findings.url` provide source attribution. `findings.data->>'scraper'` adds per-scraper telemetry (S159 verified). | **EXISTS** (informal) — needs canonical schema |
| 12 | "No proof-of-work — energy-light by design" | BFPArchitecture.jsx | Trivially true (no PoW exists). | ✅ OK |
| 13 | "Read (free) — see own behavioral fingerprint" | BFPSubjectLayer.jsx | No subject-side login. `UserPreview.jsx` exists as a *consumer dashboard preview* (operator-facing demo, route `/user-preview`), not a subject auth portal. | **HARD** — Subject portal sprint |
| 14 | "Guidance (free) — remediation per finding" | BFPSubjectLayer.jsx | `findings.description` has generic descriptions. No subject-facing per-finding remediation copy. `getRemediationLink()` in `PlatformIcon.jsx` provides per-platform security-settings URLs (S159b) — closest existing artifact. | **PARTIAL** — Subject portal sprint |
| 15 | "Monitoring (Play 3a) — continuous tracking + alerts" | BFPSubjectLayer.jsx | Not implemented. No recurring-scan-per-subject scheduler. No Stripe / billing. No alert delivery. | **HARD** — Future (post legal-entity decision) |
| 16 | "Managed remediation (Play 3b) — xposeTIP acts on subject's behalf" | BFPSubjectLayer.jsx | Not implemented. Operator-facing manual cleanup only. | **HARD** — Future |
| 17 | "Takedown protocol — legal safety valve" | BFPSubjectLayer.jsx + BFPEthics.jsx | No takedown intake form, no GDPR Art. 8 workflow, no court-order ingestion path. `grep "takedown\|gdpr\|opt_out"` returns 0 hits in `api/`. Removal currently = manual DB delete. | **HARD** — Phase TBD |
| 18 | "Local-first / no cloud lock-in" | BFPHero.jsx | False as of today — xposeTIP runs in cloud (Docker Compose stack, single Postgres). No "local binary" exists. | **HARD** — Phase 4 (full federation work) |
| 19 | "Auditable methodology — scoring algorithm published" | BFPEthics.jsx | Methodology IS in source (open repo). But no formal SPEC document yet (`docs/BFP_SPEC_v0.md` exists as untracked stub, not committed). | **PARTIAL** — Doc sprint can close |
| 20 | "Reference implementation open-source" | BFPEthics.jsx + BFPStatus.jsx | True — AGPL-3.0 (S114). | ✅ OK |
| 21 | "Page Status: 127 scrapers / 11 axes / v1.3.4" | BFPStatus.jsx | Hardcoded in `STATS` array. Will drift the moment next scraper or axis is added/removed. | **DRIFT RISK** — API-driven endpoint needed |
| 22 | "Cross-source convergence resists single-source poisoning" | BFPArchitecture.jsx | Threat model claim. The `findings.verified` signal IS computed across sources. Robustness against adversarial source not formally proven. | **PARTIAL** — needs validation framework |

**Summary:**
- **15 HARD gaps** requiring greenfield implementation (rows 1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 15, 16, 17, 18 + DRIFT row 21).
- **5 partial gaps** adaptable from existing infra (rows 10, 11, 14, 19, 22).
- **2 already-existing** (rows 12, 20).
- **Cross-verification signal (`findings.verified`) is the ONLY trust-layer infrastructure that already exists.** Everything else listed in the Architecture/Cryptography/Subject Layer/Ethics sections is page copy ahead of code.

---

## 6. Tech debt visible pre-BFP

- **Alembic migrations applied:** 17 total, last = `alembic/versions/016_fix_indicator_type_taxonomy.py` (S159, 2026-05-22).
- **FIXME/TODO/XXX/HACK markers in fingerprint + intelligence paths:** **0** (`grep -rE "FIXME|TODO|XXX|HACK" api/services/layer4/ api/services/intelligence/` returns nothing). Code paths are clean post-S148-S159 reliability + taxonomy work.
- **Disabled scrapers (17):**
  `bodacc_search · breachdirectory · courtlistener_search · dehashed_public · google_linkedin_search · gravatar_json · gravatar_profile_v2 · haveibeensold · lbr_luxembourg · namemc_profile · numverify_phone · opencorporates_officers · proxycurl_linkedin · rocketreach_lookup · securitytrails_ping · uk_gazette_search · veriphone_phone`
  Of these, `bodacc_search · courtlistener_search · uk_gazette_search · lbr_luxembourg · opencorporates_officers` have Python implementations under `api/scrapers/` but are toggled off in the DB scrapers table — likely retired/API-key-required/superseded.
- **Prior forensic baselines:**
  - `docs/qa/forensic_round_4_2026-05-21.md` — HEAD `d6d4671` (S133), Friends workspace, 5 sampled targets, post-S131 similarity engine + S132 landing/Compare context
  - `docs/qa/forensic_round_3_2026-05-22.md` — HEAD `9226a37` (S127), Friends workspace, 3 sampled targets, post-S122 chain
  - `docs/qa/forensic_2026-05-20.md` — Original E2E pipeline audit (nabz0r@gmail.com / nabilukson@gmail.com)
  - 4 S148-S159 smoke reports also present (S157 UX refonte, S158 / S159 verify, S148-S152 smoke).
- **Untracked stubs in docs/ that may affect Phase 1 scope:**
  - `docs/BFP_AXES_AUDIT.md`
  - `docs/BFP_SPEC_v0.md`
  - `docs/diag/fingerprint_calibration_dataminr_20260521-2102.{md,json}`
  - `docs/diag/fingerprint_calibration_kpmg_20260521-2102.{md,json}`
  - `rescan_kpmg_dataminr.sh`
  These have been untracked across multiple sprints. Worth a decision (commit / .gitignore / delete) before BFP work begins.

**Items to address before or during Phase 1:**
1. Commit or gitignore `docs/BFP_SPEC_v0.md` + `docs/BFP_AXES_AUDIT.md` (these are referenced by name in roadmap docs but not in repo)
2. Add `liboqs-python` / `pyspx` evaluation as a pre-Phase-3 spike — must precede any signing-code sprint
3. Decide on the future of `findings.verified` semantics (current = boolean post-hoc; BFP needs ≥N convergence count exposed). Migration 017 candidate
4. Audit the 5 disabled-but-implemented scrapers (bodacc/courtlistener/uk_gazette/lbr/opencorporates) — either re-enable as legal_record sources for axis 10 or remove the Python files

---

## 7. Recommended Phase 1 sprint sequencing

| Order | Sprint | Scope | Rationale | Risk |
|---|---|---|---|---|
| 1 | **S165 — invariance diag** | Read all 223 targets' `fingerprint_history` arrays. For each of the 11 axes, measure across-snapshot variance per target + cross-target distribution. Output: `docs/diag/invariance_2026-05-23.{md,json}`. No code change, no DB write. | 206/223 targets have ≥2 snapshots — substrate is ready. Without this measurement, axis selection for the canonical hash is guesswork. | **Low** — read-only |
| 2 | **S166 — canonical hash MVP** | New method `_compute_canonical_hash_bfp(axes, raw, email)` in `FingerprintEngine`. MinHash + SHA-3-256 over the K most-invariant axes identified by S165. Add `targets.bfp_canonical_hash` column (Alembic 017). Backfill via `scripts/recompute_bfp_hash.py`. | First real BFP code in repo. Bridges page narrative to implementation. Plugs cleanly into existing `compute()` at line 385. | **Medium** — one schema migration, one new script |
| 3 | **S167 — claim log scaffolding** | New `bfp_claims` table (Alembic 018) with `merkle_position` / `parent_hash` / `signature_placeholder` columns. Dual-write from `findings.persist_scanner_results`. `bfp_claims` is **read-only** for now — Merkle root computation deferred to S169. | Foundation for Phase 2 append-only log. Can run in parallel with S166 (different layer). | **Medium** — schema migration + dual-write |
| 4 | **S168 — `findings.verified` formalization** | Migration 019: add `findings.cross_verification_count` (int) and `findings.cross_verification_sources` (jsonb). Backfill from existing cross-verification logic. Surface in `/api/v1/findings/{id}` response. Adapts S124-S126 work into BFP-conformant trust signal. | Closes the partial gap from Section 5. The ONLY adaptable existing infra deserves formalization before claim-log goes live. | **Low** — additive columns + backfill |
| 5 | **PRE-S169 — PQC library evaluation spike** | One-day timeboxed evaluation: install `liboqs-python` (Python bindings to liboqs), benchmark SPHINCS+ sign/verify, evaluate `pyspx` as fallback. Output: short MD note on chosen library + integration shape. No code committed yet. | Phase 3 signature work is blocked on this choice. Doing the eval as a pre-sprint avoids a half-done sprint if the chosen library has dealbreakers (e.g., no aarch64 wheels). | **Low** — eval only, no commits |
| 6 | **S169 — Merkle root computation** | After S167's claim log has a few hundred rows, implement Merkle root + inclusion proofs. Add CT-style append-only log endpoint. | Phase 2 core. Pre-req: S167 must be live and stable. | **Medium** |

**Critical path dependencies:**
- S166 (canonical hash) depends on S165 (axis selection)
- S167 (claim log) can run in parallel with S166 (different layer of the architecture)
- S168 (verified formalization) can run anytime after S167 ships (or before — no hard dep)
- S169 (Merkle) depends on S167 having real data
- PRE-S169 PQC eval depends on nothing; can start day 1 of Phase 3

**Sprints intentionally NOT in this plan:**
- Subject portal (Level I/II UI) — separate concern, no canonical-hash dependency. Can ship parallel.
- Play 3a Monitoring / Play 3b Remediation — gated on legal-entity decision, billing, scheduler. Not on Phase 1-2 critical path.
- Takedown protocol — separate workflow sprint, no crypto dependency.
- Status page API-driven endpoint — drift-risk fix, low priority.

---

**Audit ends here. Next step per S164 spec:** Nabil reads, validates recommended sequencing, confirms (or adjusts) S165 invariance diag as the next sprint. CC does NOT auto-spec S165 from this audit alone.
