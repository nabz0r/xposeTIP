# Fingerprint calibration diagnostic — default

_Generated 2026-05-21 14:06 UTC · script S143-v1_

## A — Summary

- Workspace: **Default** (`default`, id `32f8ec0e-d03e-4f79-9daa-4e2815fa0cbb`)
- Total targets: **13**
- Targets with fingerprint key: **13**
- Targets with extractable axes (_extract_axes ≠ None): **13**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 13 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | 1.000 | 1.000 | 1.000 |
| platforms | 13 | 0.992 | 0.028 | 0.900 | 1.000 | 0.0 | 92.3 | 0.940 | 1.000 | 1.000 |
| username_reuse | 13 | 0.892 | 0.290 | 0.000 | 1.000 | 7.7 | 84.6 | 0.240 | 1.000 | 1.000 |
| breaches | 13 | 0.585 | 0.191 | 0.200 | 0.800 | 0.0 | 0.0 | 0.200 | 0.600 | 0.800 |
| geo_spread | 13 | 0.289 | 0.085 | 0.250 | 0.500 | 0.0 | 0.0 | 0.250 | 0.250 | 0.480 |
| data_leaked | 13 | 0.192 | 0.232 | 0.000 | 0.625 | 46.2 | 0.0 | 0.000 | 0.125 | 0.625 |
| email_age | 13 | 0.587 | 0.477 | 0.000 | 1.000 | 30.8 | 46.2 | 0.000 | 0.927 | 1.000 |
| security | 13 | 0.231 | 0.360 | 0.000 | 0.750 | 69.2 | 0.0 | 0.000 | 0.000 | 0.750 |
| public_exposure | 13 | 0.019 | 0.069 | 0.000 | 0.250 | 92.3 | 0.0 | 0.000 | 0.000 | 0.150 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ·········█
platforms          ·········█
username_reuse      ···· ···█
breaches           ··▂··█··▃·
geo_spread         ··█   ····
data_leaked        █▁▄▁··▂···
email_age          ▄▁···▁···█
security           █······▃··
public_exposure    █· ·······
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=15) | 13 | 29.154 | 7.022 | 15.000 | 42.000 | 100.0 | 16.200 | 30.000 | 39.200 |
| platforms (`platforms`, max=10) | 13 | 14.923 | 3.278 | 9.000 | 21.000 | 92.3 | 9.400 | 15.000 | 19.800 |
| username_reuse (`username_reuse`, max=5) | 13 | 5.154 | 1.819 | 0.000 | 7.000 | 84.6 | 1.200 | 6.000 | 6.600 |
| breaches (`breaches`, max=5) | 13 | 2.923 | 0.954 | 1.000 | 4.000 | 0.0 | 1.000 | 3.000 | 4.000 |
| geo_spread (`geo_spread`, max=5) | 13 | 1.446 | 0.424 | 1.250 | 2.500 | 0.0 | 1.250 | 1.250 | 2.400 |
| data_leaked (`data_leaked`, max=8) | 13 | 1.538 | 1.854 | 0.000 | 5.000 | 0.0 | 0.000 | 1.000 | 5.000 |
| email_age (`email_age_years`, max=15) | 13 | 11.023 | 9.446 | 0.000 | 23.200 | 46.2 | 0.000 | 13.900 | 22.720 |
| security (`security_weak`, max=4) | 13 | 0.923 | 1.441 | 0.000 | 3.000 | 0.0 | 0.000 | 0.000 | 3.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 13 | 0.019 | 0.069 | 0.000 | 0.250 | 0.0 | 0.000 | 0.000 | 0.150 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ·········█
platforms          ·········█
username_reuse      ····· ··█
breaches           ··▂···█·▃·
geo_spread         ··█   ····
data_leaked        █▁▄▁··▂···
email_age          ▄▁···▁···█
security           █······▃··
public_exposure    █· ·······
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 13 | 100.0% |
| 5 | 13 | 100.0% |
| 7 | 6 | 46.2% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **78** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.872 · stdev = 0.079

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 78 | 100.00% |
| 0.6 | 78 | 100.00% |
| 0.7 | 74 | 94.87% |
| 0.8 | 68 | 87.18% |
| 0.9 | 23 | 29.49% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ······ ▁█▄
```

**Threshold sanity:** 94.87% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 1.000 | `antony.franz@lessentiel.lu` | `sebastien.bonoris@lessentiel.lu` | accounts, platforms, username_reuse |
| 2 | 1.000 | `frederic.noel@lessentiel.lu` | `ahmed.feddag@lessentiel.lu` | accounts, platforms, username_reuse |
| 3 | 0.998 | `annick.charlier@lessentiel.lu` | `thierry.bollekens@lessentiel.lu` | accounts, platforms, username_reuse |
| 4 | 0.998 | `thierry.bollekens@lessentiel.lu` | `celines.hess@lessentiel.lu` | accounts, platforms, username_reuse |
| 5 | 0.994 | `annick.charlier@lessentiel.lu` | `emmanuel.fleig@lessentiel.lu` | accounts, platforms, username_reuse |
| 6 | 0.991 | `annick.charlier@lessentiel.lu` | `celines.hess@lessentiel.lu` | accounts, platforms, username_reuse |
| 7 | 0.988 | `thierry.bollekens@lessentiel.lu` | `emmanuel.fleig@lessentiel.lu` | accounts, platforms, username_reuse |
| 8 | 0.984 | `antony.franz@lessentiel.lu` | `thomas.fullenwarth@lessentiel.lu` | accounts, platforms, email_age |
| 9 | 0.984 | `thomas.fullenwarth@lessentiel.lu` | `sebastien.bonoris@lessentiel.lu` | accounts, platforms, email_age |
| 10 | 0.977 | `celines.hess@lessentiel.lu` | `emmanuel.fleig@lessentiel.lu` | accounts, platforms, username_reuse |
| 11 | 0.957 | `frederic.noel@lessentiel.lu` | `antony.franz@lessentiel.lu` | accounts, platforms, username_reuse |
| 12 | 0.957 | `frederic.noel@lessentiel.lu` | `sebastien.bonoris@lessentiel.lu` | accounts, platforms, username_reuse |
| 13 | 0.955 | `ahmed.feddag@lessentiel.lu` | `antony.franz@lessentiel.lu` | accounts, platforms, username_reuse |
| 14 | 0.955 | `ahmed.feddag@lessentiel.lu` | `sebastien.bonoris@lessentiel.lu` | accounts, platforms, username_reuse |
| 15 | 0.954 | `us.petitions@rb.nic.in` | `lisa.meyer@adem.etat.lu` | accounts, username_reuse, platforms |
| 16 | 0.944 | `frederic.noel@lessentiel.lu` | `thomas.fullenwarth@lessentiel.lu` | accounts, platforms, email_age |
| 17 | 0.941 | `youcef.damardji@abouthebrand.lu` | `lisa.meyer@adem.etat.lu` | accounts, platforms, username_reuse |
| 18 | 0.940 | `ahmed.feddag@lessentiel.lu` | `thomas.fullenwarth@lessentiel.lu` | accounts, platforms, email_age |
| 19 | 0.915 | `antony.franz@lessentiel.lu` | `us.petitions@rb.nic.in` | accounts, username_reuse, email_age |
| 20 | 0.915 | `sebastien.bonoris@lessentiel.lu` | `us.petitions@rb.nic.in` | accounts, username_reuse, email_age |

## G — Auto-flagged observations

- saturation: `accounts` is 100.0% saturated — AXIS_MAX[`accounts`]=15 likely too low
- saturation: `platforms` is 92.3% saturated — AXIS_MAX[`platforms`]=10 likely too low
- saturation: `username_reuse` is 84.6% saturated — AXIS_MAX[`username_reuse`]=5 likely too low
- saturation: `email_age` is 46.2% saturated — AXIS_MAX[`email_age_years`]=15 likely too low
- starved: `public_exposure` is zero for 92.3% of fingerprints — data plumbing or AXIS_MAX too high
- saturation cause confirmed: `accounts` raw ≥ AXIS_MAX (=15) in 100.0% of fingerprints
- saturation cause confirmed: `platforms` raw ≥ AXIS_MAX (=10) in 92.3% of fingerprints
- saturation cause confirmed: `username_reuse` raw ≥ AXIS_MAX (=5) in 84.6% of fingerprints
- saturation cause confirmed: `email_age` raw ≥ AXIS_MAX (=15) in 46.2% of fingerprints
- similarity threshold sanity: 94.87% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 6 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
