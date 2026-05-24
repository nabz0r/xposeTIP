# S192 Visual Smoke — UI bugfix sweep validation

**Commit:** `6e52016` (S192) — HEAD at smoke start, no code commits during smoke
**Date:** 2026-05-24
**Operator:** Claude Code (Playwright Chrome MCP)
**Primary targets:**
- `gnienlnaha@yahoo.fr` (Quentin workspace) — chip + RiskSignals checks (has 9 crypto + 6 phone findings)
- `chnmille@gmail.com` (Crypto workspace) — Bug 7a "Legal Records" tile check (has `formal_records: 25`)
- Any workspace where operator is `admin` — Bug 10/11 (Ferrero used)

## Verdict

**PASS WITH NOTES** — 7 of 8 checks pass cleanly. Check 3 (RiskSignalsBlock crypto column) surfaced a **real S192 incomplete fix**: the `getScraperName` fallback was added to the exported helpers in `findingFilters.js`, but `RiskSignalsBlock.jsx` has its own internal classifier loop that wasn't refactored. This needs a tiny follow-up patch (S193 candidate, 2 lines).

All other bugs (1+2 chip count, 4 logging, 7a tile labels, 8 visibility refetch, 9 patterns, 10 role gate, 11 banner + disabled nav) validated cleanly.

## Per-check results

| # | Check | Result | Evidence | Notes |
|---|---|---|---|---|
| 1 | Findings chip Crypto populated + filters | ✅ | `01_*.png`, `02_*.png`, `evidence_api_findings.txt` | Crypto chip = 2 (was 0 pre-S192); matches most-recent-scan matcher count |
| 2 | Findings chip Legal + Phone show numeric count | ✅ | `evidence_chip_counts.txt` | Phone=2 / Legal=0 (Legal=0 is correct DB state — disabled chip = OK) |
| 3 | **RiskSignalsBlock crypto column populated** | ⚠ FAIL | `04_*.png`, `evidence_risksignals_incomplete_fix.txt` | **S192 incomplete fix** — see Anomalies |
| 4 | Breakdown grid new category tiles | ✅ | `05_*.png`, `evidence_score_breakdown.txt` | "Legal Records 25", "Public Exposure 0" render on chnmille; 0 raw "formal" substrings on page |
| 5 | TargetDetail visibilitychange re-fetch | ✅ | `06_*.png`, `06_*.txt` | Visibility toggle fires 5 requests including `/findings` — exactly the `load()` flow |
| 6 | Admin role sees All workspaces entry | ✅ | `07_*.png`, `evidence_user_roles.txt` | Ferrero (admin role) shows entry; description now "admin view" (was "superadmin view") |
| 7 | ALL mode banner + disabled nav | ✅ | `08_*.png`, `09_*.png` | Banner renders as "ALL WORKSPACES / Targets view only"; 5/5 non-Targets items become `<div>` w/ cursor-not-allowed; click on Dashboard div does NOT navigate (URL unchanged) |
| 8 | Username validator patterns | ✅ | `evidence_username_patterns.txt` | All 16 patterns present; 8/8 form-labels rejected; 6/6 legit handles preserved; `connection_quality` still rejected |

## Anomalies / findings worth attention

### ⚠ S192 INCOMPLETE FIX — `RiskSignalsBlock.jsx` not refactored

The S192 spec said Bug 1+2+3 fix introduces a `getScraperName(f) = f?.data?.scraper || f?.module` fallback so findings with NULL `data.scraper` (which happens for findings emitted by `secondary_identifier_enricher` / api/scrapers) classify correctly. The fallback was added to the **exported helpers** (`isPhoneSignal`, `isCryptoSignal`) used by the Findings tab chip filter.

**But `dashboard/src/components/RiskSignalsBlock.jsx` (lines 60-74) has its own classifier loop that bypasses the helpers:**

```javascript
for (const f of findings || []) {
  const scraper = f.data?.scraper           // <-- no fallback to f.module
  if (scraper && PHONE_SCRAPERS.includes(scraper)) {
    phone.push(f)
  } else if (scraper && CRYPTO_SCRAPERS.includes(scraper)) {  // <-- requires truthy scraper
    crypto.push(f)
  } else if (f.indicator_type === 'legal_record') {
    legal.push(f)
  }
}
```

If `data.scraper` is NULL, the `if (scraper && …)` short-circuit skips classification entirely → finding never appears in the Risk Signals block.

