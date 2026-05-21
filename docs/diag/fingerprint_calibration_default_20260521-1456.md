# Fingerprint calibration diagnostic — default

_Generated 2026-05-21 14:56 UTC · script S143-v1_

## A — Summary

- Workspace: **Default** (`default`, id `32f8ec0e-d03e-4f79-9daa-4e2815fa0cbb`)
- Total targets: **13**
- Targets with fingerprint key: **13**
- Targets with extractable axes (_extract_axes ≠ None): **13**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 13 | 0.486 | 0.117 | 0.250 | 0.700 | 0.0 | 0.0 | 0.270 | 0.500 | 0.653 |
| platforms | 13 | 0.298 | 0.066 | 0.180 | 0.420 | 0.0 | 0.0 | 0.188 | 0.300 | 0.396 |
| username_reuse | 13 | 0.515 | 0.182 | 0.000 | 0.700 | 7.7 | 0.0 | 0.120 | 0.600 | 0.660 |
| breaches | 13 | 0.585 | 0.191 | 0.200 | 0.800 | 0.0 | 0.0 | 0.200 | 0.600 | 0.800 |
| geo_spread | 13 | 0.335 | 0.063 | 0.310 | 0.500 | 0.0 | 0.0 | 0.310 | 0.310 | 0.480 |
| data_leaked | 13 | 0.062 | 0.074 | 0.000 | 0.200 | 46.2 | 0.0 | 0.000 | 0.040 | 0.200 |
| email_age | 13 | 0.056 | 0.113 | 0.000 | 0.352 | 76.9 | 0.0 | 0.000 | 0.000 | 0.290 |
| security | 13 | 0.231 | 0.360 | 0.000 | 0.750 | 69.2 | 0.0 | 0.000 | 0.000 | 0.750 |
| public_exposure | 13 | 0.019 | 0.069 | 0.000 | 0.250 | 92.3 | 0.0 | 0.000 | 0.000 | 0.150 |
| formal_records | 13 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ··▂·▃█▁···
platforms          ·▁█▆▁·····
username_reuse      · ··█ ···
breaches           ··▂··█··▃·
geo_spread         ···█  ····
data_leaked        █ ▁·······
email_age          █▁· ······
security           █······▃··
public_exposure    █· ·······
formal_records     █·········
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=60) | 13 | 29.154 | 7.022 | 15.000 | 42.000 | 0.0 | 16.200 | 30.000 | 39.200 |
| platforms (`platforms`, max=50) | 13 | 14.923 | 3.278 | 9.000 | 21.000 | 0.0 | 9.400 | 15.000 | 19.800 |
| username_reuse (`username_reuse`, max=10) | 13 | 5.154 | 1.819 | 0.000 | 7.000 | 0.0 | 1.200 | 6.000 | 6.600 |
| breaches (`breaches`, max=5) | 13 | 2.923 | 0.954 | 1.000 | 4.000 | 0.0 | 1.000 | 3.000 | 4.000 |
| geo_spread (`geo_spread`, max=5) | 13 | 1.677 | 0.314 | 1.550 | 2.500 | 0.0 | 1.550 | 1.550 | 2.400 |
| data_leaked (`data_leaked`, max=25) | 13 | 1.538 | 1.854 | 0.000 | 5.000 | 0.0 | 0.000 | 1.000 | 5.000 |
| email_age (`email_age_years`, max=40) | 13 | 2.238 | 4.532 | 0.000 | 14.100 | 0.0 | 0.000 | 0.000 | 11.620 |
| security (`security_weak`, max=4) | 13 | 0.923 | 1.441 | 0.000 | 3.000 | 0.0 | 0.000 | 0.000 | 3.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 13 | 0.019 | 0.069 | 0.000 | 0.250 | 0.0 | 0.000 | 0.000 | 0.150 |
| formal_records (`formal_records_raw`, max=5) | 13 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ··▁▁▃█·▁··
platforms          ·▁▃█▁·····
username_reuse     ▁··▁·▃█▁··
breaches           ··▂···█·▃·
geo_spread         ···█  ····
data_leaked        █ ▁·······
email_age          █▁· ······
security           █······▃··
public_exposure    █· ·······
formal_records     █·········
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 13 | 100.0% |
| 5 | 13 | 100.0% |
| 7 | 3 | 23.1% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **78** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.830 · stdev = 0.157

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 78 | 100.00% |
| 0.6 | 73 | 93.59% |
| 0.7 | 51 | 65.38% |
| 0.8 | 49 | 62.82% |
| 0.9 | 38 | 48.72% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ·····▁▄ ▂█
```

**Threshold sanity:** 65.38% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 1.000 | `antony.franz@lessentiel.lu` | `celines.hess@lessentiel.lu` | username_reuse, breaches, accounts |
| 2 | 0.998 | `thierry.bollekens@lessentiel.lu` | `sebastien.bonoris@lessentiel.lu` | breaches, accounts, username_reuse |
| 3 | 0.996 | `antony.franz@lessentiel.lu` | `sebastien.bonoris@lessentiel.lu` | breaches, accounts, username_reuse |
| 4 | 0.996 | `celines.hess@lessentiel.lu` | `sebastien.bonoris@lessentiel.lu` | breaches, accounts, username_reuse |
| 5 | 0.996 | `antony.franz@lessentiel.lu` | `annick.charlier@lessentiel.lu` | username_reuse, breaches, accounts |
| 6 | 0.996 | `celines.hess@lessentiel.lu` | `annick.charlier@lessentiel.lu` | username_reuse, breaches, accounts |
| 7 | 0.993 | `thierry.bollekens@lessentiel.lu` | `antony.franz@lessentiel.lu` | breaches, accounts, username_reuse |
| 8 | 0.993 | `thierry.bollekens@lessentiel.lu` | `celines.hess@lessentiel.lu` | breaches, accounts, username_reuse |
| 9 | 0.992 | `emmanuel.fleig@lessentiel.lu` | `annick.charlier@lessentiel.lu` | username_reuse, breaches, accounts |
| 10 | 0.990 | `frederic.noel@lessentiel.lu` | `ahmed.feddag@lessentiel.lu` | breaches, username_reuse, accounts |
| 11 | 0.990 | `sebastien.bonoris@lessentiel.lu` | `annick.charlier@lessentiel.lu` | breaches, username_reuse, accounts |
| 12 | 0.989 | `thierry.bollekens@lessentiel.lu` | `annick.charlier@lessentiel.lu` | breaches, username_reuse, accounts |
| 13 | 0.988 | `frederic.noel@lessentiel.lu` | `emmanuel.fleig@lessentiel.lu` | breaches, username_reuse, accounts |
| 14 | 0.987 | `sebastien.bonoris@lessentiel.lu` | `emmanuel.fleig@lessentiel.lu` | breaches, accounts, username_reuse |
| 15 | 0.986 | `antony.franz@lessentiel.lu` | `emmanuel.fleig@lessentiel.lu` | username_reuse, breaches, accounts |
| 16 | 0.986 | `celines.hess@lessentiel.lu` | `emmanuel.fleig@lessentiel.lu` | username_reuse, breaches, accounts |
| 17 | 0.986 | `thierry.bollekens@lessentiel.lu` | `emmanuel.fleig@lessentiel.lu` | breaches, accounts, username_reuse |
| 18 | 0.984 | `thierry.bollekens@lessentiel.lu` | `thomas.fullenwarth@lessentiel.lu` | breaches, accounts, platforms |
| 19 | 0.984 | `sebastien.bonoris@lessentiel.lu` | `thomas.fullenwarth@lessentiel.lu` | breaches, accounts, platforms |
| 20 | 0.982 | `us.petitions@rb.nic.in` | `youcef.damardji@abouthebrand.lu` | security, username_reuse, geo_spread |

## G — Auto-flagged observations

- starved: `public_exposure` is zero for 92.3% of fingerprints — data plumbing or AXIS_MAX too high
- starved: `formal_records` is zero for 100.0% of fingerprints — data plumbing or AXIS_MAX too high
- similarity threshold sanity: 65.38% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 3 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
