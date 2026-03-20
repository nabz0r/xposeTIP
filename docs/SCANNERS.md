# Scanners Reference

## Overview

xpose has **25+ scanner modules** across 4 layers. Scanners are lazy-loaded via `importlib` — missing dependencies don't crash the worker.

## Scanner Registry

### Layer 1 — Passive Recon

| Scanner | ID | Category | Auth | Description |
|---------|----|----------|:----:|-------------|
| Email Validator | `email_validator` | metadata | - | MX records, disposable provider detection, format validation |
| Holehe | `holehe` | social | - | Email-to-account enumeration across 120+ services |
| Have I Been Pwned | `hibp` | breach | API key | Breach history lookup — names, dates, data types exposed |
| Sherlock | `sherlock` | social | - | Username search across 400+ social networks |
| Maigret | `maigret` | social | - | Username enumeration across 2500+ sites |
| GHunt | `ghunt` | metadata | Special | Google account metadata (requires DroidGuard patch) |
| h8mail | `h8mail` | breach | - | Email breach and credential leak search |
| Gravatar | `gravatar` | metadata | - | Profile, avatar, linked social accounts via email hash |
| Social Enricher | `social_enricher` | social | - | GitHub profile — name, bio, location, repos, followers |
| Email Reputation | `emailrep` | metadata | - | Reputation score, breach status, domain security (emailrep.io) |
| Epieos Google | `epieos` | metadata | - | Google account discovery — ID, name, photo (epieos.com) |
| FullContact | `fullcontact` | metadata | API key | Person enrichment — name, age, social profiles, company |
| GitHub Deep | `github_deep` | social | - | Full profile, events, gists, alternate emails from commits |
| Google Profile | `google_profile` | metadata | - | Gmail/Workspace detection, YouTube presence |
| Username Hunter | `username_hunter` | social | - | Username permutations across Reddit, Steam, Keybase, GitLab, etc. |
| Reverse Image | `reverse_image` | metadata | API key | Face matching via PimEyes + TinEye reverse search |

### Layer 2 — Public Databases

| Scanner | ID | Category | Auth | Description |
|---------|----|----------|:----:|-------------|
| DNS Intelligence | `dns_deep` | metadata | - | SPF, DMARC, DKIM, MX, NS — email security posture |
| WHOIS Lookup | `whois_lookup` | domain | - | Domain registration and ownership data |
| Free GeoIP | `geoip` | geolocation | - | IP geolocation via ip-api.com (45 req/min) |
| MaxMind GeoIP | `maxmind_geo` | geolocation | License | IP geolocation via local GeoLite2 database |
| Leaked Domains | `leaked_domains` | breach | - | Breach check via XposedOrNot — history, data types |
| Data Broker Check | `databroker_check` | data_broker | - | Spokeo, WhitePages, BeenVerified presence (US/UK/CA/AU) |
| Paste Monitor | `paste_monitor` | paste | - | Email/username search in public paste sites |
| VirusTotal | `virustotal` | metadata | API key | Domain reputation, malware, SSL certs, subdomains |
| Shodan | `shodan` | metadata | API key | Ports, services, OS, vulnerabilities |
| Intelligence X | `intelx` | breach | API key | Darkweb, paste, breach, document search |
| Hunter.io | `hunter` | metadata | API key | Email discovery, domain search, verification |
| Dehashed | `dehashed` | breach | API key | Credential search — hashed passwords, IPs, phones |

### Layer 3 — Self-Audit (OAuth)

| Scanner | ID | Category | Auth | Description |
|---------|----|----------|:----:|-------------|
| Google Audit | `google_audit` | app_permission | OAuth | Drive public files, Gmail forwarding, connected apps |
| Microsoft Audit | `microsoft_audit` | app_permission | OAuth | OAuth app grants, profile, device list |
| Exodus Tracker | `exodus_tracker` | tracking | - | App tracker detection via Exodus Privacy DB |
| Browser Audit | `browser_auditor` | browser | - | Extensions, cookies, tracking exposure |

### Layer 4 — Intelligence

| Analyzer | Category | Description |
|----------|----------|-------------|
| IP Analyzer | infrastructure | ASN lookup, reverse DNS, geolocation cross-reference |
| Domain Analyzer | security | Subdomain discovery, security headers, SSL analysis |
| Username Correlator | identity | Cross-platform username reuse and variation detection |
| Breach Correlator | breach | Password reuse risk, exposure timeline analysis |
| Risk Assessor | risk | Overall risk level + prioritized remediation actions |

## Implementation Status

- **Implemented**: 17 scanners with full `BaseScanner` classes in `SCANNER_REGISTRY`
- **Placeholder**: 8 modules seeded in DB, scanner class not yet built
- **Intelligence**: 5 analyzers in analysis pipeline (always runs post-scan)

Modules without a registered scanner are marked `implemented: false` in the API and excluded from scan dispatch.

## Adding a New Scanner

See [CONTRIBUTING.md](CONTRIBUTING.md).