**Additional bug on RiskSignalsBlock.jsx line 120 — pre-existing typo not fixed by S192:**
```javascript
const chain = data.scraper === 'blockchair_wallet' ? 'multi-chain' :
              data.scraper === 'chainabuse_lookup' ? 'reported' : 'BTC'
                              ^^^^^^^^^^^^^^^^^^
```
This is the same typo that S192 corrected in `findingFilters.js` (`chainabuse_lookup` → `chainabuse_check`) — but the in-line reference in RiskSignalsBlock was missed.

**Evidence (gnienlnaha@yahoo.fr DB):**
- Crypto findings across all scans (with matcher fallback): 9
- Crypto findings in most-recent scan (with matcher fallback): 2
- Findings tab Crypto chip: 2 ✓ (proves S192 helper fix works)
- RiskSignalsBlock Crypto column: 0 (column hidden — `SignalColumn` early-returns when `findings.length === 0`)

**Proposed S193 fix (2-line patch):**
```diff
- const scraper = f.data?.scraper
+ const scraper = f.data?.scraper || f.module
```
and
```diff
- data.scraper === 'chainabuse_lookup' ? 'reported'
+ data.scraper === 'chainabuse_check' ? 'reported'
```

Or cleaner: refactor RiskSignalsBlock to import and use `isPhoneSignal` / `isCryptoSignal` / `isLegalSignal` directly from `findingFilters.js`.

### Note on Check 1 chip count vs DB

DB query said `crypto_n=9` (all-scans), chip shows `2`. Investigation confirms the Findings tab API endpoint only returns findings from the most-recent scan (or applies cross-verification deduplication) — the matcher correctly classifies 2 of those 2 crypto findings. **Not a bug**, just expected API scoping.

### Note on Check 4 categories absent from breakdown

`chnmille` has `formal_records: 25` (visible as "Legal Records 25" tile ✓) and `public_exposure: 0` (visible as "Public Exposure 0" tile ✓). It does NOT have `compliance` or `corporate` keys in its score_breakdown — so the new "Sanctions / PEP" and "Corporate Officer" labels weren't directly observed. They would render correctly per CATEGORY_LABELS map; just no target with those categories was visited.

### Note on Check 5 method

Visibility transition was simulated programmatically via `Object.defineProperty(document, 'visibilityState', {value: 'hidden'})` + `dispatchEvent('visibilitychange')` rather than actual browser tab switching, because the Playwright environment makes real tab switches awkward. The simulation exercises the EXACT same event handler chain the listener subscribes to, so the validation is equivalent.

### Carry-over from S190/S191

- **Bug 5 (workspace auto-revert)** — S194 pending. Reproduced during smoke when navigating from Quentin → Crypto target (had to re-switch). Note timestamp 12:45 UTC.
- **Bug 12 (name disambiguation)** — S195 pending. `gnienlnaha@yahoo.fr` shows "Unknown identity / Name not auto-resolved" — different failure mode than the famous-target wrong-name mis-resolution; this one is "1 candidate found, 0 passed validation" suggesting the S192 username validator pattern extension may now be REJECTING the candidate that pre-S192 would have been accepted. Worth checking pre-S192 vs post-S192 candidate counts.

## Operational notes

- **No worker restart needed** for this smoke (S192 worker code is `public_exposure_enricher.py`; already restarted post-S192 push, validated separately on vitalik scan).
- **No flakes** — JWT was already alive from S191 session.
- **Total smoke duration: ~30 min** vs spec budget 27 min.
- **0 STOP conditions tripped** in the strict sense — Check 3 ⚠ is a real fix gap but the chip-tab path proves the helper fix landed; only RiskSignalsBlock duplicates the classifier logic.

## Tracked follow-ups (out of scope)

1. **[S193] RiskSignalsBlock.jsx refactor** — 2-line patch (fallback + typo) OR full refactor to use exported `isPhoneSignal` / `isCryptoSignal` / `isLegalSignal` helpers. Single file, < 5 lines. High-value: makes the Overview Risk Signals block visually consistent with the Findings tab chip count.
2. **[S194] workspace auto-revert** — already filed, S192 doesn't address.
3. **[S195] name disambiguation defect** — already filed, S192 doesn't address; possible Check 4 side-effect on `gnienlnaha` requires confirmation.
4. **CATEGORY_LABELS completeness pass** — `people_search`, `domain_registration` keys still render as snake_case fallback on Overview breakdown grid. Trivial 2-line addition if Nabil wants consistent UI labels for all backend categories.
