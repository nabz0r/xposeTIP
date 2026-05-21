# Fingerprint calibration diagnostic — quentin

_Generated 2026-05-21 15:33 UTC · script S143-v1_

## A — Summary

- Workspace: **Quentin** (`quentin`, id `5f632c1c-c181-4a1f-8010-531e06626847`)
- Total targets: **30**
- Targets with fingerprint key: **30**
- Targets with extractable axes (_extract_axes ≠ None): **30**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 30 | 0.331 | 0.130 | 0.067 | 0.617 | 0.0 | 0.0 | 0.233 | 0.283 | 0.528 |
| platforms | 30 | 0.272 | 0.061 | 0.080 | 0.380 | 0.0 | 0.0 | 0.240 | 0.280 | 0.338 |
| username_reuse | 30 | 0.253 | 0.226 | 0.000 | 0.700 | 3.3 | 0.0 | 0.100 | 0.100 | 0.600 |
| breaches | 30 | 0.653 | 0.203 | 0.000 | 0.800 | 6.7 | 0.0 | 0.600 | 0.600 | 0.800 |
| geo_spread | 30 | 0.260 | 0.116 | 0.000 | 0.450 | 10.0 | 0.0 | 0.025 | 0.250 | 0.450 |
| data_leaked | 30 | 0.109 | 0.142 | 0.000 | 0.680 | 33.3 | 0.0 | 0.000 | 0.060 | 0.276 |
| email_age | 30 | 0.109 | 0.139 | 0.000 | 0.447 | 46.7 | 0.0 | 0.000 | 0.013 | 0.345 |
| security | 30 | 0.508 | 0.325 | 0.000 | 0.750 | 23.3 | 0.0 | 0.000 | 0.750 | 0.750 |
| public_exposure | 30 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| formal_records | 30 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| network_signature | 30 | 0.823 | 0.017 | 0.803 | 0.905 | 0.0 | 0.0 | 0.813 | 0.818 | 0.831 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ▁·█▂▃▁ ···
platforms            █▂······
username_reuse      █▂· ▂▁···
breaches           ▁····█··█·
geo_spread         ▁·█·▁·····
data_leaked        █▃▂··· ···
email_age          █▁▁▁ ·····
security           ▃·▁·· ·█··
public_exposure    █·········
formal_records     █·········
network_signature  ········█ 
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=60) | 30 | 19.867 | 7.807 | 4.000 | 37.000 | 0.0 | 14.000 | 17.000 | 31.700 |
| platforms (`platforms`, max=50) | 30 | 13.600 | 3.047 | 4.000 | 19.000 | 0.0 | 12.000 | 14.000 | 16.900 |
| username_reuse (`username_reuse`, max=10) | 30 | 2.533 | 2.255 | 0.000 | 7.000 | 0.0 | 1.000 | 1.000 | 6.000 |
| breaches (`breaches`, max=5) | 30 | 3.267 | 1.015 | 0.000 | 4.000 | 0.0 | 3.000 | 3.000 | 4.000 |
| geo_spread (`geo_spread`, max=5) | 30 | 1.300 | 0.578 | 0.000 | 2.250 | 0.0 | 0.125 | 1.250 | 2.250 |
| data_leaked (`data_leaked`, max=25) | 30 | 2.733 | 3.562 | 0.000 | 17.000 | 0.0 | 0.000 | 1.500 | 6.900 |
| email_age (`email_age_years`, max=40) | 30 | 4.343 | 5.543 | 0.000 | 17.900 | 0.0 | 0.000 | 0.500 | 13.800 |
| security (`security_weak`, max=4) | 30 | 2.033 | 1.299 | 0.000 | 3.000 | 0.0 | 0.000 | 3.000 | 3.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 30 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| formal_records (`formal_records_raw`, max=5) | 30 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| network_signature (`network_signature_raw`, max=1.0) | 30 | 0.823 | 0.017 | 0.803 | 0.905 | 0.0 | 0.813 | 0.818 | 0.831 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ▁·█▂▃ ▁···
platforms            █▅······
username_reuse      █▁▁ ·▂▁··
breaches           ▁·····█·█·
geo_spread         ▁·█ ▁·····
data_leaked        █▃▂··· ···
email_age          █▁▁▁ ·····
security           ▃·▁·· ·█··
public_exposure    █·········
formal_records     █·········
network_signature  ········█ 
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 29 | 96.7% |
| 5 | 28 | 93.3% |
| 7 | 17 | 56.7% |
| 9 | 3 | 10.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **435** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.868 · stdev = 0.106

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 435 | 100.00% |
| 0.6 | 420 | 96.55% |
| 0.7 | 401 | 92.18% |
| 0.8 | 333 | 76.55% |
| 0.9 | 211 | 48.51% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ·····  ▂▄█
```

**Threshold sanity:** 92.18% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 1.000 | `gmelahaye@gmail.com` | `drkavichopra@gmail.com` | network_signature, security, breaches |
| 2 | 0.999 | `vihihid@gmail.com` | `adrienfargue@gmail.com` | network_signature, breaches, security |
| 3 | 0.999 | `davidastratoff@gmail.com` | `sammynesville@gmail.com` | network_signature, breaches, security |
| 4 | 0.998 | `gmelahaye@gmail.com` | `guillaumelahaye@glgroup.fr` | network_signature, security, breaches |
| 5 | 0.998 | `drkavichopra@gmail.com` | `guillaumelahaye@glgroup.fr` | network_signature, security, breaches |
| 6 | 0.997 | `gmelahaye@gmail.com` | `g.lahaye.glimmobilier@gmail.com` | network_signature, security, breaches |
| 7 | 0.997 | `gmelahaye@gmail.com` | `drbastin38@gmail.com` | network_signature, security, breaches |
| 8 | 0.997 | `drkavichopra@gmail.com` | `g.lahaye.glimmobilier@gmail.com` | network_signature, security, breaches |
| 9 | 0.997 | `drkavichopra@gmail.com` | `drbastin38@gmail.com` | network_signature, security, breaches |
| 10 | 0.997 | `vihihid@gmail.com` | `juliefranck@gmail.com` | network_signature, breaches, security |
| 11 | 0.996 | `davidastratoff@gmail.com` | `adrienfargue@gmail.com` | network_signature, breaches, security |
| 12 | 0.996 | `g.lahaye.glimmobilier@gmail.com` | `guillaumelahaye@glgroup.fr` | network_signature, security, breaches |
| 13 | 0.996 | `drbastin38@gmail.com` | `guillaumelahaye@glgroup.fr` | network_signature, security, breaches |
| 14 | 0.996 | `adrienfargue@gmail.com` | `juliefranck@gmail.com` | network_signature, breaches, security |
| 15 | 0.994 | `adrienfargue@gmail.com` | `sammynesville@gmail.com` | network_signature, breaches, security |
| 16 | 0.994 | `vihihid@gmail.com` | `davidastratoff@gmail.com` | network_signature, breaches, security |
| 17 | 0.993 | `davidastratoff@gmail.com` | `juliefranck@gmail.com` | network_signature, breaches, security |
| 18 | 0.993 | `elyes.prudor@gmail.com` | `cnakache.kine@gmail.com` | network_signature, security, username_reuse |
| 19 | 0.992 | `thyfaine.knock@intertrustgroup.com` | `bruno.diogo@devinci.fr` | network_signature, username_reuse, breaches |
| 20 | 0.991 | `sammynesville@gmail.com` | `armandoalve@gmail.com` | network_signature, breaches, security |

## G — Auto-flagged observations

- starved: `public_exposure` is zero for 100.0% of fingerprints — data plumbing or AXIS_MAX too high
- starved: `formal_records` is zero for 100.0% of fingerprints — data plumbing or AXIS_MAX too high
- similarity threshold sanity: 92.18% of pairs ≥ 0.7 → threshold likely too low

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
