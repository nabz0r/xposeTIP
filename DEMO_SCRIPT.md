# NEXUS 2026 DEMO SCRIPT — xpose Identity Threat Intelligence

**Event**: Nexus 2026 · Luxembourg · June 10-11 · €100K Grand Prize
**Duration**: 3 minutes

---

## [0:00] Opening (20s)

> "Every data breach starts with one thing: an email address. From that single string, an attacker can map your entire digital life — your accounts, your passwords, your location, your real name. Today, only intelligence analysts have the tools to see this. xpose changes that."

## [0:20] Live Scan (40s)

**Action**: Landing page is displayed with animated HeroGraph.

- Type demo email into the scan form
- Click **Scan**
- Show real-time module progress badges updating
- "25 scanners running in parallel — breaches, social networks, DNS, metadata, archives"

**Scan completes** → navigate to target detail.

## [1:00] Exposure Dashboard (30s)

> "Exposure score: 73 out of 100. That's not good."

Walk through:
1. **Profile header**: "Real name, location, 8 social profiles — all from one email"
2. **Identity card**: "Gender, estimated age, probable nationality — derived from public APIs"
3. **Digital fingerprint**: "8-axis radar — unique identity signature. Eigenvalue topology means no two people get the same shape"
4. **Generative avatar**: "This abstract shape is generated from the identity graph structure. Same data = same avatar. Data changes = avatar evolves"

## [1:30] Identity Graph (30s)

**Switch to Graph tab.**

> "Every node is a data point. Every edge is a proven connection."

- **Zoom into cluster**: "These 3 accounts share the same username — persona engine grouped them automatically"
- **Highlight breach nodes**: "Two breaches connected to the same credentials — password reuse detected"
- **Point out edge weights**: "Confidence scores propagate through the graph like Google's PageRank. A name confirmed by 3 independent paths gets higher confidence"

## [2:00] Remediation (20s)

**Switch to Findings tab.**

> "Every finding is actionable."

- Show critical findings: passwords leaked in cleartext
- Show finding status toggle: active → resolved
- Show remediation progress bar
- Quick mention: CSV export for compliance

## [2:20] Differentiator (25s)

> "What makes xpose different?"

1. "SpiderFoot and Maltego are powerful — but built for analysts. xpose gives the same intelligence with consumer-grade UX"
2. "Aura and NordProtect monitor breaches — but they don't show you the identity graph. They don't cluster personas. They don't give you a digital fingerprint"
3. "76 intelligence modules. Open source. GDPR compliant. On-premise deployment"

## [2:45] Close (15s)

> "Your digital exposure is a liability. xpose turns it into intelligence. Free tier today — scan yourself, see what we find."

**End on landing page with scan form visible.**

---

## Demo Checklist

- [ ] Pre-scan demo target 24h before (results cached in DB)
- [ ] Have backup pre-scanned target ready
- [ ] Test HeroGraph animation renders smoothly on projector
- [ ] Verify all Docker services: `docker compose ps`
- [ ] Clear browser cache for fresh landing page load
- [ ] Font check: Instrument Sans + JetBrains Mono rendering
- [ ] Pre-load Graph tab in second browser tab as backup
- [ ] Chrome fullscreen, dark mode
- [ ] Stable internet connection (scanners hit external APIs)

## Key Numbers

| Metric | Value |
|--------|-------|
| Scanners | 25 (17 implemented + 8 planned) |
| Scrapers | 51 across 8 categories |
| Intelligence analyzers | 5 |
| Fingerprint axes | 8 |
| Scan time | ~30 seconds |
| Sites checked | 120+ (via Holehe + scrapers) |
| Breach databases | HIBP + XposedOrNot + paste sites |
| Confidence model | PageRank (damping=0.85) |

## Fallback Plan

If live scanning fails:
- Pre-scan results are cached in the database
- Navigate directly to the target detail page
- All findings, graph, and analysis are already computed
- HeroGraph on landing page works offline (pure CSS animation)
