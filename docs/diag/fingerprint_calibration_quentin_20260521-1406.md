# Fingerprint calibration diagnostic — quentin

_Generated 2026-05-21 14:06 UTC · script S143-v1_

## A — Summary

- Workspace: **Quentin** (`quentin`, id `5f632c1c-c181-4a1f-8010-531e06626847`)
- Total targets: **30**
- Targets with fingerprint key: **30**
- Targets with extractable axes (_extract_axes ≠ None): **30**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 30 | 0.947 | 0.177 | 0.267 | 1.000 | 0.0 | 83.3 | 0.933 | 1.000 | 1.000 |
| platforms | 30 | 0.963 | 0.140 | 0.400 | 1.000 | 0.0 | 93.3 | 1.000 | 1.000 | 1.000 |
| username_reuse | 30 | 0.447 | 0.347 | 0.000 | 1.000 | 3.3 | 23.3 | 0.200 | 0.200 | 1.000 |
| breaches | 30 | 0.653 | 0.203 | 0.000 | 0.800 | 6.7 | 0.0 | 0.600 | 0.600 | 0.800 |
| geo_spread | 30 | 0.260 | 0.116 | 0.000 | 0.450 | 10.0 | 0.0 | 0.025 | 0.250 | 0.450 |
| data_leaked | 30 | 0.304 | 0.319 | 0.000 | 1.000 | 33.3 | 3.3 | 0.000 | 0.188 | 0.863 |
| email_age | 30 | 0.866 | 0.288 | 0.000 | 1.000 | 6.7 | 76.7 | 0.400 | 1.000 | 1.000 |
| security | 30 | 0.508 | 0.325 | 0.000 | 0.750 | 23.3 | 0.0 | 0.000 | 0.750 | 0.750 |
| public_exposure | 30 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ··  ·····█
platforms          ····  ···█
username_reuse      ·█·▁▁·· ▃
breaches           ▁····█··█·
geo_spread         ▁·█·▁·····
data_leaked        █▄▁▃·▂·▂▁ 
email_age           ··  · · █
security           ▃·▁·· ·█··
public_exposure    █·········
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=15) | 30 | 19.867 | 7.807 | 4.000 | 37.000 | 83.3 | 14.000 | 17.000 | 31.700 |
| platforms (`platforms`, max=10) | 30 | 13.600 | 3.047 | 4.000 | 19.000 | 93.3 | 12.000 | 14.000 | 16.900 |
| username_reuse (`username_reuse`, max=5) | 30 | 2.533 | 2.255 | 0.000 | 7.000 | 23.3 | 1.000 | 1.000 | 6.000 |
| breaches (`breaches`, max=5) | 30 | 3.267 | 1.015 | 0.000 | 4.000 | 0.0 | 3.000 | 3.000 | 4.000 |
| geo_spread (`geo_spread`, max=5) | 30 | 1.300 | 0.578 | 0.000 | 2.250 | 0.0 | 0.125 | 1.250 | 2.250 |
| data_leaked (`data_leaked`, max=8) | 30 | 2.733 | 3.562 | 0.000 | 17.000 | 3.3 | 0.000 | 1.500 | 6.900 |
| email_age (`email_age_years`, max=15) | 30 | 19.650 | 8.155 | 0.000 | 30.000 | 76.7 | 6.000 | 22.000 | 29.200 |
| security (`security_weak`, max=4) | 30 | 2.033 | 1.299 | 0.000 | 3.000 | 0.0 | 0.000 | 3.000 | 3.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 30 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ··  ·····█
platforms          ····  ···█
username_reuse      ·█·▁·▁· ▃
breaches           ▁·····█·█·
geo_spread         ▁·█ ▁·····
data_leaked        █▄▁▃·▂·▂▁ 
email_age           ··  · · █
security           ▃·▁·· ·█··
public_exposure    █·········
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 30 | 100.0% |
| 5 | 29 | 96.7% |
| 7 | 23 | 76.7% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **435** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.883 · stdev = 0.110

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 429 | 98.62% |
| 0.6 | 423 | 97.24% |
| 0.7 | 392 | 90.11% |
| 0.8 | 372 | 85.52% |
| 0.9 | 252 | 57.93% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ····    ▃█
```

**Threshold sanity:** 90.11% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 1.000 | `thyfaine.knock@intertrustgroup.com` | `bruno.diogo@devinci.fr` | accounts, platforms, username_reuse |
| 2 | 1.000 | `gmelahaye@gmail.com` | `drkavichopra@gmail.com` | platforms, email_age, accounts |
| 3 | 1.000 | `adrienfargue@gmail.com` | `juliefranck@gmail.com` | accounts, platforms, email_age |
| 4 | 0.999 | `davidastratoff@gmail.com` | `sammynesville@gmail.com` | accounts, platforms, email_age |
| 5 | 0.998 | `vihihid@gmail.com` | `adrienfargue@gmail.com` | accounts, platforms, email_age |
| 6 | 0.998 | `vihihid@gmail.com` | `juliefranck@gmail.com` | accounts, platforms, email_age |
| 7 | 0.996 | `davidastratoff@gmail.com` | `armandoalve@gmail.com` | accounts, platforms, email_age |
| 8 | 0.995 | `sammynesville@gmail.com` | `armandoalve@gmail.com` | accounts, platforms, email_age |
| 9 | 0.994 | `gmelahaye@gmail.com` | `g.lahaye.glimmobilier@gmail.com` | platforms, email_age, accounts |
| 10 | 0.994 | `g.lahaye.glimmobilier@gmail.com` | `drkavichopra@gmail.com` | platforms, email_age, accounts |
| 11 | 0.994 | `vihihid@gmail.com` | `gmelahaye@gmail.com` | platforms, email_age, accounts |
| 12 | 0.994 | `vihihid@gmail.com` | `drkavichopra@gmail.com` | platforms, email_age, accounts |
| 13 | 0.993 | `gmelahaye@gmail.com` | `drbastin38@gmail.com` | platforms, email_age, accounts |
| 14 | 0.993 | `drkavichopra@gmail.com` | `drbastin38@gmail.com` | platforms, email_age, accounts |
| 15 | 0.993 | `avocatv.elkaim@hotmail.fr` | `elyes.prudor@gmail.com` | accounts, platforms, username_reuse |
| 16 | 0.991 | `samleeml@gmail.com` | `sammynesville@gmail.com` | accounts, platforms, email_age |
| 17 | 0.991 | `elyes.prudor@gmail.com` | `cnakache.kine@gmail.com` | accounts, platforms, username_reuse |
| 18 | 0.990 | `drbastin38@gmail.com` | `kivsko91@gmail.com` | accounts, platforms, email_age |
| 19 | 0.990 | `samleeml@gmail.com` | `armandoalve@gmail.com` | accounts, platforms, email_age |
| 20 | 0.990 | `vihihid@gmail.com` | `kivsko91@gmail.com` | accounts, platforms, email_age |

## G — Auto-flagged observations

- saturation: `accounts` is 83.3% saturated — AXIS_MAX[`accounts`]=15 likely too low
- saturation: `platforms` is 93.3% saturated — AXIS_MAX[`platforms`]=10 likely too low
- saturation: `email_age` is 76.7% saturated — AXIS_MAX[`email_age_years`]=15 likely too low
- starved: `public_exposure` is zero for 100.0% of fingerprints — data plumbing or AXIS_MAX too high
- saturation cause confirmed: `accounts` raw ≥ AXIS_MAX (=15) in 83.3% of fingerprints
- saturation cause confirmed: `platforms` raw ≥ AXIS_MAX (=10) in 93.3% of fingerprints
- saturation cause confirmed: `username_reuse` raw ≥ AXIS_MAX (=5) in 23.3% of fingerprints
- saturation cause confirmed: `email_age` raw ≥ AXIS_MAX (=15) in 76.7% of fingerprints
- similarity threshold sanity: 90.11% of pairs ≥ 0.7 → threshold likely too low

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
