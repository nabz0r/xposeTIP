# R&D — Scraper scope expansion (post-S196, 24 May 2026)

**Context** : S196 shipped 3→8 phone scrapers via fd4c18b. Before locking S197 smoke target (real-estate broker), Nabil's call : R&D the scope expansion first to avoid smoke-redo loops.

**Repo state at audit time** : `fd4c18b` on main, 144 scrapers / 24 active in seed (119 active in live DB).

---

## Coverage already in xposeTIP (audit honest)

After enumerating every scraper name in seed_scrapers.py (AST-driven), the **50 social scrapers** already cover :

```
reddit, github, steam, keybase, medium, hackernews, devto, gitlab, aboutme,
imgur, mastodon, stackoverflow, pinterest, linktree, disqus, twitch, telegram,
letterboxd, buymeacoffee, mixcloud, duolingo, pastebin, dockerhub, slideshare,
lastfm, bandcamp, bluesky, flickr, replit, npm, pypi, codeberg, hashnode,
discogs, soundcloud, tiktok, vimeo, tumblr, goodreads, strava, threads,
huggingface, kaggle, bitbucket, packagist, rubygems, producthunt, behance,
dribbble, github_user_api
```

→ **Sherlock-equivalent coverage already substantial**. Net-new gain from blind Sherlock-import = limited.

Maigret (3000+ sites) diff vs above 50 = estimated 50-100 net-new high-quality after dedup + region/dead-site filter. Diff itself = an audit task.

---

## Gap matrix (4 tiers)

### TIER A — Quick wins, URL-template, 1 sprint each (or grouped)

| # | Source | Endpoint sketch | Key? | Pipeline impact |
|---|---|---|---|---|
| 1 | Maigret diff mass-add | data.json import post-dedup | No | ~50-100 username scrapers |
| 2 | HackerNews Algolia search | `hn.algolia.com/api/v1/search?query={input}` | No | content pivot for tech personas |
| 3 | arXiv author API | `export.arxiv.org/api/query?search_query=au:{fullname}` | No | academic identity |
| 4 | ORCID public API | `pub.orcid.org/v3.0/search/?q={fullname}` | No | researcher ID |
| 5 | urlscan.io search | `urlscan.io/api/v1/search/?q=domain:{domain}` | Free key | scan archive presence |
| 6 | AlienVault OTX | `otx.alienvault.com/api/v1/indicators/domain/{domain}/general` | No (basic) | threat intel cross-ref |
| 7 | DBLP author | `dblp.org/search/author/api?q={fullname}&format=json` | No | CS publications |
| 8 | Semantic Scholar | `api.semanticscholar.org/graph/v1/author/search?query={fullname}` | No | broader academia |

### TIER B — Module-level (api/scrapers/*.py), medium effort

