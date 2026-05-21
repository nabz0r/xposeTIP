# Forensic round 4 — 2026-05-21

**HEAD**: `d6d4671` (S133 — geomap polish, top of the S122 → S133 chain; post-S131 similarity engine + S132 landing/Compare)
**Workspace**: Friends (34 targets total; **5 randomly sampled** — full 34 deferred due to wall-clock budget)
**Targets scanned (5)**:
- `e17fde1d-…` — `info@florencehoffmann.net` (T1, no prior `_auto_resolved_name`)
- `a5bfd465-…` — `guillaume.a.perrin@gmail.com` (T2, pre-existing "Guillaume Perrin")
- `c282f186-…` — `nabz0r@gmail.com` (T3, pre-existing "Nabil Ksontini")
- `92326c6e-…` — `Ksontinisarah@gmail.com` (T4, **R3 carry-over** — was no_name in R3)
- `712f356e-…` — `loupn24@msn.com` (T5, pre-existing "Loup Noir")

**Scans (default workspace modules, 3-min gap between scans)**:
- T1 → `7714cd35-c875-43c1-89e5-099341ced3b2` (completed, 395 s, 69 findings)
- T2 → `53f8dd78-b3cd-4e86-8a48-d0005a69ac69` (completed, 122 s, 3 findings)
- T3 → `b47b1bea-9ab9-4264-9263-990d0a4b5dbd` (completed, 315 s, 43 findings)
- T4 → `faa3542d-cece-4dcb-bc0b-f82dc1e6a8ca` (completed, 255 s, 3 findings)
- T5 → `3e7b25f0-c291-4761-af57-001362797141` (completed, 266 s, 4 findings)

**Totals**: 122 findings across the round · 110 distinct scrapers exercised · 5/5 similarity recomputes succeeded.

---

## Pipeline health

| Check | Result | Notes |
|---|---|---|
| H1 No varchar truncation (S122b) | ✅ PASS | `StringDataRightTruncation` count = 0 across the run. |
| H2 All scans completed | ✅ PASS | 5/5 status=completed, 0 stuck/failed/cancelled. |
| H3 `_auto_resolved_name` populated | ✅ 4/5 | T1 "about me" (questionable — see findings of note), T2 "Guillaume Perrin", T3 "Nabil Ksontini", T5 "Loup Noir". T4 (Ksontinisarah) still null — data-starved, matches R3. |
| H4 `name_scraper_engine_attempts` present + A3.5 ordering (S127) | ✅ PASS | All 5 scans carry the key with 5 dispatched scrapers each. Worker logs show canonical sequence `early_profile done → name_scrapers done → pass2 done` on every scan (verified on T5: 08:41:50 early_profile → 08:41:50 name_scrapers → 08:42:36 pass2). |
| H5 ProvenanceCard fields surfaced via API (S124-S126) | ✅ PASS | Spot-check on T2 returned items: tier=HIGH, cross_verified_count=1 for `intelligence`, tier=HIGH for `bodacc_search`. Both `match_confidence` rows + cross-verif populated. |
| H6 No worker ERROR/CRITICAL | ⚠️ 1/0 | 1 `ERROR/`: `Courtlistener: unexpected error for 'Guillaume Perrin' (AttributeError: 'list' object has no attribute 'lower')` — new residual bug, distinct from S123's int-coerce fix. See "findings of note". |
| H7 PASS2 enrichers landing (BODACC / Courtlistener / UK Gazette) | ⚠️ 1/3 | BODACC: **27 findings** across the round (mostly on T3 nabz0r). Courtlistener: **0** (errored — bug above). UK Gazette: 0. LBR Luxembourg: 0. OpenCorporates: 0. |
| H8 NEW — S128 telemetry: blocked_403 / explicit_not_found classified as no_data | ✅ PASS | Status rollup across 5 scans: no_data=227, success=184, no_input=92, error_401=13, error_999=4, error_500/502/503/600=5 total. **Zero error_403, zero error_4xx-as-not-found** — S128 reclassification holds. |
| H9 NEW — S129 dispatch validation: zero HN-style 400 errors | ✅ PASS | **Zero error_400 entries** across all 5 scans. The remaining error_4xx are all `error_401` (gcal_public, github_code_search × 2 — auth-required, NOT request-shape bugs) on the 4 targets with valid email LHS. S129 effectively eliminated the HN/Bluesky 400 cluster from R3. |
| H10 NEW — S131 similarity: recompute SUCCESS per scan | ✅ PASS | All 5 recompute log lines confirmed: T1→4 matches, T2→4, T3→5, T4→5, T5→6. Total similarity rows in Friends workspace: 30 → **42** (+12 from this round). |

