# Demo Script — xposeTIP

**Audience** : prospects de consulting (DD firms, law firms, family offices, cyber insurance, VC diligence) **et** prospects SaaS (CISO, red team, compliance, threat intel analysts).
**Duration** : 5 minutes core flow, +5 min Q&A.
**Channel** : screen share — Chrome fullscreen, dark mode, stable connexion.

This script is dual-purpose by design. The same product narrative works for Play 1 (productized consulting reports, €2.5K–€40K) and Play 2 (open-source-then-monetize SaaS, €0–€2 500+/mo). Decide which CTA to hit based on prospect signal.

---

## [0:00] Opening (30s)

> "Threat intelligence today is drowning in indicators that don't last. An IP changes in 24 hours. A hash morphs by the time you write a detection rule. Sanctions screening catches names, but the same person operates under three usernames you've never seen.
>
> What persists across all of that is the identity behind the activity. xposeTIP makes identity itself a first-class indicator. One email in — the full digital portrait out. Two minutes."

**On screen** : landing page, animated HeroGraph visible.

---

## [0:30] The scan (60s)

**Action** : type a real, pre-seeded email into the scan form on the landing page. Click **Scan**.

> "127 OSINT sources fire in parallel — social platforms, breach databases, code leak indexes, archive.org, DNS/email metadata, public exposure (news, sanctions, corporate registries, court records in US, France, UK). Pass 1.5 expands usernames found into 70-something more platforms. Pass 2 enriches by resolved name against sanctions, PEP, corporate officer records. Total elapsed: under two minutes."

**While scanning** : narrate one of the module badges that updates ("HIBP returned a breach... Sherlock found 14 platforms... OpenSanctions clean...").

---

## [1:30] Identity Portrait (90s)

**Scan completes** → navigate to target detail page.

> "This is what they call a digital footprint. Most products show you a count. We show you the shape."

Walk the Overview tab:

1. **Score** : "Exposure 73, threat 41. Exposure is digital footprint size — high here. Threat is breach severity weighted by credential leaks. The ratio tells you what kind of problem you have."
2. **9-axis behavioral radar** : "This is the persistent signature. Accounts, platforms, username reuse, breach history, geographic spread, data leak volume, email age, security posture, public exposure. The shape persists across scans even when individual indicators rotate."
3. **Generative pixel art avatar** : "Deterministic from the identity graph eigenvalues. Same data, same avatar — when data shifts, the avatar evolves. 5.4 billion combinations, zero GPU, zero external API."
4. **Risk Signals block** (if visible) : "Phone numbers extracted from breach data. Crypto wallets cross-referenced against scam flags. Legal record matches in US federal court, French BODACC, UK Gazette. All actionable in one block."

---

## [3:00] Identity Graph (60s)

Switch to Graph tab.

> "Every node is a verified indicator. Every edge is a typed link with a confidence score."

- **Zoom into a cluster** : "These three accounts share the same username — persona engine clustered them automatically. We didn't just match strings, we ran PageRank across the graph to confirm cross-verification."
- **Highlight breach node** : "Two breaches connected to the same credentials. Password reuse detected. Click any node — provenance is fully audit­able: which source, which confidence tier, when first seen, when last seen."
- **Edge confidence** : "Confidence isn't a single number. We surface match_confidence separately from finding confidence, so an OpenSanctions partial-name match doesn't get confused with an HIBP exact-email hit."

---

## [4:00] Output & action (60s)

Switch to Findings tab → filter chips.

> "Findings are filterable by category — Phone / Crypto / Legal — and by severity. Each finding has a 'Why this matters' explanation in plain language, not jargon. Deep Scan any indicator to chain across types: from email → usernames → emails → domains, cascade depth one."

Click **Export PDF** :

> "Identity report, dark-themed, plan-tiered, ReportLab. Five pages. Pro tier gets the full Identity Assessment template — what we deliver as the productized consulting service."

---

## [5:00] The two ways to engage (60s)

> "Two ways to work with us:"

**Play 1 — Productized Identity Intelligence Reports**

> "We deliver this analysis as a service for due diligence, compliance screening, threat attribution. Four tiers — Quick Profile €2 500, Identity Assessment €6 500, Deep Investigation €15K, Strategic Briefing €25–40K. Turnaround days, not weeks. Capped at four engagements per month so we don't sacrifice depth. Email contact@redbird.co.com."

**Play 2 — Self-serve SaaS**

