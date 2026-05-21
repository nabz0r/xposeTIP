# Fingerprint calibration diagnostic — nexus-2026

_Generated 2026-05-21 13:49 UTC · script S143-v1_

## A — Summary

- Workspace: **Nexus 2026** (`nexus-2026`, id `6e74ecc2-1081-4486-9b45-431fa5d68071`)
- Total targets: **21**
- Targets with fingerprint key: **19**
- Targets with extractable axes (_extract_axes ≠ None): **19**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 19 | 0.965 | 0.153 | 0.333 | 1.000 | 0.0 | 94.7 | 1.000 | 1.000 | 1.000 |
| platforms | 19 | 0.974 | 0.115 | 0.500 | 1.000 | 0.0 | 94.7 | 1.000 | 1.000 | 1.000 |
| username_reuse | 19 | 0.874 | 0.260 | 0.200 | 1.000 | 0.0 | 78.9 | 0.400 | 1.000 | 1.000 |
| breaches | 19 | 0.642 | 0.184 | 0.000 | 0.800 | 5.3 | 0.0 | 0.600 | 0.600 | 0.800 |
| geo_spread | 19 | 0.278 | 0.045 | 0.250 | 0.420 | 0.0 | 0.0 | 0.250 | 0.250 | 0.310 |
| data_leaked | 19 | 0.224 | 0.272 | 0.000 | 1.000 | 21.1 | 5.3 | 0.000 | 0.125 | 0.875 |
| email_age | 19 | 0.443 | 0.442 | 0.000 | 1.000 | 26.3 | 26.3 | 0.000 | 0.313 | 1.000 |
| security | 19 | 0.184 | 0.274 | 0.000 | 0.750 | 57.9 | 0.0 | 0.000 | 0.000 | 0.750 |
| public_exposure | 19 | 0.061 | 0.120 | 0.000 | 0.350 | 73.7 | 0.0 | 0.000 | 0.000 | 0.350 |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ··· ·····█
platforms          ····· ···█
username_reuse     ·· ·▁ ···█
breaches            ····█··▅·
geo_spread         ··█▄ ·····
data_leaked        ▄█▄▁····▁▁
email_age          ▆▁▂▃·····█
security           █·▃····▂··
public_exposure    █▁ ▁······
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=15) | 19 | 30.842 | 7.805 | 5.000 | 38.000 | 94.7 | 22.000 | 33.000 | 38.000 |
| platforms (`platforms`, max=10) | 19 | 15.789 | 2.800 | 5.000 | 19.000 | 94.7 | 14.000 | 16.000 | 18.000 |
| username_reuse (`username_reuse`, max=5) | 19 | 5.316 | 1.857 | 1.000 | 7.000 | 78.9 | 2.000 | 6.000 | 7.000 |
| breaches (`breaches`, max=5) | 19 | 3.211 | 0.918 | 0.000 | 4.000 | 0.0 | 3.000 | 3.000 | 4.000 |
| geo_spread (`geo_spread`, max=5) | 19 | 1.389 | 0.223 | 1.250 | 2.100 | 0.0 | 1.250 | 1.250 | 1.550 |
| data_leaked (`data_leaked`, max=8) | 19 | 1.842 | 2.340 | 0.000 | 9.000 | 5.3 | 0.000 | 1.000 | 7.000 |
| email_age (`email_age_years`, max=15) | 19 | 9.800 | 11.367 | 0.000 | 29.200 | 26.3 | 0.000 | 4.700 | 27.300 |
| security (`security_weak`, max=4) | 19 | 0.737 | 1.098 | 0.000 | 3.000 | 0.0 | 0.000 | 0.000 | 3.000 |
| public_exposure (`public_exposure_raw`, max=1.0) | 19 | 0.061 | 0.120 | 0.000 | 0.350 | 0.0 | 0.000 | 0.000 | 0.350 |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ··· ·····█
platforms          ····· ···█
username_reuse     ·· ·▁· ··█
breaches            ·····█·▅·
geo_spread         ··█▄ ·····
data_leaked        ▄█▄▁····▁▁
email_age          ▆▁▂▃·····█
security           █·▃····▂··
public_exposure    █▁ ▁······
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 19 | 100.0% |
| 5 | 18 | 94.7% |
| 7 | 13 | 68.4% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

- Total unique pairs: **171** (N·(N-1)/2)
- Ignoring the 0.70 storage filter applied by `similarity_engine`
- mean = 0.895 · stdev = 0.073

