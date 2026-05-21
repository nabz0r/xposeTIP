# Fingerprint calibration diagnostic — friends

_Generated 2026-05-21 14:56 UTC · script S143-v1_

## A — Summary

- Workspace: **Friends** (`friends`, id `4b0f2983-dd94-4bcf-b7a2-7f4fd144420f`)
- Total targets: **34**
- Targets with fingerprint key: **8**
- Targets with extractable axes (_extract_axes ≠ None): **8**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 8 | 0.512 | 0.152 | 0.300 | 0.750 | 0.0 | 0.0 | 0.295 | 0.550 | 0.765 |
| platforms | 8 | 0.380 | 0.166 | 0.260 | 0.760 | 0.0 | 0.0 | 0.258 | 0.330 | 0.790 |
| username_reuse | 8 | 0.375 | 0.276 | 0.100 | 0.700 | 0.0 | 0.0 | 0.100 | 0.250 | 0.700 |
| breaches | 8 | 0.775 | 0.071 | 0.600 | 0.800 | 0.0 | 0.0 | 0.580 | 0.800 | 0.800 |
| geo_spread | 8 | 0.424 | 0.153 | 0.300 | 0.740 | 0.0 | 0.0 | 0.299 | 0.365 | 0.764 |
| data_leaked | 8 | 0.240 | 0.267 | 0.040 | 0.880 | 0.0 | 0.0 | 0.032 | 0.140 | 0.944 |
| email_age | 8 | 0.197 | 0.185 | 0.000 | 0.453 | 25.0 | 0.0 | 0.000 | 0.208 | 0.454 |
| security | 8 | 0.719 | 0.088 | 0.500 | 0.750 | 0.0 | 0.0 | 0.475 | 0.750 | 0.750 |
| public_exposure | 8 | 0.031 | 0.088 | 0.000 | 0.250 | 87.5 | 0.0 | 0.000 | 0.000 | 0.275 |
| formal_records | 8 | 0.250 | 0.382 | 0.000 | 1.000 | 62.5 | 12.5 | 0.000 | 0.000 | 1.040 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ··▂▂▂█·▂··
platforms          ··██▂··▂··
username_reuse     ·▅█···█···
breaches           ·····▁··█·
geo_spread         ··▂█▂▅·▂··
data_leaked        ▂█▄·····▂·
email_age          █▂▅·▅·····
security           ·····▁·█··
public_exposure    █·▁·······
formal_records     █···▁▁···▁
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=60) | 8 | 30.750 | 9.099 | 18.000 | 45.000 | 0.0 | 17.700 | 33.000 | 45.900 |
| platforms (`platforms`, max=50) | 8 | 19.000 | 8.281 | 13.000 | 38.000 | 0.0 | 12.900 | 16.500 | 39.500 |
| username_reuse (`username_reuse`, max=10) | 8 | 3.750 | 2.765 | 1.000 | 7.000 | 0.0 | 1.000 | 2.500 | 7.000 |
| breaches (`breaches`, max=5) | 8 | 3.875 | 0.354 | 3.000 | 4.000 | 0.0 | 2.900 | 4.000 | 4.000 |
| geo_spread (`geo_spread`, max=5) | 8 | 2.119 | 0.765 | 1.500 | 3.700 | 0.0 | 1.495 | 1.825 | 3.820 |
| data_leaked (`data_leaked`, max=25) | 8 | 6.000 | 6.676 | 1.000 | 22.000 | 0.0 | 0.800 | 3.500 | 23.600 |
| email_age (`email_age_years`, max=40) | 8 | 7.900 | 7.409 | 0.000 | 18.100 | 0.0 | 0.000 | 8.350 | 18.120 |
| security (`security_weak`, max=4) | 8 | 2.875 | 0.354 | 2.000 | 3.000 | 0.0 | 1.900 | 3.000 | 3.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 8 | 0.031 | 0.088 | 0.000 | 0.250 | 0.0 | 0.000 | 0.000 | 0.275 |
| formal_records (`formal_records_raw`, max=5) | 8 | 2.625 | 5.528 | 0.000 | 16.000 | 12.5 | 0.000 | 0.000 | 17.300 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ···█▄██▄··
platforms          ··██▂··▂··
username_reuse     ·▅▅▂···█··
breaches           ······▁·█·
geo_spread         ···█▂▄·▂··
data_leaked        ▂█▄·····▂·
email_age          █▂▅·▅·····
security           ·····▁·█··
public_exposure    █·▁·······
formal_records     █···▁·▁··▁
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 8 | 100.0% |
| 5 | 8 | 100.0% |
| 7 | 8 | 100.0% |
| 9 | 1 | 12.5% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **28** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.838 · stdev = 0.086

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 28 | 100.00% |
| 0.6 | 28 | 100.00% |
| 0.7 | 27 | 96.43% |
| 0.8 | 19 | 67.86% |
| 0.9 | 7 | 25.00% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ······ ▅█▄
```

**Threshold sanity:** 96.43% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 0.992 | `booking.lxb@gmail.com` | `abed.belaid@gmail.com` | security, username_reuse, breaches |
| 2 | 0.978 | `camelia.belab@gmail.com` | `abed.belaid@gmail.com` | breaches, security, username_reuse |
| 3 | 0.977 | `booking.lxb@gmail.com` | `camelia.belab@gmail.com` | security, username_reuse, breaches |
| 4 | 0.958 | `Ksontinisarah@gmail.com` | `loupn24@msn.com` | breaches, security, formal_records |
| 5 | 0.943 | `loupn24@msn.com` | `guillaume.a.perrin@gmail.com` | breaches, formal_records, security |
| 6 | 0.903 | `camelia.belab@gmail.com` | `info@florencehoffmann.net` | breaches, security, accounts |
| 7 | 0.902 | `Ksontinisarah@gmail.com` | `guillaume.a.perrin@gmail.com` | breaches, security, formal_records |
| 8 | 0.876 | `nabz0r@gmail.com` | `info@florencehoffmann.net` | breaches, security, accounts |
| 9 | 0.862 | `Ksontinisarah@gmail.com` | `nabz0r@gmail.com` | breaches, security, geo_spread |
| 10 | 0.861 | `Ksontinisarah@gmail.com` | `camelia.belab@gmail.com` | breaches, security, geo_spread |
| 11 | 0.855 | `abed.belaid@gmail.com` | `info@florencehoffmann.net` | breaches, security, accounts |
| 12 | 0.853 | `Ksontinisarah@gmail.com` | `info@florencehoffmann.net` | breaches, security, geo_spread |
| 13 | 0.852 | `camelia.belab@gmail.com` | `nabz0r@gmail.com` | breaches, security, accounts |
| 14 | 0.842 | `Ksontinisarah@gmail.com` | `abed.belaid@gmail.com` | breaches, security, accounts |
| 15 | 0.838 | `loupn24@msn.com` | `info@florencehoffmann.net` | breaches, security, geo_spread |
| 16 | 0.836 | `camelia.belab@gmail.com` | `loupn24@msn.com` | breaches, security, geo_spread |
| 17 | 0.835 | `booking.lxb@gmail.com` | `info@florencehoffmann.net` | security, breaches, accounts |
| 18 | 0.821 | `Ksontinisarah@gmail.com` | `booking.lxb@gmail.com` | security, breaches, geo_spread |
| 19 | 0.805 | `loupn24@msn.com` | `abed.belaid@gmail.com` | breaches, security, accounts |
| 20 | 0.785 | `nabz0r@gmail.com` | `loupn24@msn.com` | breaches, security, geo_spread |

## G — Auto-flagged observations

- starved: `public_exposure` is zero for 87.5% of fingerprints — data plumbing or AXIS_MAX too high
- similarity threshold sanity: 96.43% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 8 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