> "Or you run it yourself. Free tier — 25 scans a month, basic exposure check. Starter €49 — 250 full scans, 127-source pipeline, identity graph, PDF reports. Team €299 — 2 000 scans, 5 seats, API access for your SIEM/SOAR. Enterprise from €2 500 — multi-tenant, SSO, audit log, SLA, custom scrapers. The core engine is open source — AGPL-3.0 — you can audit every line."

---

## Close

Pick the close based on the room:

**Consulting close** :
> "If you have a specific subject you'd like screened — pre-deal diligence, compliance review, an identity you can't yet pin down — that's where we start. Email is the only thing I need."

**SaaS close** :
> "If you want to test it cold: the free tier scans you. Run it on yourself first. See what we find. Decide if it belongs in your stack."

---

## Pricing — both plays

### Play 1 — Identity Intelligence Reports (productized consulting)

| Tier | Price | Turnaround | Scope |
|---|---|---|---|
| Quick Profile | €2 500 | 48h | 1 identity, full pipeline, executive summary |
| Identity Assessment | €6 500 | 5 days | 1 identity, full pipeline, full PDF report, deep narrative |
| Deep Investigation | €15 000 | 10 days | Up to 5 connected identities, persona analysis, OSINT analyst review |
| Strategic Briefing | €25–40 000 | 3–4 weeks | Custom — multi-target, attribution-grade, board-ready (max 2/qtr) |

### Play 2 — SaaS

| Plan | Price | Scans/mo | Seats | Key Features |
|---|---|---|---|---|
| Free | €0 | 25 | 1 | Basic exposure scan, single identifier, fingerprint preview |
| Starter | €49/mo | 250 | 1 | Full 127-source pipeline, identity graph + personas, PDF reports |
| Team | €299/mo | 2 000 | 5 | API access (SIEM/SOAR), multi-workspace, shared targets |
| Enterprise | From €2 500/mo | Custom | Unlimited | Multi-tenant + SSO, audit log + SLA, custom scrapers, managed APIs |

Migration to usage-based pricing planned for v2 (per-scan/per-API-call), 12–18 months out.

---

## Key numbers (reference)

| Metric | Value |
|---|---|
| Data-driven scrapers | 127 (110 active, 17 disabled placeholders) |
| Scraper categories | 11 |
| Scanner modules | 26 (5 disabled placeholders) |
| Intelligence analyzers | 9 |
| Fingerprint axes | 9 |
| Scan time (median) | ~90 seconds |
| Breach databases | HIBP + XposedOrNot + LeakCheck + IntelX + LeakLookup + paste sites |
| Confidence model | PageRank (damping=0.85, 20 iterations) |
| Geo signals (cross-correlated) | 6 (self-reported, timezone, nationalize, language, geoip, ground truth) |
| Legal record coverage | US (Courtlistener/RECAP) + FR (BODACC) + UK (Gazette x3 editions) |

---

## Demo prep checklist

- [ ] Pre-scan demo target 24h before (results cached in DB — narrate live but display cached)
- [ ] Have backup pre-scanned target ready in second browser tab
- [ ] Verify Docker services up: `docker compose ps`
- [ ] Clear browser cache for fresh landing page load
- [ ] Font check: Instrument Sans + JetBrains Mono rendering
- [ ] Pre-load Graph tab in second browser tab as backup
- [ ] Chrome fullscreen, dark mode
- [ ] Stable internet (scanners hit external APIs)
- [ ] Have `contact@redbird.co.com` and the consulting tier sheet ready in a side window for follow-up

## Fallback plan

If live scanning fails or runs slow:
- Pre-scanned results are cached — navigate directly to the target detail page
- All findings, graph, fingerprint, analysis already computed
- HeroGraph on landing page works offline (pure CSS animation)
- Skip the Pass 1.5 / Pass 2 narrative if scan was cached — go straight to Identity Portrait

---

## Audience-specific tweaks

**For consulting prospects (DD firms, law firms, family offices, VC, cyber insurance)**
- Lean on Play 1 close
- Emphasize: turnaround, capped engagements, OSINT analyst review on Deep Investigation, Strategic Briefing as board-ready
- Skip the SaaS price ladder unless asked

**For SaaS prospects (CISO, red team, compliance team, threat intel analyst)**
- Lean on Play 2 close
- Emphasize: API access at Team tier, AGPL-3.0 core (auditable), self-hostable, multi-tenant + audit log at Enterprise
- Skip the consulting price ladder unless asked

**For mixed-signal prospects (e.g. compliance officer at a bank exploring both)**
- Run the full both-plays close
- Frame: "Use Starter to test fit, engage us for high-stakes investigations"
