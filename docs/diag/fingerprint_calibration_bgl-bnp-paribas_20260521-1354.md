# Fingerprint calibration diagnostic — bgl-bnp-paribas

_Generated 2026-05-21 13:54 UTC · script S143-v1_

## A — Summary

- Workspace: **BGL BNP Paribas** (`bgl-bnp-paribas`, id `fbef7faa-f844-415b-9af8-6a1ea9912447`)
- Total targets: **47**
- Targets with fingerprint key: **47**
- Targets with extractable axes (_extract_axes ≠ None): **47**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 47 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | 1.000 | 1.000 | 1.000 |
| platforms | 47 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | 1.000 | 1.000 | 1.000 |
| username_reuse | 47 | 0.860 | 0.273 | 0.200 | 1.000 | 0.0 | 76.6 | 0.200 | 1.000 | 1.000 |
| breaches | 47 | 0.609 | 0.041 | 0.600 | 0.800 | 0.0 | 0.0 | 0.600 | 0.600 | 0.600 |
| geo_spread | 47 | 0.254 | 0.029 | 0.250 | 0.450 | 0.0 | 0.0 | 0.250 | 0.250 | 0.250 |
| data_leaked | 47 | 0.029 | 0.079 | 0.000 | 0.375 | 85.1 | 0.0 | 0.000 | 0.000 | 0.125 |
| email_age | 47 | 0.586 | 0.473 | 0.000 | 1.000 | 27.7 | 53.2 | 0.000 | 1.000 | 1.000 |
| security | 47 | 0.250 | 0.000 | 0.250 | 0.250 | 0.0 | 0.0 | 0.250 | 0.250 | 0.250 |
| public_exposure | 47 | 0.088 | 0.125 | 0.000 | 0.350 | 59.6 | 0.0 | 0.000 | 0.000 | 0.292 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ·········█
platforms          ·········█
username_reuse     ··▁· ▁···█
breaches           ·····█·· ·
geo_spread         ··█· ·····
data_leaked        █   ······
email_age          ▄▁·· · · █
security           ··█·······
public_exposure    █▂▂▁······
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=15) | 47 | 28.915 | 3.574 | 20.000 | 35.000 | 100.0 | 23.000 | 30.000 | 32.200 |
| platforms (`platforms`, max=10) | 47 | 15.745 | 0.988 | 13.000 | 17.000 | 100.0 | 14.000 | 16.000 | 17.000 |
| username_reuse (`username_reuse`, max=5) | 47 | 5.000 | 1.757 | 1.000 | 6.000 | 76.6 | 1.000 | 6.000 | 6.000 |
| breaches (`breaches`, max=5) | 47 | 3.043 | 0.204 | 3.000 | 4.000 | 0.0 | 3.000 | 3.000 | 3.000 |
| geo_spread (`geo_spread`, max=5) | 47 | 1.271 | 0.146 | 1.250 | 2.250 | 0.0 | 1.250 | 1.250 | 1.250 |
| data_leaked (`data_leaked`, max=8) | 47 | 0.234 | 0.633 | 0.000 | 3.000 | 0.0 | 0.000 | 0.000 | 1.000 |
| email_age (`email_age_years`, max=15) | 47 | 15.445 | 13.264 | 0.000 | 27.900 | 53.2 | 0.000 | 26.600 | 27.900 |
| security (`security_weak`, max=4) | 47 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 1.000 | 1.000 | 1.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 47 | 0.088 | 0.125 | 0.000 | 0.350 | 0.0 | 0.000 | 0.000 | 0.292 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ·········█
platforms          ·········█
username_reuse     ··▁· ·▁··█
breaches           ······█· ·
geo_spread         ··█· ·····
data_leaked        █   ······
email_age          ▄▁·· · · █
security           ··█·······
public_exposure    █▂▂▁······
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 47 | 100.0% |
| 5 | 47 | 100.0% |
| 7 | 33 | 70.2% |
| 9 | 3 | 6.4% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **1081** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.920 · stdev = 0.066

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 1081 | 100.00% |
| 0.6 | 1081 | 100.00% |
| 0.7 | 1081 | 100.00% |
| 0.8 | 1014 | 93.80% |
| 0.9 | 619 | 57.26% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ······· ▅█
```

**Threshold sanity:** 100.00% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 1.000 | `sebastien.labbe@bgl.lu` | `marc.lennert@bgl.lu` | accounts, platforms, username_reuse |
| 2 | 1.000 | `sebastien.labbe@bgl.lu` | `beatrice.belorgey@bgl.lu` | accounts, platforms, username_reuse |
| 3 | 1.000 | `sebastien.labbe@bgl.lu` | `gilles.scholtus@bgl.lu` | accounts, platforms, username_reuse |
| 4 | 1.000 | `sebastien.labbe@bgl.lu` | `patrice.maraschi@bgl.lu` | accounts, platforms, username_reuse |
| 5 | 1.000 | `sebastien.labbe@bgl.lu` | `frederic.kieffer@bgl.lu` | accounts, platforms, username_reuse |
| 6 | 1.000 | `sebastien.labbe@bgl.lu` | `hichem.safar@bgl.lu` | accounts, platforms, username_reuse |
| 7 | 1.000 | `sebastien.labbe@bgl.lu` | `tajana.zidani@bgl.lu` | accounts, platforms, username_reuse |
| 8 | 1.000 | `sebastien.labbe@bgl.lu` | `mariam.bouras@bgl.lu` | accounts, platforms, username_reuse |
| 9 | 1.000 | `sebastien.labbe@bgl.lu` | `michele.detaille@bgl.lu` | accounts, platforms, username_reuse |
| 10 | 1.000 | `marc.lennert@bgl.lu` | `beatrice.belorgey@bgl.lu` | accounts, platforms, username_reuse |
| 11 | 1.000 | `marc.lennert@bgl.lu` | `gilles.scholtus@bgl.lu` | accounts, platforms, username_reuse |
| 12 | 1.000 | `marc.lennert@bgl.lu` | `patrice.maraschi@bgl.lu` | accounts, platforms, username_reuse |
| 13 | 1.000 | `marc.lennert@bgl.lu` | `frederic.kieffer@bgl.lu` | accounts, platforms, username_reuse |
| 14 | 1.000 | `marc.lennert@bgl.lu` | `hichem.safar@bgl.lu` | accounts, platforms, username_reuse |
| 15 | 1.000 | `marc.lennert@bgl.lu` | `tajana.zidani@bgl.lu` | accounts, platforms, username_reuse |
| 16 | 1.000 | `marc.lennert@bgl.lu` | `mariam.bouras@bgl.lu` | accounts, platforms, username_reuse |
| 17 | 1.000 | `marc.lennert@bgl.lu` | `michele.detaille@bgl.lu` | accounts, platforms, username_reuse |
| 18 | 1.000 | `beatrice.belorgey@bgl.lu` | `gilles.scholtus@bgl.lu` | accounts, platforms, username_reuse |
| 19 | 1.000 | `beatrice.belorgey@bgl.lu` | `patrice.maraschi@bgl.lu` | accounts, platforms, username_reuse |
| 20 | 1.000 | `beatrice.belorgey@bgl.lu` | `frederic.kieffer@bgl.lu` | accounts, platforms, username_reuse |

## G — Auto-flagged observations

- saturation: `accounts` is 100.0% saturated — AXIS_MAX[`accounts`]=15 likely too low
- saturation: `platforms` is 100.0% saturated — AXIS_MAX[`platforms`]=10 likely too low
- saturation: `username_reuse` is 76.6% saturated — AXIS_MAX[`username_reuse`]=5 likely too low
- starved: `data_leaked` is zero for 85.1% of fingerprints — data plumbing or AXIS_MAX too high
- saturation: `email_age` is 53.2% saturated — AXIS_MAX[`email_age_years`]=15 likely too low
- saturation cause confirmed: `accounts` raw ≥ AXIS_MAX (=15) in 100.0% of fingerprints
- saturation cause confirmed: `platforms` raw ≥ AXIS_MAX (=10) in 100.0% of fingerprints
- saturation cause confirmed: `username_reuse` raw ≥ AXIS_MAX (=5) in 76.6% of fingerprints
- saturation cause confirmed: `email_age` raw ≥ AXIS_MAX (=15) in 53.2% of fingerprints
- similarity threshold sanity: 100.00% of pairs ≥ 0.7 → threshold likely too low

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
