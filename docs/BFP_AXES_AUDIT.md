# BFP Axes Audit — v0 draft

**Status**: internal working document, not for publication.
**Purpose**: extract the implicit Behavioral Fingerprint Protocol from xposeTIP's current 9-axis implementation, identify gaps, and define candidate new axes before any code change or scraper sprint.
**Source of truth for current state**: `api/services/layer4/fingerprint_engine.py`, `docs/ARCHITECTURE.md`, `README.md`.

---

## 1. Framework

A behavioral fingerprint is a vector across N orthogonal-ish axes, each measuring one *layer* of identity. We posit 6 layers:

| Layer | What it captures | Drift behavior |
|---|---|---|
| **Surface** | Visibility of the entity online | Moderate, grows with activity |
| **Forensic** | Presence in formal records | Monotonic non-decreasing |
| **Temporal** | How identity persists and evolves over time | Monotonic + slow |
| **Linguistic** | How the entity expresses itself | Very stable (high persistence) |
| **Relational** | Shape of the entity's network | Stable |
| **Adverse** | Signals of evasion or risk | Stepwise (event-driven) |

Coverage hypothesis to test in this audit: **the 9 existing axes are heavily Surface-biased and almost blind to Temporal, Linguistic, Relational, Adverse layers.** This bias likely reflects what was easy to scrape from L1/L2 modules, not what behavioral identity actually is.

---

## 2. Cross-cutting design questions (must be answered before per-axis spec freeze)

### 2.1 Empty-axis semantics in similarity computation

The current `similarity_engine` computes cosine over the 9-axis vector with threshold 0.7. If axes are added with `data_available=false` (value=null or 0), cosine degenerates:

- **Two targets both with 4 unpopulated axes**: artificially high similarity (the 4 zero-zero pairs inflate the dot product baseline).
- **One target rich, one target sparse**: artificially low similarity (the rich target's populated axes get zero contribution from the sparse one's nulls).

Options for the spec:
- **(a) Per-pair drop**: comparison only over axes populated in *both* targets. Cleanest, but pair-dependent vector length means cosine becomes non-comparable across target pairs.
- **(b) Confidence-weighted**: each axis carries `value` + `confidence`, similarity weights by `min(conf_A, conf_B)`. More principled but heavier.
- **(c) Minimum-axes guard**: refuse to emit similarity unless ≥N axes are populated in both. Simple, defensible, throws away weak comparisons.

**Recommendation**: (c) for v0 + plan (b) for v1. Threshold for "valid comparison" = 6/15 populated axes minimum.

### 2.2 Axis value range and normalization

Current 9 axes appear to all output 0-1 normalized floats (per fingerprint hash construction). The normalization function per axis is not documented anywhere. **Risk**: implementers diverge on normalization, fingerprints become non-comparable across implementations.

**Spec must mandate per-axis**: input domain, normalization function, output range. Probably most axes use log-scaling (counts → log-normalized 0-1) but this needs to be made explicit.

### 2.3 Axis independence

For cosine similarity to be meaningful, axes should be roughly independent. Current 9 axes have overlap problems (see §3). Spec choice: tolerate correlation or enforce orthogonality? Recommendation: tolerate but document; force orthogonality is unrealistic for behavioral data.

---

## 3. Audit: 9 existing axes

For each axis: layer, definition, methodology, value range, drift, current impl reference, empty-state behavior, confidence, audit findings.

### 3.1 `accounts`

- **Layer**: Surface
- **Definition (current, inferred)**: Number of confirmed accounts linked to the entity across all discovered platforms.
- **Methodology**: Count of distinct accounts confirmed by scrapers (HIBP, Sherlock, Maigret, Holehe, scraper_engine outputs).
- **Value range**: 0-1 normalized (likely log-scaled — *to verify in fingerprint_engine.py*).
- **Drift**: Monotonic non-decreasing in active period; can drop on account deletion.
- **Current impl**: `api/services/layer4/fingerprint_engine.py`
- **Empty-state**: 0.0 if no confirmed accounts.
- **Confidence**: HIGH — well-supported by data.
- **Audit finding**: ⚠ **Overlap with `platforms`.** A user with 5 accounts all on Twitter scores differently than a user with 1 account on each of 5 platforms — the distinction must be normatively explicit, not implicit. Today it isn't.

