# Fingerprint calibration diagnostic — threatconnect-cs

_Generated 2026-05-21 14:00 UTC · script S143-v1_

## A — Summary

- Workspace: **Threatconnect CS** (`threatconnect-cs`, id `bde2184b-7ab7-4a29-83b3-958033ad809d`)
- Total targets: **12**
- Targets with fingerprint key: **12**
- Targets with extractable axes (_extract_axes ≠ None): **12**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 12 | 0.800 | 0.277 | 0.267 | 1.000 | 0.0 | 58.3 | 0.287 | 1.000 | 1.000 |
| platforms | 12 | 0.850 | 0.232 | 0.400 | 1.000 | 0.0 | 58.3 | 0.400 | 1.000 | 1.000 |
| username_reuse | 12 | 0.250 | 0.124 | 0.200 | 0.600 | 0.0 | 0.0 | 0.200 | 0.200 | 0.540 |
| breaches | 12 | 0.417 | 0.217 | 0.000 | 0.600 | 16.7 | 0.0 | 0.000 | 0.400 | 0.600 |
| geo_spread | 12 | 0.522 | 0.260 | 0.250 | 1.000 | 0.0 | 8.3 | 0.250 | 0.450 | 0.955 |
| data_leaked | 12 | 0.135 | 0.164 | 0.000 | 0.500 | 41.7 | 0.0 | 0.000 | 0.125 | 0.463 |
| email_age | 12 | 0.694 | 0.420 | 0.000 | 1.000 | 25.0 | 8.3 | 0.000 | 0.883 | 0.986 |
| security | 12 | 0.062 | 0.217 | 0.000 | 0.750 | 91.7 | 0.0 | 0.000 | 0.000 | 0.525 |
| public_exposure | 12 | 0.040 | 0.094 | 0.000 | 0.250 | 83.3 | 0.0 | 0.000 | 0.000 | 0.245 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ··▁▁·▁▁▁·█
platforms          ····▂·▁·▁█
username_reuse     ··█·  ····
breaches           ▃···██····
geo_spread         ··█▂█▂▂·▅▂
data_leaked        █▆▁▁·▁····
email_age          ▄·······▆█
security           █······ ··
public_exposure    █·▁·······
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=15) | 12 | 22.917 | 15.957 | 4.000 | 56.000 | 58.3 | 4.300 | 23.000 | 49.700 |
| platforms (`platforms`, max=10) | 12 | 18.750 | 12.920 | 4.000 | 45.000 | 58.3 | 4.000 | 19.500 | 40.200 |
| username_reuse (`username_reuse`, max=5) | 12 | 1.250 | 0.622 | 1.000 | 3.000 | 0.0 | 1.000 | 1.000 | 2.700 |
| breaches (`breaches`, max=5) | 12 | 2.083 | 1.084 | 0.000 | 3.000 | 0.0 | 0.000 | 2.000 | 3.000 |
| geo_spread (`geo_spread`, max=5) | 12 | 2.633 | 1.342 | 1.250 | 5.250 | 8.3 | 1.250 | 2.250 | 4.950 |
| data_leaked (`data_leaked`, max=8) | 12 | 1.083 | 1.311 | 0.000 | 4.000 | 0.0 | 0.000 | 1.000 | 3.700 |
| email_age (`email_age_years`, max=15) | 12 | 10.675 | 6.579 | 0.000 | 18.200 | 8.3 | 0.000 | 13.250 | 17.030 |
| security (`security_weak`, max=4) | 12 | 0.250 | 0.866 | 0.000 | 3.000 | 0.0 | 0.000 | 0.000 | 2.100 |
| public_exposure (`public_exposure_raw`, max=1.0) | 12 | 0.040 | 0.094 | 0.000 | 0.250 | 0.0 | 0.000 | 0.000 | 0.245 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ··▁▁··▂▁·█
platforms          ····▂··▁▁█
username_reuse     ··█· · ···
breaches           ▃···█·█···
geo_spread         ··█▂█▂▂·▅▂
data_leaked        █▆▁▁·▁····
email_age          ▄·······▆█
security           █······ ··
public_exposure    █·▁·······
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 12 | 100.0% |
| 5 | 11 | 91.7% |
| 7 | 8 | 66.7% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **66** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.876 · stdev = 0.100

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 66 | 100.00% |
| 0.6 | 66 | 100.00% |
| 0.7 | 62 | 93.94% |
| 0.8 | 47 | 71.21% |
| 0.9 | 31 | 46.97% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ······▁▃▄█
```

**Threshold sanity:** 93.94% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 0.995 | `ewray@threatconnect.com` | `mbrash@threatconnect.com` | accounts, platforms, email_age |
| 2 | 0.993 | `cpugalis@threatconnect.com` | `mbrash@threatconnect.com` | accounts, platforms, email_age |
| 3 | 0.993 | `mbivolaru@threatconnect.com` | `rczintos@threatconnect.com` | email_age, platforms, accounts |
| 4 | 0.991 | `cpugalis@threatconnect.com` | `ewray@threatconnect.com` | accounts, platforms, email_age |
| 5 | 0.988 | `adelacruz@threatconnect.com` | `cpugalis@threatconnect.com` | accounts, platforms, email_age |
| 6 | 0.988 | `cpugalis@threatconnect.com` | `rczintos@threatconnect.com` | email_age, platforms, accounts |
| 7 | 0.987 | `adelacruz@threatconnect.com` | `rczintos@threatconnect.com` | email_age, platforms, accounts |
| 8 | 0.982 | `cpugalis@threatconnect.com` | `mbivolaru@threatconnect.com` | email_age, platforms, accounts |
| 9 | 0.982 | `adelacruz@threatconnect.com` | `mbrash@threatconnect.com` | accounts, platforms, email_age |
| 10 | 0.981 | `adelacruz@threatconnect.com` | `mbivolaru@threatconnect.com` | email_age, platforms, accounts |
| 11 | 0.981 | `wmoore@threatconnect.com` | `mbrash@threatconnect.com` | accounts, platforms, email_age |
| 12 | 0.981 | `pbetancourt@threatconnect.com` | `mbrash@threatconnect.com` | accounts, platforms, email_age |
| 13 | 0.980 | `ewray@threatconnect.com` | `rczintos@threatconnect.com` | email_age, platforms, accounts |
| 14 | 0.980 | `adelacruz@threatconnect.com` | `ewray@threatconnect.com` | accounts, platforms, email_age |
| 15 | 0.977 | `wmoore@threatconnect.com` | `ewray@threatconnect.com` | accounts, platforms, email_age |
| 16 | 0.977 | `rczintos@threatconnect.com` | `mbrash@threatconnect.com` | email_age, platforms, accounts |
| 17 | 0.973 | `pbetancourt@threatconnect.com` | `cpugalis@threatconnect.com` | accounts, platforms, email_age |
| 18 | 0.972 | `tmeyers@threatconnect.com` | `phoot@threatconnect.com` | platforms, geo_spread, accounts |
| 19 | 0.965 | `mbivolaru@threatconnect.com` | `mbrash@threatconnect.com` | email_age, platforms, accounts |
| 20 | 0.963 | `mbivolaru@threatconnect.com` | `ewray@threatconnect.com` | email_age, platforms, accounts |

## G — Auto-flagged observations

- saturation: `accounts` is 58.3% saturated — AXIS_MAX[`accounts`]=15 likely too low
- saturation: `platforms` is 58.3% saturated — AXIS_MAX[`platforms`]=10 likely too low
- starved: `security` is zero for 91.7% of fingerprints — data plumbing or AXIS_MAX too high
- starved: `public_exposure` is zero for 83.3% of fingerprints — data plumbing or AXIS_MAX too high
- saturation cause confirmed: `accounts` raw ≥ AXIS_MAX (=15) in 58.3% of fingerprints
- saturation cause confirmed: `platforms` raw ≥ AXIS_MAX (=10) in 58.3% of fingerprints
- similarity threshold sanity: 93.94% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 8 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
