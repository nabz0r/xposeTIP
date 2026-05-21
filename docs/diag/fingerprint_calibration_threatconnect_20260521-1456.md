# Fingerprint calibration diagnostic — threatconnect

_Generated 2026-05-21 14:56 UTC · script S143-v1_

## A — Summary

- Workspace: **Threatconnect** (`threatconnect`, id `99fbe6bb-2209-4b48-8810-da1711751988`)
- Total targets: **12**
- Targets with fingerprint key: **12**
- Targets with extractable axes (_extract_axes ≠ None): **12**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 12 | 0.386 | 0.213 | 0.100 | 0.750 | 0.0 | 0.0 | 0.110 | 0.342 | 0.725 |
| platforms | 12 | 0.377 | 0.232 | 0.080 | 0.760 | 0.0 | 0.0 | 0.086 | 0.350 | 0.742 |
| username_reuse | 12 | 0.125 | 0.045 | 0.100 | 0.200 | 0.0 | 0.0 | 0.100 | 0.100 | 0.200 |
| breaches | 12 | 0.467 | 0.246 | 0.000 | 0.800 | 16.7 | 0.0 | 0.000 | 0.600 | 0.740 |
| geo_spread | 12 | 0.346 | 0.212 | 0.250 | 1.000 | 0.0 | 8.3 | 0.250 | 0.280 | 0.823 |
| data_leaked | 12 | 0.097 | 0.071 | 0.000 | 0.240 | 16.7 | 0.0 | 0.000 | 0.100 | 0.216 |
| email_age | 12 | 0.159 | 0.151 | 0.000 | 0.453 | 25.0 | 0.0 | 0.000 | 0.173 | 0.409 |
| security | 12 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| public_exposure | 12 | 0.013 | 0.046 | 0.000 | 0.158 | 91.7 | 0.0 | 0.000 | 0.000 | 0.111 |
| formal_records | 12 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ·▄█▂▄·▄▂··
platforms          ▄████·█▄··
username_reuse     ·█▂·······
breaches           ▂···▄█··▁·
geo_spread         ··█▅▁····▁
data_leaked        █▆▁·······
email_age          █▄▃▁▁·····
security           █·········
public_exposure    █ ········
formal_records     █·········
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=60) | 12 | 23.167 | 12.748 | 6.000 | 45.000 | 0.0 | 6.600 | 20.500 | 43.500 |
| platforms (`platforms`, max=50) | 12 | 18.833 | 11.622 | 4.000 | 38.000 | 0.0 | 4.300 | 17.500 | 37.100 |
| username_reuse (`username_reuse`, max=10) | 12 | 1.250 | 0.452 | 1.000 | 2.000 | 0.0 | 1.000 | 1.000 | 2.000 |
| breaches (`breaches`, max=5) | 12 | 2.333 | 1.231 | 0.000 | 4.000 | 0.0 | 0.000 | 3.000 | 3.700 |
| geo_spread (`geo_spread`, max=5) | 12 | 1.833 | 1.412 | 1.250 | 6.250 | 8.3 | 1.250 | 1.400 | 4.990 |
| data_leaked (`data_leaked`, max=25) | 12 | 2.417 | 1.782 | 0.000 | 6.000 | 0.0 | 0.000 | 2.500 | 5.400 |
| email_age (`email_age_years`, max=40) | 12 | 6.342 | 6.025 | 0.000 | 18.100 | 0.0 | 0.000 | 6.900 | 16.360 |
| security (`security_weak`, max=4) | 12 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 12 | 0.013 | 0.046 | 0.000 | 0.158 | 0.0 | 0.000 | 0.000 | 0.111 |
| formal_records (`formal_records_raw`, max=5) | 12 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ·▅▅█▅·▅▂··
platforms          ▂▅▂█▅·▂▅··
username_reuse     ·█▂·······
breaches           ▂···▄·█·▁·
geo_spread         ··█▅▁····▁
data_leaked        █▆▁·······
email_age          █▄▁▃▁·····
security           █·········
public_exposure    █ ········
formal_records     █·········
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 11 | 91.7% |
| 5 | 9 | 75.0% |
| 7 | 2 | 16.7% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **66** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.818 · stdev = 0.163

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 63 | 95.45% |
| 0.6 | 54 | 81.82% |
| 0.7 | 48 | 72.73% |
| 0.8 | 45 | 68.18% |
| 0.9 | 32 | 48.48% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ···· ▂▁ ▃█
```

**Threshold sanity:** 72.73% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 0.995 | `tbhullar@threatconnect.com` | `jmcfadyen@threatconnect.com` | breaches, accounts, platforms |
| 2 | 0.986 | `moblack@threatconnect.com` | `hbrandon@threatconnect.com` | accounts, platforms, breaches |
| 3 | 0.982 | `jjacobs@threatconnect.com` | `hbrandon@threatconnect.com` | accounts, platforms, breaches |
| 4 | 0.979 | `moblack@threatconnect.com` | `jjacobs@threatconnect.com` | platforms, accounts, breaches |
| 5 | 0.976 | `hbrandon@threatconnect.com` | `jsjones@threatconnect.com` | accounts, platforms, breaches |
| 6 | 0.975 | `moblack@threatconnect.com` | `jmcfadyen@threatconnect.com` | breaches, accounts, platforms |
| 7 | 0.974 | `hbrandon@threatconnect.com` | `jmcfadyen@threatconnect.com` | breaches, accounts, platforms |
| 8 | 0.973 | `jjacobs@threatconnect.com` | `jmcfadyen@threatconnect.com` | breaches, accounts, platforms |
| 9 | 0.970 | `jjacobs@threatconnect.com` | `tbhullar@threatconnect.com` | breaches, accounts, platforms |
| 10 | 0.969 | `tbhullar@threatconnect.com` | `hbrandon@threatconnect.com` | breaches, accounts, platforms |
| 11 | 0.966 | `tbhullar@threatconnect.com` | `dtineo@threatconnect.com` | breaches, accounts, geo_spread |
| 12 | 0.961 | `moblack@threatconnect.com` | `tbhullar@threatconnect.com` | breaches, accounts, platforms |
| 13 | 0.959 | `byelamanchili@threatconnect.com` | `dtineo@threatconnect.com` | breaches, geo_spread, accounts |
| 14 | 0.958 | `moblack@threatconnect.com` | `jsjones@threatconnect.com` | accounts, platforms, breaches |
| 15 | 0.949 | `jmcfadyen@threatconnect.com` | `dtineo@threatconnect.com` | breaches, accounts, geo_spread |
| 16 | 0.949 | `dcole@threatconnect.com` | `akim@threatconnect.com` | geo_spread, accounts, username_reuse |
| 17 | 0.939 | `jjacobs@threatconnect.com` | `jsjones@threatconnect.com` | accounts, platforms, breaches |
| 18 | 0.937 | `tbhullar@threatconnect.com` | `btomes@threatconnect.com` | breaches, platforms, geo_spread |
| 19 | 0.935 | `btomes@threatconnect.com` | `dtineo@threatconnect.com` | breaches, accounts, geo_spread |
| 20 | 0.930 | `btomes@threatconnect.com` | `jsjones@threatconnect.com` | breaches, platforms, accounts |

## G — Auto-flagged observations

- starved: `security` is zero for 100.0% of fingerprints — data plumbing or AXIS_MAX too high
- starved: `public_exposure` is zero for 91.7% of fingerprints — data plumbing or AXIS_MAX too high
- starved: `formal_records` is zero for 100.0% of fingerprints — data plumbing or AXIS_MAX too high
- similarity threshold sanity: 72.73% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 2 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
