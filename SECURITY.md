# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities by email to: **`contact@redbird.co.com`**

Subject line: `[SECURITY] <short description>`

Please include:
- The version of xposeTIP affected (commit SHA preferred, or release tag)
- A description of the vulnerability and its impact
- Steps to reproduce, if possible
- Any mitigations you have already identified

## What to expect

- Acknowledgement within **3 business days** (Europe / Luxembourg time)
- Initial assessment and severity rating within **7 business days**
- Coordinated disclosure timeline: typically 90 days from acknowledgement, faster for critical issues

We follow responsible disclosure principles. Please **do not** disclose vulnerabilities publicly until we have coordinated a release.

## Out of scope

The following are NOT considered vulnerabilities for the purpose of this policy:
- Findings from automated scanning tools without a working exploit
- Theoretical issues without a demonstrated impact on confidentiality, integrity, or availability
- Issues in dependencies of xposeTIP (please report those upstream)
- Self-XSS, denial of service via resource exhaustion (rate limiting is a known operational concern, not a vuln)

## Acknowledgement

Researchers who report valid vulnerabilities are acknowledged in release notes unless they prefer to remain anonymous. We do not currently offer a bug bounty, but we appreciate responsible disclosure.

## Public disclosure

After a fix is released and deployed, we will publish a security advisory via GitHub Security Advisories with appropriate CVE assignment if applicable.
