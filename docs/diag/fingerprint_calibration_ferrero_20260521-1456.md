# Fingerprint calibration diagnostic — ferrero

_Generated 2026-05-21 14:56 UTC · script S143-v1_

## A — Summary

- Workspace: **Ferrero** (`ferrero`, id `1d6f7b40-b038-4403-a54b-c8a32c026f95`)
- Total targets: **14**
- Targets with fingerprint key: **2**
- Targets with extractable axes (_extract_axes ≠ None): **2**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 2 | 0.500 | 0.047 | 0.467 | 0.533 | 0.0 | 0.0 | 0.421 | 0.500 | 0.579 |
| platforms | 2 | 0.380 | 0.085 | 0.320 | 0.440 | 0.0 | 0.0 | 0.236 | 0.380 | 0.524 |
| username_reuse | 2 | 0.400 | 0.283 | 0.200 | 0.600 | 0.0 | 0.0 | -0.080 | 0.400 | 0.880 |
| breaches | 2 | 0.800 | 0.000 | 0.800 | 0.800 | 0.0 | 0.0 | 0.800 | 0.800 | 0.800 |
| geo_spread | 2 | 0.480 | 0.240 | 0.310 | 0.650 | 0.0 | 0.0 | 0.072 | 0.480 | 0.888 |
| data_leaked | 2 | 0.380 | 0.537 | 0.000 | 0.760 | 50.0 | 0.0 | -0.532 | 0.380 | 1.292 |
| email_age | 2 | 0.275 | 0.389 | 0.000 | 0.550 | 50.0 | 0.0 | -0.385 | 0.275 | 0.935 |
| security | 2 | 0.500 | 0.354 | 0.250 | 0.750 | 0.0 | 0.0 | -0.100 | 0.500 | 1.100 |
| public_exposure | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| formal_records | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ····██····
platforms          ···██·····
username_reuse     ··█··█····
breaches           ········█·
geo_spread         ···█··█···
data_leaked        █······█··
email_age          █····█····
security           ··█····█··
public_exposure    █·········
formal_records     █·········
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=60) | 2 | 30.000 | 2.828 | 28.000 | 32.000 | 0.0 | 25.200 | 30.000 | 34.800 |
| platforms (`platforms`, max=50) | 2 | 19.000 | 4.243 | 16.000 | 22.000 | 0.0 | 11.800 | 19.000 | 26.200 |
| username_reuse (`username_reuse`, max=10) | 2 | 4.000 | 2.828 | 2.000 | 6.000 | 0.0 | -0.800 | 4.000 | 8.800 |
| breaches (`breaches`, max=5) | 2 | 4.000 | 0.000 | 4.000 | 4.000 | 0.0 | 4.000 | 4.000 | 4.000 |
| geo_spread (`geo_spread`, max=5) | 2 | 2.400 | 1.202 | 1.550 | 3.250 | 0.0 | 0.360 | 2.400 | 4.440 |
| data_leaked (`data_leaked`, max=25) | 2 | 9.500 | 13.435 | 0.000 | 19.000 | 0.0 | -13.300 | 9.500 | 32.300 |
| email_age (`email_age_years`, max=40) | 2 | 11.000 | 15.556 | 0.000 | 22.000 | 0.0 | -15.400 | 11.000 | 37.400 |
| security (`security_weak`, max=4) | 2 | 2.000 | 1.414 | 1.000 | 3.000 | 0.0 | -0.400 | 2.000 | 4.400 |
| public_exposure (`public_exposure_raw`, max=1.0) | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| formal_records (`formal_records_raw`, max=5) | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ····██····
platforms          ···██·····
username_reuse     ··█···█···
breaches           ········█·
geo_spread         ···█··█···
data_leaked        █······█··
email_age          █····█····
security           ··█····█··
public_exposure    █·········
formal_records     █·········
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 2 | 100.0% |
| 5 | 2 | 100.0% |
| 7 | 1 | 50.0% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **1** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.728 · stdev = 0.000

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 1 | 100.00% |
| 0.6 | 1 | 100.00% |
| 0.7 | 1 | 100.00% |
| 0.8 | 0 | 0.00% |
| 0.9 | 0 | 0.00% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ·······█··
```

**Threshold sanity:** 100.00% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 0.728 | `aurelija.duderyte@ferrero.com` | `nabz0r@gmail.com` | breaches, accounts, platforms |

## G — Auto-flagged observations

- similarity threshold sanity: 100.00% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 1 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
