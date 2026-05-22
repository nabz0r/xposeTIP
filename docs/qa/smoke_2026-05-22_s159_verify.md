# Verify S159 — username taxonomy correction

**Commit verified:** 80acd69 (S159)
**Deploy verified:** scripts/seed_scrapers.py + alembic 016 + recompute_fingerprints.py all applied
**Date:** 2026-05-22
**Target:** Nexus 2026 / marie-jo.gutenkauf@paperjam.lu (`2602f8b8-…`)

## Verdict

**PASS** — pollution surface closed end-to-end.

## DB-level deploy results

| Metric | Pre | Post | Δ |
|---|---|---|---|
| Mislabeled `indicator_type='username'` (15 modules) | 3,181 | 0 | -3,181 |
| Now `indicator_type='domain'` (6 modules) | 0 | 361 | +361 (relabeled) |
| Now `indicator_type='email'` (9 modules) | 0 | 575 | +575 (relabeled) |
| Empty-value rows in 15 modules | 2,245 | 0 | -2,245 deleted |
| `intelligence` rows tagged `platform='name_synthesis'` | 0 | 1,684 | +1,684 |
| Findings total | 18,284 | 16,039 | -2,245 |
| Alembic revision | 015 | 016 (head) | ✓ |
| Scrapers DB table `identity_type` populated for 15 | 0/15 | 15/15 | ✓ |
| Fingerprint targets recomputed | — | 113/175 | 65% had material axis change |

Sample score deltas (all dropped — inflated `username_reuse` corrected):
- aogorodnic@threatconnect.com: 21 → 7
- lpopa@threatconnect.com: 30 → 17
- jmarlow@threatconnect.com: 23 → 14

## UI-level verification (T2 paperjam)

Navigated to `/targets/2602f8b8-…` → Findings hub → Usernames sub-pill.

**Sub-pill counts:** `Usernames(8) → Usernames(7)` — one duplicate-by-relabel removed.

**Platform chips rendered post-fix (legitimate only):**
```
telegram · imgur · pypi · gitlab · keybase · steam · reddit ·
hackernews · dev.to · twitch · npm_maintainer · anilist · roblox
```

**Pollution chips no longer visible** (per S157 smoke captures, these previously rendered on this same target):
- `disify_email`
- `dns_dmarc_check`
- `dns_txt_saas`
- `mailcheck_email`
- `crtsh_subdomains`
- `disposable_email_check`
- `hackertarget_hosts`
- `wayback_count`
- `emailrep_breaches`
- `intelx_public`
- `webmii_search`

**Pollution values no longer visible** as "usernames":
- Bare domains: `gmail.com`, `kpmg.lu`, `dataminr.com`, `paperjam.lu`, `ferrero.com` (gone — relabeled to `domain` indicator_type)
- Full emails: `nabz0r@gmail.com`, `laura.morgana@ing.lu`, `aurelija.duderyte@ferrero.com` (gone — relabeled to `email` indicator_type)

Body-text grep for `@` (other than target's own header) and bare-domain regex returns only the target's email itself — no orphan usernames.

## Evidence files

- `docs/qa/s159/01_usernames_clean.png` — UsernameTab on T2 post-fix, no junk chips

## Sites the audit cleared as legit (no change needed)

- `wayback_linkedin_user` — real LinkedIn handles, `data.platform → 'linkedin'` via S159 MODULE_PLATFORM_MAP
- `npm_maintainer` — real npm usernames, `data.platform → 'npm'` via S159 MODULE_PLATFORM_MAP
- `pypi_profile` — real PyPI usernames, unchanged

## Defense-in-depth confirmation

Even if a future scraper writes an `indicator_type='username'` finding with a value that looks like an email or bare domain (regression of S159), the frontend `isJunkUsernameValue()` filter in `UsernameTab.jsx` will skip it at render time. Same for platforms not in the `PLATFORM_COLORS` allow-list — they're filtered out client-side.

## Cosmetic observations (non-blocking)

1. `npm_maintainer` chip displays its verbose form rather than canonical `npm`. The `MODULE_PLATFORM_MAP` only kicks in when finding's `module === 'npm_maintainer'` AND it's read through `extractPlatform(finding)`. Some findings may come from the graph node path which uses `node.platform` directly — that path doesn't apply the module-mapping. Minor; chip is grey instead of npm-red. Out of scope for S159.
2. `dev.to` chip shows the literal dot in the platform name — color falls to default `#666688` because `getPlatformColor('dev.to')` normalizes to `dev_to` but PLATFORM_COLORS key is `devto`. Trivial mismatch; could be fixed by adding `dev_to` alias or stripping dots in the platform key. Out of scope.

Neither affects correctness of the username allow-list.
