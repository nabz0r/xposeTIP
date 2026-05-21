# Fingerprint calibration diagnostic — dataminr

_Generated 2026-05-21 15:33 UTC · script S143-v1_

## A — Summary

- Workspace: **Dataminr** (`dataminr`, id `2ec3c06a-c3f4-4ccd-9838-ebfc647dc220`)
- Total targets: **9**
- Targets with fingerprint key: **9**
- Targets with extractable axes (_extract_axes ≠ None): **9**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 9 | 0.439 | 0.240 | 0.083 | 0.833 | 0.0 | 0.0 | 0.083 | 0.467 | 0.833 |
| platforms | 9 | 0.382 | 0.225 | 0.100 | 0.800 | 0.0 | 0.0 | 0.100 | 0.340 | 0.800 |
| username_reuse | 9 | 0.289 | 0.232 | 0.100 | 0.700 | 0.0 | 0.0 | 0.100 | 0.200 | 0.700 |
| breaches | 9 | 0.511 | 0.302 | 0.000 | 0.800 | 22.2 | 0.0 | 0.000 | 0.600 | 0.800 |
| geo_spread | 9 | 0.508 | 0.139 | 0.410 | 0.740 | 0.0 | 0.0 | 0.410 | 0.420 | 0.740 |
| data_leaked | 9 | 0.067 | 0.146 | 0.000 | 0.440 | 66.7 | 0.0 | 0.000 | 0.000 | 0.440 |
| email_age | 9 | 0.161 | 0.188 | 0.000 | 0.425 | 44.4 | 0.0 | 0.000 | 0.102 | 0.425 |
| security | 9 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| public_exposure | 9 | 0.028 | 0.083 | 0.000 | 0.250 | 88.9 | 0.0 | 0.000 | 0.000 | 0.250 |
| formal_records | 9 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |
| network_signature | 9 | 0.826 | 0.021 | 0.809 | 0.866 | 0.0 | 0.0 | 0.809 | 0.817 | 0.866 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ▅··▂▅█··▂·
platforms          ·▄·█▂·▂·▂·
username_reuse     ·█▄·▂▂▂···
breaches           ▃····█··▃·
geo_spread         ····█·▁▂··
data_leaked        █▁··▁·····
email_age          █▄·▂▄·····
security           █·········
public_exposure    █·▁·······
formal_records     █·········
network_signature  ········█·
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=60) | 9 | 26.333 | 14.387 | 5.000 | 50.000 | 0.0 | 5.000 | 28.000 | 50.000 |
| platforms (`platforms`, max=50) | 9 | 19.111 | 11.263 | 5.000 | 40.000 | 0.0 | 5.000 | 17.000 | 40.000 |
| username_reuse (`username_reuse`, max=10) | 9 | 2.889 | 2.315 | 1.000 | 7.000 | 0.0 | 1.000 | 2.000 | 7.000 |
| breaches (`breaches`, max=5) | 9 | 2.556 | 1.509 | 0.000 | 4.000 | 0.0 | 0.000 | 3.000 | 4.000 |
| geo_spread (`geo_spread`, max=5) | 9 | 2.539 | 0.695 | 2.050 | 3.700 | 0.0 | 2.050 | 2.100 | 3.700 |
| data_leaked (`data_leaked`, max=25) | 9 | 1.667 | 3.640 | 0.000 | 11.000 | 0.0 | 0.000 | 0.000 | 11.000 |
| email_age (`email_age_years`, max=40) | 9 | 6.444 | 7.502 | 0.000 | 17.000 | 0.0 | 0.000 | 4.100 | 17.000 |
| security (`security_weak`, max=4) | 9 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 9 | 0.028 | 0.083 | 0.000 | 0.250 | 0.0 | 0.000 | 0.000 | 0.250 |
| formal_records (`formal_records_raw`, max=5) | 9 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |
| network_signature (`network_signature_raw`, max=1.0) | 9 | 0.826 | 0.021 | 0.809 | 0.866 | 0.0 | 0.809 | 0.817 | 0.866 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ▅··▂▅█··▂·
platforms          ·▄·█▂·▂·▂·
username_reuse     ·█▂▂▂·▂▂··
breaches           ▃·····█·▃·
geo_spread         ····█·▁▂··
data_leaked        █▁··▁·····
email_age          █▄·▂▄·····
security           █·········
public_exposure    █·▁·······
formal_records     █·········
network_signature  ········█·
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 7 | 77.8% |
| 5 | 7 | 77.8% |
| 7 | 4 | 44.4% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **36** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.850 · stdev = 0.104

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 36 | 100.00% |
| 0.6 | 36 | 100.00% |
| 0.7 | 34 | 94.44% |
| 0.8 | 22 | 61.11% |
| 0.9 | 14 | 38.89% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ······▁▆▄█
```

**Threshold sanity:** 94.44% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 1.000 | `info@dataminr.com` | `dsouza@dataminr.com` | network_signature, geo_spread, platforms |
| 2 | 0.998 | `regina.bonsu@dataminr.com` | `becki.bailey@dataminr.com` | network_signature, username_reuse, breaches |
| 3 | 0.991 | `rbasset@dataminr.com` | `kpoulsen@dataminr.com` | network_signature, geo_spread, breaches |
| 4 | 0.970 | `balaji.yelamanchili@dataminr.com` | `regina.bonsu@dataminr.com` | network_signature, breaches, accounts |
| 5 | 0.968 | `tbailey@dataminr.com` | `kpoulsen@dataminr.com` | network_signature, geo_spread, platforms |
| 6 | 0.961 | `wbenner@dataminr.com` | `rbasset@dataminr.com` | network_signature, breaches, geo_spread |
| 7 | 0.960 | `balaji.yelamanchili@dataminr.com` | `becki.bailey@dataminr.com` | network_signature, breaches, accounts |
| 8 | 0.943 | `tbailey@dataminr.com` | `rbasset@dataminr.com` | network_signature, geo_spread, breaches |
| 9 | 0.938 | `balaji.yelamanchili@dataminr.com` | `wbenner@dataminr.com` | network_signature, breaches, geo_spread |
| 10 | 0.935 | `wbenner@dataminr.com` | `kpoulsen@dataminr.com` | network_signature, breaches, geo_spread |
| 11 | 0.927 | `balaji.yelamanchili@dataminr.com` | `rbasset@dataminr.com` | network_signature, breaches, accounts |
| 12 | 0.922 | `tbailey@dataminr.com` | `wbenner@dataminr.com` | network_signature, breaches, geo_spread |
| 13 | 0.920 | `balaji.yelamanchili@dataminr.com` | `kpoulsen@dataminr.com` | network_signature, breaches, accounts |
| 14 | 0.905 | `wbenner@dataminr.com` | `regina.bonsu@dataminr.com` | network_signature, breaches, geo_spread |
| 15 | 0.896 | `tbailey@dataminr.com` | `balaji.yelamanchili@dataminr.com` | network_signature, breaches, accounts |
| 16 | 0.887 | `regina.bonsu@dataminr.com` | `kpoulsen@dataminr.com` | network_signature, breaches, accounts |
| 17 | 0.885 | `regina.bonsu@dataminr.com` | `rbasset@dataminr.com` | network_signature, breaches, accounts |
| 18 | 0.881 | `wbenner@dataminr.com` | `becki.bailey@dataminr.com` | network_signature, breaches, geo_spread |
| 19 | 0.875 | `tbailey@dataminr.com` | `regina.bonsu@dataminr.com` | network_signature, breaches, accounts |
| 20 | 0.868 | `becki.bailey@dataminr.com` | `kpoulsen@dataminr.com` | network_signature, breaches, accounts |

## G — Auto-flagged observations

- starved: `security` is zero for 100.0% of fingerprints — data plumbing or AXIS_MAX too high
- starved: `public_exposure` is zero for 88.9% of fingerprints — data plumbing or AXIS_MAX too high
- starved: `formal_records` is zero for 100.0% of fingerprints — data plumbing or AXIS_MAX too high
- similarity threshold sanity: 94.44% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 4 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
