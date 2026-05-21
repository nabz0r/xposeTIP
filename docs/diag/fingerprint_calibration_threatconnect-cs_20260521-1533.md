# Fingerprint calibration diagnostic — threatconnect-cs

_Generated 2026-05-21 15:33 UTC · script S143-v1_

## A — Summary

- Workspace: **Threatconnect CS** (`threatconnect-cs`, id `bde2184b-7ab7-4a29-83b3-958033ad809d`)
- Total targets: **12**
- Targets with fingerprint key: **12**
- Targets with extractable axes (_extract_axes ≠ None): **12**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 12 | 0.382 | 0.266 | 0.067 | 0.933 | 0.0 | 0.0 | 0.072 | 0.383 | 0.828 |
| platforms | 12 | 0.375 | 0.258 | 0.080 | 0.900 | 0.0 | 0.0 | 0.080 | 0.390 | 0.804 |
| username_reuse | 12 | 0.125 | 0.062 | 0.100 | 0.300 | 0.0 | 0.0 | 0.100 | 0.100 | 0.270 |
| breaches | 12 | 0.417 | 0.217 | 0.000 | 0.600 | 16.7 | 0.0 | 0.000 | 0.400 | 0.600 |
| geo_spread | 12 | 0.473 | 0.211 | 0.250 | 1.000 | 0.0 | 8.3 | 0.268 | 0.450 | 0.895 |
| data_leaked | 12 | 0.043 | 0.052 | 0.000 | 0.160 | 41.7 | 0.0 | 0.000 | 0.040 | 0.148 |
| email_age | 12 | 0.150 | 0.176 | 0.000 | 0.460 | 50.0 | 0.0 | 0.000 | 0.050 | 0.424 |
| security | 12 | 0.062 | 0.217 | 0.000 | 0.750 | 91.7 | 0.0 | 0.000 | 0.000 | 0.525 |
| public_exposure | 12 | 0.040 | 0.094 | 0.000 | 0.250 | 83.3 | 0.0 | 0.000 | 0.000 | 0.245 |
| formal_records | 12 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| network_signature | 12 | 0.069 | 0.239 | 0.000 | 0.827 | 91.7 | 0.0 | 0.000 | 0.000 | 0.579 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ▄▆▂·▂█···▂
platforms          ▃▄▁··█···▁
username_reuse     ·█▁·······
breaches           ▃···██····
geo_spread         ··▂█▄▄▄··▂
data_leaked        █▁········
email_age          █▁▂▂▁·····
security           █······ ··
public_exposure    █·▁·······
formal_records     █·········
network_signature  █······· ·
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=60) | 12 | 22.917 | 15.957 | 4.000 | 56.000 | 0.0 | 4.300 | 23.000 | 49.700 |
| platforms (`platforms`, max=50) | 12 | 18.750 | 12.920 | 4.000 | 45.000 | 0.0 | 4.000 | 19.500 | 40.200 |
| username_reuse (`username_reuse`, max=10) | 12 | 1.250 | 0.622 | 1.000 | 3.000 | 0.0 | 1.000 | 1.000 | 2.700 |
| breaches (`breaches`, max=5) | 12 | 2.083 | 1.084 | 0.000 | 3.000 | 0.0 | 0.000 | 2.000 | 3.000 |
| geo_spread (`geo_spread`, max=5) | 12 | 2.383 | 1.111 | 1.250 | 5.250 | 8.3 | 1.340 | 2.250 | 4.650 |
| data_leaked (`data_leaked`, max=25) | 12 | 1.083 | 1.311 | 0.000 | 4.000 | 0.0 | 0.000 | 1.000 | 3.700 |
| email_age (`email_age_years`, max=40) | 12 | 5.992 | 7.023 | 0.000 | 18.400 | 0.0 | 0.000 | 2.000 | 16.960 |
| security (`security_weak`, max=4) | 12 | 0.250 | 0.866 | 0.000 | 3.000 | 0.0 | 0.000 | 0.000 | 2.100 |
| public_exposure (`public_exposure_raw`, max=1.0) | 12 | 0.040 | 0.094 | 0.000 | 0.250 | 0.0 | 0.000 | 0.000 | 0.245 |
| formal_records (`formal_records_raw`, max=5) | 12 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| network_signature (`network_signature_raw`, max=1.0) | 12 | 0.069 | 0.239 | 0.000 | 0.827 | 0.0 | 0.000 | 0.000 | 0.579 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ▄▆▂·▂█···▂
platforms          ▃▄▁··█···▁
username_reuse     ·█  ······
breaches           ▃···█·█···
geo_spread         ··▂█▄▄▄··▂
data_leaked        █▁········
email_age          █▁▂▂▁·····
security           █······ ··
public_exposure    █·▁·······
formal_records     █·········
network_signature  █······· ·
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 10 | 83.3% |
| 5 | 6 | 50.0% |
| 7 | 1 | 8.3% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **66** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.765 · stdev = 0.246

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 55 | 83.33% |
| 0.6 | 55 | 83.33% |
| 0.7 | 48 | 72.73% |
| 0.8 | 40 | 60.61% |
| 0.9 | 27 | 40.91% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ··▂ ··▂▂▃█
```

**Threshold sanity:** 72.73% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 0.996 | `mbivolaru@threatconnect.com` | `rczintos@threatconnect.com` | breaches, geo_spread, accounts |
| 2 | 0.994 | `cpugalis@threatconnect.com` | `ckeppie@threatconnect.com` | breaches, geo_spread, accounts |
| 3 | 0.994 | `cpugalis@threatconnect.com` | `rczintos@threatconnect.com` | breaches, geo_spread, accounts |
| 4 | 0.994 | `cpugalis@threatconnect.com` | `mbivolaru@threatconnect.com` | breaches, geo_spread, platforms |
| 5 | 0.992 | `ckeppie@threatconnect.com` | `mbivolaru@threatconnect.com` | breaches, geo_spread, platforms |
| 6 | 0.989 | `ckeppie@threatconnect.com` | `rczintos@threatconnect.com` | breaches, geo_spread, accounts |
| 7 | 0.985 | `wmoore@threatconnect.com` | `mbrash@threatconnect.com` | geo_spread, accounts, platforms |
| 8 | 0.972 | `pbetancourt@threatconnect.com` | `mbrash@threatconnect.com` | breaches, geo_spread, platforms |
| 9 | 0.971 | `ewray@threatconnect.com` | `mbrash@threatconnect.com` | breaches, accounts, platforms |
| 10 | 0.967 | `ewray@threatconnect.com` | `wmoore@threatconnect.com` | accounts, geo_spread, platforms |
| 11 | 0.963 | `adelacruz@threatconnect.com` | `wmoore@threatconnect.com` | accounts, platforms, geo_spread |
| 12 | 0.962 | `adelacruz@threatconnect.com` | `mbrash@threatconnect.com` | accounts, platforms, geo_spread |
| 13 | 0.954 | `pbetancourt@threatconnect.com` | `ewray@threatconnect.com` | breaches, geo_spread, platforms |
| 14 | 0.945 | `pbetancourt@threatconnect.com` | `wmoore@threatconnect.com` | geo_spread, platforms, accounts |
| 15 | 0.944 | `cpugalis@threatconnect.com` | `ewray@threatconnect.com` | breaches, geo_spread, accounts |
| 16 | 0.940 | `adelacruz@threatconnect.com` | `pbetancourt@threatconnect.com` | platforms, accounts, geo_spread |
| 17 | 0.934 | `ewray@threatconnect.com` | `ckeppie@threatconnect.com` | breaches, geo_spread, accounts |
| 18 | 0.927 | `cpugalis@threatconnect.com` | `mbrash@threatconnect.com` | breaches, geo_spread, accounts |
| 19 | 0.927 | `adelacruz@threatconnect.com` | `ewray@threatconnect.com` | platforms, accounts, geo_spread |
| 20 | 0.916 | `pbetancourt@threatconnect.com` | `cpugalis@threatconnect.com` | breaches, geo_spread, accounts |

## G — Auto-flagged observations

- starved: `security` is zero for 91.7% of fingerprints — data plumbing or AXIS_MAX too high
- starved: `public_exposure` is zero for 83.3% of fingerprints — data plumbing or AXIS_MAX too high
- starved: `formal_records` is zero for 100.0% of fingerprints — data plumbing or AXIS_MAX too high
- starved: `network_signature` is zero for 91.7% of fingerprints — data plumbing or AXIS_MAX too high
- similarity threshold sanity: 72.73% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 1 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