| threshold | count ≥ | % of pairs |
|--:|--:|--:|
| 0.5 | 171 | 100.00% |
| 0.6 | 171 | 100.00% |
| 0.7 | 169 | 98.83% |
| 0.8 | 151 | 88.30% |
| 0.9 | 89 | 52.05% |

Histogram (bin width 0.1):

```
similarity         0───────────────────────1
pair density       ······ ▁▅█
```

**Threshold sanity:** 98.83% of pairs ≥ 0.7. If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.

## F — Top 20 highest-similarity pairs (fresh recompute)

| rank | sim | target a (email) | target b (email) | top-3 co-axes |
|--:|--:|---|---|---|
| 1 | 1.000 | `pascal.steichen@lhc.lu` | `angelique.joyeux@lhc.lu` | accounts, platforms, username_reuse |
| 2 | 0.998 | `david.foy@luxinnovation.lu` | `jonas.mercier@luxinnovation.lu` | accounts, platforms, username_reuse |
| 3 | 0.998 | `michael.renotte@thedots.lu` | `virginie.huvelle@thedots.lu` | accounts, platforms, username_reuse |
| 4 | 0.995 | `david.foy@luxinnovation.lu` | `aurelie.paini@thedots.lu` | accounts, platforms, username_reuse |
| 5 | 0.995 | `cindy.tereba@cc.lu` | `aurelie.paini@thedots.lu` | accounts, platforms, username_reuse |
| 6 | 0.994 | `mike.koedinger@paperjam.lu` | `konstantin.notman@ocsial.com` | accounts, platforms, username_reuse |
| 7 | 0.993 | `jonas.mercier@luxinnovation.lu` | `aurelie.paini@thedots.lu` | accounts, platforms, username_reuse |
| 8 | 0.992 | `alexander.link@luxinnovation.lu` | `konstantin.notman@ocsial.com` | accounts, platforms, username_reuse |
| 9 | 0.992 | `cindy.tereba@cc.lu` | `jonas.mercier@luxinnovation.lu` | accounts, platforms, username_reuse |
| 10 | 0.991 | `sidonie.stire@thedots.lu` | `michael.renotte@thedots.lu` | accounts, platforms, username_reuse |
| 11 | 0.990 | `sidonie.stire@thedots.lu` | `cindy.tereba@cc.lu` | accounts, platforms, username_reuse |
| 12 | 0.990 | `michael.renotte@thedots.lu` | `cindy.tereba@cc.lu` | accounts, platforms, username_reuse |
| 13 | 0.989 | `david.foy@luxinnovation.lu` | `cindy.tereba@cc.lu` | accounts, platforms, username_reuse |
| 14 | 0.989 | `aurelie.paini@thedots.lu` | `thierry.labro@paperjam.lu` | accounts, platforms, username_reuse |
| 15 | 0.988 | `cindy.tereba@cc.lu` | `thierry.labro@paperjam.lu` | accounts, platforms, username_reuse |
| 16 | 0.986 | `jonas.mercier@luxinnovation.lu` | `thierry.labro@paperjam.lu` | accounts, platforms, username_reuse |
| 17 | 0.986 | `michael.renotte@thedots.lu` | `aurelie.paini@thedots.lu` | accounts, platforms, username_reuse |
| 18 | 0.985 | `alexander.link@luxinnovation.lu` | `sasha.baillie@luxinnovation.lu` | accounts, platforms, username_reuse |
| 19 | 0.984 | `david.foy@luxinnovation.lu` | `thierry.labro@paperjam.lu` | accounts, platforms, username_reuse |
| 20 | 0.984 | `aurelie.paini@thedots.lu` | `virginie.huvelle@thedots.lu` | accounts, platforms, username_reuse |

## G — Auto-flagged observations

- saturation: `accounts` is 94.7% saturated — AXIS_MAX[`accounts`]=15 likely too low
- saturation: `platforms` is 94.7% saturated — AXIS_MAX[`platforms`]=10 likely too low
- saturation: `username_reuse` is 78.9% saturated — AXIS_MAX[`username_reuse`]=5 likely too low
- saturation cause confirmed: `accounts` raw ≥ AXIS_MAX (=15) in 94.7% of fingerprints
- saturation cause confirmed: `platforms` raw ≥ AXIS_MAX (=10) in 94.7% of fingerprints
- saturation cause confirmed: `username_reuse` raw ≥ AXIS_MAX (=5) in 78.9% of fingerprints
- saturation cause confirmed: `email_age` raw ≥ AXIS_MAX (=15) in 26.3% of fingerprints
- similarity threshold sanity: 98.83% of pairs ≥ 0.7 → threshold likely too low

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
