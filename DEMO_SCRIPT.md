# NEXUS 2026 DEMO SCRIPT — xpose Identity Threat Intelligence

**Time: 3 minutes**

---

## [0:00] Opening

> "Every employee in your company has a digital shadow.
> Let me show you what an attacker sees."

## [0:15] Quick Scan

- Type email in the landing page
- Click **Scan**
- Show real-time scan animation (modules completing one by one)
- Modules complete: Email Validator, DNS Intelligence, GeoIP, Holehe, GitHub Deep...

## [0:45] Profile Appears

> "In 30 seconds, we found 23 exposures across 7 sources."

- Profile header: real name, photo, email security badge
- Risk level banner: **HIGH** with score 42/100
- Accounts strip: Reddit, Steam, Keybase, Amazon, Spotify...
- Each with platform icon and "Secure" link

## [1:00] Findings Tab

> "DNS shows Microsoft 365 with weak DMARC — an attacker can spoof emails from this domain."

> "Username 'loupn' is reused across 3 platforms — credential stuffing risk."

- Show intelligence findings: username correlation, breach timeline, data exposure summary

## [1:15] Identity Graph

> "This is the identity graph — every node is a connection an attacker can exploit."

- Email at center, social accounts radiating out
- Username nodes connecting multiple platforms
- Breach nodes in red
- Click a node to see details

## [1:30] Google Account Audit

> "Let me show you what your own Google account is exposing."

- Click **Connect Google Account** in Accounts tab
- Authorize with Google OAuth
- Results appear: "12 Drive files shared publicly. 47 third-party apps connected."

> "This is what your employees don't know they're exposing."

## [2:00] Remediation Panel

> "xpose doesn't just find problems — it tells you exactly how to fix them."

- Show Top Actions Required:
  1. Change leaked passwords (3 breaches found)
  2. Enable 2FA on Amazon, Spotify
  3. Restrict 12 publicly shared Drive files
  4. Strengthen DMARC policy
- Each action has direct links to security settings pages

## [2:15] Organization View

> "For security teams: bulk import your company's emails, monitor exposure across the organization."

- Show organization page with multiple targets
- Comparative exposure scores
- "Generate compliance report" button

## [2:30] Closing

> "xpose is built in Luxembourg, GDPR compliant, runs on-premise.
> 25 intelligence scanners, source-scored findings, automated remediation.
> We're looking for pilot companies ready to audit their digital exposure."

## [3:00] Call to Action

- Show landing page URL
- **"Try it yourself: xpose.dev"**

---

## Technical Requirements for Demo

1. Pre-scan a demo email 24h before to have full results cached
2. Ensure Google OAuth is configured (test mode, 100 users)
3. Have a Google account with some shared Drive files
4. Stable internet connection (scanners hit external APIs)
5. Use Chrome in fullscreen, dark mode
6. Dashboard at `http://localhost:5173`

## Fallback Plan

If live scanning fails:
- Pre-scan results are cached in the database
- Navigate directly to the target detail page
- All findings, graph, and analysis are already computed
