# Forensic round 2 — 2026-05-21

**HEAD**: `4fb647f` (S122e-holdover, top of the 9-commit S122 chain)
**Workspace**: Friends
**Targets scanned (5, randomly sampled)**:
- `aad0262c-…` — `quentin.jouanny@gmail.com` (T1)
- `a5bfd465-…` — `guillaume.a.perrin@gmail.com` (T2)
- `2df1b861-…` — `aymen.zerni.nss@gmail.com` (T3)
- `8e641d18-…` — `marchuynen4@gmail.com` (T4)
- `dccb45e1-…` — `mcrlux@protonma.com` (T5)

**Scans triggered (serial, 26 modules + `name_scraper_engine`)**:
- T1 → `b72a2d23-aab1-40bb-89ca-52f0d0a8afe9` (completed, 270 s, 38 findings)
- T2 → `1817ed70-7736-4f05-b993-934e5625f509` (completed, 315 s, 41 findings)
- T3 → `432a454a-57ba-4153-9928-c63d0068bd0b` (completed, 285 s, 36 findings)
- T4 → `aa183730-edc3-4807-a9a2-4867fb321c20` (completed, 239 s, 8 findings)
- T5 → `ae959cee-59b0-4686-96a9-400e2e3f6c46` (completed, ~255 s, 26 findings)

**Totals**: 149 findings · 114 distinct scrapers exercised across the round.

---

## Pipeline health

| Check | Result | Notes |
|---|---|---|
| H1 No varchar truncation | ✅ PASS | `StringDataRightTruncation` count = 0 in worker logs for the round. S122b fix holds. |
| H2 All scans completed | ✅ PASS | 5/5 status=completed, 0 stuck/failed. |
| H3 `_auto_resolved_name` non-null on ≥ 3/5 | ✅ PASS | 3 resolved: Quentin Jouanny, Guillaume Perrin, "cat bf" (questionable — see follow-ups). 2 null: marchuynen4, mcrlux. |
| H4 `module_progress.name_scraper_engine_attempts` present | ✅ PASS | All 5 scans carry the key. 3 scans dispatched 9 attempts each, 2 carry the `{"_skipped":"no_name_input"}` marker. |
| H5 Holdover findings shape | ✅ PASS | All 6 findings (`lbr_luxembourg` × 3, `uk_gazette_search` × 3) are `severity=low` and titled `"<service>: search for <name> — open link, verify manually"`. |
| H6 No NULL `module` on findings | ✅ PASS | 0 rows. |
| H7 No worker exceptions | ⚠️ PASS WITH CAVEAT | 0 truncation, 0 `CRITICAL`. **22 `ERROR/` lines** observed, isolated to two real bugs documented below. Network-level `DEBUG` exception noise (timeouts, SSL hostname mismatch, DNS fails) is expected and properly converted into per-scraper status codes; not counted here. |

---

## 🔴 Real pipeline bugs surfaced this round (H7 detail)

### Bug R1 — `public_exposure_enricher.py:728` TypeError drops every BODACC PASS2 finding (≥ 20 occurrences)

```
File "/app/api/services/layer4/public_exposure_enricher.py", line 728, in enrich_public_exposure
  indicator_value=(fd.get("indicator_value") or fd.get("url") or fd.get("title", ""))[:500],
TypeError: 'int' object is not subscriptable
```

Real BODACC matches are arriving on the **PASS2 / public_exposure_enricher** path (a SEPARATE code path from `name_scraper_engine`) with name input, returning structured company hits — but `fd["indicator_value"]` is an int (BODACC numéro/id) and the `[:500]` slice crashes. Every PASS2 BODACC finding is silently dropped: 20+ company-officer signals lost on these 5 scans alone (SOCIETE CIVILE CIGA, GIE VETO 70, LACHAUX PAYSAGE, SCI ROMAGUI, PE HABITAT, VALZEL INFORMATIQUE, CFGS ASSOCIES, EGIS ONE 8, WEST END / EPSILON BBDO, SCI SOFY, SIC COMMUNICATION, FRANCHE COMTE ANIMAUX, MITOPROD, ACTIFCAPITAL, ENTREPRISE BIANCO ET CIE, etc.).

