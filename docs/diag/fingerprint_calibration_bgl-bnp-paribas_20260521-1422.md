# Fingerprint calibration diagnostic — bgl-bnp-paribas

_Generated 2026-05-21 14:22 UTC · script S143-v1_

## A — Summary

- Workspace: **BGL BNP Paribas** (`bgl-bnp-paribas`, id `fbef7faa-f844-415b-9af8-6a1ea9912447`)
- Total targets: **47**
- Targets with fingerprint key: **47**
- Targets with extractable axes (_extract_axes ≠ None): **47**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 47 | 0.482 | 0.060 | 0.333 | 0.583 | 0.0 | 0.0 | 0.383 | 0.500 | 0.536 |
| platforms | 47 | 0.315 | 0.020 | 0.260 | 0.340 | 0.0 | 0.0 | 0.280 | 0.320 | 0.340 |
| username_reuse | 47 | 0.500 | 0.176 | 0.100 | 0.600 | 0.0 | 0.0 | 0.100 | 0.600 | 0.600 |
| breaches | 47 | 0.609 | 0.041 | 0.600 | 0.800 | 0.0 | 0.0 | 0.600 | 0.600 | 0.600 |
| geo_spread | 47 | 0.309 | 0.009 | 0.250 | 0.310 | 0.0 | 0.0 | 0.310 | 0.310 | 0.310 |
| data_leaked | 47 | 0.009 | 0.025 | 0.000 | 0.120 | 85.1 | 0.0 | 0.000 | 0.000 | 0.040 |
| email_age | 47 | 0.055 | 0.095 | 0.000 | 0.310 | 55.3 | 0.0 | 0.000 | 0.000 | 0.241 |
| security | 47 | 0.250 | 0.000 | 0.250 | 0.250 | 0.0 | 0.0 | 0.250 | 0.250 | 0.250 |
| public_exposure | 47 | 0.088 | 0.125 | 0.000 | 0.350 | 59.6 | 0.0 | 0.000 | 0.000 | 0.292 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ···▂▄█····
platforms          ··▄█······
username_reuse     ·▁▁··█····
breaches           ·····█·· ·
geo_spread         ·· █······
data_leaked        █ ········
email_age          █▁  ······
security           ··█·······
public_exposure    █▂▂▁······
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=60) | 47 | 28.915 | 3.574 | 20.000 | 35.000 | 0.0 | 23.000 | 30.000 | 32.200 |
| platforms (`platforms`, max=50) | 47 | 15.745 | 0.988 | 13.000 | 17.000 | 0.0 | 14.000 | 16.000 | 17.000 |
| username_reuse (`username_reuse`, max=10) | 47 | 5.000 | 1.757 | 1.000 | 6.000 | 0.0 | 1.000 | 6.000 | 6.000 |
| breaches (`breaches`, max=5) | 47 | 3.043 | 0.204 | 3.000 | 4.000 | 0.0 | 3.000 | 3.000 | 3.000 |
| geo_spread (`geo_spread`, max=5) | 47 | 1.544 | 0.044 | 1.250 | 1.550 | 0.0 | 1.550 | 1.550 | 1.550 |
| data_leaked (`data_leaked`, max=25) | 47 | 0.234 | 0.633 | 0.000 | 3.000 | 0.0 | 0.000 | 0.000 | 1.000 |
| email_age (`email_age_years`, max=40) | 47 | 2.200 | 3.783 | 0.000 | 12.400 | 0.0 | 0.000 | 0.000 | 9.620 |
| security (`security_weak`, max=4) | 47 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 1.000 | 1.000 | 1.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 47 | 0.088 | 0.125 | 0.000 | 0.350 | 0.0 | 0.000 | 0.000 | 0.292 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ···▂▄█····
platforms          ·· █······
username_reuse     ·▁ ▁· █···
breaches           ······█· ·
geo_spread         ·· █······
data_leaked        █ ········
email_age          █▁  ······
security           ··█·······
public_exposure    █▂▂▁······
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 47 | 100.0% |
| 5 | 47 | 100.0% |
| 7 | 15 | 31.9% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **1081** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.952 · stdev = 0.047

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 1081 | 100.00% |
| 0.6 | 1081 | 100.00% |
| 0.7 | 1081 | 100.00% |
| 0.8 | 1081 | 100.00% |
| 0.9 | 885 | 81.87% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ········▁█
```

**Threshold sanity:** 100.00% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 1.000 | `marc.lennert@bgl.lu` | `alain.nyckees@bgl.lu` | username_reuse, breaches, accounts |
| 2 | 1.000 | `patrice.maraschi@bgl.lu` | `sandrine.devuyst@bgl.lu` | username_reuse, breaches, accounts |
| 3 | 1.000 | `patrice.maraschi@bgl.lu` | `valerie.sini@bgl.lu` | username_reuse, breaches, accounts |
| 4 | 1.000 | `francoise.thoma@bgl.lu` | `gregory.gillet@bgl.lu` | username_reuse, breaches, accounts |
| 5 | 1.000 | `sebastien.labbe@bgl.lu` | `vincent.delfosse@bgl.lu` | username_reuse, breaches, accounts |
| 6 | 1.000 | `sebastien.labbe@bgl.lu` | `frederic.kieffer@bgl.lu` | username_reuse, breaches, accounts |
| 7 | 1.000 | `cedric.bossaert@bgl.lu` | `pauline.monginot@bgl.lu` | username_reuse, breaches, accounts |
| 8 | 1.000 | `gilles.scholtus@bgl.lu` | `hichem.safar@bgl.lu` | username_reuse, breaches, accounts |
| 9 | 1.000 | `vincent.delfosse@bgl.lu` | `frederic.kieffer@bgl.lu` | username_reuse, breaches, accounts |
| 10 | 1.000 | `sandrine.devuyst@bgl.lu` | `valerie.sini@bgl.lu` | username_reuse, breaches, accounts |
| 11 | 1.000 | `marc.lennert@bgl.lu` | `francoise.thoma@bgl.lu` | username_reuse, breaches, accounts |
| 12 | 1.000 | `marc.lennert@bgl.lu` | `sebastien.labbe@bgl.lu` | username_reuse, breaches, accounts |
| 13 | 1.000 | `marc.lennert@bgl.lu` | `cedric.bossaert@bgl.lu` | username_reuse, breaches, accounts |
| 14 | 1.000 | `marc.lennert@bgl.lu` | `vincent.delfosse@bgl.lu` | username_reuse, breaches, accounts |
| 15 | 1.000 | `marc.lennert@bgl.lu` | `gregory.gillet@bgl.lu` | username_reuse, breaches, accounts |
| 16 | 1.000 | `marc.lennert@bgl.lu` | `frederic.kieffer@bgl.lu` | username_reuse, breaches, accounts |
| 17 | 1.000 | `marc.lennert@bgl.lu` | `pauline.monginot@bgl.lu` | username_reuse, breaches, accounts |
| 18 | 1.000 | `patrice.maraschi@bgl.lu` | `mariam.bouras@bgl.lu` | username_reuse, breaches, accounts |
| 19 | 1.000 | `patrice.maraschi@bgl.lu` | `gilles.scholtus@bgl.lu` | username_reuse, breaches, accounts |
| 20 | 1.000 | `patrice.maraschi@bgl.lu` | `hichem.safar@bgl.lu` | username_reuse, breaches, accounts |

## G — Auto-flagged observations

- starved: `data_leaked` is zero for 85.1% of fingerprints — data plumbing or AXIS_MAX too high
- similarity threshold sanity: 100.00% of pairs ≥ 0.7 → threshold likely too low

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
