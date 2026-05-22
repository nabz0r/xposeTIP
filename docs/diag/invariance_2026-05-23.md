# BFP invariance diagnostic — 2026-05-23

**HEAD:** `fb0c2486`
**Workspace scope:** `all`
**Corpus:** 206 targets analyzed (≥2 snapshots), avg 6.98 snapshots/target (min=2, max=47)
**Methodology:** per S165 spec — mean absolute delta + CV + range per (target, axis), aggregated across corpus.

Snapshot shape (verified via psql before run): `{"axes": {<name>: float}, "raw_values": {...}, "score": int, "hash": str, "computed_at": ISO}`.
Older snapshots (pre-S145 / pre-S147) lack `formal_records` / `network_signature` axes — affected targets contribute shorter series for those axes; `n_targets` per axis reflects the actual observed coverage.

## 1. Axis stability ranking

Ascending by `mean_of_mean_abs_delta` (most stable first).

Two complementary signals: **intra-target stability** (axis doesn't drift for ONE person across re-scans — `Mean abs delta` low) AND **inter-target discrimination** (axis varies BETWEEN people — `Across-pop stdev` non-trivial, `Unique` buckets > a handful). A canonical-hash-worthy axis needs BOTH.

| Rank | Axis | Mean abs delta | Median abs delta | Mean range | Max range | Across-pop stdev | Across-pop min..max | Unique | N targets |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `security` | 0.000000 | 0.000000 | 0.0000 | 0.0000 | 0.3066 | 0.000..0.750 | 4 | 206 |
| 2 | `public_exposure` | 0.002687 | 0.000000 | 0.0071 | 0.2820 | 0.0910 | 0.000..0.350 | 18 | 189 |
| 3 | `network_signature` | 0.008003 | 0.000000 | 0.0080 | 0.1890 | 0.2617 | 0.000..0.908 | 9 | 143 |
| 4 | `geo_spread` | 0.021084 | 0.004356 | 0.0861 | 0.8000 | 0.1213 | 0.000..1.000 | 36 | 206 |
| 5 | `formal_records` | 0.027963 | 0.000000 | 0.0522 | 1.0000 | 0.1560 | 0.000..1.000 | 9 | 180 |
| 6 | `data_leaked` | 0.030369 | 0.011753 | 0.1629 | 1.0000 | 0.1669 | 0.000..1.000 | 45 | 206 |
| 7 | `username_reuse` | 0.081134 | 0.075000 | 0.3301 | 1.0000 | 0.2806 | 0.000..1.000 | 52 | 206 |
| 8 | `breaches` | 0.108046 | 0.120000 | 0.4476 | 0.8000 | 0.1966 | 0.000..0.800 | 44 | 206 |
| 9 | `accounts` | 0.112728 | 0.112500 | 0.4564 | 0.8000 | 0.2172 | 0.030..1.000 | 70 | 206 |
| 10 | `email_age` | 0.130958 | 0.123482 | 0.5647 | 1.0000 | 0.2283 | 0.000..1.000 | 61 | 206 |
| 11 | `platforms` | 0.134212 | 0.165000 | 0.5765 | 0.9000 | 0.2089 | 0.000..1.000 | 63 | 206 |

## 2. Cumulative coverage

If we include only the top K most-stable axes, what fraction of the inverse-stability budget do they capture?

| K | Axes included | Cumulative coverage |
|---|---|---|
| 1 | `security` | 100.0% |
| 2 | `security` · `public_exposure` | 100.0% |
| 3 | `security` · `public_exposure` · `network_signature` | 100.0% |
| 4 | `security` · `public_exposure` · `network_signature` · `geo_spread` | 100.0% |
| 5 | `security` · `public_exposure` · `network_signature` · `geo_spread` · `formal_records` | 100.0% |
| 6 | `security` · `public_exposure` · `network_signature` · `geo_spread` · `formal_records` · `data_leaked` | 100.0% |
| 7 | `security` · `public_exposure` · `network_signature` · `geo_spread` · `formal_records` · `data_leaked` · `username_reuse` | 100.0% |
| 8 | `security` · `public_exposure` · `network_signature` · `geo_spread` · `formal_records` · `data_leaked` · `username_reuse` · `breaches` | 100.0% |
| 9 | `security` · `public_exposure` · `network_signature` · `geo_spread` · `formal_records` · `data_leaked` · `username_reuse` · `breaches` · `accounts` | 100.0% |
| 10 | `security` · `public_exposure` · `network_signature` · `geo_spread` · `formal_records` · `data_leaked` · `username_reuse` · `breaches` · `accounts` · `email_age` | 100.0% |
| 11 | `security` · `public_exposure` · `network_signature` · `geo_spread` · `formal_records` · `data_leaked` · `username_reuse` · `breaches` · `accounts` · `email_age` · `platforms` | 100.0% |

**Observation:** curve shows a knee at K=1 — beyond this, each added axis contributes <5% additional inverse-stability coverage.

## 3. Per-target deep dive

### Most-stable target sample (3 targets)

- **`ebc95942-7a81-484f-90ac-caf6c9489603`** — 2 snapshots, 9 axes measured
  - Top 3 stable: `accounts` (0.0000), `breaches` (0.0000), `security` (0.0000)
  - Top 3 drifting: `public_exposure` (0.0000), `username_reuse` (0.0000), `data_leaked` (0.0000)
- **`46ee201a-230c-4ea3-a97a-272c7bc41be4`** — 4 snapshots, 10 axes measured
  - Top 3 stable: `breaches` (0.0000), `security` (0.0000), `email_age` (0.0000)
  - Top 3 drifting: `data_leaked` (0.0283), `accounts` (0.0167), `formal_records` (0.0000)
- **`af4e6677-2f61-4452-8827-b167acc7a71e`** — 7 snapshots, 10 axes measured
  - Top 3 stable: `breaches` (0.0000), `security` (0.0000), `email_age` (0.0000)
  - Top 3 drifting: `data_leaked` (0.0350), `geo_spread` (0.0250), `accounts` (0.0083)

### Least-stable target sample (3 targets)

- **`6db581cd-a43a-4256-ae97-4c1f5519bf12`** — 2 snapshots, 11 axes measured
  - Top 3 stable: `security` (0.0000), `data_leaked` (0.0000), `public_exposure` (0.0000)
  - Top 3 drifting: `formal_records` (1.0000), `breaches` (0.6000), `accounts` (0.5500)
- **`a4360e44-211a-468a-a671-143835ab0b1b`** — 2 snapshots, 11 axes measured
  - Top 3 stable: `security` (0.0000), `formal_records` (0.0000), `public_exposure` (0.0000)
  - Top 3 drifting: `username_reuse` (0.8000), `breaches` (0.8000), `accounts` (0.6830)
- **`ca836e7f-fce0-40e4-b773-351157d6612e`** — 2 snapshots, 11 axes measured
  - Top 3 stable: `security` (0.0000), `email_age` (0.0000), `data_leaked` (0.0000)
  - Top 3 drifting: `username_reuse` (0.8000), `accounts` (0.6330), `breaches` (0.6000)

### Outliers

Targets where one or more axes exceed the corpus p95 mean_abs_delta. Top 5 by exceeding-axis count.

- **`6db581cd-a43a-4256-ae97-4c1f5519bf12`** — 8 axes above p95: `accounts`(0.5500), `breaches`(0.6000), `email_age`(0.2920), `platforms`(0.4200), `geo_spread`(0.2500), `formal_records`(1.0000)
- **`ef355b6f-be47-4ce7-ad8f-03e995996b5c`** — 6 axes above p95: `accounts`(0.5160), `breaches`(0.6000), `platforms`(0.3400), `geo_spread`(0.2500), `username_reuse`(0.4000), `network_signature`(0.1830)
- **`cdee8a3e-0c2b-4492-bb76-e3186ebb5bc8`** — 6 axes above p95: `accounts`(0.5500), `breaches`(0.6000), `platforms`(0.3400), `geo_spread`(0.2500), `username_reuse`(0.7000), `network_signature`(0.1830)
- **`a4360e44-211a-468a-a671-143835ab0b1b`** — 6 axes above p95: `accounts`(0.6830), `breaches`(0.8000), `platforms`(0.4400), `geo_spread`(0.2500), `username_reuse`(0.8000), `network_signature`(0.0400)
- **`342b1ab3-0d48-4c63-9aa0-025cbb83a039`** — 6 axes above p95: `accounts`(0.4000), `breaches`(0.6000), `platforms`(0.3200), `geo_spread`(0.2500), `username_reuse`(0.4000), `network_signature`(0.1860)

## 4. Recommendation for S166

Based on observed distribution across 206 targets:

- **Coverage-curve degenerate:** ≥1 axis has near-zero mean_abs_delta (perfectly invariant per-target), so the inverse-stability weight collapses to that axis. Don't read K from coverage alone — read the per-axis table.

- **Most stable single axis (lowest delta):** `security`.
- **Top 3 most stable:** `security`, `public_exposure`, `network_signature`.
- **Stable AND discriminating** (mean_abs_delta < 0.05 AND ≥10 unique-bucket values across targets): `public_exposure`, `geo_spread`, `data_leaked` — best candidates for canonical hash inclusion.

- **Caveats (stable-mean, high-tail):**
  - `geo_spread` is stable on average (mean_abs_delta=0.0211) but has been observed to swing as much as 0.80 for at least one target — investigate the affected target before relying on it for canonical hash
  - `formal_records` is stable on average (mean_abs_delta=0.0280) but has been observed to swing as much as 1.00 for at least one target — investigate the affected target before relying on it for canonical hash
  - `data_leaked` is stable on average (mean_abs_delta=0.0304) but has been observed to swing as much as 1.00 for at least one target — investigate the affected target before relying on it for canonical hash

- **Decision deferred to operator:** the exact K and any per-axis weighting in MinHash construction. This report measures, it does not decide.

---

_Generated by `scripts/bfp_invariance_diag.py` at 2026-05-22T22:24:55.505260+00:00._
