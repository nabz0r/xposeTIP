# Forensic round 3 — 2026-05-22

**HEAD**: `9226a37` (S127 — name_scraper_engine A3.5 ordering fix, top of the S122 → S127 chain)
**Workspace**: Friends
**Targets scanned (3, randomly sampled, intentionally smaller sample than round 2)**:
- `92326c6e-…` — `Ksontinisarah@gmail.com` (T1, no prior `_auto_resolved_name`)
- `6214e28c-…` — `abed.belaid@gmail.com` (T2, pre-existing `_auto_resolved_name="Abed Belaid"`)
- `bbd28a36-…` — `booking.lxb@gmail.com` (T3, no prior `_auto_resolved_name`, data-starved)

**Scans (default workspace modules — 26 scanners, A3.5 dispatches name_scraper_engine sequentially per S127)**:
- T1 → `a9d41a10-e168-4fab-853e-697b1287227d` (completed, 216 s, 29 findings)
- T2 → `18a9391e-adc4-442c-8a30-325341eefe2b` (completed, 295 s, 36 findings)
- T3 → `2cfbbf03-1401-4377-bf1a-1530b4bff5c5` (completed, 263 s, 30 findings)

**Totals**: 95 findings · 110 distinct scrapers exercised.

---

## Pipeline health

| Check | Result | Notes |
|---|---|---|
| H1 No varchar truncation | ✅ PASS | `StringDataRightTruncation` count = 0. S122b holds. |
| H2 All scans completed | ✅ PASS | 3/3 status=completed, 0 stuck/failed. |
| H3 `_auto_resolved_name` populated | ⚠️ 1/3 | T2 ✅ "Abed Belaid", T1 + T3 null. Data-availability issue (see below), not a regression. |
| H4 `name_scraper_engine_attempts` present, A3.5 ordering correct | ✅ PASS | All 3 scans carry the key. T1 + T2 each dispatched 5 scrapers, T3 correctly `{_skipped: no_name_input}`. |
| H5 ProvenanceCard fields surfaced via API | ✅ PASS | `tier`, `source_reliability`, `cross_verified_count` all present on returned items. |
| H6 No worker `ERROR/`/`CRITICAL/` lines | ✅ PASS | 0 lines. Network-level DEBUG noise excluded (expected — properly converted to per-scraper status codes via S122-obs). |
| H7 PASS2 BODACC still landing post-S123 | ✅ PASS | 2 BODACC findings on T2 (`abed.belaid`) created via the public_exposure_enricher path. |

---

## 🟢 S127 ordering fix — DEFINITIVELY VERIFIED

Worker log timestamps for all 3 scans show the same canonical sequence:

```
PIPELINE[…]: early_profile done (bootstrap for Pass 2)
PIPELINE[…]: name_scrapers done       ← NEW A3.5 STEP (S127)
PIPELINE[…]: pass2 done
PIPELINE[…]: graph_builder done
PIPELINE[…]: pagerank done
PIPELINE[…]: profile_aggregator done (final)
```

**T1 (Ksontinisarah)** is the regression-buster: target had `_auto_resolved_name = null` BEFORE this scan. The A3.5 step still dispatched 5 name-input scrapers (`gdelt_news`, `gnews_news`, `google_news_rss`, `interpol_red_notices`, `opensanctions_search`) — proving early_profile produced a usable tentative name that A3.5 consumed. Pre-S127, this same scan would have returned `{_skipped: no_name_input}` because the parallel `name_scraper_engine` dispatched at scan-start saw no resolved name.

**T3 (booking.lxb)** correctly skipped with `{_skipped: no_name_input}` — confirms the skip path still works for genuinely data-starved targets (no early_profile name signal). Not a regression — A3.5 can't dispatch if there's truly nothing to dispatch with.

| Target | Pre-scan resolved name | Post-A3.5 attempts | Post-final resolved name |
|---|---|---|---|
| T1 Ksontinisarah | null | **5 dispatched** | null (final aggregation reverted) |
| T2 abed.belaid | "Abed Belaid" | 5 dispatched | "Abed Belaid" |
| T3 booking.lxb | null | `_skipped: no_name_input` | null |

T1's post-final null is a separate observation: the early_profile resolved name (likely a low-confidence first-pass guess) was used by A3.5 but the final aggregation pass at orchestrator line 412 — which has access to `graph_context` — re-aggregated and produced null. That's the **final aggregate stage being stricter than early_profile**, not a bug in S127. Possibly a future Bug 5: "early_profile and final_profile disagree". Out of S127 scope.

---

## 🟢 S122 chain regression sweep

All shipped fixes still hold:

