<!--
Copyright 2026 xposeTIP authors. Licensed under the Apache License, Version 2.0.
SPDX-License-Identifier: Apache-2.0
-->

# Phone scraper landscape R&D (v0)

| Field              | Value                                                        |
|--------------------|--------------------------------------------------------------|
| Status             | Working draft, v0. Substrate for S217+ implementation sprints. |
| Eval date          | 2026-05-25                                                   |
| Eval sprint        | S216                                                         |
| Methodology        | Repo inventory + candidate landscape survey + 9-field per-source eval cells + viability rubric (0-5) + RGPD posture matrix per category |
| Reference impl     | xposeTIP v1.6.27 (post-S215)                                 |
| Companion          | `docs/specs/pqc_choices_v0.md` (pattern reference)           |
| Disclaimer         | RGPD posture sections are **informational only, not legal advice**. Operator is responsible for per-campaign LIA. Luxembourg CNPD is supervisory authority. |

---

## 0. Executive summary

xposeTIP today has **zero person-centric phone OSINT scrapers** reaching the
pipeline. 4 metadata dorks are active; 4 carrier-validator scrapers are
disabled because their seed dicts carry placeholder API keys that were never
provisioned. The cascade work shipped in S211 propagates phone indicators
downstream for Deep-Scan, but the cascade hits an empty fleet.

This document scopes the MVP fix: which scrapers to ship, in which order, with
what authentication and lawful-basis posture. **No code change in this
sprint.** The §0.1 LOCKED short-list is the input to S217+.

### 0.1 LOCKED CHOICES

| # | Source                  | Tier        | Auth                       | Free quota                | Identity_type produced       | Implementation sprint |
|---|-------------------------|-------------|----------------------------|---------------------------|------------------------------|-----------------------|
| 1 | `numverify_phone`       | A validator | free API key (≤5 min)      | 100/month                 | `phone` (carrier, line_type, country) | S217 |
| 2 | `veriphone_phone`       | A validator | free API key (≤5 min)      | 1000/month                | `phone` (carrier, line_type, country) | S217 |
| 3 | `api_ninjas_phone`      | A validator | free API key (≤5 min)      | 50000/month (per-day cap) | `phone` (carrier, location, valid)    | S217 |
| 4 | `abstractapi_phone`     | A validator | free API key (≤5 min)      | 250/month                 | `phone` (carrier, line_type, country) | S217 |

> `google_phonebook_dork` was LOCKED in v0 of this doc; S218 live-eval
> proved the PhoneBook operator is DEAD (Google removed ~2021). Cell
> §2.15 flipped to DEAD, §3 score 4 → 0, REJECTED. See §7.1.

WhatsApp / Telegram / Viber URL-trick presence checks **deliberately NOT
locked**. They scored ≥4 on raw viability but RGPD posture is HIGH and the
2026 platform ecosystem actively retaliates against URL-probe automation
(see §0.3 caveat 2, §2.13 cell, §4 social-presence row). They go to backlog
with a conditional-sprint marker; operator decides.

### 0.2 Headline reasoning

- **Validators picked first because they're zero-effort wins.** The 4 disabled
  scrapers already have URL templates + extraction rules wired. The only
  missing step is API key provisioning — which is a 5-minute operator task per
  source. Re-enabling them lifts the phone fleet from 4 dorks to 8 sources
  without code change beyond `enabled=True` flips and key insertion.
- **Tier coverage chosen for redundancy, not breadth.** All 4 validators
  produce overlapping fields (carrier / line_type / country). Picking all 4
  rather than the single best one is intentional: each has a different free
  quota (100, 1k, 50k, 250 / month), and the pipeline can round-robin OR
  fail-over without per-scraper sprint work. Free-tier diversity is
  cheap insurance against any single provider yanking the free plan.
- **Google PhoneBook dork picked because it's free + zero-auth + adds a
  qualitatively different signal** (public web mentions vs carrier metadata).
  The 4 existing `*_phone_dork` modules use generic web search; adding a
  PhoneBook-flavoured variant gives one more discriminator and matches
  PhoneInfoga's proven pattern.
- **Reverse-lookup people-search (Tier B) deferred** to a follow-up sprint
  even when viability ≥4. US-centric coverage is poor for xposeTIP's EU
  primary corpus, and bot-detection on `truepeoplesearch.com` /
  `numlookup.com` is intermediate-to-high; warrants dedicated bot-evasion
  audit before shipping.
- **Breach DB (Tier C) needs S214-style audit first** to determine whether
  existing email-input breach scrapers (LeakCheck, IntelX, HIBP) accept
  phone input cleanly through the same endpoint or need new entries.
  S217 viability dwarfs this; it lands later.
