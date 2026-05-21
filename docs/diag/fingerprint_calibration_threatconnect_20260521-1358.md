# Fingerprint calibration diagnostic — threatconnect

_Generated 2026-05-21 13:58 UTC · script S143-v1_

## A — Summary

- Workspace: **Threatconnect** (`threatconnect`, id `99fbe6bb-2209-4b48-8810-da1711751988`)
- Total targets: **12**
- Targets with fingerprint key: **12**
- Targets with extractable axes (_extract_axes ≠ None): **12**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 12 | 0.894 | 0.210 | 0.400 | 1.000 | 0.0 | 75.0 | 0.440 | 1.000 | 1.000 |
| platforms | 12 | 0.883 | 0.221 | 0.400 | 1.000 | 0.0 | 75.0 | 0.430 | 1.000 | 1.000 |
| username_reuse | 12 | 0.250 | 0.090 | 0.200 | 0.400 | 0.0 | 0.0 | 0.200 | 0.200 | 0.400 |
| breaches | 12 | 0.467 | 0.246 | 0.000 | 0.800 | 16.7 | 0.0 | 0.000 | 0.600 | 0.740 |
| geo_spread | 12 | 0.379 | 0.234 | 0.250 | 1.000 | 0.0 | 8.3 | 0.250 | 0.250 | 0.895 |
| data_leaked | 12 | 0.302 | 0.223 | 0.000 | 0.750 | 16.7 | 0.0 | 0.000 | 0.312 | 0.675 |
| email_age | 12 | 0.674 | 0.414 | 0.000 | 1.000 | 16.7 | 8.3 | 0.000 | 0.873 | 0.986 |
| security | 12 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| public_exposure | 12 | 0.013 | 0.046 | 0.000 | 0.158 | 91.7 | 0.0 | 0.000 | 0.000 | 0.111 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ····  ·· █
platforms          ····   ··█
username_reuse     ··█·▂·····
breaches           ▂···▄█··▁·
geo_spread         ··█·▂·▁··▁
data_leaked        ▅▅▅█·▅·▂··
email_age          ▄·····▁·▄█
security           █·········
public_exposure    █ ········
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=15) | 12 | 23.167 | 12.748 | 6.000 | 45.000 | 75.0 | 6.600 | 20.500 | 43.500 |
| platforms (`platforms`, max=10) | 12 | 18.833 | 11.622 | 4.000 | 38.000 | 75.0 | 4.300 | 17.500 | 37.100 |
| username_reuse (`username_reuse`, max=5) | 12 | 1.250 | 0.452 | 1.000 | 2.000 | 0.0 | 1.000 | 1.000 | 2.000 |
| breaches (`breaches`, max=5) | 12 | 2.333 | 1.231 | 0.000 | 4.000 | 0.0 | 0.000 | 3.000 | 3.700 |
| geo_spread (`geo_spread`, max=5) | 12 | 2.000 | 1.485 | 1.250 | 6.250 | 8.3 | 1.250 | 1.250 | 5.350 |
| data_leaked (`data_leaked`, max=8) | 12 | 2.417 | 1.782 | 0.000 | 6.000 | 0.0 | 0.000 | 2.500 | 5.400 |
| email_age (`email_age_years`, max=15) | 12 | 10.358 | 6.465 | 0.000 | 17.900 | 8.3 | 0.000 | 13.100 | 16.820 |
| security (`security_weak`, max=4) | 12 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 12 | 0.013 | 0.046 | 0.000 | 0.158 | 0.0 | 0.000 | 0.000 | 0.111 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ····  ·· █
platforms          ····  · ·█
username_reuse     ··█·▂·····
breaches           ▂···▄·█·▁·
geo_spread         ··█·▂·▁··▁
data_leaked        ▅▅▅█·▅·▂··
email_age          ▄·····▁·▄█
security           █·········
public_exposure    █ ········
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 12 | 100.0% |
| 5 | 12 | 100.0% |
| 7 | 7 | 58.3% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **66** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.876 · stdev = 0.101

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 66 | 100.00% |
| 0.6 | 66 | 100.00% |
| 0.7 | 62 | 93.94% |
| 0.8 | 49 | 74.24% |
| 0.9 | 33 | 50.00% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ······ ▃▃█
```

**Threshold sanity:** 93.94% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 0.992 | `jjacobs@threatconnect.com` | `dtineo@threatconnect.com` | accounts, platforms, email_age |
| 2 | 0.991 | `tbhullar@threatconnect.com` | `hbrandon@threatconnect.com` | accounts, platforms, email_age |
| 3 | 0.990 | `moblack@threatconnect.com` | `btomes@threatconnect.com` | accounts, platforms, email_age |
| 4 | 0.990 | `jjacobs@threatconnect.com` | `tbhullar@threatconnect.com` | accounts, platforms, email_age |
| 5 | 0.988 | `dtineo@threatconnect.com` | `hbrandon@threatconnect.com` | accounts, platforms, email_age |
| 6 | 0.985 | `tbhullar@threatconnect.com` | `btomes@threatconnect.com` | accounts, platforms, email_age |
| 7 | 0.985 | `dtineo@threatconnect.com` | `tbhullar@threatconnect.com` | accounts, platforms, email_age |
| 8 | 0.984 | `hbrandon@threatconnect.com` | `jmcfadyen@threatconnect.com` | accounts, platforms, email_age |
| 9 | 0.983 | `tbhullar@threatconnect.com` | `jmcfadyen@threatconnect.com` | accounts, platforms, email_age |
| 10 | 0.978 | `jmcfadyen@threatconnect.com` | `btomes@threatconnect.com` | accounts, platforms, email_age |
| 11 | 0.977 | `jjacobs@threatconnect.com` | `hbrandon@threatconnect.com` | accounts, platforms, email_age |
| 12 | 0.972 | `asalcedo@threatconnect.com` | `moblack@threatconnect.com` | accounts, platforms, email_age |
| 13 | 0.970 | `dtineo@threatconnect.com` | `byelamanchili@threatconnect.com` | email_age, accounts, platforms |
| 14 | 0.967 | `hbrandon@threatconnect.com` | `btomes@threatconnect.com` | accounts, platforms, email_age |
| 15 | 0.967 | `jjacobs@threatconnect.com` | `btomes@threatconnect.com` | accounts, platforms, email_age |
| 16 | 0.967 | `dtineo@threatconnect.com` | `jmcfadyen@threatconnect.com` | accounts, platforms, email_age |
| 17 | 0.966 | `moblack@threatconnect.com` | `tbhullar@threatconnect.com` | accounts, platforms, email_age |
| 18 | 0.962 | `moblack@threatconnect.com` | `jmcfadyen@threatconnect.com` | accounts, platforms, email_age |
| 19 | 0.961 | `jjacobs@threatconnect.com` | `jmcfadyen@threatconnect.com` | accounts, platforms, email_age |
| 20 | 0.959 | `jjacobs@threatconnect.com` | `byelamanchili@threatconnect.com` | email_age, accounts, platforms |

## G — Auto-flagged observations

- saturation: `accounts` is 75.0% saturated — AXIS_MAX[`accounts`]=15 likely too low
- saturation: `platforms` is 75.0% saturated — AXIS_MAX[`platforms`]=10 likely too low
- starved: `security` is zero for 100.0% of fingerprints — data plumbing or AXIS_MAX too high
- starved: `public_exposure` is zero for 91.7% of fingerprints — data plumbing or AXIS_MAX too high
- saturation cause confirmed: `accounts` raw ≥ AXIS_MAX (=15) in 75.0% of fingerprints
- saturation cause confirmed: `platforms` raw ≥ AXIS_MAX (=10) in 75.0% of fingerprints
- similarity threshold sanity: 93.94% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 7 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