### 3.2 `platforms`

- **Layer**: Surface
- **Definition (inferred)**: Number of distinct platform types where the entity has presence.
- **Methodology**: Distinct platform count derived from accounts.
- **Value range**: 0-1 normalized.
- **Drift**: Similar to `accounts` but slower.
- **Current impl**: `fingerprint_engine.py`
- **Empty-state**: 0.0
- **Confidence**: HIGH.
- **Audit finding**: ⚠ Tightly coupled to `accounts`. Could be redefined as *platform diversity* (entropy-based) rather than count, which would orthogonalize from `accounts`.

### 3.3 `username_reuse`

- **Layer**: hybrid Surface/Behavioral (closer to Linguistic in spirit)
- **Definition (inferred)**: Degree to which the same username pattern is reused across platforms.
- **Methodology**: Username similarity scoring across accounts (likely SequenceMatcher, per `persona_engine.py` usage).
- **Value range**: 0-1 (0 = no reuse, 1 = identical handle everywhere).
- **Drift**: Very stable — username choice is persistent personality trait.
- **Current impl**: `fingerprint_engine.py` + `persona_engine.py`
- **Empty-state**: undefined when <2 platforms (currently outputs 0.0 — *to verify*).
- **Confidence**: HIGH.
- **Audit finding**: ⚠ Mis-categorized as Surface. This is actually a behavioral persistence signal — handle choice is identity expression. Consider renaming to `handle_persistence` and moving conceptually to Linguistic/Behavioral layer.

### 3.4 `breaches`

- **Layer**: Forensic
- **Definition (inferred)**: Count of distinct breach incidents the entity appears in.
- **Methodology**: Distinct breach name count from HIBP, LeakCheck, XposedOrNot, IntelX, DeHashed.
- **Value range**: 0-1 normalized (log-scaled likely).
- **Drift**: Monotonic non-decreasing (breaches are permanent record).
- **Current impl**: `fingerprint_engine.py`
- **Empty-state**: 0.0
- **Confidence**: HIGH.
- **Audit finding**: ⚠⚠ **MAJOR OVERLAP with `data_leaked`.** Both measure breach exposure. The distinction in code is implicit (count vs severity?). Spec must normatively differentiate or merge. Proposal: `breaches` = COUNT axis, `data_leaked` = SEVERITY/types axis. Make explicit in spec.

### 3.5 `geo_spread`

- **Layer**: Surface (geographic projection)
- **Definition (inferred)**: Geographic dispersion of entity's digital footprint.
- **Methodology**: Distinct countries/cities from `geo_consistency.py` (6 signals: IP, breach geo, profile location, timezone, language, platform metadata).
- **Value range**: 0-1 normalized.
- **Drift**: Slow but real (relocations, travel patterns).
- **Current impl**: `fingerprint_engine.py` + `analyzers/geo_consistency.py`
- **Empty-state**: 0.0 if no geo signals.
- **Confidence**: MEDIUM-HIGH.
- **Audit finding**: Solid axis. Could be enriched by integrating timezone consistency signal (already computed in `timezone_analyzer.py`).

### 3.6 `data_leaked`

- **Layer**: Forensic
- **Definition (inferred)**: Volume or severity of data exposed in breaches.
- **Methodology**: Weighted sum of breach data types (password hashes, plaintext passwords, financial, PII, biometric).
- **Value range**: 0-1 normalized.
- **Drift**: Monotonic non-decreasing.
- **Current impl**: `fingerprint_engine.py`
- **Empty-state**: 0.0
- **Confidence**: HIGH but co-dependent with `breaches`.
- **Audit finding**: ⚠⚠ See §3.4. Must explicitly differentiate from `breaches` in spec.

### 3.7 `email_age`

- **Layer**: Temporal
- **Definition**: Inferred age of the email account.
- **Methodology**: Earliest timestamp from all findings (BreachDate, created_at, joined, member_since, first_seen), capped by domain launch date, 30-year sanity cap. Documented in ARCHITECTURE.md "Email Age Inference".
- **Value range**: 0-1 normalized (probably scaled to a max like 25-30 years).
- **Drift**: Monotonic increasing, linear with calendar time.
- **Current impl**: `fingerprint_engine.py`, methodology in ARCHITECTURE.md.
- **Empty-state**: 0.0 if no temporal signals.
- **Confidence**: MEDIUM — heuristic inference, noisy on aliases.
- **Audit finding**: ⚠⚠ **This is the ONLY axis in the entire Temporal layer.** Anemic. Doesn't capture activity continuity, depth of historical presence, or rhythm. Strong case for adding `temporal_persistence` and `activity_rhythm` as siblings.

