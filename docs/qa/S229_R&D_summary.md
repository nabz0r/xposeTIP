# S229 — Username R&D Refresh: Synthesis

_Generated: 2026-05-25, audit run `docs/qa/S229_username_audit_20260525T191950Z/`._

## Validator-fail baseline drift

| Sprint | Validator-fail rate | Total username findings |
|---|---:|---:|
| S213 baseline (pre-cleanup) | 38.5% | 7,645 |
| S214 post-cleanup | 2.5% | 4,827 |
| **S229 current** | **1.6%** | **5,045** |

**Verdict: validator is holding.** Post-S214 rate has actually drifted *down* from 2.5% to 1.6% even as the corpus grew by 218 findings (+4.5%). The prod `is_valid_username` (S179 design) plus the migration 026 cleanup (S214) plus the S215 scope-drift relabel (wayback/rdap) is doing the job — no regression sprint needed for the validator itself.

The 82 remaining validator-fail rows are scattered across modules with `multi_dot_handle` / `fqdn_tld` / `paren_pattern` reasons — small-volume legacy bleed, not worth a dedicated cleanup migration. Roll them into a periodic sweep if/when one is scheduled.

## Advanced patterns (NEW S229 signal)

### `looks_like_full_name` — 237 findings, 4.8% of validator-PASS

Sample values:

| module | indicator_value |
|---|---|
| `bluesky_profile` | Akim Reinhardt |
| `bluesky_profile` | Kevin Poulsen |
| `bluesky_profile` | Justin Jacobs |
| `buymeacoffee_profile` | Timothy Cuenca |
| `buymeacoffee_profile` | Jesse Li |
| `chesscom_profile` | Andrea Marconi |
| `chesscom_profile` | Rowen Dsouza |

Top emitter modules (full table in `by_module_advanced.csv`):

| module | pass count | advanced count | advanced rate % |
|---|---:|---:|---:|
| `kofi_profile` | 40 | 35 | 87.5% |
| `gumroad_profile` | 37 | 30 | 81.1% |
| `gitlab_profile` | 135 | 102 | 75.6% |
| `ifttt_profile` | 30 | 22 | 73.3% |
| `medium_profile` | 47 | 34 | 72.3% |

**Interpretation:** these are scope-drift candidates, NOT junk. The scrapers are extracting real-name display fields from profile pages and tagging them `indicator_type='username'` instead of `'name'`. Values are valid identity data — they belong in the `name` bucket. The 237 row count is small but the affected modules are 13 high-rate emitters (>50% advanced rate on validator-PASS). The structural fix is upstream extraction config or a S215-pattern relabel migration.

### `single_dot_ambiguous` — 1,081 findings, 21.8% of validator-PASS

Sample values:

| module | indicator_value |
|---|---|
| `anilist_profile` | aurelie.paini |
| `anilist_profile` | pascal.steichen |
| `anilist_profile` | jonas.mercier |
| `anilist_profile` | alexander.link |
| `anilist_profile` | philip.meyers |
| `anilist_profile` | allesandro.nervegna |
| `anilist_profile` | emmanuel.fleig |

**Interpretation:** likely a mostly-valid bucket. Most samples are `firstname.lastname` shape dotted handles, which S179 explicitly chose to spare from the prod validator (handles like `josephine.lespierre` are real Steam-style usernames). This advanced classifier flags any single-dot `word.word` whose suffix isn't in the known-TLD allow-list (`.tech`, `.online`, etc. — *32 TLDs covered*) but it cannot disambiguate `aurelie.paini` (valid handle) from `acme.tech` (missed-TLD domain — `.tech` is in fact covered here, so this is an example only).

**The high rate (21.8%) is misleading without triage.** It mostly reflects the legitimate `firstname.lastname` handle convention that dominates corporate-cohort scans. Needs manual review on a 30-50 row sample before any cleanup action.

## S230 cleanup scope proposals

Three options, ranked by signal-to-noise:

### S230a — Relabel `looks_like_full_name` (LOW-RISK, HIGH-CLARITY)

**Pattern:** S215 migration 027 (in-place `UPDATE indicator_type` based on classifier rule replayed inside the migration).

Scope: 237 rows across 13 high-rate modules (`kofi_profile`/`gumroad_profile`/`gitlab_profile`/`ifttt_profile`/`medium_profile`/`devto_profile`/`strava_profile`/`vimeo_profile`/`buymeacoffee_profile`/`keybase_profile`/`threads_profile`/`snapchat_profile`/`twitch_profile`). Relabel from `username` → `name`. Values preserved.

Companion upstream fix: add `identity_type='name'` to the 13 scraper definitions in `seed_scrapers.py` (or whichever extraction config governs them) so future scans emit correctly.

Recommended sequencing: do the seed fix first, restart worker, validate 1 fresh scan emits `name` instead of `username`, THEN run the relabel migration.

### S230b — Validator hardening (HIGHER-RISK, MAYBE REJECTS LEGIT HANDLES)

Add `looks_like_full_name` detection to prod `is_valid_username`. Risk: may reject legit handles like `JohnDoe` (single-word Title Case is NOT caught by the current S229 regex — needs ≥1 space — so `JohnDoe` is safe; but `Jane Doe` style handles do exist on some platforms like Discord display names).

Defer unless S230a alone proves insufficient — the upstream fix in S230a (scrapers tagging correctly at source) is the cleaner intervention.

### S230c — `single_dot_ambiguous` manual triage (NEEDED BEFORE ANY ACTION)

Manual review of a 50-row stratified sample from `flagged_single_dot_ambiguous.csv` (1,081 rows, spread across `anilist_profile`/`twitch_profile`/`imgur_profile`/`kaggle_profile`/`pinterest_profile` plus ~25 other modules):

- If >90% are valid handles (likely outcome per S179 design intent): extend the S229 classifier's TLD allow-list with whatever missed TLDs surface, RE-RUN, archive the resulting smaller bucket as "validator-correctly-spares". No DB action.
- If >30% are missed-TLD domains: extend `_DOMAIN_TLD_RE` in `username_validator.py` (S179) with those TLDs and relabel via migration.

Until triaged, treat the 21.8% rate as a **classifier sensitivity signal**, not a data-quality problem.

## Out of scope (this sprint)

- No DB migration
- No prod validator change (`username_validator.py` untouched)
- No deletion or relabel
- No scraper extraction config touched
