# Smoke S157 — TargetDetail UX refonte (13 → 5 tabs)

**Commit:** 3e57517 (S157)
**Date:** 2026-05-22
**Operator:** Claude Code (Playwright via Chrome MCP)
**Primary target:** Nexus 2026 / marie-jo.gutenkauf@paperjam.lu (`2602f8b8-75a4-48e2-87e2-32e26be86992`)
**Secondary target (Checks 9-10):** ING Luxembourg / laura.morgana@ing.lu (`a6a982ce-144e-4bf7-9eaa-4a2c5c82fb77`)
**Viewport:** 1440×900 (Checks 1-10, 12), 700×900 (Check 11)

## Verdict

**PASS WITH NOTES**

All 12 S157-specific checks green. One pre-existing render bug in `ScansTab.jsx:88` (unrelated to S157, last touched in Sprint 45) surfaced during Check 8 — documented under "Findings worth your attention".

## Per-check results

| # | Check | Result | Evidence | Notes |
|---|---|---|---|---|
| 1 | 5 top tabs visible, no forbidden | ✅ PASS | `01_overview_5tabs.png` | Tabs: `Overview`, `Findings(88)`, `Graph`, `Sources`, `Scans(3)`. 0 forbidden top tabs. `overflow-x-auto` present |
| 2 | Counts on Findings/Scans top tabs | ✅ PASS | `01_overview_5tabs.png` | Findings(88) + Scans(3) match `GET /findings?total=88` + `GET /scans?total=3` exactly |
| 3 | 7 Findings sub-pills, All highlighted, Discovered no count | ✅ PASS | `02_findings_default.png` | Pills: All(88) Public exposure(10) Breaches(3) Usernames(8) Photos(2) Locations(2) Discovered. All highlighted via `bg-[#00ff88]/20`. Discovered correctly countless |
| 4 | Each sub-pill renders correct child | ✅ PASS | `03..08`, `09_findings_all_back.png` | Sequential clicks: exposure→PublicExposureTab (media/article text), breaches→BreachesTab (breach/hibp text), usernames→UsernameTab, photos→PhotosTab (images present), locations→LocationMap (SVG world map), discovered→DiscoveredTab ("Web Discovery" text). Back to All works |
| 5 | Sub-pill state persists across top-tab switch | ✅ PASS | `10_findings_breaches_persisted.png` | Set Findings→Breaches, click Graph, click Findings → Breaches sub-pill STILL active |
| 6 | Graph hub: 2 sub-pills, Graph default, D3 SVG | ✅ PASS | `11_graph_default.png`, `12_graph_timeline.png` | Sub-pills: Graph(active), Timeline. 72 SVG circles confirm D3 force graph rendered. Timeline sub renders timeline content |
| 7 | Sources hub: 2 sub-pills, Connected accounts works | ✅ PASS | `13_sources_default.png`, `14_sources_accounts.png` | Sub-pills: Sources(active), Connected accounts. Both render their respective components |
| 8 | Scans top tab unchanged, no sub-pills | ⚠️ PASS WITH NOTE | `15_scans.png` | No sub-pills present (S157 behavior correct). However, **pre-existing render error surfaced** — see "Findings #1" below. S157 did NOT modify `ScansTab.jsx` (last touched Sprint 45, `b15ab1a`). |
| 9 | Compat shim — Overview deep-link to Breaches | ✅ PASS | `16_overview_deeplink_breaches.png` | "View details" button on Overview (which calls `setActiveTab('breaches')` per pre-S157 API) correctly routed via shim to `Findings → Breaches`. Confirms `setActiveTabCompat` works |
| 10 | RiskSignalsBlock "View all" → Findings All + preset | ✅ PASS | `17_risksignals_viewall.png` | T2 has no risk signals → switched to T1 (laura.morgana@ing.lu, has 3 legal records). Clicked "View all 3" → landed on `Findings(97) → All97` with phone/crypto/legal preset chips visible. S120 behavior preserved through S157 |
| 11 | Mobile 700×900 — overflow + flex-wrap | ✅ PASS | `18_mobile_700.png` | window=700 / body scrollWidth=700 (no horizontal page scroll). 5 top tabs fit in 646px (overflow-x-auto safety class present). Sub-pills row has `flex-wrap: true` |
| 12 | Console + network hygiene | ⚠️ PASS WITH NOTE | `19_console.txt`, `20_network.txt` | All console errors traced to: (a) JWT session expiry mid-walk (401 burst, pre-existing), (b) ScansTab render bug (Finding #1, pre-existing), (c) gstatic favicon 404s (pre-existing, scrapers data). **Zero errors caused by S157 per `git diff 1f7ade4..3e57517` cross-reference.** Network: getAccounts() correctly fired on Sources hub entry (validates CC catch from S157 commit, line 200 useEffect re-wiring) |

## Console / network hygiene detail

**Total console messages captured:** 128 lines across the session, mostly DEBUG. Errors:
- ~10 × HTTP 401 on `/api/v1/{scans,findings,targets,auth/me,workspaces}` — clustered around the 13-min mark when JWT expired. Pre-existing access-token lifetime, unrelated to S157.
- ~5 × React render errors `Objects are not valid as a React child` from `ScansTab.jsx:47` — see Finding #1.
- ~2 × `Failed to load resource: 404` for `t3.gstatic.com/faviconV2` — pre-existing, scraper-data favicon misses.

**Network log:** 30 API requests captured, all 2xx except the 401 burst noted above. Notably:
- `getAccounts()` fires when Sources top tab activated (S157 line 200 useEffect rewrite validated — accounts load WITHOUT requiring sub-pill click on Connected accounts).
- `getScraperProgress()` polled during scan-in-flight detection (no impact this session, no scan running).

## Findings worth your attention

### 1. ⚠️ Pre-existing render bug in ScansTab.jsx:88 — NOT S157

**Symptom:** When viewing the Scans top tab on a target with at least one completed scan whose `module_progress` field has a nested-object value, React throws:

```
Objects are not valid as a React child
(found: object with keys {agify, genderize, gcal_public, leak_lookup, ...})
```

**Location:** `dashboard/src/pages/tabs/ScansTab.jsx:88`:
```jsx
{Object.entries(scan.module_progress || {}).map(([mod, status]) => (
  <span key={mod}>
    {mod}: <span>{status}</span>   // ← {status} is sometimes an object, not a string
  </span>
))}
```

**Root cause:** `scan.module_progress.scraper_engine` can store either:
- A string status (`'queued'`, `'running'`, `'completed'`, `'failed'`, `'skipped'`) — the documented contract, OR
- A nested **`{scraper_name: status}` dict** — sub-progress per individual scraper (e.g., `{agify: 'completed', genderize: 'completed', ...}`)

ScansTab assumes the string form everywhere. When the dict form appears, React refuses to render an object as a child.

**Provenance:** `ScansTab.jsx` last touched in Sprint 45 (`b15ab1a Sprint 45: Split TargetDetail + System into tab components`). NOT in the S157 diff (`git show --stat 3e57517` confirms zero ScansTab.jsx changes). This bug existed before S157 and would have manifested whenever this data shape appeared on a Scans tab.

**Why it didn't show in earlier smokes:** T1 (laura.morgana@ing.lu) doesn't have the nested-object module_progress shape. T2 (paperjam) does — apparently from the scan launched during the S148-S152 smoke (commit 05299a1). The shape difference is tied to whether scraper_engine surfaced per-scraper sub-progress via Redis at finalize time.

**Suggested follow-up sprint (S158):** Defensive render in ScansTab to handle both shapes — `typeof status === 'object' ? <SubProgressBlock data={status}/> : <SimpleStatus value={status}/>`. Or normalize at API boundary so the UI only sees string statuses.

### 2. JWT session expiry mid-walk

Access token lifetime is ~15 min based on `iat`/`exp` claims. During the ~13-min walk, the access token expired and `/api/v1/*` started returning 401s. The dashboard's refresh-token logic didn't auto-recover cleanly within Playwright's session — required manual re-login and workspace re-switch to continue.

This is unrelated to S157 but worth noting because longer QA walks against this stack will hit it.

### 3. Compat shim deserves a callout

The S157 spec's emphasis on the compat shim was justified — Check 9's "View details" button on OverviewTab triggers `setActiveTab('breaches')` (pre-S157 API), and the shim correctly routed it to `{top: findings, sub: breaches}`. Without the shim, OverviewTab would have needed direct refactoring. The OverviewTab.jsx file is genuinely untouched.

### 4. `getAccounts()` line 200 catch validated

The CC-side adjustment during S157 implementation (rewiring the connected-accounts useEffect from `activeTab === 'accounts'` to `activeTab === 'sources'`) is observable in the network log: when Sources top tab is clicked, `GET /accounts?target_id=...` fires immediately, before the user clicks the Connected accounts sub-pill. That's the over-fetch we explicitly accepted in S157.

### 5. Gaps / not exercisable

- **Check 10 on T2** was not exercisable (no RiskSignalsBlock on paperjam target). Switched to T1 (ING Luxembourg / laura.morgana) which has 3 legal records → exercised successfully there. Recommend keeping T1 as the canonical RiskSignals test target for future smokes.

## Evidence files

```
docs/qa/s157/
├── 01_overview_5tabs.png
├── 02_findings_default.png
├── 03_findings_exposure.png
├── 04_findings_breaches.png
├── 05_findings_usernames.png
├── 06_findings_photos.png
├── 07_findings_locations.png
├── 08_findings_discovered.png
├── 09_findings_all_back.png
├── 10_findings_breaches_persisted.png
├── 11_graph_default.png
├── 12_graph_timeline.png
├── 13_sources_default.png
├── 14_sources_accounts.png
├── 15_scans.png                          ← shows the pre-existing ScansTab render error
├── 16_overview_deeplink_breaches.png     ← compat shim exercise
├── 17_risksignals_viewall.png            ← S120 preset chip flow on T1
├── 18_mobile_700.png
├── 19_console.txt                        ← full console log dump
└── 20_network.txt                        ← filtered API request log
```

(`16_overview_deeplink_search.png` is the pre-click search state, kept for context.)
