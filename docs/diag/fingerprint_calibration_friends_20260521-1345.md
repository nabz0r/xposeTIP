# Fingerprint calibration diagnostic — friends

_Generated 2026-05-21 13:45 UTC · script S143-v1_

## A — Summary

- Workspace: **Friends** (`friends`, id `4b0f2983-dd94-4bcf-b7a2-7f4fd144420f`)
- Total targets: **34**
- Targets with fingerprint key: **8**
- Targets with extractable axes (_extract_axes ≠ None): **8**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 8 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | 1.000 | 1.000 | 1.000 |
| platforms | 8 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | 1.000 | 1.000 | 1.000 |
| username_reuse | 8 | 0.600 | 0.355 | 0.200 | 1.000 | 0.0 | 37.5 | 0.200 | 0.500 | 1.000 |
| breaches | 8 | 0.775 | 0.071 | 0.600 | 0.800 | 0.0 | 0.0 | 0.580 | 0.800 | 0.800 |
| geo_spread | 8 | 0.424 | 0.153 | 0.300 | 0.740 | 0.0 | 0.0 | 0.299 | 0.365 | 0.764 |
| data_leaked | 8 | 0.531 | 0.281 | 0.125 | 1.000 | 0.0 | 12.5 | 0.100 | 0.438 | 1.025 |
| email_age | 8 | 0.477 | 0.419 | 0.000 | 1.000 | 25.0 | 25.0 | 0.000 | 0.556 | 1.000 |
| security | 8 | 0.719 | 0.088 | 0.500 | 0.750 | 0.0 | 0.0 | 0.475 | 0.750 | 0.750 |
| public_exposure | 8 | 0.088 | 0.134 | 0.000 | 0.350 | 62.5 | 0.0 | 0.000 | 0.000 | 0.365 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ·········█
platforms          ·········█
username_reuse     ··▅·▅▂···█
breaches           ·····▁··█·
geo_spread         ··▂█▂▅·▂··
data_leaked        ·▂·█·▂·▅·▂
email_age          █···▂·▅··▅
security           ·····▁·█··
public_exposure    █▁▁▁······
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=15) | 8 | 30.750 | 9.099 | 18.000 | 45.000 | 100.0 | 17.700 | 33.000 | 45.900 |
| platforms (`platforms`, max=10) | 8 | 19.000 | 8.281 | 13.000 | 38.000 | 100.0 | 12.900 | 16.500 | 39.500 |
| username_reuse (`username_reuse`, max=5) | 8 | 3.750 | 2.765 | 1.000 | 7.000 | 37.5 | 1.000 | 2.500 | 7.000 |
| breaches (`breaches`, max=5) | 8 | 3.875 | 0.354 | 3.000 | 4.000 | 0.0 | 2.900 | 4.000 | 4.000 |
| geo_spread (`geo_spread`, max=5) | 8 | 2.119 | 0.765 | 1.500 | 3.700 | 0.0 | 1.495 | 1.825 | 3.820 |
| data_leaked (`data_leaked`, max=8) | 8 | 6.000 | 6.676 | 1.000 | 22.000 | 12.5 | 0.800 | 3.500 | 23.600 |
| email_age (`email_age_years`, max=15) | 8 | 7.900 | 7.409 | 0.000 | 18.100 | 25.0 | 0.000 | 8.350 | 18.120 |
| security (`security_weak`, max=4) | 8 | 2.875 | 0.354 | 2.000 | 3.000 | 0.0 | 1.900 | 3.000 | 3.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 8 | 0.088 | 0.134 | 0.000 | 0.350 | 0.0 | 0.000 | 0.000 | 0.365 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ·········█
platforms          ·········█
username_reuse     ··▅·▅·▂··█
breaches           ······▁·█·
geo_spread         ···█▂▄·▂··
data_leaked        ·▂·█·▂·▅·▂
email_age          █···▂·▅··▅
security           ·····▁·█··
public_exposure    █▁▁▁······
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 8 | 100.0% |
| 5 | 8 | 100.0% |
| 7 | 8 | 100.0% |
| 9 | 2 | 25.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **28** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.910 · stdev = 0.055

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 28 | 100.00% |
| 0.6 | 28 | 100.00% |
| 0.7 | 28 | 100.00% |
| 0.8 | 27 | 96.43% |
| 0.9 | 18 | 64.29% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ······· ▄█
```

**Threshold sanity:** 100.00% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 0.994 | `booking.lxb@gmail.com` | `abed.belaid@gmail.com` | accounts, platforms, username_reuse |
| 2 | 0.971 | `info@florencehoffmann.net` | `loupn24@msn.com` | accounts, platforms, breaches |
| 3 | 0.968 | `Ksontinisarah@gmail.com` | `nabz0r@gmail.com` | accounts, platforms, breaches |
| 4 | 0.965 | `Ksontinisarah@gmail.com` | `loupn24@msn.com` | accounts, platforms, breaches |
| 5 | 0.960 | `guillaume.a.perrin@gmail.com` | `abed.belaid@gmail.com` | accounts, platforms, breaches |
| 6 | 0.955 | `info@florencehoffmann.net` | `nabz0r@gmail.com` | accounts, platforms, email_age |
| 7 | 0.950 | `booking.lxb@gmail.com` | `camelia.belab@gmail.com` | accounts, platforms, username_reuse |
| 8 | 0.948 | `camelia.belab@gmail.com` | `loupn24@msn.com` | accounts, platforms, breaches |
| 9 | 0.945 | `camelia.belab@gmail.com` | `abed.belaid@gmail.com` | accounts, platforms, username_reuse |
| 10 | 0.944 | `booking.lxb@gmail.com` | `guillaume.a.perrin@gmail.com` | accounts, platforms, security |
| 11 | 0.944 | `nabz0r@gmail.com` | `loupn24@msn.com` | accounts, platforms, breaches |
| 12 | 0.935 | `camelia.belab@gmail.com` | `info@florencehoffmann.net` | accounts, platforms, breaches |
| 13 | 0.932 | `Ksontinisarah@gmail.com` | `camelia.belab@gmail.com` | accounts, platforms, breaches |
| 14 | 0.932 | `Ksontinisarah@gmail.com` | `info@florencehoffmann.net` | accounts, platforms, breaches |
| 15 | 0.930 | `guillaume.a.perrin@gmail.com` | `loupn24@msn.com` | accounts, platforms, breaches |
| 16 | 0.924 | `camelia.belab@gmail.com` | `nabz0r@gmail.com` | accounts, platforms, breaches |
| 17 | 0.906 | `Ksontinisarah@gmail.com` | `guillaume.a.perrin@gmail.com` | accounts, platforms, breaches |
| 18 | 0.901 | `guillaume.a.perrin@gmail.com` | `camelia.belab@gmail.com` | accounts, platforms, breaches |
| 19 | 0.895 | `abed.belaid@gmail.com` | `loupn24@msn.com` | accounts, platforms, breaches |
| 20 | 0.885 | `booking.lxb@gmail.com` | `loupn24@msn.com` | accounts, platforms, breaches |

## G — Auto-flagged observations

- saturation: `accounts` is 100.0% saturated — AXIS_MAX[`accounts`]=15 likely too low
- saturation: `platforms` is 100.0% saturated — AXIS_MAX[`platforms`]=10 likely too low
- saturation: `username_reuse` is 37.5% saturated — AXIS_MAX[`username_reuse`]=5 likely too low
- saturation cause confirmed: `accounts` raw ≥ AXIS_MAX (=15) in 100.0% of fingerprints
- saturation cause confirmed: `platforms` raw ≥ AXIS_MAX (=10) in 100.0% of fingerprints
- saturation cause confirmed: `username_reuse` raw ≥ AXIS_MAX (=5) in 37.5% of fingerprints
- saturation cause confirmed: `email_age` raw ≥ AXIS_MAX (=15) in 25.0% of fingerprints
- similarity threshold sanity: 100.00% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 8 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