### 3.8 `security`

- **Layer**: Forensic/hybrid
- **Definition (inferred)**: Email and domain security posture.
- **Methodology**: DNS SPF/DMARC/DKIM analysis (`dns_deep`), MX records, password strength signals from breaches, 2FA presence indicators.
- **Value range**: 0-1 normalized (probably inverted — higher = more secure).
- **Drift**: User-tunable (security improvements move the score).
- **Current impl**: `fingerprint_engine.py` + `dns_deep` scanner.
- **Empty-state**: 0.0
- **Confidence**: MEDIUM.
- **Audit finding**: ⚠ Heterogeneous. Mixes *domain-level* posture (DNS) with *account-level* hygiene (2FA, password strength). Consider decomposing into `email_security_posture` (domain) + `account_hygiene` (personal). Or accept the hybrid but document it normatively.

### 3.9 `public_exposure`

- **Layer**: Surface + partially Forensic
- **Definition (inferred)**: Public mentions of the entity in news media, sanctions lists, corporate registries, legal records.
- **Methodology**: GDELT, GNews, Google News RSS, OpenSanctions, OpenCorporates, Interpol Red Notices, Courtlistener, BODACC, UK Gazette, LBR Luxembourg.
- **Value range**: 0-1 normalized (log-scaled).
- **Drift**: Increases with notoriety; can include negative events.
- **Current impl**: `fingerprint_engine.py` + multiple Public Exposure scrapers.
- **Empty-state**: 0.0
- **Confidence**: MEDIUM (high data but heterogeneous).
- **Audit finding**: ⚠⚠⚠ **CATCH-ALL.** Lumps press mentions, sanctions hits, court records, corporate officer records. These are categorically different signals with different meanings. Must split: at minimum a `formal_records` axis should extract sanctions/court/registry signals out of `public_exposure`, leaving the latter as pure media presence.

---

## 4. Cross-cutting audit findings

### 4.1 Layer imbalance

| Layer | Axes covering it (existing 9) |
|---|---|
| Surface | accounts, platforms, geo_spread, public_exposure (4-5 axes) |
| Forensic | breaches, data_leaked, security, parts of public_exposure (~3 axes) |
| Temporal | email_age (1 axis — anemic) |
| Linguistic | 0 (gap) |
| Relational | 0 (gap — but identity graph exists, just not surfaced as axis) |
| Adverse | 0 (signals scattered in data_leaked, security, code_leak_analyzer — never aggregated) |

**Conclusion**: the 9-axis system reflects scraper output topology, not behavioral identity ontology. Reasonable starting point, but for BFP-as-protocol this bias must be corrected.

### 4.2 Overlap and co-dependence

| Pair | Overlap risk | Resolution |
|---|---|---|
| `breaches` / `data_leaked` | HIGH — both measure breach exposure | Differentiate normatively: count vs severity |
| `accounts` / `platforms` | MEDIUM — coupled by construction | Redefine `platforms` as diversity/entropy |
| `public_exposure` / future `formal_records` | If we split, low; if we don't, public_exposure stays catch-all | Split |
| `email_age` / future `temporal_persistence` | LOW if defined carefully — point estimate vs distribution | Spec both, distinct |
| `security` internal heterogeneity | Domain vs personal hygiene | Decompose or accept hybrid |

### 4.3 Naming hygiene

Several existing names are not normative-friendly: `breaches` (plural? noun? event count?), `security` (too generic for a protocol), `public_exposure` (catch-all by name). For a spec, canonical names should be unambiguous. Proposed renames (open for discussion):

| Current | Proposed canonical |
|---|---|
| `accounts` | `account_count` |
| `platforms` | `platform_diversity` |
| `username_reuse` | `handle_persistence` |
| `breaches` | `breach_incidents` |
| `data_leaked` | `breach_severity` |
| `geo_spread` | `geo_dispersion` (keep) |
| `email_age` | `email_age` (keep, well-bounded) |
| `security` | `security_posture` |
| `public_exposure` | `media_presence` (after splitting out formal_records) |

