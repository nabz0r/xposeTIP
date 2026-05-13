# Contributing to xposeTIP

Thanks for your interest in contributing. xposeTIP is identity threat intelligence infrastructure — every contribution helps make the identity layer better.

## Before you start

By submitting a pull request to this repository, you agree to the [Contributor License Agreement](.github/CLA.md). The cla-assistant bot will guide you through signing it the first time you open a PR.

Why a CLA: xposeTIP is dual-licensed (AGPL-3.0 + commercial). The CLA grants the project owner the right to include your contribution in both license tracks. You retain copyright of your work.

## Development setup

See [INSTALL.md](docs/INSTALL.md) for the full local stack setup (Docker Compose, Postgres, Redis, Celery, FastAPI, React).

Quick start:

```bash
git clone https://github.com/nabz0r/xposeTIP.git
cd xposeTIP
cp .env.example .env  # edit values
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_modules.py
docker compose exec api python scripts/seed_scrapers.py
```

## Branching

- `main` is the only protected long-lived branch.
- Feature branches: `feat/<short-description>` or `fix/<short-description>`.
- Pull requests should be small and focused. Squash before merge.

## Commit messages

Format: `<type>: <Sprint NNN> — <Short description> (<version>)`

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

Example: `feat: Sprint 115 — Add LinkedIn scraper (v1.1.12)`

## Pull request checklist

- [ ] CLA signed (cla-assistant bot will check automatically)
- [ ] Tests pass locally (`docker compose exec api pytest`)
- [ ] Frontend builds clean (`cd dashboard && npm run build`)
- [ ] No new Python or npm dependencies without prior discussion in an issue
- [ ] No secrets, API keys, or personal data in code, fixtures, or test data
- [ ] No alembic migrations unless required (and documented in PR description)
- [ ] README / CLAUDE.md / docs updated if behavior changes

## Code style

- **Python**: type hints required for new functions. PEP 8 mostly (line length flexible).
- **JS/JSX**: existing style, Tailwind for CSS, functional components with hooks.
- **No commented-out code** in PRs. If a commented block is needed for context, explain in a code comment or PR description.

## What we won't accept

- New scrapers / data sources that violate ToS of the target platform.
- Code that breaks the Ethical OSINT pillars (see [Manifesto](dashboard/src/pages/Manifesto.jsx) — consent-first, transparency, purpose limitation).
- Features that exfiltrate user data to third parties without explicit consent.
- Dependencies introducing GPL-incompatible licenses (LGPL is fine; proprietary or "source-available" licenses are not).

## Reporting security issues

Do NOT open a public GitHub issue for security vulnerabilities. See [SECURITY.md](SECURITY.md) for the responsible disclosure process.

## Getting help

- Discussions: GitHub Discussions tab
- Bug reports: GitHub Issues
- Commercial / partnership inquiries: `contact@redbird.co.com`
