# Fingerprint calibration diagnostic — kpmg

_Generated 2026-05-21 21:02 UTC · script S143-v1_

## A — Summary

- Workspace: **KPMG** (`kpmg`, id `ad96117e-ffff-487b-a05b-119f2cccc976`)
- Total targets: **3**
- Targets with fingerprint key: **2**
- Targets with extractable axes (_extract_axes ≠ None): **2**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 2 | 0.567 | 0.023 | 0.550 | 0.583 | 0.0 | 0.0 | 0.527 | 0.567 | 0.606 |
| platforms | 2 | 0.340 | 0.000 | 0.340 | 0.340 | 0.0 | 0.0 | 0.340 | 0.340 | 0.340 |
| username_reuse | 2 | 0.700 | 0.000 | 0.700 | 0.700 | 0.0 | 0.0 | 0.700 | 0.700 | 0.700 |
| breaches | 2 | 0.700 | 0.141 | 0.600 | 0.800 | 0.0 | 0.0 | 0.460 | 0.700 | 0.940 |
| geo_spread | 2 | 0.310 | 0.000 | 0.310 | 0.310 | 0.0 | 0.0 | 0.310 | 0.310 | 0.310 |
| data_leaked | 2 | 0.080 | 0.000 | 0.080 | 0.080 | 0.0 | 0.0 | 0.080 | 0.080 | 0.080 |
| email_age | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| security | 2 | 0.250 | 0.000 | 0.250 | 0.250 | 0.0 | 0.0 | 0.250 | 0.250 | 0.250 |
| public_exposure | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| formal_records | 2 | 0.300 | 0.424 | 0.000 | 0.600 | 50.0 | 0.0 | -0.420 | 0.300 | 1.020 |
| network_signature | 2 | 0.817 | 0.001 | 0.816 | 0.818 | 0.0 | 0.0 | 0.815 | 0.817 | 0.819 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ·····█····
platforms          ···█······
username_reuse     ······█···
breaches           ·····█··█·
geo_spread         ···█······
data_leaked        █·········
email_age          █·········
security           ··█·······
public_exposure    █·········
formal_records     █····█····
network_signature  ········█·
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=60) | 2 | 34.000 | 1.414 | 33.000 | 35.000 | 0.0 | 31.600 | 34.000 | 36.400 |
| platforms (`platforms`, max=50) | 2 | 17.000 | 0.000 | 17.000 | 17.000 | 0.0 | 17.000 | 17.000 | 17.000 |
| username_reuse (`username_reuse`, max=10) | 2 | 7.000 | 0.000 | 7.000 | 7.000 | 0.0 | 7.000 | 7.000 | 7.000 |
| breaches (`breaches`, max=5) | 2 | 3.500 | 0.707 | 3.000 | 4.000 | 0.0 | 2.300 | 3.500 | 4.700 |
| geo_spread (`geo_spread`, max=5) | 2 | 1.550 | 0.000 | 1.550 | 1.550 | 0.0 | 1.550 | 1.550 | 1.550 |
| data_leaked (`data_leaked`, max=25) | 2 | 2.000 | 0.000 | 2.000 | 2.000 | 0.0 | 2.000 | 2.000 | 2.000 |
| email_age (`email_age_years`, max=40) | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| security (`security_weak`, max=4) | 2 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 1.000 | 1.000 | 1.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| formal_records (`formal_records_raw`, max=5) | 2 | 1.500 | 2.121 | 0.000 | 3.000 | 0.0 | -2.100 | 1.500 | 5.100 |
| network_signature (`network_signature_raw`, max=1.0) | 2 | 0.817 | 0.001 | 0.816 | 0.818 | 0.0 | 0.815 | 0.817 | 0.819 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ·····█····
platforms          ···█······
username_reuse     ·······█··
breaches           ······█·█·
geo_spread         ···█······
data_leaked        █·········
email_age          █·········
security           ··█·······
public_exposure    █·········
formal_records     █·····█···
network_signature  ········█·
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
- mean = 0.918 · stdev = 0.000

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
| 1 | 0.918 | `benjamin.lavault@kpmg.lu` | `nicolas.huynen@kpmg.lu` | network_signature, username_reuse, breaches |

## G — Auto-flagged observations

- similarity threshold sanity: 100.00% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 2 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