Renames are breaking changes for the existing radar UI and persisted fingerprints — to be timed with other refactor or kept as internal-canonical with display aliases.

---

## 5. Candidate new axes (6)

### 5.1 `formal_records` — NEW

- **Layer**: Forensic
- **Definition**: Presence in formal/governmental records — courts, corporate registries, sanctions, beneficial ownership databases.
- **Methodology**: Aggregate signals from Courtlistener (US), BODACC (FR), UK Gazette, OpenSanctions, OpenCorporates, Interpol Red Notices, LBR Luxembourg.
- **Value range**: 0-1 normalized.
- **Drift**: Monotonic non-decreasing.
- **Current impl**: TBD — data exists, must be re-routed out of `public_exposure`.
- **Empty-state**: 0.0
- **Confidence**: HIGH — peuplable day-1.
- **Source future**: re-route existing extracts. No new scraper needed.
- **Rationale**: cleanly separates official adversarial signals (court records, sanctions) from media presence. Critical for Play 1 DD use case.

### 5.2 `temporal_persistence` — NEW

- **Layer**: Temporal
- **Definition**: Breadth and depth of observed activity over time — distinct from point-estimate age. Captures *how long has this identity been continuously active across N platforms*.
- **Methodology**: Account creation dates aggregated (multi-platform), activity timestamp spread, Wayback Machine archive depth.
- **Value range**: 0-1 normalized.
- **Drift**: Slow monotonic.
- **Current impl**: TBD — partial signals exist (account_created dates on some platforms, Wayback depth via archive scrapers).
- **Empty-state**: 0.0 if <N temporal signals.
- **Confidence**: MEDIUM — partially populatable from existing data.
- **Source future**: enrich existing scrapers to extract created_at consistently.

### 5.3 `activity_rhythm` — NEW

- **Layer**: Temporal/Behavioral
- **Definition**: Statistical patterns in temporal activity — time-of-day, weekly cycles, posting cadence.
- **Methodology**: Activity timestamp clustering, simple frequency analysis, timezone inference cross-correlation.
- **Value range**: 0-1 (entropy-like measure of pattern distinctiveness).
- **Drift**: Very stable — circadian patterns persist across years.
- **Current impl**: TBD — `timezone_analyzer.py` computes related signal but not rhythm itself.
- **Empty-state**: null / `data_available=false`.
- **Confidence**: LOW initially. Requires new collection logic.
- **Source future**: new scraper layer for activity-pattern extraction (v2).

### 5.4 `linguistic_signature` — NEW

- **Layer**: Linguistic
- **Definition**: Stylometric and lexical fingerprint of the entity's expression across collected text.
- **Methodology**: Sentence embeddings, vocabulary diversity, syntactic patterns, characteristic n-grams. Computed from bios, posts, code commits.
- **Value range**: 0-1 (similarity-to-baseline OR distinctiveness metric — TBD).
- **Drift**: Very stable. Highest persistence axis. Survives username changes, identity rotation, deletion.
- **Current impl**: TBD — text is collected by several scrapers (GitHub bios, Reddit posts, Mastodon, blog excerpts) but no stylometric analyzer exists.
- **Empty-state**: null.
- **Confidence**: N/A (gap total).
- **Source future**: stylometry pipeline (v3). Likely embedding-based with cached vectors.
- **Strategic note**: this is the BFP holy-grail axis. The signal that survives intentional identity rotation. Worth defining now even if populatable in v3.

### 5.5 `network_signature` — NEW

- **Layer**: Relational
- **Definition**: Properties of the entity's social network — clustering coefficient, neighborhood density, centrality.
- **Methodology**: Compute graph metrics from existing identity graph (`graph_builder.py`). Doesn't require new data, only new computation on existing.
- **Value range**: 0-1 normalized.
- **Drift**: Stable.
- **Current impl**: TBD — graph exists, signature computation doesn't.
- **Empty-state**: 0.0 if graph too sparse (e.g., <10 nodes).
- **Confidence**: MEDIUM. Data exists.
- **Source future**: graph metrics computation layer, likely 1-2 days work in `fingerprint_engine.py`.

### 5.6 `adversarial_indicators` — NEW

