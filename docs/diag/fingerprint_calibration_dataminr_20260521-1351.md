# Fingerprint calibration diagnostic — dataminr

_Generated 2026-05-21 13:51 UTC · script S143-v1_

## A — Summary

- Workspace: **Dataminr** (`dataminr`, id `2ec3c06a-c3f4-4ccd-9838-ebfc647dc220`)
- Total targets: **9**
- Targets with fingerprint key: **9**
- Targets with extractable axes (_extract_axes ≠ None): **9**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 9 | 0.852 | 0.294 | 0.333 | 1.000 | 0.0 | 77.8 | 0.333 | 1.000 | 1.000 |
| platforms | 9 | 0.889 | 0.220 | 0.500 | 1.000 | 0.0 | 77.8 | 0.500 | 1.000 | 1.000 |
| username_reuse | 9 | 0.511 | 0.348 | 0.200 | 1.000 | 0.0 | 22.2 | 0.200 | 0.400 | 1.000 |
| breaches | 9 | 0.511 | 0.302 | 0.000 | 0.800 | 22.2 | 0.0 | 0.000 | 0.600 | 0.800 |
| geo_spread | 9 | 0.548 | 0.171 | 0.410 | 0.850 | 0.0 | 0.0 | 0.410 | 0.450 | 0.850 |
| data_leaked | 9 | 0.167 | 0.337 | 0.000 | 1.000 | 66.7 | 11.1 | 0.000 | 0.000 | 1.000 |
| email_age | 9 | 0.778 | 0.441 | 0.000 | 1.000 | 22.2 | 77.8 | 0.000 | 1.000 | 1.000 |
| security | 9 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| public_exposure | 9 | 0.028 | 0.083 | 0.000 | 0.250 | 88.9 | 0.0 | 0.000 | 0.000 | 0.250 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ···▂·····█
platforms          ·····▂···█
username_reuse     ··█·▂▂··▂▄
breaches           ▃····█··▃·
geo_spread         ····█▁·▃▁·
data_leaked        █▁·▁·····▁
email_age          ▂········█
security           █·········
public_exposure    █·▁·······
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=15) | 9 | 26.333 | 14.387 | 5.000 | 50.000 | 77.8 | 5.000 | 28.000 | 50.000 |
| platforms (`platforms`, max=10) | 9 | 19.111 | 11.263 | 5.000 | 40.000 | 77.8 | 5.000 | 17.000 | 40.000 |
| username_reuse (`username_reuse`, max=5) | 9 | 2.889 | 2.315 | 1.000 | 7.000 | 22.2 | 1.000 | 2.000 | 7.000 |
| breaches (`breaches`, max=5) | 9 | 2.556 | 1.509 | 0.000 | 4.000 | 0.0 | 0.000 | 3.000 | 4.000 |
| geo_spread (`geo_spread`, max=5) | 9 | 2.739 | 0.853 | 2.050 | 4.250 | 0.0 | 2.050 | 2.250 | 4.250 |
| data_leaked (`data_leaked`, max=8) | 9 | 1.667 | 3.640 | 0.000 | 11.000 | 11.1 | 0.000 | 0.000 | 11.000 |
| email_age (`email_age_years`, max=15) | 9 | 12.933 | 7.333 | 0.000 | 16.800 | 77.8 | 0.000 | 16.600 | 16.800 |
| security (`security_weak`, max=4) | 9 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 9 | 0.028 | 0.083 | 0.000 | 0.250 | 0.0 | 0.000 | 0.000 | 0.250 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ···▂·····█
platforms          ·····▂···█
username_reuse     ··█·▂·▂·▂▄
breaches           ▃·····█·▃·
geo_spread         ····█▁·▃▁·
data_leaked        █▁·▁·····▁
email_age          ▂········█
security           █·········
public_exposure    █·▁·······
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 9 | 100.0% |
| 5 | 7 | 77.8% |
| 7 | 4 | 44.4% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **36** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.859 · stdev = 0.108

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 36 | 100.00% |
| 0.6 | 36 | 100.00% |
| 0.7 | 33 | 91.67% |
| 0.8 | 22 | 61.11% |
| 0.9 | 18 | 50.00% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ······▁▄▁█
```

**Threshold sanity:** 91.67% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 1.000 | `regina.bonsu@dataminr.com` | `becki.bailey@dataminr.com` | accounts, platforms, username_reuse |
| 2 | 0.999 | `info@dataminr.com` | `dsouza@dataminr.com` | platforms, geo_spread, accounts |
| 3 | 0.991 | `kpoulsen@dataminr.com` | `rbasset@dataminr.com` | accounts, platforms, email_age |
| 4 | 0.989 | `regina.bonsu@dataminr.com` | `balaji.yelamanchili@dataminr.com` | accounts, platforms, email_age |
| 5 | 0.989 | `becki.bailey@dataminr.com` | `balaji.yelamanchili@dataminr.com` | accounts, platforms, email_age |
| 6 | 0.971 | `wbenner@dataminr.com` | `kpoulsen@dataminr.com` | accounts, platforms, email_age |
| 7 | 0.961 | `kpoulsen@dataminr.com` | `balaji.yelamanchili@dataminr.com` | accounts, platforms, email_age |
| 8 | 0.954 | `wbenner@dataminr.com` | `rbasset@dataminr.com` | accounts, platforms, email_age |
| 9 | 0.950 | `regina.bonsu@dataminr.com` | `kpoulsen@dataminr.com` | accounts, platforms, email_age |
| 10 | 0.947 | `becki.bailey@dataminr.com` | `kpoulsen@dataminr.com` | accounts, platforms, email_age |
| 11 | 0.944 | `tbailey@dataminr.com` | `wbenner@dataminr.com` | accounts, platforms, email_age |
| 12 | 0.927 | `wbenner@dataminr.com` | `balaji.yelamanchili@dataminr.com` | accounts, platforms, email_age |
| 13 | 0.926 | `balaji.yelamanchili@dataminr.com` | `rbasset@dataminr.com` | accounts, platforms, email_age |
| 14 | 0.923 | `tbailey@dataminr.com` | `kpoulsen@dataminr.com` | accounts, platforms, email_age |
| 15 | 0.909 | `regina.bonsu@dataminr.com` | `rbasset@dataminr.com` | accounts, platforms, email_age |
| 16 | 0.906 | `regina.bonsu@dataminr.com` | `wbenner@dataminr.com` | accounts, platforms, email_age |
| 17 | 0.905 | `becki.bailey@dataminr.com` | `wbenner@dataminr.com` | accounts, platforms, email_age |
| 18 | 0.905 | `becki.bailey@dataminr.com` | `rbasset@dataminr.com` | accounts, platforms, email_age |
| 19 | 0.884 | `tbailey@dataminr.com` | `rbasset@dataminr.com` | accounts, platforms, email_age |
| 20 | 0.880 | `tbailey@dataminr.com` | `balaji.yelamanchili@dataminr.com` | accounts, platforms, email_age |

## G — Auto-flagged observations

- saturation: `accounts` is 77.8% saturated — AXIS_MAX[`accounts`]=15 likely too low
- saturation: `platforms` is 77.8% saturated — AXIS_MAX[`platforms`]=10 likely too low
- saturation: `email_age` is 77.8% saturated — AXIS_MAX[`email_age_years`]=15 likely too low
- starved: `security` is zero for 100.0% of fingerprints — data plumbing or AXIS_MAX too high
- starved: `public_exposure` is zero for 88.9% of fingerprints — data plumbing or AXIS_MAX too high
- saturation cause confirmed: `accounts` raw ≥ AXIS_MAX (=15) in 77.8% of fingerprints
- saturation cause confirmed: `platforms` raw ≥ AXIS_MAX (=10) in 77.8% of fingerprints
- saturation cause confirmed: `username_reuse` raw ≥ AXIS_MAX (=5) in 22.2% of fingerprints
- saturation cause confirmed: `email_age` raw ≥ AXIS_MAX (=15) in 77.8% of fingerprints
- similarity threshold sanity: 91.67% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 4 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