| # | Source | Why module not seed |
|---|---|---|
| 9 | **Pappers.fr** | Free 100 req/mo (per https://www.pappers.fr/api), key required. Data sources : INSEE+INPI+BODACC. KYC-grade officer history, financials, beneficial owners. Paginated structured response → needs Python parsing not URL-template. Superset of current BODACC scraper. |
| 10 | Censys | Free 250/mo + key. Cert transparency → domain/SAN pivot from a single email domain |
| 11 | DeBank | Free public no key. Ethereum portfolio breakdown by wallet |
| 12 | Pappers International | Same key as #9. EU companies beyond FR |

### TIER C — Web3 / BFP-strategic (long-term alignment)

| # | Source | BFP angle |
|---|---|---|
| 13 | Lens Protocol GraphQL | Decentralized social — handle ↔ wallet binding signal |
| 14 | Farcaster (Neynar) | FID/username ↔ wallet ↔ casts — onchain identity fingerprint |
| 15 | Mirror.xyz | Wallet → essays — content fingerprint |
| 16 | OpenSea | Wallet → NFT trail — collection-membership fingerprint |

### TIER D — Defer / fragile / ethical question

| # | Source | Issue |
|---|---|---|
| 17 | Holehe-style email-existence | Triggers password-reset endpoints on 120+ sites. Grey-zone vs transparency-empowerment ethic. **Decision required from Nabil before adding.** |
| 18 | TruePeopleSearch / Spy Dialer / NumLookup US | Heavy bot protection (Cloudflare/captcha), needs Playwright module, low fire rate |
| 19 | AnnuaireInverse FR | Needs `accepts_country` chain-shape gate (S185-analog) first |
| 20 | Untappd / AllTrails / Komoot | Low ROI, niche-persona only |

---

## OSS license compatibility (xposeTIP = AGPLv3)

| Project | License | Compat | Useful slice |
|---|---|---|---|
| Sherlock | MIT | ✅ | already substantially imported |
| WhatsMyName | MIT | ✅ | superset, diff target |
| **Maigret** | MIT | ✅ | 3000+ sites JSON config — **prime diff target** |
| Holehe | GPLv3 | ✅ | email-existence pattern (ethics flag) |
| PhoneInfoga | GPLv3 | ✅ | 100% covered post-S196, no net new |
| theHarvester | GPLv2 | ⚠️ grey | partial overlap, prefer reimplem |
| GHunt | "Educational" | ❌ | unclear license, skip |
| Mosint | MIT | ✅ | orchestration only, no module to wrap |

**License rule** : URL-template scrapers take the endpoint knowledge, not source code → license doesn't propagate. Python module reimplementations from API docs (not source) are safe everywhere.

---

## Proposed sprint sequence (Nabil decides ordering)

### Option A — Smoke-first
- **S197** : real-estate broker smoke (validates S196 phone pipeline on rich-corpus target)
- **S198** : Maigret diff audit
- **S199** : Maigret mass-add (post-dedup)
- **S200+** : Tier A bulk, then Tier B Pappers.fr, then Tier C Web3 incrementally
- Pro : S196 validated fast, learn from smoke before mass-adds
- Con : multiple smokes (S197 then post-Tier-A then post-Tier-B...)

### Option B — R&D-first
- **S197** : Maigret diff audit
- **S198** : Maigret mass-add
- **S199** : Tier A grouped (HN Algolia + ORCID + arXiv + DBLP + urlscan + OTX + Semantic Scholar)
- **S200** : Tier B Pappers.fr module
- **S201** : Tier C Farcaster + Lens
- **S202+** : single comprehensive smoke on full 250+ scrapers
- Pro : one smoke validates everything
- Con : S196 untested in production for longer, regression risk accumulates

### Option C — Mix
- **S197** : phone-only smoke (minimal — just verify S196 fires) in parallel with R&D specs
- **S198+** : Tier A through Tier C in sequence
- Final consolidated smoke after Tier C
- Pro : balanced regression coverage + R&D pace
- Con : context switching

---

## Out of scope for this R&D doc

- **`accepts_country` chain-shape gate** for phones (S185 analog) — needed before adding region-specific phone scrapers (AnnuaireInverse, NumLookup-US). Defer until region-specific scrapers actually queue up.
- **Image / facial reverse search** (Yandex Images, Google Lens, PimEyes) — facial-data collection violates xposeTIP's own ethical posture. Hard exclude.
- **Discord / Telegram message search** — requires auth + privacy-grey, defer indefinitely.
- **Property records / cadastre** — paywall-heavy US, FR cadastre free but anonymized. Low ROI.

---

## Quick stats summary

- Today : 144 scrapers / ~119 active live / 11 categories / 11-axis radar
- Post-Tier-A (estimate) : ~210-260 scrapers / ~190 active
- Post-Tier-B : +4 modules in api/scrapers/ (Pappers FR + Pappers Intl + Censys + DeBank)
- Post-Tier-C : +4 Web3 scrapers (Lens + Farcaster + Mirror + OpenSea)
- Net delta if all tiers ship : **~+90-140 scrapers**, mostly URL-template (Green-Intelligence compliant — no new dependencies, no migrations)

---

## Rule alignment

- Rule #1 ✅ pre-spec grep done — current coverage enumerated via AST
- Rule #5 ✅ tactical (4 tiers) + systemic (`accepts_country` flagged, ethical question on Holehe flagged) upfront
- Rule #4 ✅ pipeline impact articulated per tier
- Rule #3 ⚠️ each future sprint needs to respect 3-4 file cap — Maigret mass-add likely 1 file (seed) + 2 docs = OK; Pappers.fr module = 1 new api/scrapers/pappers_fr.py + seed entry + SCANNERS.md + inventory = 4 files exactly. Manageable.
- Rule #7 ✅ counts measured by AST, not from memory
