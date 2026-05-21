# Fingerprint calibration diagnostic — nexus-2026

_Generated 2026-05-21 14:56 UTC · script S143-v1_

## A — Summary

- Workspace: **Nexus 2026** (`nexus-2026`, id `6e74ecc2-1081-4486-9b45-431fa5d68071`)
- Total targets: **21**
- Targets with fingerprint key: **19**
- Targets with extractable axes (_extract_axes ≠ None): **19**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 19 | 0.514 | 0.130 | 0.083 | 0.633 | 0.0 | 0.0 | 0.367 | 0.550 | 0.633 |
| platforms | 19 | 0.316 | 0.056 | 0.100 | 0.380 | 0.0 | 0.0 | 0.280 | 0.320 | 0.360 |
| username_reuse | 19 | 0.532 | 0.186 | 0.100 | 0.700 | 0.0 | 0.0 | 0.200 | 0.600 | 0.700 |
| breaches | 19 | 0.642 | 0.184 | 0.000 | 0.800 | 5.3 | 0.0 | 0.600 | 0.600 | 0.800 |
| geo_spread | 19 | 0.313 | 0.029 | 0.250 | 0.420 | 0.0 | 0.0 | 0.310 | 0.310 | 0.310 |
| data_leaked | 19 | 0.074 | 0.094 | 0.000 | 0.360 | 21.1 | 0.0 | 0.000 | 0.040 | 0.280 |
| email_age | 19 | 0.055 | 0.112 | 0.000 | 0.352 | 68.4 | 0.0 | 0.000 | 0.000 | 0.323 |
| security | 19 | 0.184 | 0.274 | 0.000 | 0.750 | 57.9 | 0.0 | 0.000 | 0.000 | 0.750 |
| public_exposure | 19 | 0.061 | 0.120 | 0.000 | 0.350 | 73.7 | 0.0 | 0.000 | 0.000 | 0.350 |
| formal_records | 19 | 0.000 | 0.000 | 0.000 | 0.000 | 100.0 | 0.0 | 0.000 | 0.000 | 0.000 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts            ·· ▂█▄···
platforms          ·  █······
username_reuse     · ▂··█▂···
breaches            ····█··▅·
geo_spread         ·· █ ·····
data_leaked        █   ······
email_age          █▁·▁······
security           █·▃····▂··
public_exposure    █▁ ▁······
formal_records     █·········
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=60) | 19 | 30.842 | 7.805 | 5.000 | 38.000 | 0.0 | 22.000 | 33.000 | 38.000 |
| platforms (`platforms`, max=50) | 19 | 15.789 | 2.800 | 5.000 | 19.000 | 0.0 | 14.000 | 16.000 | 18.000 |
| username_reuse (`username_reuse`, max=10) | 19 | 5.316 | 1.857 | 1.000 | 7.000 | 0.0 | 2.000 | 6.000 | 7.000 |
| breaches (`breaches`, max=5) | 19 | 3.211 | 0.918 | 0.000 | 4.000 | 0.0 | 3.000 | 3.000 | 4.000 |
| geo_spread (`geo_spread`, max=5) | 19 | 1.563 | 0.147 | 1.250 | 2.100 | 0.0 | 1.550 | 1.550 | 1.550 |
| data_leaked (`data_leaked`, max=25) | 19 | 1.842 | 2.340 | 0.000 | 9.000 | 0.0 | 0.000 | 1.000 | 7.000 |
| email_age (`email_age_years`, max=40) | 19 | 2.200 | 4.487 | 0.000 | 14.100 | 0.0 | 0.000 | 0.000 | 12.900 |
| security (`security_weak`, max=4) | 19 | 0.737 | 1.098 | 0.000 | 3.000 | 0.0 | 0.000 | 0.000 | 3.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 19 | 0.061 | 0.120 | 0.000 | 0.350 | 0.0 | 0.000 | 0.000 | 0.350 |
| formal_records (`formal_records_raw`, max=5) | 19 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 | 0.000 | 0.000 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts            ·· ▂█▄···
platforms          ·  █······
username_reuse     · ▁ · █▃··
breaches            ·····█·▅·
geo_spread         ·· █ ·····
data_leaked        █   ······
email_age          █▁·▁······
security           █·▃····▂··
public_exposure    █▁ ▁······
formal_records     █·········
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 18 | 94.7% |
| 5 | 18 | 94.7% |
| 7 | 5 | 26.3% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **171** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.875 · stdev = 0.124

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 170 | 99.42% |
| 0.6 | 160 | 93.57% |
| 0.7 | 148 | 86.55% |
| 0.8 | 137 | 80.12% |
| 0.9 | 94 | 54.97% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ····  ▁ ▃█
```

**Threshold sanity:** 86.55% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 1.000 | `pascal.steichen@lhc.lu` | `angelique.joyeux@lhc.lu` | security, username_reuse, breaches |
| 2 | 1.000 | `michael.renotte@thedots.lu` | `aurelie.paini@thedots.lu` | username_reuse, breaches, accounts |
| 3 | 1.000 | `alexander.link@luxinnovation.lu` | `jonas.mercier@luxinnovation.lu` | breaches, accounts, username_reuse |
| 4 | 0.999 | `alexander.link@luxinnovation.lu` | `david.foy@luxinnovation.lu` | breaches, accounts, username_reuse |
| 5 | 0.999 | `david.foy@luxinnovation.lu` | `jonas.mercier@luxinnovation.lu` | breaches, accounts, username_reuse |
| 6 | 0.998 | `aurelie.paini@thedots.lu` | `virginie.huvelle@thedots.lu` | username_reuse, breaches, accounts |
| 7 | 0.998 | `michael.renotte@thedots.lu` | `virginie.huvelle@thedots.lu` | username_reuse, breaches, accounts |
| 8 | 0.996 | `sidonie.stire@thedots.lu` | `aurelie.paini@thedots.lu` | username_reuse, breaches, accounts |
| 9 | 0.995 | `sidonie.stire@thedots.lu` | `michael.renotte@thedots.lu` | username_reuse, breaches, accounts |
| 10 | 0.995 | `sidonie.stire@thedots.lu` | `cindy.tereba@cc.lu` | username_reuse, breaches, accounts |
| 11 | 0.994 | `mike.koedinger@paperjam.lu` | `thierry.labro@paperjam.lu` | username_reuse, breaches, accounts |
| 12 | 0.993 | `cindy.tereba@cc.lu` | `michael.renotte@thedots.lu` | username_reuse, breaches, accounts |
| 13 | 0.993 | `cindy.tereba@cc.lu` | `aurelie.paini@thedots.lu` | username_reuse, breaches, accounts |
| 14 | 0.993 | `michael.renotte@thedots.lu` | `david.foy@luxinnovation.lu` | username_reuse, breaches, accounts |
| 15 | 0.993 | `michael.renotte@thedots.lu` | `jonas.mercier@luxinnovation.lu` | username_reuse, breaches, accounts |
| 16 | 0.992 | `aurelie.paini@thedots.lu` | `jonas.mercier@luxinnovation.lu` | username_reuse, breaches, accounts |
| 17 | 0.992 | `sidonie.stire@thedots.lu` | `virginie.huvelle@thedots.lu` | username_reuse, breaches, accounts |
| 18 | 0.992 | `david.foy@luxinnovation.lu` | `aurelie.paini@thedots.lu` | username_reuse, breaches, accounts |
| 19 | 0.992 | `alexander.link@luxinnovation.lu` | `michael.renotte@thedots.lu` | username_reuse, breaches, accounts |
| 20 | 0.992 | `alexander.link@luxinnovation.lu` | `aurelie.paini@thedots.lu` | username_reuse, breaches, accounts |

## G — Auto-flagged observations

- starved: `formal_records` is zero for 100.0% of fingerprints — data plumbing or AXIS_MAX too high
- similarity threshold sanity: 86.55% of pairs ≥ 0.7 → threshold likely too low
- calibration thin: only 5 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
