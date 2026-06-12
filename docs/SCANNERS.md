# Intelligence Modules — xposeTIP v1.2.0

## Overview

xposeTIP has **28 active scanner modules** across 4 layers, **176 data-driven scrapers** (155 active by default)
across 11 categories, and **10 intelligence analyzers** that run post-scan.

## Scanner Modules (28)

### Layer 1 — Passive Recon (15)

| Scanner | ID | Description |
|---------|----|-------------|
| Email Validator | `email_validator` | MX records, disposable provider detection, format validation |
| Holehe | `holehe` | Email-to-account enumeration across 120+ services (vendored library) |
| Have I Been Pwned | `hibp` | Breach history lookup — names, dates, data types exposed |
| Sherlock | `sherlock` | Username search across 400+ social networks |
| Gravatar | `gravatar` | Profile, avatar, linked social accounts via email hash |
| Social Enricher | `social_enricher` | GitHub profile — name, bio, location, repos, followers |
| Email Reputation | `emailrep` | Reputation score, breach status, domain security |
| Epieos Google | `epieos` | Google account discovery — ID, name, photo |
| FullContact | `fullcontact` | Person enrichment — name, age, social profiles, company |
| GitHub Deep | `github_deep` | Full profile, events, gists, alternate emails from commits |
| GPG Keys | `gpg_keys` | GPG public-key lookup via keys.openpgp.org — V4 fingerprint + UID emails (feeds cascade) |
| Google Profile | `google_profile` | Gmail/Workspace detection, YouTube presence |
| Username Hunter | `username_hunter` | Username permutations across Reddit, Steam, Keybase, GitLab |
| Scraper Engine | `scraper_engine` | Runs all 155 active data-driven scrapers (176 defined, 21 disabled — see below) |
| Name Scraper Engine | `name_scraper_engine` | Meta-scanner — runs all enabled name-input scrapers against the resolved person name |

### Layer 2 — Public Databases (10)

| Scanner | ID | Description |
|---------|----|-------------|
| DNS Intelligence | `dns_deep` | SPF, DMARC, DKIM, MX, NS — email security posture |
| WHOIS Lookup | `whois_lookup` | Domain registration and ownership data |
| Free GeoIP | `geoip` | IP geolocation via ip-api.com |
| MaxMind GeoIP | `maxmind_geo` | IP geolocation via local GeoLite2 database |
| Leaked Domains | `leaked_domains` | Breach check via XposedOrNot |
| VirusTotal | `virustotal` | Domain reputation, malware, SSL certs, subdomains |
| Shodan | `shodan` | Ports, services, OS, vulnerabilities |
| Intelligence X | `intelx` | Darkweb, paste, breach, document search |
| Hunter.io | `hunter` | Email discovery, domain search, verification |
| Dehashed | `dehashed` | Credential search — hashed passwords, IPs, phones |

### Layer 3 — Self-Audit / OAuth (2)

| Scanner | ID | Description |
|---------|----|-------------|
| Google Audit | `google_audit` | Drive public files, Gmail forwarding, connected apps |
| Microsoft Audit | `microsoft_audit` | OAuth app grants, profile, device list |

### Layer 4 — Intelligence (1)

| Scanner | ID | Description |
|---------|----|-------------|
| Reverse Image | `reverse_image` | Face matching via PimEyes + TinEye reverse search |

> **Formerly listed, not in the dispatch registry:** maigret, ghunt, h8mail,
> databroker_check, paste_monitor, exodus_tracker, browser_auditor,
> intelligence, scraper_scanner. These rows documented planned or removed
> modules; they are not dispatchable via SCANNER_REGISTRY and were dropped
> from the nominal tables in S280. (The L4 intelligence analyzers are
> documented in their own section below — they run inside the pipeline,
> not as registry scanners.)

## Intelligence Analyzers (10)

