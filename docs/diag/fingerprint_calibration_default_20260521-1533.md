# Fingerprint calibration diagnostic — default

_Generated 2026-05-21 15:33 UTC · script S143-v1_

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
| network_signature | 13 | 0.826 | 0.005 | 0.813 | 0.831 | 0.0 | 0.0 | 0.816 | 0.827 | 0.831 |

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
network_signature  ········█·
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
| network_signature (`network_signature_raw`, max=1.0) | 13 | 0.826 | 0.005 | 0.813 | 0.831 | 0.0 | 0.816 | 0.827 | 0.831 |

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
network_signature  ········█·
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 13 | 100.0% |
| 5 | 13 | 100.0% |
| 7 | 6 | 46.2% |
| 9 | 1 | 7.7% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **78** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.886 · stdev = 0.102

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 78 | 100.00% |
| 0.6 | 78 | 100.00% |
| 0.7 | 78 | 100.00% |
| 0.8 | 54 | 69.23% |
| 0.9 | 39 | 50.00% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ·······▄▃█
```

**Threshold sanity:** 100.00% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 1.000 | `celines.hess@lessentiel.lu` | `antony.franz@lessentiel.lu` | network_signature, username_reuse, breaches |
| 2 | 0.999 | `thierry.bollekens@lessentiel.lu` | `sebastien.bonoris@lessentiel.lu` | network_signature, breaches, accounts |
| 3 | 0.998 | `celines.hess@lessentiel.lu` | `sebastien.bonoris@lessentiel.lu` | network_signature, breaches, accounts |
| 4 | 0.998 | `sebastien.bonoris@lessentiel.lu` | `antony.franz@lessentiel.lu` | network_signature, breaches, accounts |
| 5 | 0.997 | `celines.hess@lessentiel.lu` | `annick.charlier@lessentiel.lu` | network_signature, username_reuse, breaches |
| 6 | 0.997 | `annick.charlier@lessentiel.lu` | `antony.franz@lessentiel.lu` | network_signature, username_reuse, breaches |
| 7 | 0.996 | `thierry.bollekens@lessentiel.lu` | `celines.hess@lessentiel.lu` | network_signature, breaches, accounts |
| 8 | 0.996 | `thierry.bollekens@lessentiel.lu` | `antony.franz@lessentiel.lu` | network_signature, breaches, accounts |
| 9 | 0.994 | `sebastien.bonoris@lessentiel.lu` | `annick.charlier@lessentiel.lu` | network_signature, breaches, username_reuse |
| 10 | 0.993 | `ahmed.feddag@lessentiel.lu` | `frederic.noel@lessentiel.lu` | network_signature, breaches, username_reuse |
| 11 | 0.993 | `thierry.bollekens@lessentiel.lu` | `annick.charlier@lessentiel.lu` | network_signature, breaches, username_reuse |
| 12 | 0.993 | `emmanuel.fleig@lessentiel.lu` | `annick.charlier@lessentiel.lu` | network_signature, username_reuse, breaches |
| 13 | 0.991 | `emmanuel.fleig@lessentiel.lu` | `frederic.noel@lessentiel.lu` | network_signature, breaches, username_reuse |
| 14 | 0.989 | `sebastien.bonoris@lessentiel.lu` | `thomas.fullenwarth@lessentiel.lu` | network_signature, breaches, accounts |
| 15 | 0.989 | `celines.hess@lessentiel.lu` | `emmanuel.fleig@lessentiel.lu` | network_signature, username_reuse, breaches |
| 16 | 0.989 | `emmanuel.fleig@lessentiel.lu` | `antony.franz@lessentiel.lu` | network_signature, username_reuse, breaches |
| 17 | 0.989 | `thierry.bollekens@lessentiel.lu` | `thomas.fullenwarth@lessentiel.lu` | network_signature, breaches, accounts |
| 18 | 0.989 | `thierry.bollekens@lessentiel.lu` | `emmanuel.fleig@lessentiel.lu` | network_signature, breaches, accounts |
| 19 | 0.988 | `sebastien.bonoris@lessentiel.lu` | `emmanuel.fleig@lessentiel.lu` | network_signature, breaches, accounts |
| 20 | 0.988 | `us.petitions@rb.nic.in` | `youcef.damardji@abouthebrand.lu` | network_signature, security, username_reuse |

## G — Auto-flagged observations

- starved: `public_exposure` is zero for 92.3% of fingerprints — data plumbing or AXIS_MAX too high
- starved: `formal_records` is zero for 100.0% of fingerprints — data plumbing or AXIS_MAX too high
- similarity threshold sanity: 100.00% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 6 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