- **Layer**: Adverse
- **Definition**: Signals of evasion behavior, threat actor presence, or risk exposure. Distinct from `formal_records` (which are formal adverse) — this axis captures informal/behavioral adverse signals.
- **Methodology**: Dark web mentions, code leak presence (`code_leak_analyzer.py` output), anti-OSINT patterns (privacy tools, deliberate obfuscation), threat intel feeds.
- **Value range**: 0-1 normalized.
- **Drift**: Stepwise event-driven.
- **Current impl**: TBD — signals scattered across `data_leaked`, `security`, code_leak_analyzer. Needs consolidation into dedicated axis.
- **Empty-state**: 0.0.
- **Confidence**: HIGH — data exists, requires aggregation.
- **Source future**: aggregation layer over existing analyzers.

---

## 6. Summary: 15-axis BFP v0 candidate set

| # | Axis | Layer | Day-1 populatable? |
|---|---|---|---|
| 1 | account_count | Surface | ✓ |
| 2 | platform_diversity | Surface | ✓ |
| 3 | handle_persistence | Linguistic-adjacent | ✓ |
| 4 | breach_incidents | Forensic | ✓ |
| 5 | geo_dispersion | Surface | ✓ |
| 6 | breach_severity | Forensic | ✓ |
| 7 | email_age | Temporal | ✓ |
| 8 | security_posture | Forensic | ✓ |
| 9 | media_presence | Surface | ✓ (after split) |
| 10 | **formal_records** | Forensic | ✓ (re-route) |
| 11 | **temporal_persistence** | Temporal | ~ (partial) |
| 12 | **activity_rhythm** | Temporal/Behavioral | ✗ (v2) |
| 13 | **linguistic_signature** | Linguistic | ✗ (v3) |
| 14 | **network_signature** | Relational | ~ (graph exists) |
| 15 | **adversarial_indicators** | Adverse | ✓ (aggregation) |

**Layer balance (post-v0)**: Surface 4 / Forensic 4 / Temporal 3 / Linguistic 2 / Relational 1 / Adverse 1. Much more balanced than current 5/3/1/0/0/0.

---

## 7. Open decisions (require Nabil's call)

1. **Naming**: keep current names for backward compatibility, or rename to canonical (proposed §4.3) now to avoid re-renaming at v1.0 publication? **Recommendation**: rename now, before any external consumer depends on names.

2. **Renaming vs aliasing**: if renaming, do we ship code aliases (current names → canonical) for one release, or hard-break? **Recommendation**: alias one release, hard-break v1.0.

3. **`breaches` / `data_leaked` split**: confirm count vs severity? Or merge into a single `breach_exposure` axis? **Recommendation**: keep split with explicit count/severity differentiation.

4. **`security` decomposition**: split into `email_security_posture` + `account_hygiene`, or keep as hybrid documented axis? **Recommendation**: keep as hybrid for v0, decompose in v1.

5. **`public_exposure` → `media_presence` + `formal_records` split**: confirm split? **Recommendation**: yes — strong rationale.

6. **`username_reuse` → `handle_persistence` rename + layer reassignment**: confirm? **Recommendation**: yes.

7. **Empty-axis similarity behavior**: option (a) per-pair drop / (b) confidence-weighted / (c) minimum-axes guard? **Recommendation**: (c) for v0, plan (b) for v1.

8. **Normalization functions per axis**: document existing per-axis normalization in §3 entries (currently TBD) before locking spec.

9. **Linguistic + activity_rhythm + network_signature**: include in v0 spec as defined-but-unpopulated, or defer to v1 spec? **Recommendation**: include in v0. Defining them early lets implementations build toward them; deferring them risks the spec being seen as Surface-only.

---

## 8. Next steps

1. **Verify §3 TBDs in code**: read `fingerprint_engine.py` line by line, confirm or correct each axis's methodology and normalization function.
2. **Resolve open decisions §7**: Nabil call on each.
3. **Produce `docs/BFP_SPEC_v0.md`**: based on this audit + decisions. Per-axis sections become normative spec text.
4. **Identify implementation gap tickets**: each axis with `Current impl: TBD` becomes a future sprint candidate.
5. **Reseed-or-migrate plan**: any axis rename requires fingerprint recompute. Plan with migration 015 if applicable.

---

*End of audit doc v0 draft.*
