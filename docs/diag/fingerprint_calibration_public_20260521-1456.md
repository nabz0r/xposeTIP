# Fingerprint calibration diagnostic — public

_Generated 2026-05-21 14:56 UTC · script S143-v1_

## A — Summary

- Workspace: **Quick Scans** (`public`, id `db21eec7-8125-4599-8a2f-ab52ab75d982`)
- Total targets: **3**
- Targets with fingerprint key: **3**
- Targets with extractable axes (_extract_axes ≠ None): **3**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 3 | 0.045 | 0.048 | 0.017 | 0.100 | 0.0 | 0.0 | 0.017 | 0.017 | 0.150 |
| platforms | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| username_reuse | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| breaches | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| geo_spread | 3 | 0.050 | 0.000 | 0.050 | 0.050 | 0.0 | 0.0 | 0.050 | 0.050 | 0.050 |
| data_leaked | 3 | 0.107 | 0.115 | 0.040 | 0.240 | 0.0 | 0.0 | 0.040 | 0.040 | 0.360 |
| email_age | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| security | 3 | 0.667 | 0.144 | 0.500 | 0.750 | 0.0 | 0.0 | 0.350 | 0.750 | 0.750 |
| public_exposure | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| formal_records | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           █▄········
platforms          █·········
username_reuse     █·········
breaches           █·········
geo_spread         █·········
data_leaked        █·▄·······
email_age          █·········
security           ·····▄·█··
public_exposure    █·········
formal_records     █·········
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=60) | 3 | 2.667 | 2.887 | 1.000 | 6.000 | 0.0 | 1.000 | 1.000 | 9.000 |
| platforms (`platforms`, max=50) | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| username_reuse (`username_reuse`, max=10) | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| breaches (`breaches`, max=5) | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| geo_spread (`geo_spread`, max=5) | 3 | 0.250 | 0.000 | 0.250 | 0.250 | 0.0 | 0.250 | 0.250 | 0.250 |
| data_leaked (`data_leaked`, max=25) | 3 | 2.667 | 2.887 | 1.000 | 6.000 | 0.0 | 1.000 | 1.000 | 9.000 |
| email_age (`email_age_years`, max=40) | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| security (`security_weak`, max=4) | 3 | 2.667 | 0.577 | 2.000 | 3.000 | 0.0 | 1.400 | 3.000 | 3.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| formal_records (`formal_records_raw`, max=5) | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           █▄········
platforms          █·········
username_reuse     █·········
breaches           █·········
geo_spread         █·········
data_leaked        █·▄·······
email_age          █·········
security           ·····▄·█··
public_exposure    █·········
formal_records     █·········
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 0 | 0.0% |
| 5 | 0 | 0.0% |
| 7 | 0 | 0.0% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **3** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.977 · stdev = 0.019

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 3 | 100.00% |
| 0.6 | 3 | 100.00% |
| 0.7 | 3 | 100.00% |
| 0.8 | 3 | 100.00% |
| 0.9 | 3 | 100.00% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ·········█
```

**Threshold sanity:** 100.00% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 0.999 | `bobyblues@gmail.com` | `loupn24@msn.com` | security, geo_spread, data_leaked |
| 2 | 0.969 | `jon.doe@gmail.com` | `loupn24@msn.com` | security, geo_spread, data_leaked |
| 3 | 0.962 | `bobyblues@gmail.com` | `jon.doe@gmail.com` | security, geo_spread, data_leaked |

## G — Auto-flagged observations

- similarity threshold sanity: 100.00% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 0 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
