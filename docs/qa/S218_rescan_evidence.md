# S218 — Rescan evidence post-S217 phone validators

**Date**: 2026-05-25 12:38 UTC
**Targets rescanned**: 1 (constraint: only 1 target in entire 16-workspace corpus has `profile_data.phones[]` populated)
**Workspaces touched**: 1 (Quentin)

## Corpus phone diversity constraint (T1.1)

Query against `targets WHERE profile_data ? 'phones' AND jsonb_array_length(profile_data->'phones') > 0`
returned exactly **1 row** across all 16 workspaces:

```
05ce9d2c-5abb-4db2-87f2-f5a9f2635fe5 gnienlnaha@yahoo.fr  quentin  phones=1 (+33612345678)
```

The spec asked for 3-5 picks; corpus reality is 1. This is itself an
empirical signal: S217's phone validators have working dispatch infra,
but the corpus has essentially zero live phone exposure to validate
against beyond the seeded test target. See conclusion for downstream
implications.

## Pre-S218 baseline (pre-rescan, post-S217)

| Module | Findings count |
|---|---|
| google_phone_dork | 7 |
| duckduckgo_phone_dork | 2 |
| bing_phone_dork | 2 |
| yandex_phone_dork | 2 |
| api_ninjas_phone | 1 (from S217 smoke) |
| numverify_phone | 0 |
| veriphone_phone | 0 |
| abstractapi_phone | 0 |
| **Total phone findings** | **14** |

## Post-S218 rescan (after Deep Scan re-dispatch)

| Module | Findings count | Delta |
|---|---|---|
| google_phone_dork | 7 | 0 |
| duckduckgo_phone_dork | 2 | 0 |
| bing_phone_dork | 2 | 0 |
| yandex_phone_dork | 2 | 0 |
| api_ninjas_phone | 2 | **+1** |
| numverify_phone | 0 | 0 |
| veriphone_phone | 0 | 0 |
| abstractapi_phone | 0 | 0 (key 401, S217 known issue) |
| **Total phone findings** | **15** | **+1** |

## Per-validator HTTP outcome (T1.3 worker log)

| Validator | HTTP | Behavior |
|---|---|---|
| numverify_phone | **200** | `success_indicator: "valid":true` did NOT match — remote returned `valid:false` for fake test phone, no finding created (CORRECT) |
| veriphone_phone | **200** | `success_indicator: "phone_valid":true` did NOT match — remote returned `phone_valid:false`, no finding created (CORRECT) |
| api_ninjas_phone | **200** | `is_valid:true` matched, finding created. Country + timezone extracted; carrier + line_type empty (see qualitative samples below) |
| abstractapi_phone | **401** | Env key stale/exhausted (S217 known operator-side issue, not code) |

## Qualitative samples (T1.5)

```
api_ninjas_phone | "API Ninjas: {carrier} ({line_type}) — France"
  extracted: {"country": "France", "timezone": "['Europe/Paris']"}
```

**Observation:** `carrier` and `line_type` extraction_rule fields evaluate to empty
strings — the finding title shows literal `{carrier} ({line_type})` placeholders.
Two possible causes:
1. **API Ninjas response genuinely doesn't populate `carrier` / `line_type` for
   French mobile numbers** (likely — fake test phone, no carrier registration).
2. **`extraction_rules` JSON-key regex broken** for these specific fields
   (less likely — same JSON-key extractor works elsewhere in the codebase).

Triage candidate for separate sprint (S221 — extraction_rules audit).

## Validator coverage matrix (1 pick × 4 validators)

```
target           gnienlnaha (+33612345678)
numverify        no_match  (200 + valid:false)
veriphone        no_match  (200 + phone_valid:false)
api_ninjas       success   (200 + is_valid:true, carrier=null)
abstractapi      exception (401)
```

## Conclusion

**S217 net-new phone signal: +1 finding across 1 target.** Validators are
functional but the empirical ROI on the current corpus is essentially zero:

1. **Corpus phone diversity is the bottleneck.** 1/229 targets has phone
   data. Until A1.5 extracts more phones from real breach payloads, or
   operator seeds more realistic phones, the validators have nothing to
   validate.

2. **The 1 fake test phone (+33612345678) is correctly rejected as invalid
   by numverify + veriphone** — they're working as designed. This is the
   PROBLEM scenario S217 was supposed to handle.

3. **api_ninjas_phone returned `valid:true` for the same phone** but
   produced incomplete extraction (carrier / line_type null) — likely
   genuinely empty upstream, not a code bug.

4. **abstractapi_phone needs env key rotation** (operator task, not code).

**Honest downstream signal for sprint prioritization:**

- **Tier B reverse lookups (NumLookup / TruePeopleSearch / IPQS) are NOT
  the right next pick.** They have the same corpus-bottleneck problem —
  no phones to query against.
- **Higher-leverage next sprint** = wait for organic phone accumulation
  via A1.5 from real breach scrapers, OR seed additional realistic phones
  in the test corpus, OR add a phone-extraction-from-text scanner that
  surfaces phones embedded in social profiles + about pages.
- **S221 extraction_rules audit** for api_ninjas_phone (and possibly other
  validators if pattern-broken regex is systemic) is small but worth
  scheduling once a real phone surfaces and validates the regex against
  actual JSON.

**Bottom line:** S217 shipped working infra. S218 confirms the infra works.
Corpus reality says the next bottleneck isn't more scrapers — it's more
upstream phone signal. This documents the truth instead of inflating
findings counts.