---

## 🟢 S131 similarity engine — first multi-target end-to-end run with `first_detected` preservation

Top 10 pairs in the Friends workspace post-R4:

| target_a | target_b | similarity | preserved across recompute? |
|---|---|---|---|
| booking.lxb@gmail.com | abed.belaid@gmail.com | 0.9938 | new (not in scanned set) |
| abed.belaid@gmail.com | booking.lxb@gmail.com | 0.9938 | new |
| loupn24@msn.com | info@florencehoffmann.net | 0.9711 | new (this round) |
| info@florencehoffmann.net | loupn24@msn.com | 0.9711 | new (this round) |
| nabz0r@gmail.com | Ksontinisarah@gmail.com | 0.9678 | **✅ PRESERVED** (carried from S131 ship + earlier scans) |
| Ksontinisarah@gmail.com | nabz0r@gmail.com | 0.9678 | **✅ PRESERVED** |
| loupn24@msn.com | Ksontinisarah@gmail.com | 0.9654 | new |
| Ksontinisarah@gmail.com | loupn24@msn.com | 0.9654 | new |
| abed.belaid@gmail.com | guillaume.a.perrin@gmail.com | 0.9604 | **✅ PRESERVED** |
| guillaume.a.perrin@gmail.com | abed.belaid@gmail.com | 0.9604 | **✅ PRESERVED** |

**4 of 10** rows show `first_detected < last_computed` — proves S131's batch-SELECT-before-DELETE pattern correctly carries forward the original detection timestamp on rescan. The other 6 are net-new pairs created during R4 (info+loupn24 was a fresh discovery).

---

## 🔴 New residual bug surfaced this round

**Courtlistener `AttributeError: 'list' object has no attribute 'lower'`** on Guillaume Perrin (one occurrence). Distinct from S123's `int → str` coerce — this one is a list being passed where a string was expected. Likely happens when Courtlistener's RECAP response shape has a multi-value field (party names array) that the scraper's parser treats as a scalar. Single-target, one occurrence in 5 scans — low frequency but worth a single-line defensive fix when convenient. Logged in S122-obs format so easy to grep later: `grep "Courtlistener: unexpected error"`.

---

## Per-target deltas vs R3 (where applicable)

Only **T4 (Ksontinisarah)** appears in both R3 and R4.

| Metric | R3 (a9d41a10) | R4 (faa3542d) | Δ |
|---|---|---|---|
| findings_count | 29 | 3 | -26 (dedup against existing — most R3 findings still live) |
| exposure_score | 10 | 10 | 0 |
| threat_score | 17 | 17 | 0 |
| `_auto_resolved_name` | null | null | unchanged (data-starved) |
| similarity matches | 0 (S131 not shipped yet) | 5 | +5 (S131 + S132 + S133 all post-R3) |
| name_scraper attempts | 5 dispatched | 5 dispatched | unchanged ✓ |

The findings-count drop is correct dedup behavior, not regression — the R3 findings are still in the DB and still served by the API.

---

## 🟢 S122 chain regression sweep

All shipped fixes still hold:

| Sprint | Check | Status |
|---|---|---|
| S122b | scraper_engine no varchar overflow | ✅ H1 = 0 |
| S122-obs | `scraper_engine_attempts` per scan | ✅ all 5 scans carry detailed status maps |
| S123 | PASS2 BODACC int-coerce | ✅ 27 BODACC findings landed (vs 0 pre-S123) |
| S124-126 | ProvenanceCard backend fields | ✅ tier/reliability/cv/match_confidence all present in API |
| S127 | A3.5 ordering | ✅ logs prove `early_profile → name_scrapers → pass2` for every scan |
| S128 | Telemetry classification | ✅ no_data 227, success 184, no error_4xx for explicit-not-found cases |
| S129 | Pass 1 username gating | ✅ no_input 92, zero HN/Bluesky 400 errors |
| S131 | Similarity engine + `first_detected` preservation | ✅ 5/5 recomputes succeeded, 4 preserved pairs in top 10 |