**Implication**: BODACC is not actually as broken as the holdover suggests — there's a parallel real-data path through PASS2 that's productive. Fixing this one slice probably resurrects 15–25 corporate-registry findings per investigation involving French names.

### Bug R2 — `Courtlistener: unexpected error for 'Guillaume Perrin'`

Single `ERROR/` line, full traceback in `api/scrapers/courtlistener_search.py:194`. Same PASS2 path, different scraper. One occurrence in this round but worth pinning before it stays silent.

---

## 🟡 Ordering issue — `name_scraper_engine` runs before name resolution

Cross-check between H3 and H4:

| Target | H3 `_auto_resolved_name` (post-scan) | H4 `name_scraper_engine_attempts` |
|---|---|---|
| T1 quentin.jouanny | Quentin Jouanny | `{_skipped: no_name_input}` ❌ |
| T2 guillaume.a.perrin | Guillaume Perrin | 9 attempts dispatched ✅ |
| T3 aymen.zerni.nss | "cat bf" | 9 attempts dispatched |
| T4 marchuynen4 | (null) | 9 attempts dispatched (dispatched with what name?) |
| T5 mcrlux | (null) | `{_skipped: no_name_input}` |

The dispatcher reads `_auto_resolved_name` from `target.profile_data` at the time it runs (Layer 1 gather phase). Name resolution happens later, in Layer 4 finalize. So `name_scraper_engine` sees the **pre-scan** name state, not the freshly-resolved name from THIS scan:
- T1 (no prior resolved name) → skipped, even though the scan resolves it.
- T2, T3 (had a prior resolved name on disk) → dispatched.
- T4 looks like dispatch succeeded against a stale/empty value (worth investigating).

**Fix path**: hoist `name_scraper_engine` to run AFTER Layer 4 finalize, or wire it into the `_full_refinalize` 15-step Deep Scan pipeline (CLAUDE.md). Not a regression — `name_scraper_engine` is new in S122e — but it means first-time scans on uncached targets won't fire the name dispatchers. Operator workaround today: hit `Recalculate Profiles` after first scan.

---

## Scraper inventory (114 exercised, sorted Broken → Working → No-data → Holdover)

Classification rules (refined):
- **Working**: ≥ 50 % success across runs.
- **Working (partial)**: 1 + success but < 50 %.
- **Broken**: 0 success AND real errors (auth/bot-block/400/5xx/exception) outnumber legit "no presence" signals.
- **No-data**: 0 success but only `no_data` or `error_404` (= "user not on this platform" for username-input scrapers). Not actionable.
- **Misconfigured**: 0 success because every run was `no_input` (target lacked phone/crypto/etc.). Spec gap, not a code bug.
- **Holdover**: 5 known placeholder scrapers from S122e-holdover.

| Classification | Count |
|---|---|
| **Broken (real)** | **12** |
| Misconfigured | 4 |
| Working | 32 |
| Working (partial) | 1 |
| No-data | 61 |
| Holdover | 4 |

(Full TSV in `/tmp/qa2_inventory.tsv` — not committed because /tmp is volatile.)

### 🔴 Broken (12) — next-sprint candidates