| Analyzer | File | Description |
|----------|------|-------------|
| Behavioral Profiler | `behavioral_profiler.py` | 5 archetypes from cross-platform activity metrics |
| Breach Correlator | `breach_correlator.py` | Password reuse risk, exposure timeline |
| Code Leak Analyzer | `code_leak_analyzer.py` | GitHub Code Search, Gists, paste dump detection |
| Domain Analyzer | `domain_analyzer.py` | Subdomain discovery, security headers, SSL |
| Geo Consistency | `geo_consistency.py` | 6-signal geographic consistency analysis |
| IP Analyzer | `ip_analyzer.py` | ASN lookup, reverse DNS, geolocation cross-ref |
| Language Analyzer | `language_analyzer.py` | Language detection from free-text finding fields (lingua, ~25 languages) |
| Risk Assessor | `risk_assessor.py` | Overall risk level + prioritized remediation actions |
| Timezone Analyzer | `timezone_analyzer.py` | Timezone inference from activity timestamps |
| Username Correlator | `username_correlator.py` | Cross-platform username reuse detection |

## Scraper Engine (176 scrapers across 11 categories)

| Category | Count | Examples |
|----------|-------|---------|
| Social | 74 | Reddit, Steam, Telegram, Twitch, Pinterest, Strava, Snapchat, Threads, Bluesky, SoundCloud, Last.fm, + S197 Maigret picks: Issuu, Weebly, Calendly, Blogger, Giphy, Instructables, PayPal, Gumroad, iStock, Ko-fi, Wikidot, ReverbNation, Codecademy, HackerNoon, Speakerdeck, Wattpad, IFTTT, HackMD, OpenCollective, Steemit, + S209 Maigret tranche 2: DeviantArt, Scratch, Couchsurfing, Patreon... |
| Metadata | 19 | DNS DMARC, crt.sh, Gravatar (x3), disposable check, mailcheck, disify, github_timezone, gcal_public, google_phone_dork, duckduckgo_phone_dork, bing_phone_dork, yandex_phone_dork, hackernews_algolia_email_mentions... |
| People Search | 11 | WebMii, Google Scholar, Google Groups, npm, PyPI, Snapchat, Crunchbase... |
| Gaming | 10 | Steam, Chess.com, Roblox, Lichess, Xbox, RuneScape, MyAnimeList, Anilist, Speedrun, CodeWars |
| Public Exposure | 15 | GDELT, GNews, Google News RSS, OpenSanctions, Interpol Red Notices, OpenCorporates, LBR Luxembourg, Courtlistener (US federal courts), BODACC (FR), UK Gazette, arXiv, ORCID, DBLP, Semantic Scholar, AlienVault OTX |
| Breach | 9 | LeakCheck, IntelX, EmailRep, HackerTarget, XposedOrNot, LeakLookup... |
| Archive | 9 | Wayback Domain/Count/Profile + Wayback LinkedIn/Twitter/Instagram/Facebook/GitHub |
| Identity | 8 | Agify (age), Genderize (gender), Nationalize (nationality), NumVerify (phone), Veriphone (phone), API Ninjas (phone), AbstractAPI (phone), +1 |
| Code Leak | 3 | GitHub Code Search (email), GitHub Code Search (username), GitHub Gists |
| Financial | 14 | Blockchain.info, Blockchair, ChainAbuse, Etherscan, BscScan, Polygonscan, Snowtrace, Arbiscan, Optimistic, Basescan, Tronscan, SolanaFM, Mempool BTC/LTC/DOGE |
| Social Account | 2 | LinkedIn Profile, Proxycurl LinkedIn |

> **Note** : Les phone scrapers sont split en 2 catégories. `metadata` regroupe les dorks de moteurs de recherche (google, duckduckgo, bing, yandex) qui ne sont pas des APIs phone mais des requêtes web. `identity` regroupe les vrais validateurs API (NumVerify, Veriphone, API Ninjas, AbstractAPI) qui retournent carrier/line_type/country. Total phone-input scrapers = 8 (3 metadata-dork actifs + 1 dork `google_phone_dork` historique sous metadata + 4 identity API-key-required).

Scrapers are data-driven JSON configs stored in the database. Editable via Scrapers UI —
no code deploy needed. Each scraper has: URL template, extraction rules (regex/JSONPath),
rate limiting, finding output mapping (title, category, severity). Per-scraper module
attribution means each finding is tagged with the real scraper name (Sprint 89).

## Adding a New Module

See [CONTRIBUTING.md](CONTRIBUTING.md).
