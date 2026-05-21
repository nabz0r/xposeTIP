# UX smoke protocol

Conventions for manual UX smoke runs in `docs/qa/`. Established post-S136 (commit 39c0427).

## When to run a smoke

After any sprint that touches:
- Visible UI components (header, cards, lists, charts)
- Cascade / scan state machine
- Backend contract fields consumed by the dashboard (avatar_seed, fingerprint_axes, etc.)

A smoke is **not** a substitute for a forensic round. Forensic = backend pipeline correctness on many targets. Smoke = UI/contract sanity on one well-known target after a UI sprint.

## File naming

- Report: `docs/qa/ux_smoke_<YYYY-MM-DD>_<sprints>.md`
- Screenshots: `docs/qa/screenshots_<YYYY-MM-DD>/ux_smoke_<NN>_<short_name>.png`
- API evidence: `docs/qa/screenshots_<YYYY-MM-DD>/evidence_api_<short_name>.json`

If multiple smokes happen the same day, distinguish via the `<sprints>` suffix (e.g. `s134_s135_s136`).

## Skip-if-recent rule

For sprints that touch cascade or scan-state UI, the smoke needs to capture the cascade transitions in the UI. Re-running a scan is expensive (~3–5 min) and adds noise.

**Rule**: if the smoke target's most-recent scan completed **within the last 60 minutes**, the cascade UI screenshots may be reused from an earlier same-day smoke that captured the same scan ID. The report MUST state:
- The age of the most-recent scan at smoke time
- The scan ID
- The path to the reused screenshots
- A worker-log timeline of the cascade transitions for that exact scan ID

If reuse is invoked, the cascade transitions remain verified via worker logs (DB layer evidence) even though the UI screenshots are not freshly captured.

If no qualifying recent screenshot exists, **trigger a fresh scan** on a different target rather than waiting out the 60-min window.

## Multi-layer evidence

Every smoke report must collect evidence across at least three of these four layers, with at least one being DB or worker-log:

| Layer | Tool | Output |
|---|---|---|
| DB | `psql` queries | inline tables / row counts in the report |
| Worker logs | `docker compose logs worker` | timestamped transition log snippets |
| API | `curl` to FastAPI endpoints | JSON evidence files (saved alongside screenshots) |
| UI | Playwright MCP browser | PNG screenshots (saved in `screenshots_<DATE>/`) |

The report's evidence section uses one sub-section per layer, with tables for facts and code blocks for raw output.

## Per-check table

Every check listed in the spec gets a row in a Check Table:

| Check | Expected | Observed | Status | Screenshot |
|---|---|---|---|---|

Status uses ✅ (pass), ⚠️ (partial — explain in Findings section), ❌ (fail).

## Mandatory sections

1. **TL;DR** — one paragraph stating PASS/PARTIAL/FAIL count + the single most important finding
2. **Reference IDs** — target_id, workspace_id, scan_id, HEAD commit
3. **DB layer evidence**
4. **API layer evidence** (with file paths to saved JSONs)
5. **UI layer evidence** (with file paths to saved PNGs)
6. **Per-check table** (one row per check from the spec)
7. **Findings of note** — anything that warrants attention even if it passed
8. **Open items / follow-ups** — tracked work for future sprints

## Pre-existing residual issues

When an error or warning observed in this smoke also existed before the sprint being smoke-tested, label it explicitly:

> One pre-existing residual `<error message>` log line on a sibling scan window — already tracked from `<R-NUMBER or sprint>`.

This prevents the next maintainer from thinking the sprint introduced the issue.

## Commit & push

A smoke commit contains, at minimum:
- the markdown report
- all referenced screenshots
- all referenced API evidence JSONs

The commit message format:

```
chore(qa): UX smoke test <SPRINTS> — <target name> in browser with multi-layer evidence
```

Push to `main` only after manual review of the report.
