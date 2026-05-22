# Verify S158 — module_progress dict-vs-string fix

**Commit verified:** 3a13640 (S158)
**Date:** 2026-05-22
**Target:** Nexus 2026 / marie-jo.gutenkauf@paperjam.lu (`2602f8b8-...`)
**Pre-fix repro:** S157 QA smoke (commit cb4d1e1, `docs/qa/s157/15_scans.png`)

## Verdict

**PASS** — bug closed.

## What changed

| Before (commit 3e57517) | After (commit 3a13640) |
|---|---|
| Click Scans tab on T2 → React error boundary triggers, 5 errors logged: `Objects are not valid as a React child (found: object with keys {agify, genderize, gcal_public, ...})` | Click Scans tab on T2 → page renders cleanly, zero React errors |
| ScansTab content blank / partial render | All scan rows visible, module chips visible |

## Live verification

1. Logged in → switched to Nexus 2026 → navigated to T2 (`/targets/2602f8b8-...`)
2. Clicked **Scans** top tab
3. Inspected DOM: `scraper_engine_attempts` chip now reads:
   ```
   scraper_engine_attempts: 64 no_data / 32 success / 4 no_input / 3 error_401 / 1 error_999 / 1 error_400
   ```
4. String-shape chips unchanged: `scraper_engine: completed` (×3)
5. Console: **0 × "Objects are not valid as a React child"** errors
   (residual errors are pre-existing — favicon 404s + stale 401s from prior session; unrelated to S158)

## Root cause refinement

The S157 smoke attributed the crash to `module_progress.scraper_engine` having a dict shape. The actual culprit was a **sibling module** named `scraper_engine_attempts` — a per-error-class counter map (`{no_data: 64, success: 32, error_401: 3, ...}`). The S158 helper handles it correctly: dict → `formatModuleStatus` returns "64 no_data / 32 success / ..." sorted by count desc.

The 4 sites fixed in S158 normalize via `normalizeModuleStatus(value)` which prioritizes worst-case (failed > running > completed/skipped > mixed). For `scraper_engine_attempts` the values are non-canonical (`no_data`, `success`, `error_401`, ...) so the aggregate falls through to `'mixed'` → chip color is orange (`#ff8800`), surfacing the partial-state nature visually.

## Evidence files

- `docs/qa/s158/01_scans_t2_fixed.png` — Scans tab full view, rendering cleanly
- `docs/qa/s158/02_dict_chip_summary.png` — zoom on the `scraper_engine_attempts` chip showing the count summary

## Sites not directly re-exercised

Sites 2-4 in `TargetDetail.jsx` (the silent correctness fixes for progress-bar interpolation and scraper sub-progress poll engagement) require a fresh **running scan** with dict-shape `scraper_engine` to observe live. The Node-based helper smoke (10 assertions) executed at S158 commit time covered the normalizing logic. Live observation deferred to next opportunity when a fresh scan is in flight.
