# S224 — BFP behavioral_hash_v1 cluster audit

_Generated 2026-05-25T15:23:54.486008Z_

**Total post-scan targets with behavioral_hash**: 155
**Distinct hash prefixes (16 hex chars)**: 18

## Verdict: `GENUINE_CLUSTER`

Top bucket holds 52.3% of all targets but axes are NOT uniformly near-zero. This is consistent with genuine cross-corporate behavioral similarity — the hash correctly groups behaviorally similar targets.

## Phase 1 — Top hash prefixes

| Rank | Prefix | Targets | % of total |
|------|--------|---------|-----------|
| 1 | `f9a5400a00000000` | 81 | 52.3% |
| 2 | `14e0de8400000000` | 37 | 23.9% |
| 3 | `3abb873e00000000` | 8 | 5.2% |
| 4 | `2950324300000000` | 4 | 2.6% |
| 5 | `9fb8098400000000` | 4 | 2.6% |
| 6 | `c1d6015d00000000` | 3 | 1.9% |
| 7 | `86e8fe3800000000` | 2 | 1.3% |
| 8 | `c291c37100000000` | 2 | 1.3% |
| 9 | `5473632000000000` | 2 | 1.3% |
| 10 | `3cb637af00000000` | 2 | 1.3% |

## Phase 2 — Top bucket `f9a5400a00000000` axis breakdown

Of the 3 axes that drive the hash (S166):

| Axis | n_present | n_null | mean | median | p10 | p90 | near_zero_pct |
|------|-----------|--------|------|--------|-----|-----|---------------|
| `public_exposure` | 69 | 12 | 0.0709 | 0.0 | 0.0 | 0.282 | 68.1% |
| `geo_spread` | 69 | 12 | 0.31 | 0.31 | 0.31 | 0.31 | 0.0% |
| `data_leaked` | 69 | 12 | 0.0307 | 0.0 | 0.0 | 0.12 | 79.7% |

### Sample members of top bucket (10 of 81)

| Workspace | Email | public_exposure | geo_spread | data_leaked |
|-----------|-------|----------------|-----------|-------------|
| bgl-bnp-paribas | `cedric.bossaert@bgl.lu` | 0.0 | 0.31 | 0.0 |
| nexus-2026 | `angelique.joyeux@lhc.lu` | 0.0 | 0.31 | 0.04 |
| threatconnect-cs | `tmeyers@threatconnect.com` | 0.0 | 0.31 | 0.04 |
| threatconnect-support | `rvasquez@threatconnect.com` | 0.0 | 0.31 | 0.0 |
| bgl-bnp-paribas | `romain.gerardin@bgl.lu` | 0.35 | 0.31 | 0.0 |
| bgl-bnp-paribas | `beatrice.belorgey@bgl.lu` | 0.0 | 0.31 | 0.0 |
| bgl-bnp-paribas | `tajana.zidani@bgl.lu` | 0.0 | 0.31 | 0.0 |
| friends | `abed.belaid@gmail.com` | 0.0 | 0.3 | 0.12 |
| bgl-bnp-paribas | `nicolas.otton@bgl.lu` | 0.282 | 0.31 | 0.0 |
| bgl-bnp-paribas | `sandrine.devuyst@bgl.lu` | 0.0 | 0.31 | 0.0 |

## Reco

Narrative win — the hash is doing what it's designed to do. Surface more aggressively in product (cluster explorer S225 candidate). No engine change.

---

_Audit script: `scripts/audit_bfp_clusters.py`. Read-only. Re-run after rescans / new corpus / engine changes to re-evaluate._