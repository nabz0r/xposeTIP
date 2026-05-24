# Audit Phase 1 — Producteurs & backlog S180

Repo HEAD: `79d0e56` (S181 doc sync). v1.6.13.

---

## Architecture des producteurs — **3 systèmes, pas 2**

| Système | Loc | Compte | Dispatch |
|---|---|---|---|
| **A. SCANNER_REGISTRY** | `api/tasks/module_tasks.py` | **27 scanners** | Celery → `_get_scanner(module_id)` |
| **B. URL-template seed** | `scripts/seed_scrapers.py` | **127 entries** | Via `scraper_engine` + `name_scraper_engine` (2 entries de A) |
| **C. Public exposure scrapers** | `api/scrapers/*.py` | **10 modules** | Importés direct par `layer4/public_exposure_enricher.py` |

Plus **9 L4 analyzers** (`api/services/layer4/analyzers/`) consommateurs de findings.

### A. SCANNER_REGISTRY (27)
- Layer 1: 15 (email_validator, holehe, hibp, sherlock, gravatar, social_enricher, google_profile, emailrep, epieos, fullcontact, github_deep, username_hunter, scraper_engine, name_scraper_engine, reverse_image)
- Layer 2: 10 (whois_lookup, maxmind_geo, geoip, leaked_domains, dns_deep, virustotal, shodan, intelx, hunter, dehashed)
- Layer 3: 2 OAuth (google_audit, microsoft_audit)

**Handoff disait 26 — drift +1.**

### C. api/scrapers (10)
bodacc_search, courtlistener_search, gdelt_news, gnews_news, google_news_rss, interpol_red_notices, lbr_luxembourg, opencorporates_officers, opensanctions_search, uk_gazette_search

---

## Seed catalog — réalité vs handoff

| | Handoff | Audit |
|---|---|---|
| Total | 127 | ✅ 127 |
| Disabled | 112 | ❌ **17 explicit-disabled** |
| Enabled | 15 | ❌ 15 explicit-enabled + **95 sans flag** (default→True via model) |

**Modèle:** `enabled: Mapped[bool] = mapped_column(Boolean, default=True)`.

Donc 95 entrées sans `enabled` héritent `True` au premier seed. État DB réel = inconnu sans accès, mais le handoff "88% graveyard" est presque certainement faux en lecture statique.

Par `input_type`: username 74 / email 24 / name 10 / domain 9 / first_name 3 / phone 3 / crypto_wallet 3 / fullname 1.

---

## Backlog S180-A→F — validation contre code actuel

### ⚠️ S180-D — **STALE, à supprimer du backlog**

Claim handoff: "8 domain-scrapers writing `indicator_type='username'` for FQDN values"

Réalité code (`scraper_scanner.py:166`):
```python
indicator_type=scraper.identity_type or scraper.input_type,
```
Commentaire S159: "default to input_type. A DNS scraper given a domain should write 'domain' findings, not pretend it produced a 'username'."

Audit des 9 entries `input_type=domain`:
- 6/9 ont déjà `identity_type='domain'` explicite
- 3/9 absent → fallback à `input_type='domain'` via S159
- **0/9 émettrait `indicator_type='username'`**

Doublement protégé: `username_validator.py:_DOMAIN_TLD_RE` filtre les FQDN qui passent quand même. → **S179 + S159 ont déjà fermé ce gap.**

### S180-A/B/C/E/F — défensivement mitigés

`username_validator.py` (S179) catch les symptômes upstream:

| Item | Symptôme upstream | Filtre S179 actif |
|---|---|---|
| S180-A | aboutme/linktree/linkedin title extraction | `_TITLE_PATTERNS` contient "linktree", "instagram"; pipe `\|` rejeté |
| S180-B | bandcamp HTML entities dans og:title | `&amp;` / `&#` rejeté |
| S180-C | replit "handle (Full Name)" suffix | `(` / `)` rejeté |
| S180-E | telegram generic title | `_TITLE_PATTERNS` contient "telegram" + en-dash rejeté |
| S180-F | threads `connection_quality` JSON key | `_TITLE_PATTERNS` contient "connection_quality" |

Le validator est le safety net et il marche. Les fixes S180-A→F sont de l'**upstream hygiene** (réduction de bruit côté production, mais le user-visible state est déjà propre).

**Levier réel: faible.** Tous mitigés en aval.

### S180-G ✅ shipped (observability)
### S180-J catalog expansion → **vrai levier**

---

## Recommandation direction

**Skip S180-A→F.** Le validator S179 fait le job. Ces "bugs" ne produisent pas de symptôme user-visible.

Direction proposée:

1. **S182 — Phase 2 réduite** : un seul sprint chirurgical pour supprimer S180-D du SPRINT_LOG/backlog docs (closure formelle, pas de code change).

2. **S183+ — Phase 3 (catalog expansion)** = la vraie attaque. Le handoff a déjà listé les candidats:
   - **Crypto** (gap obvious): Etherscan, DeBank multi-chain, Solscan/Solana Beach
   - **Legal** (extend layer4 public_exposure_enricher): SEC EDGAR, OFAC, Companies House UK, OpenCorporates
   - **Phone**: Truecaller, IPQualityScore, Twilio Lookup
   
   Suggestion ordre: **crypto d'abord** (input_type=`crypto_wallet`, actuellement 3 scrapers seulement, biggest gap; PLUS: aligne avec BFP claim emitter qui a déjà type "ip/username/email/domain/first_name/social_url" mais pas crypto).

---

## Drifts à corriger en doc

- SCANNERS.md / CLAUDE.md disent "26 scanners" → 27
- Handoff "112 disabled seed" → 17 explicit-disabled
- Backlog S180-D → STALE
