# Fingerprint calibration diagnostic — ferrero

_Generated 2026-05-21 13:53 UTC · script S143-v1_

## A — Summary

- Workspace: **Ferrero** (`ferrero`, id `1d6f7b40-b038-4403-a54b-c8a32c026f95`)
- Total targets: **14**
- Targets with fingerprint key: **1**
- Targets with extractable axes (_extract_axes ≠ None): **1**

## B — Per-axis normalized distribution

| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts | 1 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | — | — | — |
| platforms | 1 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | — | — | — |
| username_reuse | 1 | 0.400 | 0.000 | 0.400 | 0.400 | 0.0 | 0.0 | — | — | — |
| breaches | 1 | 0.800 | 0.000 | 0.800 | 0.800 | 0.0 | 0.0 | — | — | — |
| geo_spread | 1 | 0.650 | 0.000 | 0.650 | 0.650 | 0.0 | 0.0 | — | — | — |
| data_leaked | 1 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | — | — | — |
| email_age | 1 | 1.000 | 0.000 | 1.000 | 1.000 | 0.0 | 100.0 | — | — | — |
| security | 1 | 0.750 | 0.000 | 0.750 | 0.750 | 0.0 | 0.0 | — | — | — |
| public_exposure | 1 | 0.080 | 0.000 | 0.080 | 0.080 | 0.0 | 0.0 | — | — | — |

Histogram bars (bin width 0.1, last bin includes 1.0):

```
axis               0───────────────────────1
accounts           ·········█
platforms          ·········█
username_reuse     ····█·····
breaches           ········█·
geo_spread         ······█···
data_leaked        ·········█
email_age          ·········█
security           ·······█··
public_exposure    █·········
```

## C — Per-axis raw distribution

| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| accounts (`accounts`, max=15) | 1 | 32.000 | 0.000 | 32.000 | 32.000 | 100.0 | — | — | — |
| platforms (`platforms`, max=10) | 1 | 22.000 | 0.000 | 22.000 | 22.000 | 100.0 | — | — | — |
| username_reuse (`username_reuse`, max=5) | 1 | 2.000 | 0.000 | 2.000 | 2.000 | 0.0 | — | — | — |
| breaches (`breaches`, max=5) | 1 | 4.000 | 0.000 | 4.000 | 4.000 | 0.0 | — | — | — |
| geo_spread (`geo_spread`, max=5) | 1 | 3.250 | 0.000 | 3.250 | 3.250 | 0.0 | — | — | — |
| data_leaked (`data_leaked`, max=8) | 1 | 19.000 | 0.000 | 19.000 | 19.000 | 100.0 | — | — | — |
| email_age (`email_age_years`, max=15) | 1 | 22.000 | 0.000 | 22.000 | 22.000 | 100.0 | — | — | — |
| security (`security_weak`, max=4) | 1 | 3.000 | 0.000 | 3.000 | 3.000 | 0.0 | — | — | — |
| public_exposure (`public_exposure_raw`, max=1.0) | 1 | 0.080 | 0.000 | 0.080 | 0.080 | 0.0 | — | — | — |

Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):

```
axis               0───────────────────AXIS_MAX
accounts           ·········█
platforms          ·········█
username_reuse     ····█·····
breaches           ········█·
geo_spread         ······█···
data_leaked        ·········█
email_age          ·········█
security           ·······█··
public_exposure    █·········
```

## D — Rich-target count

Targets where ≥K of 9 axes have normalized value > 0.1:

| K | count | % of n_extractable |
|--:|--:|--:|
| 3 | 1 | 100.0% |
| 5 | 1 | 100.0% |
| 7 | 1 | 100.0% |
| 9 | 0 | 0.0% |

## E — Pairwise cosine similarity (fresh recompute, full distribution)

_Fewer than 2 extractable targets — no pairs possible._

## F — Top 20 highest-similarity pairs (fresh recompute)

_No pairs computed._

## G — Auto-flagged observations

- saturation: `accounts` is 100.0% saturated — AXIS_MAX[`accounts`]=15 likely too low
- saturation: `platforms` is 100.0% saturated — AXIS_MAX[`platforms`]=10 likely too low
- saturation: `data_leaked` is 100.0% saturated — AXIS_MAX[`data_leaked`]=8 likely too low
- saturation: `email_age` is 100.0% saturated — AXIS_MAX[`email_age_years`]=15 likely too low
- saturation cause confirmed: `accounts` raw ≥ AXIS_MAX (=15) in 100.0% of fingerprints
- saturation cause confirmed: `platforms` raw ≥ AXIS_MAX (=10) in 100.0% of fingerprints
- saturation cause confirmed: `data_leaked` raw ≥ AXIS_MAX (=8) in 100.0% of fingerprints
- saturation cause confirmed: `email_age` raw ≥ AXIS_MAX (=15) in 100.0% of fingerprints
- calibration thin: only 1 targets have ≥7/9 axes populated (>0.1) — consider growing the corpus before tuning weights

---

_Heuristic flags only. Read the data above and decide. Re-run this script after data growth or normalization tweaks to track drift._
