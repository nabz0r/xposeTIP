# QA Reports

This folder collects manual QA runs and forensic pipeline audits.

Naming convention: `<type>_<YYYY-MM-DD>.md` (or `<type>_<YYYY-MM-DD>_<sprints>.md` if multiple same-day runs).

## Protocols

- `SMOKE_PROTOCOL.md` — Conventions for UX smoke runs (skip-if-recent rule, multi-layer evidence, mandatory sections)

## History

- `qa_2026-05-20.md` — Initial post-S122a UI walkthrough (Playwright MCP, 14 screenshots)
- `forensic_2026-05-20.md` — Forensic E2E pipeline audit on real targets (nabz0r@, nabilukson@); surfaced varchar(500) overflow, name resolution failures, dead name-input scrapers
- `forensic_round_2_2026-05-21.md` — R2
- `forensic_round_3_2026-05-22.md` — R3
- `forensic_round_4_2026-05-21.md` — R4 (5/34 Friends sampling, post-S131 + S132 health check)
- `ux_smoke_2026-05-21_s134_s135_s136.md` — UX smoke after S134 + S135 + S136 chain (Camelia Belab, 11/12 PASS)
- `screenshots_2026-05-20/` + `screenshots_2026-05-21/` — Screenshots captured during the corresponding runs
