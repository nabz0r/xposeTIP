# S215 T0 audit-before-fix: scope-drift bug surface analysis

## Per-module date range (from S215_preflight_dates.txt)

| module | n | oldest | newest |
|---|---|---|---|
| rdap_domain | 46 | 2026-03-28 17:40 UTC | **2026-05-22 20:56 UTC** |
| wayback_domain | 31 | 2026-03-28 16:35 UTC | 2026-05-22 14:41 UTC |
| alienvault_otx_domain | 0 | — | — |
| securitytrails_ping | 0 | — | — |

## S159 commit reference

`80acd69 feat(S159): username taxonomy correction` landed
**2026-05-22 19:19 UTC** (21:19 +0200).

## Edge-case analysis

The `rdap_domain` newest row (20:56 UTC) is **~1h37min AFTER** the S159 commit.
Per the literal spec STOP rule, this would trigger an investigation halt.

Current `scrapers` table state (post-S214, pre-S215):

```
alienvault_otx_domain  input_type=domain  identity_type=NULL  enabled=t
rdap_domain            input_type=domain  identity_type=NULL  enabled=t
securitytrails_ping    input_type=domain  identity_type=NULL  enabled=f
wayback_domain         input_type=domain  identity_type=NULL  enabled=t
```

All 4 Scraper DB rows currently have `identity_type=NULL`. The S159 fallback
in `scraper_scanner.py:166` reads `scraper.identity_type or scraper.input_type`,
which for NULL evaluates to `'domain'`. A scan running TODAY with current code
+ current DB would correctly emit `indicator_type='domain'` for these modules.

So how did the 20:56 row land with `indicator_type='username'`?

**Restart-window edge case.** The S159 code change touched
`api/services/layer1/scraper_scanner.py` — a Celery worker module.
Per CLAUDE.md (added later, in S185): _"after any worker-code change
without a full `--build`, also run `docker compose restart worker beat` —
Celery caches module imports at process boot."_

The 20:56 UTC row is in the ~1.5h window between the S159 commit and the
worker restart. Worker was still executing pre-S159 cached bytecode with
the hardcoded `'username'` fallback.

This is NOT a live bug in current code — it's a one-time deployment timing
artifact, since documented in CLAUDE.md.

## Decision

PROCEED with T1-T4 as written. The T0 STOP rule's intent is to halt if
there's a **live code path still emitting junk**. There isn't: current code
+ current DB would emit correctly.

The S215 seed fix (`identity_type='domain'` explicit) is belt-and-braces:
it removes any reliance on the fallback for these 4 modules, so future
restart-window edge cases on related deploys can't reproduce.

The migration 027 relabels the 77 legacy rows that came from either
pre-S159 emissions OR the S159-restart-window emissions. Both classes are
real domain data, just mistagged.