- **Social-presence (Tier D) excluded from MVP by operator-judgment rule.**
  See §0.3 caveat 2. RGPD HIGH + platform-ToS-violating + 2025-2026 quality
  degradation = three independent vetos.

### 0.3 Caveats acknowledged

1. **Free-tier quotas may not survive 2026.** Each of the 4 validators sits
   on a small free tier that has historically been the first thing to get
   removed when these vendors raise prices. NumVerify (apilayer) and
   AbstractAPI in particular have both reshuffled their free plans in the
   2024-2026 window. Re-eval trigger captured in §0.4.
2. **WhatsApp / Telegram URL tricks are degrading.** The `wa.me/{phone}`
   redirect-status pattern (HTTP 200 if account exists, 404 otherwise)
   worked reliably 2017-2023. Post-2024 WhatsApp business changes,
   responses now sometimes return 200 even for non-existent accounts and
   surface a "phone not registered" inside the page body — requiring HTML
   parse rather than status check. Telegram `t.me/+{phone}` was similar.
   Beyond the technical degradation, both platforms actively rate-limit
   and block automation from non-residential IPs. xposeTIP would be
   contributing to a known abuse pattern; ethics layer says no without
   explicit operator decision.
3. **RGPD recital 47 ("legitimate interest") vs recital 49 ("network
   security") scope ambiguity for phone-vs-email.** Email-OSINT operates
   under recital 47 (subject's reasonable expectation that an email
   address may be used for identification). Phone numbers carry a heavier
   subject-expectation because they're often non-public. Validators
   (carrier metadata) are tenable. Reverse-lookup that exposes owner name
   is borderline and warrants per-campaign LIA. Subject-rights pathway
   (delete-on-request) is non-negotiable per xposeTIP's manifesto.
4. **`phonenumbers` lib normalization quality is excellent but not
   universal.** France mobile (+33 6/7) and Luxembourg (+352 6xx) are
   well-covered; some African and South American carriers can produce
   `is_valid_number=False` for legitimate numbers. The A1.5 extraction
   already handles this gracefully (drops the candidate); same posture
   for new scrapers.
5. **NumVerify is the riskiest LOCKED pick.** Apilayer's NumVerify has
   the smallest free tier (100/month — barely enough for one workspace's
   monthly scans) AND has the strictest UA blocking. If S217 testing
   shows the free tier is unusable, the pick deferred to "backlog
   conditional on paid tier budget" without affecting picks 2-4.

### 0.4 Re-evaluation triggers

| Trigger                                                                | Required action                                                                                |
|------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| NumVerify free tier removed / quota slashed                             | Drop pick 1, document in S217 retro, do not replace blindly                                    |
| AbstractAPI free tier removed                                           | Drop pick 4, fall back to Veriphone + API Ninjas combination                                   |
| HIBP exposes phone search endpoint publicly                             | Add Tier C pick, fast-track to first follow-up sprint                                          |
| `wa.me` returns to reliable status-differential                          | Reconsider Tier D — still requires operator sign-off                                            |
| Luxembourg CNPD issues phone-OSINT guidance                              | Revisit §4 matrix, possibly add/remove sources                                                 |
| `phonenumbers` library deprecates or major-versions                      | Sweep A1.5 extraction code + validate every scraper still parses E.164 correctly                |
| Truecaller API genuinely opens to OSINT                                  | Reconsider §6 deferral                                                                         |

---

## 1. Current state

### 1.1 Repo inventory

Live `scrapers` table query (T0 evidence in `docs/qa/S216_phone_inventory.txt`):

```
name                      category     enabled  identity_type  key_status
bing_phone_dork           metadata     True     NULL           ready
duckduckgo_phone_dork     metadata     True     NULL           ready
google_phone_dork         metadata     True     NULL           ready
yandex_phone_dork         metadata     True     NULL           ready
abstractapi_phone         identity     False    NULL           placeholder_key
api_ninjas_phone          identity     False    NULL           ready
numverify_phone           identity     False    NULL           placeholder_key
veriphone_phone           identity     False    NULL           placeholder_key
```

8 scrapers exist with `input_type='phone'`. 4 are search-engine dork
generators that emit URLs as findings rather than structured carrier or
identity data. The other 4 — the validators that would produce structured
data — are all `enabled=False` because either the URL template contains a
literal `placeholder` token (3 of 4) or the seed shipped with `enabled=False`
pending operator decision (1 of 4, `api_ninjas_phone`).

Net: the pipeline currently fails to produce ANY person-centric phone
intelligence beyond "phone X mentioned on URL Y" mentions. This is the
gap S217+ closes.

### 1.2 Adjacent infra (no work needed)

The pipeline plumbing for phone OSINT is already complete:

- **A1.5 extraction** — `api/services/secondary_identifiers.py:_extract_phones`
  uses Google's `phonenumbers` lib to find E.164-normalized phones in
  arbitrary finding-text fields. Regex match → `phonenumbers.parse` →
  `is_valid_number` filter → E.164 format normalization. Returns a flat
  list of strings ready for dispatch.
- **A1.6 dispatch** — `api/services/secondary_identifier_enricher.py` iterates
  every enabled scraper with `input_type='phone'`, formats the URL template
  with `phone` and `phone_clean` (the latter is `phone.replace("+", "")` per
  S208 fix), executes via the same `scraper_engine.py` runner that handles
  email/username/domain scrapers, materializes findings.
- **S211 cascade integration** — `_extract_cascade_indicators` Pass 3 calls
  `_extract_phones(deep_findings)`. Any deep-scan finding text that surfaces
  a new phone gets propagated as a `phone` cascade indicator subject to the
  global cap-5 and dedup against existing Identity rows.
- **Deep-Scan unlock** — S208 added `phone` to `SCANNABLE_INDICATOR_TYPES`
  (single-source via S210), to `_INDICATOR_TO_INPUT_MAP['phone'] = ['phone']`,
  and to `_build_format_kwargs` (the critical companion fix for the
  `_SafeFormatDict` placeholder substitution). Operator-triggered Deep Scan
  on a phone finding routes to all enabled `input_type='phone'` scrapers.
- **E.164 normalization** — `phonenumbers` lib pinned (already in
  `requirements.txt` from S107b crypto/phone infra sprint). No new
  dependency required.

**Adding a phone scraper = one dict entry in `seed_scrapers.py`. Infra is
ready.** This is the single most important fact justifying the
S217+ implementation sequencing: no architecture work needed, the
bottleneck is candidate selection + API-key provisioning.

---

## 2. Candidate landscape

Each cell uses the standard 9-field structure (mirrors `pqc_choices_v0.md`):

### 2.1 numverify_phone (existing, disabled)

- **Type**: validator (carrier + line-type)
- **Endpoint**: `https://apilayer.net/api/validate?access_key={key}&number={phone_clean}`
- **Auth**: free API key (signup at apilayer.com, 5 min)
- **Free quota**: 100/month
- **Output fields**: `valid`, `country_code`, `country_name`, `location`,
  `carrier`, `line_type`
- **Indicator_type produced**: `phone`
- **Bot-detection / scraping difficulty**: low (clean JSON API)
- **RGPD posture (informational)**: LOW — carrier metadata is technical
  enrichment, recital 49 covers fraud/security use
- **2026 status**: ACTIVE (free tier has shrunk over years but exists)

### 2.2 veriphone_phone (existing, disabled)

- **Type**: validator
- **Endpoint**: `https://api.veriphone.io/v2/verify?phone={phone_clean}&key={key}`
- **Auth**: free API key (signup veriphone.io, 5 min)
- **Free quota**: 1000/month
- **Output fields**: `phone_valid`, `phone_type`, `phone_region`, `country`,
  `country_code`, `country_prefix`, `international_number`, `local_number`,
  `e164`, `carrier`
- **Indicator_type produced**: `phone`
- **Bot-detection / scraping difficulty**: low
- **RGPD posture (informational)**: LOW (same rationale as 2.1)
- **2026 status**: ACTIVE

### 2.3 api_ninjas_phone (existing, disabled)

- **Type**: validator
- **Endpoint**: `https://api.api-ninjas.com/v1/validatephone?number={phone_clean}`
- **Auth**: free API key via header `X-Api-Key` (signup api-ninjas.com,
  5 min)
- **Free quota**: 50000/month with per-day cap
- **Output fields**: `is_valid`, `country`, `country_code`, `location`,
  `timezones`, `carrier`
- **Indicator_type produced**: `phone`
- **Bot-detection / scraping difficulty**: low
- **RGPD posture (informational)**: LOW
- **2026 status**: ACTIVE (largest free quota of the 4 validators)

### 2.4 abstractapi_phone (existing, disabled)

- **Type**: validator
- **Endpoint**: `https://phonevalidation.abstractapi.com/v1/?api_key={key}&phone={phone_clean}`
- **Auth**: free API key (signup abstractapi.com, 5 min)
- **Free quota**: 250/month
- **Output fields**: `valid`, `format.international`, `format.local`,
  `country.code`, `country.name`, `country.prefix`, `location`, `type`,
  `carrier`
- **Indicator_type produced**: `phone`
- **Bot-detection / scraping difficulty**: low
- **RGPD posture (informational)**: LOW
- **2026 status**: ACTIVE (small free tier — risky if it shrinks further)

### 2.5 ovh_telecom_lookup (NEW candidate)

- **Type**: validator (FR-specific)
- **Endpoint**: `https://api.ovh.com/1.0/telephony/searchPublicDirectory?number={phone_clean}` (public-directory subset; account-bound endpoints exist but require OAuth)
- **Auth**: none for public-directory search; OAuth + customer account for richer endpoints
- **Free quota**: unlimited for public-directory search, rate-limited
- **Output fields**: `name`, `address`, `postal_code` (for FR landlines listed in the public directory only — mobile is opt-in and usually absent)
- **Indicator_type produced**: `phone` (or `person` if a name is returned)
- **Bot-detection / scraping difficulty**: low (clean JSON API)
- **RGPD posture (informational)**: MEDIUM — the public directory data is
  subject-published-by-choice, but combining it with other xposeTIP signals
  creates a profile beyond the original directory purpose. LIA per campaign.
- **2026 status**: ACTIVE but practically limited — FR mobile carriers
  default-opt-out of public directory; usefulness peaks for FR landlines and
  small-business switchboards. Most useful as a low-volume corroborator, not
  a primary signal.

### 2.6 numlookup (Tier B candidate)

- **Type**: reverse lookup
- **Endpoint**: `https://www.numlookup.com/{phone_clean}` (HTML scrape)
- **Auth**: none
- **Free quota**: unlimited (rate-limited, no documented cap)
- **Output fields**: `carrier`, `line_type`, `country`, `city`, possibly
  `owner_name` (US numbers only, ~30% coverage)
- **Indicator_type produced**: `phone` + occasional `person`
- **Bot-detection / scraping difficulty**: medium (rate-limit headers + soft
  Cloudflare protection)
- **RGPD posture (informational)**: MEDIUM (US-data primary — RGPD scope
  attaches when the lookup target is an EU data subject; carrier metadata is
  recital 49 acceptable, owner_name is borderline)
- **2026 status**: ACTIVE for US/CA numbers; coverage of FR/EU numbers is
  poor (returns carrier only). Worth piloting but probably low EU yield.

### 2.7 truepeoplesearch (Tier B candidate)

- **Type**: reverse lookup (people search)
- **Endpoint**: `https://www.truepeoplesearch.com/results?phoneno={phone_clean}` (HTML scrape)
- **Auth**: none
- **Free quota**: unlimited (heavy bot-detection — practical cap unknown)
- **Output fields**: `owner_name`, `address_history`, `relatives`,
  `email_history`, `age_range` (US numbers only, almost-no EU coverage)
- **Indicator_type produced**: `person` (multi-axis enrichment)
- **Bot-detection / scraping difficulty**: HIGH (Cloudflare + behavioural
  fingerprinting; PhoneInfoga has had this scraper land/break repeatedly
  through 2024-2026)
- **RGPD posture (informational)**: MEDIUM-HIGH — when US-resident only,
  GDPR doesn't strictly attach; when used against EU subjects, the
  owner_name + relatives + addresses combination is borderline mass
  profiling. Per-campaign LIA mandatory.
- **2026 status**: DEGRADED (works intermittently from residential IPs;
  data-center IPs hit Cloudflare wall within 5-10 requests). Operator must
  budget for residential proxy if this is a serious pick.

### 2.8 ipqualityscore (Tier B candidate)

- **Type**: reverse lookup + fraud score
- **Endpoint**: `https://www.ipqualityscore.com/api/json/phone/{key}/{phone_clean}`
- **Auth**: free API key (signup ipqualityscore.com, 5 min)
- **Free quota**: 1000/month for phone lookup (free plan covers IP + URL +
  phone combined; phone-only cap in practice ~1k)
- **Output fields**: `valid`, `country_code`, `region`, `city`, `zip_code`,
  `timezone`, `carrier`, `line_type`, `fraud_score`, `recent_abuse`,
  `risky`, `VOIP`, `prepaid`, `do_not_call`, `name` (rarely populated)
- **Indicator_type produced**: `phone` (rich) + optional `person` if name
  surfaces
- **Bot-detection / scraping difficulty**: low (clean JSON API)
- **RGPD posture (informational)**: MEDIUM — fraud_score is borderline
  profiling; carrier metadata is fine. Subject access right will need to
  surface the fraud_score per Art 15 if requested.
- **2026 status**: ACTIVE (paid tiers expanding; free tier stable so far)

### 2.9 dehashed_phone (Tier C candidate)

- **Type**: breach / leak database
- **Endpoint**: `https://api.dehashed.com/search?query=phone:{phone_clean}`
- **Auth**: paid API key (account + credits — no free tier)
- **Free quota**: zero
- **Output fields**: `breach_count`, `breach_names[]`, `email[]` (paired
  emails for the phone), `username[]`, `name[]`, `address[]`,
  `password[]` (hashed where source allowed)
- **Indicator_type produced**: `breach` + cascaded `email` / `username`
- **Bot-detection / scraping difficulty**: low (paid API)
- **RGPD posture (informational)**: HIGH — DeHashed includes stolen-data
  sets. Lawful basis under Art 6(1)(f) is tenable for fraud-prevention scope
  but requires careful LIA documentation. Some breach datasets in DeHashed
  may themselves be Art 5 violation under data-minimization.
- **2026 status**: ACTIVE but DEFERRED in §0.1 picks because paid + RGPD
  HIGH posture combination needs Nabil-level legal review before any
  serious investment.

### 2.10 leakcheck_phone (Tier C candidate)

- **Type**: breach / leak database
- **Endpoint**: existing email-input `leakcheck` scraper — needs research
  whether `https://leakcheck.io/api/public?check={phone}&type=phone` works
  with the public free key
- **Auth**: free key for limited type (`leakcheck.io` documents `&type=`
  for email, username, password, hash — phone is in their paid v2 API)
- **Free quota**: 10/min for public free key (email only); phone not in
  free
- **Output fields**: would mirror existing leakcheck output (`sources[]`,
  `email`, etc.) if phone supported
- **Indicator_type produced**: `breach`
- **Bot-detection / scraping difficulty**: low
- **RGPD posture (informational)**: MEDIUM (same as existing leakcheck
  posture)
- **2026 status**: UNKNOWN-for-phone-input. Tier C pre-eval — confirm via
  vendor docs before any seed entry. Likely paid-only for phone.

### 2.11 intelx_phone (Tier C candidate)

- **Type**: breach / leak database + dark-web index
- **Endpoint**: existing `intelx` API with `selectorType: TELEPHONE` query;
  the existing email-input scraper would need a sibling entry with phone
  selector
- **Auth**: paid (existing IntelX paid subscription via API key)
- **Free quota**: zero on phone selector — IntelX free tier explicitly
  excludes telephone search
- **Output fields**: paste-site mentions, leak-set membership, dark-web
  document refs
- **Indicator_type produced**: `breach`
- **Bot-detection / scraping difficulty**: low (paid API)
- **RGPD posture (informational)**: MEDIUM (IntelX itself maintains a
  careful posture)
- **2026 status**: ACTIVE but PAID. Deferred in §0.1 pending operator
  decision on IntelX paid scope expansion (currently used for email only).

### 2.12 wa_me_existence_check (Tier D — DEFERRED)

- **Type**: social-presence check
- **Endpoint**: `https://wa.me/{phone_clean}` — pre-2024 the redirect-
  status pattern (HTTP 200 → exists, 404 → does not) was reliable; post-
  2024 needs HTML body parse for "phone not registered" string
- **Auth**: none
- **Free quota**: unlimited (effectively rate-limited by WhatsApp
  infrastructure — minutes-of-success then blocks)
- **Output fields**: `whatsapp_present` (boolean)
- **Indicator_type produced**: `social_url`
- **Bot-detection / scraping difficulty**: HIGH (WhatsApp aggressively
  blocks data-center IPs; residential proxy needed for any meaningful
  volume)
- **RGPD posture (informational)**: HIGH — Meta's ToS prohibits automated
  probing; data subject expectations around messaging-app presence are
  strong; LIA balancing test difficult to win
- **2026 status**: DEGRADED — quality + reliability + ethical risk all
  trend the wrong way

### 2.13 t_me_existence_check (Tier D — DEFERRED)

- **Type**: social-presence check
- **Endpoint**: `https://t.me/+{phone_clean}` (Telegram phone-search
  deep-link), HTML parse for redirect target
- **Auth**: none
- **Free quota**: unlimited (rate-limited)
- **Output fields**: `telegram_present` (boolean), occasionally
  `telegram_username` if the account has a public handle
- **Indicator_type produced**: `social_url` + optional `username`
- **Bot-detection / scraping difficulty**: MEDIUM-HIGH
- **RGPD posture (informational)**: HIGH (same family as 2.12)
- **2026 status**: DEGRADED (Telegram tightened phone-search privacy in
  2024-2025; many accounts now default-hidden from this lookup)

### 2.14 viber_existence_check (Tier D — DEFERRED)

- **Type**: social-presence check
- **Endpoint**: `https://viber.click/{phone_clean}` — historically returns
  Viber profile if account exists
- **Auth**: none
- **Free quota**: unlimited (rate-limited)
- **Output fields**: `viber_present` (boolean), optional display name
- **Indicator_type produced**: `social_url`
- **Bot-detection / scraping difficulty**: MEDIUM
- **RGPD posture (informational)**: HIGH
- **2026 status**: DEGRADED — Viber's market share has declined; coverage
  is patchy in 2026 outside specific EE / SE Asia regions

### 2.15 google_phonebook_dork — DEPRECATED (S218 empirical re-eval)

- **Type**: dork-generator (search-engine query crafting)
- **Endpoint (DEAD)**: `https://www.google.com/search?q=...&pb=r`
- **Auth**: none
- **Free quota**: N/A
- **Output fields**: NONE (the `pb=r` query parameter is preserved in URL
  parsing but produces no PhoneBook-specific UI block in 2026 SERP).
- **Indicator_type produced**: N/A
- **Bot-detection / scraping difficulty**: N/A
- **RGPD posture (informational)**: N/A
- **2026 status**: **DEAD** — Google removed the PhoneBook search operator
  around 2021 (searchengineland historical record; Gary Illyes Twitter
  confirmation). Live test 2026-05-25 by operator confirmed: `curl ?pb=r`
  returns identical SERP to plain query, no phonebook block in HTML.
  S216 §2.15 LOCKED this pick as "2026 status: ACTIVE" without live
  validation — pattern S209 (Maigret tranche 2 hypothesis-vs-reality gap).
  Honest acceptance: marginal value = 0, the existing `google_phone_dork`
  already covers `q="{phone_clean}"` query-by-citation, which is exactly
  what `pb=r` falls back to. **Removed from S216 §0.1 LOCKED list. S218
  unlocked as rescan validation sprint instead of phonebook seed.**

### 2.16 intelx_telephone_tool (NEW candidate)

- **Type**: dork-generator (web tool scrape)
- **Endpoint**: `https://intelx.io/tools?tab=telephone&q={phone_clean}` — HTML scrape of public web tool (no API)
- **Auth**: none for the public web tool; paid for API
- **Free quota**: unlimited for HTML scrape; rate-limited
- **Output fields**: aggregated paste-site mention count + result preview
- **Indicator_type produced**: `phone` (mention summary)
- **Bot-detection / scraping difficulty**: medium (IntelX has light
  bot-detection on their web tools)
- **RGPD posture (informational)**: MEDIUM
- **2026 status**: ACTIVE but quality-of-output is markedly lower than
  the paid API. Borderline pick.

---

## 3. Per-source viability gate

Scoring rubric:
- **+1** if free tier OR fully free
- **+1** if no API key required OR free key obtainable in <5 min
- **+1** if output produces NEW indicator_type OR NEW field xposeTIP doesn't currently capture
- **+1** if 2026 status is ACTIVE (not DEGRADED / DEAD)
- **+1** if RGPD posture is LOW or MEDIUM (HIGH = automatic 0 on this axis)

Threshold for **LOCKED MVP candidate**: score ≥ 4.
Threshold for **Backlog with conditions**: score 2-3.
Threshold for **REJECTED**: score ≤ 1.

| # | Source | Free | No-auth | New-field | 2026-active | RGPD ≤MED | Total | Verdict |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| 2.1 | numverify_phone | 1 | 1 | 1 | 1 | 1 | **5** | LOCKED |
| 2.2 | veriphone_phone | 1 | 1 | 1 | 1 | 1 | **5** | LOCKED |
| 2.3 | api_ninjas_phone | 1 | 1 | 1 | 1 | 1 | **5** | LOCKED |
| 2.4 | abstractapi_phone | 1 | 1 | 1 | 1 | 1 | **5** | LOCKED |
| 2.5 | ovh_telecom_lookup | 1 | 1 | 1 | 1 | 1 | **5** | Backlog (FR-only) |
| 2.6 | numlookup | 1 | 1 | 1 | 1 | 1 | **5** | Backlog (medium bot risk) |
| 2.7 | truepeoplesearch | 1 | 1 | 1 | 0 | 0 | **3** | Backlog (DEGRADED + RGPD borderline) |
| 2.8 | ipqualityscore | 1 | 1 | 1 | 1 | 1 | **5** | Backlog (paid scaling concern) |
| 2.9 | dehashed_phone | 0 | 0 | 1 | 1 | 0 | **2** | Backlog (paid + RGPD HIGH) |
| 2.10 | leakcheck_phone | 0 | 0 | 1 | 1 | 1 | **3** | Backlog (paid-only for phone input) |
| 2.11 | intelx_phone | 0 | 0 | 1 | 1 | 1 | **3** | Backlog (paid) |
| 2.12 | wa_me_existence_check | 1 | 1 | 1 | 0 | 0 | **3** | Backlog conditional (operator sign-off only) |
| 2.13 | t_me_existence_check | 1 | 1 | 1 | 0 | 0 | **3** | Backlog conditional (operator sign-off only) |
| 2.14 | viber_existence_check | 1 | 1 | 1 | 0 | 0 | **3** | Backlog conditional (operator sign-off only) |
| 2.15 | google_phonebook_dork | 0 | 0 | 0 | **0** | 0 | **0** | REJECTED (S218 empirical: PhoneBook operator dead since 2021) |
| 2.16 | intelx_telephone_tool | 1 | 1 | 0 | 1 | 1 | **4** | Backlog (low quality vs paid API) |

**LOCKED short-list** (mechanically derived from score ≥ 4, with §0.1 §0.2
filter for "actually useful in EU corpus"):
1. numverify_phone (5)
2. veriphone_phone (5)
3. api_ninjas_phone (5)
4. abstractapi_phone (5)
<!-- 5. google_phonebook_dork removed per S218 — see §2.15 + §7.1 -->

Sources scoring 5 but **deferred from MVP** with reasons:
- `ovh_telecom_lookup` — FR landline only, low yield in mixed-corpus tests
- `numlookup` — US-centric, medium bot risk warrants pilot before fleet add
- `ipqualityscore` — fraud-score field is valuable but paid scaling
  curve needs operator budget decision
- `truepeoplesearch` — degraded status drops effective score

---

## 4. RGPD posture matrix

> **Informational only. Not legal advice. Operator is responsible for LIA
> documentation per active campaign. Luxembourg CNPD is the supervisory
> authority of record.**

| Source category | Lawful basis under GDPR (informational) | Notes |
|---|---|---|
| **Validator (carrier/line-type)** | Art 6(1)(f) legitimate interest; recital 49 (network security) | Plausibly tenable for fraud-prevention scope. Carrier-metadata alone is technical enrichment of an existing finding. LIA per campaign recommended. The four §0.1 picks (numverify / veriphone / api_ninjas / abstractapi) live in this category. |
| **Reverse lookup people-search** | Art 6(1)(f) but balancing test tighter | Subject-identifying. xposeTIP's transparency-empowerment ethic is the strongest defense — surface result to subject themselves (Play 1) before any operator use. Document subject-rights pathway prominently. EU-subject coverage is weak for most §2 picks; US-corpus exposure is the dominant practical surface. |
| **Breach / leak DB** | Art 6(1)(f) for fraud prevention | Source legality varies per breach. DeHashed includes stolen-data sets (e.g. Collection #1) — query / ingestion of those is legally separate from breach-research purpose. IntelX's curation is more conservative. LeakCheck mid-range. Operator-level decision per source. |
| **Social-presence check (wa.me / t.me / viber.click)** | Ambiguous | Platform ToS prohibit automated probing — that's a separate-from-RGPD vector but matters because if Meta / Telegram block xposeTIP IPs, the user experience degrades silently. RGPD-wise, the data point is metadata about platform presence, not message content; the surfaceable risk is "subject did not consent to being indexed by platform X via phone-number probing". HIGH risk for any meaningful volume. Operator decision required, not a mechanical pick. |
| **Dork-generator (Google etc)** | Art 6(1)(f) | Same posture as existing email / username dorks. Aggregating public web mentions is recital 49 tenable. Lowest novelty risk of any category. The `google_phonebook_dork` pick lives here. |

**Cross-cutting requirements** (apply to every shipped scraper, not per
category):
- Subject access (Art 15) must surface every finding the operator can see.
  No internal-only enrichment fields hidden from subjects.
- Subject deletion (Art 17) must fully purge — no soft-delete, no
  cache-residual. Existing `targets.py` delete flow already enforces this
  for findings; new scrapers inherit.
- Source URL must be preserved on every finding so subjects can challenge
  upstream data quality. Already enforced via `Finding.url` column.

---

## 5. Implementation effort estimate

Per LOCKED MVP candidate from §0.1, estimated for sprint scoping:

| # | Source | Effort | Files touched | API key acquisition | Pre-flight test query |
|---|---|---|---|---|---|
| 1 | numverify_phone | **low** | `scripts/seed_scrapers.py` (flip `enabled=True`, paste real key into `placeholder` slot) | apilayer.com → free account → dashboard → API key, ~5 min | `curl 'https://apilayer.net/api/validate?access_key=XXX&number=33612345678'` expects `{"valid": true, "country_code": "FR", ...}` |
| 2 | veriphone_phone | **low** | same | veriphone.io → free account → dashboard → API key, ~5 min | `curl 'https://api.veriphone.io/v2/verify?phone=33612345678&key=XXX'` expects `{"status":"success", "phone_valid": true, ...}` |
| 3 | api_ninjas_phone | **low** | same (no placeholder to swap — already real URL, just `enabled=True`) | api-ninjas.com → free account → dashboard → API key, ~5 min | `curl -H 'X-Api-Key: XXX' 'https://api.api-ninjas.com/v1/validatephone?number=33612345678'` expects `{"is_valid": true, "country": "France", ...}` |
| 4 | abstractapi_phone | **low** | same | abstractapi.com → free account → choose "Phone Validation" → API key, ~5 min | `curl 'https://phonevalidation.abstractapi.com/v1/?api_key=XXX&phone=33612345678'` expects `{"phone": "33612345678", "valid": true, ...}` |
| 5 | google_phonebook_dork | **low** | NEW seed entry mirroring existing `google_phone_dork` with added `&pb=r` flag in URL template | none | manual visit `https://www.google.com/search?q=%2B33612345678+OR+%2233612345678%22&pb=r` (will require captcha occasionally per existing dork-scraper limits) |

S217 scope: picks 1-4 in one sprint (single `seed_scrapers.py` edit, 4
`enabled=True` flips + key substitutions, single live test per scraper to
verify end-to-end finding materialization, single `audit_username_findings.py`-equivalent
re-run to confirm no regression). Estimated 30 minutes operator time + 1
hour CC time.

S218 scope: pick 5 (Google PhoneBook dork) as a separate sprint because
the `&pb=r` modifier may behave differently from Google's standard
search response and warrants its own test isolation. Estimated 30 minutes
total.

---

## 6. Out of scope (deferred or rejected)

- **Network-layer phone signals** (IMEI, IMSI, SS7) — not OSINT, requires
  telecom adjacency, out of project scope permanently.
- **Truecaller direct API** — no public API; the existing Truecaller-style
  reverse-engineered SDK approach is a regulatory minefield, deferred
  permanently.
- **Paid breach DBs without phone indexing** — out of scope, low
  cost/benefit.
- **BFP integration of phone signals as a new behavioural-radar axis** —
  per the existing CLAUDE.md principle established around S119, phone /
  crypto / legal-record findings enrich existing axes (`accounts`,
  `geo_spread`, `public_exposure`) rather than spawning new radar axes.
  No phone-specific axis planned.
- **Phone-specific UI Findings-tab category** — existing "Phone" pill
  (added in S180 / S203) suffices; no UI sprint planned post-S217.
- **Bulk phone enrichment endpoint** — not in current UX; surface remains
  per-target manual + automatic-via-cascade.

---

## 7. Re-evaluation log

Document subsequent empirical re-evals of LOCKED picks per S216 §0.4 intent.

### 7.1 S218 (2026-05-25) — `google_phonebook_dork` DEAD

- **Trigger**: pre-S218 spec audit, live curl from operator Mac.
- **Test**: `curl ?pb=r&btnG=Search+PhoneBook` → 1 grep hit, identified as
  URL-self-reference in HTML chrome, not a structured PhoneBook result
  block. If the feature were live, the count would be 5-20+ hits across
  distinct DOM nodes (telephone-icon class, local-results wrapper,
  phonebook-listing items).
- **Decision**: DEPRECATED. §2.15 flipped to status DEAD. Removed from
  §0.1 LOCKED. §3 score 4 → 0.
- **Generalizable lesson**: R&D cells claiming `2026 status: ACTIVE`
  without live validation are a known failure mode (S209 Maigret tranche
  2 precedent — 13% pass rate vs 80-90% expectation). Future R&D MUST
  live-test before LOCKING dork / scrape candidates.

---

## Changelog

- **v0** (S216, 2026-05-25) — initial draft. LOCKED 5 MVP picks (4
  validators re-enabled + new Google PhoneBook dork). RGPD posture
  matrix per category. Implementation effort estimate scopes S217-S218.
- **v0.1** (S218, 2026-05-25) — `google_phonebook_dork` DEPRECATED per
  empirical live-curl test. LOCKED count 5 → 4. §2.15 / §3 / §0.1
  updated. NEW §7 re-evaluation log appended.