| Sprint | Check | Status |
|---|---|---|
| S122a | sync_avatars runs clean | ✅ implicit (no S122a-touched code regressed) |
| S122b | scraper_engine no varchar overflow | ✅ H1 = 0 truncation |
| S122c | name_resolution_debug populated | ✅ T2 carries it (verified separately in S122c shipping) |
| S122-clean | gravatar dupes disabled, pastebin clean | ✅ no placeholder pollution in this round |
| S122-obs | `scraper_engine_attempts` per scan | ✅ all 3 scans carry detailed status maps |
| S122-name | resolver picks correct name (no snowmen) | ✅ T2 produced "Abed Belaid" cleanly |
| S122e | `name_scraper_engine` dispatches | ✅ via S127's A3.5 step (no longer parallel) |
| S123 | PASS2 BODACC findings land | ✅ 2 BODACC findings on T2, no `[int]:500` crash |
| S124 | ProvenanceCard backend fields | ✅ tier/reliability/cv all present in API |
| S125 | confidence rebuild idempotent | ✅ baseline values match canonical formula |
| S126 | `match_confidence` data row | ✅ surfaces on PASS2 findings (visual QA not re-run) |
| S127 | A3.5 ordering | ✅ logs prove `early_profile → name_scrapers → pass2` |

---

## Scraper inventory (110 exercised)

| Classification | Count | Δ vs round 2 |
|---|---|---|
| **Broken (real)** | 12 | 0 |
| Misconfigured | 4 | 0 |
| Working | 31 | -1 |
| Working (partial) | 1 | 0 |
| No-data | 62 | +1 |
| ~~Holdover~~ | 0 | -4 (S123 disabled the 4 URL-template placeholders) |
| **Total** | **110** | -4 |

Working delta is normal target-population variance (different 3 targets have different presence profiles); the only structural change is the 4 holdovers being correctly absent.

### 🔴 Broken (same 12 as round 2 — no regression, no new issues)

| Scraper | Dominant error | Status since round 2 |
|---|---|---|
| `linkedin_profile` | `error_999` × 3 | unchanged (bot-block) |
| `gcal_public` | `error_401` × 3 | unchanged (auth) |
| `github_code_search` / `_username` | `error_401` × 3 | unchanged (needs token) |
| `crunchbase_profile` | `error_403` × 3 | unchanged (cloudflare) |
| `discogs_profile` | `error_403` × 3 | unchanged (auth) |
| `producthunt_profile` | `error_403` × 3 | unchanged |
| `wayback_domain` | `error_403` × 3 | unchanged (IA throttle) |
| `bluesky_profile` | `error_400` × 3 | unchanged (request shape) |
| `hackernews_profile` | `error_400` × 2 | unchanged |
| `interpol_red_notices` | `error_403` × 2 | unchanged (bot-block) |
| `opensanctions_search` | `error_401` × 2 | unchanged (needs API key) |

### 🟡 Misconfigured (4) — no input

`blockchain_info_btc`, `blockchair_wallet`, `chainabuse_check`, `google_phone_dork`: targets had no phone/crypto extracted. Not actionable.

---

## Recommendations (delta vs round 2)

Round 2's top-3 were: (1) Bug R1 (PASS2 int crash), (2) name_scraper_engine ordering, (3) bluesky/hackernews request shape.

After this round:
- R1 ✅ shipped in S123, validated this round (2 BODACC findings landed cleanly).
- Ordering ✅ shipped in S127, validated this round (A3.5 step fires on every scan).
- **bluesky_profile + hackernews_profile** (8 `error_400` over 6 runs combined) — still pure config fixes, still low-effort, still high-leverage. **Highest-priority remaining quick-win.**

New recommendation surfaced this round:
- **early_profile vs final_profile divergence** on T1 — early_profile resolved a name (used by A3.5) but final_profile aggregated to null. Worth checking whether `graph_context`-aware aggregation is rejecting candidates that early_profile accepted. Diagnostic-only sprint (no fix yet) — extend `name_resolution_debug` to capture BOTH early and final aggregate decisions for diff analysis.

---

## Reference IDs

- **T1** = `92326c6e-…` (Ksontinisarah@gmail.com) — S127 regression-buster
- **T2** = `6214e28c-…` (abed.belaid@gmail.com) — control (pre-resolved name)
- **T3** = `bbd28a36-…` (booking.lxb@gmail.com) — data-starved (correctly skipped)
- **S1** = `a9d41a10-e168-4fab-853e-697b1287227d`
- **S2** = `18a9391e-adc4-442c-8a30-325341eefe2b`
- **S3** = `2cfbbf03-1401-4377-bf1a-1530b4bff5c5`