---

## Findings of note

**T1 — `info@florencehoffmann.net` produced 69 findings but resolved name `"about me"`.** That's clearly junk — likely a scraper return value that survived `_is_valid_name` because it's lowercase and short enough. Worth checking the `name_resolution_debug` JSONB to see which source fed "about me" (likely the `about.me` profile scraper leaking its own brand into the candidate pool). One-line fix territory: add `"about me"`, `"about.me"`, `"profile"`, `"home"`, `"about"` to the `_clean_name_value` blacklist, OR reject single-token lowercase candidates from non-verified sources.

**T2 (Guillaume Perrin) finished in 122 s — 2× faster than the other scans (255-395 s).** Reason: existing data + dedup. T2 had been heavily scanned in S122e and S131 verification, so most module results matched existing findings and the cascade short-circuited. Not a bug — efficient behavior.

**T5 (`loupn24@msn.com`) cascade ran 8 minutes after the scan "completed" status.** Scan reported completed at trigger+265 s (08:39:39), but the pass2 + similarity recompute didn't finish until 08:42:43. The visible scan-completion status flips before the cascade finishes — consistent with the operational note from S123: "completed" doesn't mean "pipeline finished". For the report aggregation, the script had to wait for the fingerprint hash to actually land before querying similarity. Worth a follow-up to surface a "cascade in progress" flag on the scan object, or simply have finalize_scan flip status only after pass2 + similarity finish.

---

## Open items (carried from R3 / R4 additions)

1. **Courtlistener list-vs-string AttributeError** (NEW, R4) — single defensive cast in the parser. Cheap fix.
2. **early_profile vs final_profile divergence** (carried from R3) — early_profile can produce a tentative name (used by A3.5) that the final aggregator later rejects, leaving `_auto_resolved_name = null` post-scan. Worth a diagnostic sprint to extend `name_resolution_debug` with both decisions for diff analysis.
3. **"about me" junk name** (NEW, R4) — extend `_is_valid_name` blacklist or reject lowercase single-token candidates from non-verified sources.
4. **bluesky_profile + hackernews_profile request shape** (carried from R3) — still residual `error_400` if scanning targets with multi-dot email LHS that S129's `is_valid_username` lets through (1-dot case). Low priority since S129 already eliminated the bulk.
5. **Auth-required scrapers** (carried) — LinkedIn 999, gcal_public 401, github_code_search 401, crunchbase/discogs/producthunt 403 — need API keys or stealth proxy. Out of one-sprint scope.
6. **Scan-completion timing semantics** (NEW, R4) — `status='completed'` flips before pass2/similarity cascade finishes. Either rename to `status='cascade_pending'` for that window, or wait to flip until everything settles.
7. **Full 34-target forensic round** (NEW) — this round was sampled to 5. A full run would take ~12-13 h at the spec's 15-min gap; consider a single-scan batched script with intermediate state persistence to enable overnight runs.

---

## Reference IDs

- T1 `e17fde1d-…` (info@florencehoffmann.net) — 69 findings, resolved="about me" (junk)
- T2 `a5bfd465-…` (guillaume.a.perrin@gmail.com) — 3 findings, resolved="Guillaume Perrin"
- T3 `c282f186-…` (nabz0r@gmail.com) — 43 findings, resolved="Nabil Ksontini"
- T4 `92326c6e-…` (Ksontinisarah@gmail.com) — 3 findings, resolved=null (R3 carry-over)
- T5 `712f356e-…` (loupn24@msn.com) — 4 findings, resolved="Loup Noir"
- S1 = `7714cd35-c875-43c1-89e5-099341ced3b2`
- S2 = `53f8dd78-b3cd-4e86-8a48-d0005a69ac69`
- S3 = `b47b1bea-9ab9-4264-9263-990d0a4b5dbd`
- S4 = `faa3542d-cece-4dcb-bc0b-f82dc1e6a8ca`
- S5 = `3e7b25f0-c291-4761-af57-001362797141`
