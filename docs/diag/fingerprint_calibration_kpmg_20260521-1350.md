# Fingerprint calibration diagnostic — kpmg

_Generated 2026-05-21 13:50 UTC · script S143-v1_

## A — Summary

- Workspace: **KPMG** (`kpmg`, id `ad96117e-ffff-487b-a05b-119f2cccc976`)
- Total targets: **3**
- Targets with fingerprint key: **2**
- Targets with extractable axes (_extract_axes ≠ None): **2**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 2 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | 1.000 | 1.000 | 1.000 |
| platforms | 2 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | 1.000 | 1.000 | 1.000 |
| username_reuse | 2 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | 1.000 | 1.000 | 1.000 |
| breaches | 2 | 0.700 | 0.141 | 0.600 | 0.800 | 0.0 | 0.0 | 0.460 | 0.700 | 0.940 |
| geo_spread | 2 | 0.310 | 0.000 | 0.310 | 0.310 | 0.0 | 0.0 | 0.310 | 0.310 | 0.310 |
| data_leaked | 2 | 0.250 | 0.000 | 0.250 | 0.250 | 0.0 | 0.0 | 0.250 | 0.250 | 0.250 |
| email_age | 2 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | 1.000 | 1.000 | 1.000 |
| security | 2 | 0.250 | 0.000 | 0.250 | 0.250 | 0.0 | 0.0 | 0.250 | 0.250 | 0.250 |
| public_exposure | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ·········█
platforms          ·········█
username_reuse     ·········█
breaches           ·····█··█·
geo_spread         ···█······
data_leaked        ··█·······
email_age          ·········█
security           ··█·······
public_exposure    █·········
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=15) | 2 | 34.000 | 1.414 | 33.000 | 35.000 | 100.0 | 31.600 | 34.000 | 36.400 |
| platforms (`platforms`, max=10) | 2 | 17.000 | 0.000 | 17.000 | 17.000 | 100.0 | 17.000 | 17.000 | 17.000 |
| username_reuse (`username_reuse`, max=5) | 2 | 7.000 | 0.000 | 7.000 | 7.000 | 100.0 | 7.000 | 7.000 | 7.000 |
| breaches (`breaches`, max=5) | 2 | 3.500 | 0.707 | 3.000 | 4.000 | 0.0 | 2.300 | 3.500 | 4.700 |
| geo_spread (`geo_spread`, max=5) | 2 | 1.550 | 0.000 | 1.550 | 1.550 | 0.0 | 1.550 | 1.550 | 1.550 |
| data_leaked (`data_leaked`, max=8) | 2 | 2.000 | 0.000 | 2.000 | 2.000 | 0.0 | 2.000 | 2.000 | 2.000 |
| email_age (`email_age_years`, max=15) | 2 | 26.300 | 0.000 | 26.300 | 26.300 | 100.0 | 26.300 | 26.300 | 26.300 |
| security (`security_weak`, max=4) | 2 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 1.000 | 1.000 | 1.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ·········█
platforms          ·········█
username_reuse     ·········█
breaches           ······█·█·
geo_spread         ···█······
data_leaked        ··█·······
email_age          ·········█
security           ··█·······
public_exposure    █·········
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 2 | 100.0% |
| 5 | 2 | 100.0% |
| 7 | 2 | 100.0% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **1** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.996 · stdev = 0.000

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 1 | 100.00% |
| 0.6 | 1 | 100.00% |
| 0.7 | 1 | 100.00% |
| 0.8 | 1 | 100.00% |
| 0.9 | 1 | 100.00% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ·········█
```

**Threshold sanity:** 100.00% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 0.996 | `nicolas.huynen@kpmg.lu` | `benjamin.lavault@kpmg.lu` | accounts, platforms, username_reuse |

## G — Auto-flagged observations

- saturation: `accounts` is 100.0% saturated — AXIS_MAX[`accounts`]=15 likely too low
- saturation: `platforms` is 100.0% saturated — AXIS_MAX[`platforms`]=10 likely too low
- saturation: `username_reuse` is 100.0% saturated — AXIS_MAX[`username_reuse`]=5 likely too low
- saturation: `email_age` is 100.0% saturated — AXIS_MAX[`email_age_years`]=15 likely too low
- saturation cause confirmed: `accounts` raw ≥ AXIS_MAX (=15) in 100.0% of fingerprints
- saturation cause confirmed: `platforms` raw ≥ AXIS_MAX (=10) in 100.0% of fingerprints
- saturation cause confirmed: `username_reuse` raw ≥ AXIS_MAX (=5) in 100.0% of fingerprints
- saturation cause confirmed: `email_age` raw ≥ AXIS_MAX (=15) in 100.0% of fingerprints
- similarity threshold sanity: 100.00% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 2 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
