# NEXUS 2026 DEMO SCRIPT — xpose Identity Threat Intelligence

**Event**: Nexus 2026 · Luxembourg · June 10-11 · Cybersecurity category
**Duration**: 3 minutes
**Demo target**: laura.morgana@ing.lu (33 accounts, 43 sources, 87 findings)

---

## [0:00] Opening (20s)

> "Every data breach starts with one thing: an email address. From that single string, an attacker can map your entire digital life — your accounts, your passwords, your location, your real name. Today, only intelligence analysts have the tools to see this. xpose changes that."

## [0:20] Live Scan (40s)

**Action**: Landing page is displayed with animated HeroGraph.

- Type demo email into the scan form
- Click **Scan**
- Show real-time module progress badges updating
- "26 scanner modules running in parallel — breaches, social networks, DNS, metadata, archives, code leaks"

**Scan completes** → navigate to target detail.

## [1:00] Exposure Dashboard (40s)

> "Exposure score: 73 out of 100. That's not good."

Walk through:
1. **Profile header**: "Real name, location, 33 social profiles — all from one email"
2. **Identity card**: "Gender, estimated age, probable nationality — derived from public APIs"
3. **Digital fingerprint**: "9-axis behavioral radar — the person's digital DNA. Unique identity signature. Unlike an IP, this fingerprint persists"
4. **Generative avatar**: "This pixel art is generated from the identity graph structure. Same data = same avatar. Data changes = avatar evolves"
5. **Geographic intelligence**: "6 independent signals cross-correlated — timezone, location, nationality, language — all agree on Luxembourg"
6. **PDF export**: Click download → "A 5-page identity report, generated in seconds"

## [1:40] Identity Graph (20s)

**Switch to Graph tab.**

> "Every node is a data point. Every edge is a proven connection."

- **Zoom into cluster**: "These 3 accounts share the same username — persona engine grouped them automatically"
- **Highlight breach nodes**: "Two breaches connected to the same credentials — password reuse detected"
- **Edge confidence**: "Confidence scores propagate through the graph like PageRank"

## [2:00] Remediation (20s)

**Switch to Findings tab.**

> "Every finding is actionable."

- Show critical findings: passwords leaked in cleartext
- Show Deep Scan button: "Drill into any indicator — usernames, emails, domains"
- Quick mention: CSV export for compliance

## [2:20] Differentiator (25s)

> "What makes xpose different?"

1. "SpiderFoot and Maltego are powerful — but built for analysts. xpose gives the same intelligence with consumer-grade UX"
2. "Aura and NordProtect monitor breaches — but they don't build identity graphs, cluster personas, or generate behavioral fingerprints"
3. "120 intelligence sources. 9 analyzers. Open source. On-premise. GDPR compliant"

## [2:45] Close (15s)

> "Your digital exposure is a liability. xpose turns it into intelligence. Free tier today — scan yourself, see what we find."

**End on landing page with scan form visible.**

---

## Pricing (if asked)

| Plan | Price | Key Features |
|------|-------|-------------|
| Free | €0 | 25 scans/month, 9-axis fingerprint preview, single identifier |
| Starter | €49/month | 250 full scans/month, 127-source pipeline, identity graph + personas, PDF reports |
| Team | €299/month | 2 000 scans/month, 5 seats, API access (SIEM/SOAR), multi-workspace + shared targets |
| Enterprise | From €2 500/month | Multi-tenant + SSO, audit log + SLA, custom scrapers on demand, managed third-party APIs |

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
| Scanner modules | 35 (all active) |
| Data-driven scrapers | 120 across 10 categories |
| Intelligence analyzers | 9 |
| Fingerprint axes | 9 |
| Scan time | ~90 seconds |
| Sites checked | 120 (via scraper engine + scanners) |
| Breach databases | HIBP + XposedOrNot + LeakCheck + IntelX + paste sites |
| Confidence model | PageRank (damping=0.85, 20 iterations) |
| Geo signals | 6 (self-reported, timezone, nationalize, language, geoip, ground truth) |

## Fallback Plan

If live scanning fails:
- Pre-scan results are cached in the database
- Navigate directly to the target detail page
- All findings, graph, and analysis are already computed
- HeroGraph on landing page works offline (pure CSS animation)
