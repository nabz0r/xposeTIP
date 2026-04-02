# Intelligence Modules — xposeTIP v1.1.10

## Overview

xposeTIP has **26 active scanner modules** across 4 layers, **126 data-driven scrapers**
across 12 categories, and **9 intelligence analyzers** that run post-scan.
5 scanner modules are disabled placeholders (maigret, h8mail, ghunt, paste_monitor, databroker_check).

## Scanner Modules (35)

### Layer 1 — Passive Recon (16)

| Scanner | ID | Description |
|---------|----|-------------|
| Email Validator | `email_validator` | MX records, disposable provider detection, format validation |
| Holehe | `holehe` | Email-to-account enumeration across 120+ services |
| Have I Been Pwned | `hibp` | Breach history lookup — names, dates, data types exposed |
| Sherlock | `sherlock` | Username search across 400+ social networks |
| Maigret | `maigret` | Username enumeration across 2500+ sites |
| GHunt | `ghunt` | Google account metadata (requires DroidGuard patch) |
| h8mail | `h8mail` | Email breach and credential leak search |
| Gravatar | `gravatar` | Profile, avatar, linked social accounts via email hash |
| Social Enricher | `social_enricher` | GitHub profile — name, bio, location, repos, followers |
| Email Reputation | `emailrep` | Reputation score, breach status, domain security |
| Epieos Google | `epieos` | Google account discovery — ID, name, photo |
| FullContact | `fullcontact` | Person enrichment — name, age, social profiles, company |
| GitHub Deep | `github_deep` | Full profile, events, gists, alternate emails from commits |
| Google Profile | `google_profile` | Gmail/Workspace detection, YouTube presence |
| Username Hunter | `username_hunter` | Username permutations across Reddit, Steam, Keybase, GitLab |
| Scraper Engine | `scraper_engine` | Runs all 120 data-driven scrapers (see below) |

### Layer 2 — Public Databases (12)

| Scanner | ID | Description |
|---------|----|-------------|
| DNS Intelligence | `dns_deep` | SPF, DMARC, DKIM, MX, NS — email security posture |
| WHOIS Lookup | `whois_lookup` | Domain registration and ownership data |
| Free GeoIP | `geoip` | IP geolocation via ip-api.com |
| MaxMind GeoIP | `maxmind_geo` | IP geolocation via local GeoLite2 database |
| Leaked Domains | `leaked_domains` | Breach check via XposedOrNot |
| Data Broker Check | `databroker_check` | Spokeo, WhitePages, BeenVerified presence |
| Paste Monitor | `paste_monitor` | Email/username search in public paste sites |
| VirusTotal | `virustotal` | Domain reputation, malware, SSL certs, subdomains |
| Shodan | `shodan` | Ports, services, OS, vulnerabilities |
| Intelligence X | `intelx` | Darkweb, paste, breach, document search |
| Hunter.io | `hunter` | Email discovery, domain search, verification |
| Dehashed | `dehashed` | Credential search — hashed passwords, IPs, phones |

### Layer 3 — Self-Audit / OAuth (4)

| Scanner | ID | Description |
|---------|----|-------------|
| Google Audit | `google_audit` | Drive public files, Gmail forwarding, connected apps |
| Microsoft Audit | `microsoft_audit` | OAuth app grants, profile, device list |
| Exodus Tracker | `exodus_tracker` | App tracker detection via Exodus Privacy DB |
| Browser Audit | `browser_auditor` | Extensions, cookies, tracking exposure |

### Layer 4 — Intelligence (3)

| Scanner | ID | Description |
|---------|----|-------------|
| Intelligence Pipeline | `intelligence` | Runs all 9 analyzers (see below) |
| Reverse Image | `reverse_image` | Face matching via PimEyes + TinEye reverse search |
| Scraper Scanner | `scraper_scanner` | Meta-scanner that dispatches all enabled scraper definitions |

## Intelligence Analyzers (9)

| Analyzer | File | Description |
|----------|------|-------------|
| Behavioral Profiler | `behavioral_profiler.py` | 5 archetypes from cross-platform activity metrics |
| Breach Correlator | `breach_correlator.py` | Password reuse risk, exposure timeline |
| Code Leak Analyzer | `code_leak_analyzer.py` | GitHub Code Search, Gists, paste dump detection |
| Domain Analyzer | `domain_analyzer.py` | Subdomain discovery, security headers, SSL |
| Geo Consistency | `geo_consistency.py` | 6-signal geographic consistency analysis |
| IP Analyzer | `ip_analyzer.py` | ASN lookup, reverse DNS, geolocation cross-ref |
| Risk Assessor | `risk_assessor.py` | Overall risk level + prioritized remediation actions |
| Timezone Analyzer | `timezone_analyzer.py` | Timezone inference from activity timestamps |
| Username Correlator | `username_correlator.py` | Cross-platform username reuse detection |

## Scraper Engine (126 scrapers across 12 categories)

| Category | Count | Examples |
|----------|-------|---------|
| Social | 51 | Reddit, Steam, Telegram, Twitch, Pinterest, Strava, Snapchat, Threads, Bluesky... |
| Metadata | 14 | DNS, WHOIS, Gravatar, crt.sh, disposable check, mailcheck, disify... |
| People Search | 11 | WebMii, Google Scholar, Google Groups, npm, PyPI... |
| Gaming | 10 | Steam, Chess.com, Roblox, Lichess, Xbox, RuneScape, MyAnimeList... |
| Breach | 9 | LeakCheck, IntelX, EmailRep, HackerTarget, XposedOrNot... |
| Archive | 9 | Wayback Domain, Wayback Count, Wayback LinkedIn/Twitter/Instagram... |
| Public Exposure | 7 | GDELT, GNews, Google News RSS, OpenSanctions, Interpol, OpenCorporates, LBR |
| Phone | 4 | NumVerify, Veriphone, Carrier Lookup, Google Phone Dork |
| Financial | 3 | Blockchain.info (BTC), Blockchair (multi-chain), ChainAbuse (scam flags) |
| Identity Estimation | 3 | Agify (age), Genderize (gender), Nationalize (nationality) |
| Code Leak | 3 | GitHub Code Search (email), GitHub Code Search (username), GitHub Gists |
| Social Account | 2 | Misc profile scrapers |

Scrapers are data-driven JSON configs stored in the database. Editable via Scrapers UI —
no code deploy needed. Each scraper has: URL template, extraction rules (regex/JSONPath),
rate limiting, finding output mapping (title, category, severity). Per-scraper module
attribution means each finding is tagged with the real scraper name (Sprint 89).

## Adding a New Module

See [CONTRIBUTING.md](CONTRIBUTING.md).
