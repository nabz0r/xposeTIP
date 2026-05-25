# S218 — Rescan picks

| target_id | email | workspace | phones | rationale |
|---|---|---|---|---|
| 05ce9d2c-5abb-4db2-87f2-f5a9f2635fe5 | gnienlnaha@yahoo.fr | quentin | 1 (+33612345678) | **only target in entire corpus** with `profile_data.phones[]` populated. Spec asked for 3-5 picks across diverse workspaces; corpus reality is 1. This is itself the empirical signal: corpus phone diversity essentially nil pre-S217. |

**Honest constraint note.** Query against `targets WHERE profile_data ? 'phones' AND jsonb_array_length(profile_data->'phones') > 0`
returned exactly 1 row across all 16 workspaces (`docs/qa/S218_target_candidates.txt`). S217's phone validators have working
dispatch infra but the corpus has no live phone exposure to validate against beyond the seeded test target. This is a real
signal for sprint prioritization downstream — see `S218_rescan_evidence.md` conclusion.