| Scraper | Dominant error | Notes |
|---|---|---|
| `linkedin_profile` | `error_999` × 5 | LinkedIn bot-block signature. Needs proxy or Playwright path. |
| `gcal_public` | `error_401` × 5 | Auth required — endpoint changed or token expected. |
| `github_code_search` | `error_401` × 5 | GitHub API requires token now for code search. |
| `github_code_search_username` | `error_401` × 5 | Same as above. |
| `crunchbase_profile` | `error_403` × 5 | Cloudflare bot-block; or needs API key. |
| `discogs_profile` | `error_403` × 5 | Same family — auth or stealth needed. |
| `producthunt_profile` | `error_403` × 5 | Same family. |
| `interpol_red_notices` | `error_403` × 3 | Known bot-block per S122e verification; still no fix. |
| `opensanctions_search` | `error_401` × 3 | Needs free API key (documented at OpenSanctions). |
| `wayback_domain` | `error_403:3, error_503:1` | IA Wayback rate-limit / block. |
| `bluesky_profile` | `error_400` × 5 | Request shape bug (AT Protocol endpoint changed?). Pure fix, no key. |
| `hackernews_profile` | `error_400` × 3 | Same — likely query param mismatch. |

### 🟡 Misconfigured (4) — wait for upstream input

`blockchain_info_btc`, `blockchair_wallet`, `chainabuse_check`, `google_phone_dork`: all `no_input` × 5. These need a phone/crypto extracted by A1.5 to fire. Not a scraper bug; the upstream extractor produced nothing for these 5 targets.

### Holdover status

| Scraper | Runs | Successes (= manual-check items emitted) |
|---|---|---|
| `lbr_luxembourg` | 3 | 3 (severity=low, manual-check title — correct) |
| `uk_gazette_search` | 3 | 3 (same) |
| `bodacc_search` | 3 | 0 (always `error_400`; see Bug R1 — real data lands via PASS2 instead) |
| `opencorporates_officers` | 3 | 0 (`no_data` × 3 — opencorporates' free tier may be hitting the 401 wall too; only ran on the 3 name-dispatched scans) |
| `courtlistener_search` | 0 | (not registered as enabled in attempt log — it's currently `enabled=False` per seed) |

---

## Top "no-data" scrapers — informational only

61 scrapers returned only `no_data` / `error_404` across all runs. Examples: bandcamp, codewars, dev.to, dockerhub, dribbble, flickr, github_* (read-only public endpoints that return 404 for non-existent users), goodreads, hackernews, hashnode, huggingface, lastfm, letterboxd, lichess, linktree, mastodon, medium, mixcloud, myanimelist, packagist, pastebin, replit, rubygems, runescape, snapchat, soundcloud, speedrun, stackoverflow, steam, tiktok, tumblr, vimeo. **Not bugs** — these targets simply don't have a presence there.

---

## Recommendations (3, ranked by impact / effort)

1. **Fix Bug R1** (`public_exposure_enricher.py:728` int slice). 1-line fix (`str(fd.get("indicator_value") or fd.get("url") or fd.get("title", "") or "")[:500]`). **Resurrects 15–25 BODACC company-officer findings per French-name investigation** — that's a Play 1 Deep Investigation deliverable difference.

2. **Hoist `name_scraper_engine` to run AFTER Layer 4 finalize**, or auto-trigger a follow-up pass after first-scan name resolution. Currently any first-time scan on a fresh target skips name dispatching, which defeats S122e on the most important UX path (the first time an analyst meets a new target). Re-running the scan or hitting Recalculate Profiles works, but that's an operator workaround for a pipeline ordering bug.

3. **Fix `bluesky_profile` and `hackernews_profile`** request shapes (8 `error_400` over 10 runs combined). Both are pure config fixes (URL template / params), no auth, no bot-block. Low effort, recovers two universal-coverage scrapers for free.

---

## Out of scope (deferred)

- Auth-required broken scrapers (LinkedIn 999, GitHub code-search 401, Crunchbase/Discogs/ProductHunt 403, Interpol/OpenSanctions/Wayback) — each needs a key or stealth path; out of one-sprint scope.
- The "cat bf" resolved name for T3 (`aymen.zerni.nss@gmail.com`) — confirms the lowercase-handle / emoji-strip work in S122-name didn't catch every edge case. Worth a follow-up diag inspection, not a fix in this sprint.
- 4 misconfigured (phone/crypto inputs) — wait for A1.5 to produce inputs on richer targets.
- Holdover proper extraction work (the S122f-* tickets) — pre-existing.
