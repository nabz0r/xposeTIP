# Fingerprint calibration diagnostic — ing-luxembourg

_Generated 2026-05-21 13:55 UTC · script S143-v1_

## A — Summary

- Workspace: **ING Luxembourg** (`ing-luxembourg`, id `b019afad-27d9-41cb-9bd5-1a25127e8429`)
- Total targets: **3**
- Targets with fingerprint key: **3**
- Targets with extractable axes (_extract_axes ≠ None): **3**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 3 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | 1.000 | 1.000 | 1.000 |
| platforms | 3 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | 1.000 | 1.000 | 1.000 |
| username_reuse | 3 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | 1.000 | 1.000 | 1.000 |
| breaches | 3 | 0.600 | 0.000 | 0.600 | 0.600 | 0.0 | 0.0 | 0.600 | 0.600 | 0.600 |
| geo_spread | 3 | 0.270 | 0.035 | 0.250 | 0.310 | 0.0 | 0.0 | 0.250 | 0.250 | 0.346 |
| data_leaked | 3 | 0.042 | 0.072 | 0.000 | 0.125 | 66.7 | 0.0 | 0.000 | 0.000 | 0.200 |
| email_age | 3 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | 1.000 | 1.000 | 1.000 |
| security | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| public_exposure | 3 | 0.033 | 0.058 | 0.000 | 0.100 | 66.7 | 0.0 | 0.000 | 0.000 | 0.160 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ·········█
platforms          ·········█
username_reuse     ·········█
breaches           ·····█····
geo_spread         ··█▄······
data_leaked        █▄········
email_age          ·········█
security           █·········
public_exposure    █▄········
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=15) | 3 | 31.667 | 1.528 | 30.000 | 33.000 | 100.0 | 28.800 | 32.000 | 33.600 |
| platforms (`platforms`, max=10) | 3 | 16.333 | 0.577 | 16.000 | 17.000 | 100.0 | 16.000 | 16.000 | 17.600 |
| username_reuse (`username_reuse`, max=5) | 3 | 7.000 | 0.000 | 7.000 | 7.000 | 100.0 | 7.000 | 7.000 | 7.000 |
| breaches (`breaches`, max=5) | 3 | 3.000 | 0.000 | 3.000 | 3.000 | 0.0 | 3.000 | 3.000 | 3.000 |
| geo_spread (`geo_spread`, max=5) | 3 | 1.350 | 0.173 | 1.250 | 1.550 | 0.0 | 1.250 | 1.250 | 1.730 |
| data_leaked (`data_leaked`, max=8) | 3 | 0.333 | 0.577 | 0.000 | 1.000 | 0.0 | 0.000 | 0.000 | 1.600 |
| email_age (`email_age_years`, max=15) | 3 | 26.500 | 0.000 | 26.500 | 26.500 | 100.0 | 26.500 | 26.500 | 26.500 |
| security (`security_weak`, max=4) | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 3 | 0.033 | 0.058 | 0.000 | 0.100 | 0.0 | 0.000 | 0.000 | 0.160 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ·········█
platforms          ·········█
username_reuse     ·········█
breaches           ······█···
geo_spread         ··█▄······
data_leaked        █▄········
email_age          ·········█
security           █·········
public_exposure    █▄········
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 3 | 100.0% |
| 5 | 3 | 100.0% |
| 7 | 1 | 33.3% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **3** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.998 · stdev = 0.002

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
| 1 | 1.000 | `marceau.muller@ing.lu` | `laura.morgana@ing.lu` | accounts, platforms, username_reuse |
| 2 | 0.997 | `marceau.muller@ing.lu` | `laura.morgano@ing.lu` | accounts, platforms, username_reuse |
| 3 | 0.997 | `laura.morgana@ing.lu` | `laura.morgano@ing.lu` | accounts, platforms, username_reuse |

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
- calibration thin: only 1 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
