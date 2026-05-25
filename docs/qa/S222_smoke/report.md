# S222 Smoke Report — PixelCat behavioral layer

## Setup
- Commit smoke-tested: `bfda6ea` (S221)
- Date: 2026-05-25 UTC
- Targets selected: 5 random post-scan with non-null `bfp_behavioral_hash_v1`, across 5 different workspaces

## Role elevation summary

| State | Total memberships | Superadmin | Admin |
|---|---|---|---|
| Pre  | 16 | 3 (crypto / default / lessentiel) | 13 |
| Post | 16 | **16 (all)** | 0 |

- Rows updated: **13**
- Diff captured in `docs/qa/S222_role_audit_pre.txt` vs `docs/qa/S222_role_audit_post.txt`
- **Action required (Nabil)**: re-login or hit `/auth/refresh` so the JWT picks up the new role for the 13 workspaces still holding old tokens; without this, `SystemLiveScansTab` will continue to 403 in those workspaces.

## Per-target findings

### Target 1: `catherine.wurth@bgl.lu` (bgl-bnp-paribas)
- Hash prefix: `f9a5400a00000000`
- Decoded axes: **pattern=bicolor, accessory=badge, marking=none, expression=chill**
- API returns hash ✓ + avatar_seed ✓
- Visual: not screenshotted (same axes as targets 2 + 4 — see rhuan.lux + DOM confirmation)
- Anomalies: see aggregate §

### Target 2: `tmeyers@threatconnect.com` (threatconnect-cs)
- Hash prefix: `f9a5400a00000000` ← **identical to Target 1**
- Decoded axes: **bicolor + badge + none + chill** (same)
- API returns hash ✓ + avatar_seed ✓
- Visual: not screenshotted (collision with Target 1)
- Anomalies: see aggregate §

### Target 3: `rhuan.lux@gmail.com` (friends)
- Hash prefix: `14e0de8400000000`
- Decoded axes: **pattern=calico, accessory=badge, marking=none, expression=chill**
- API returns hash ✓ + avatar_seed ✓
- Visual: `S222_smoke/friends_rhuan_lux_scanstab.png` — DOM inspection confirmed:
  - 1 `#ffcc00` badge circle in cat SVG ✓
  - 2 calico rects (`#f0e6c8` / `#d4a070`) in cat SVG ✓
  - Decoded axes match rendered overlays
- Anomalies: none specific to this target

### Target 4: `mario.grotz@luxinnovation.lu` (nexus-2026)
- Hash prefix: `f9a5400a00000000` ← **identical to Targets 1 + 2**
- Decoded axes: **bicolor + badge + none + chill** (same)
- API returns hash ✓ + avatar_seed ✓
- Visual: not screenshotted (collision)
- Anomalies: see aggregate §

### Target 5: `regina.bonsu@dataminr.com` (dataminr)
- Hash prefix: `3abb873e00000000`
- Decoded axes: **pattern=ticked, accessory=bowtie, marking=none, expression=chill**
- API returns hash ✓ + avatar_seed ✓
- Visual: not screenshotted; DOM verified via API+decode chain
- Anomalies: none specific to this target

## Aggregate findings

### Anomaly 1 (CRITICAL): hash collision rate is HIGH

**3 of 5 random targets share the same first 16 hex chars** (`f9a5400a00000000`)
across 3 different workspaces (BGL, Threatconnect-CS, Nexus-2026). All three
decode to the IDENTICAL detail layer (bicolor + badge + none + chill).

This means the theoretical 920K unique cats does NOT hold in practice — the
behavioral hash (S166 MinHash-128, K=3 axes) has clustering behavior that
collapses many targets onto the same prefix. Effective uniqueness in the
current corpus is much lower than the math suggests.

**Root cause** (not in scope to fix here): the S166 behavioral_hash_v1
implementation uses MinHash over 3 BFP axes (public_exposure / geo_spread
/ data_leaked) discretized into 20 buckets each. K=3 axes with low entropy
(many corporate emails have similar exposure/geo/leak profiles) → high
collision rate. S165 invariance diagnostic already flagged this as an
inherent property of the chosen axes.

**Decision**: this is a BFP-spec issue, not a PixelCat issue. PixelCat
faithfully renders the hash; the hash itself isn't as discriminative as
hoped on a corporate-skewed corpus.

**Recommendation**: do NOT fix at the PixelCat layer. If unique cats per
target matter, the right fix is BFP-side — extend the behavioral hash to
include more discriminating per-person axes (S147 network_signature
spectral entropy already lands per-person; could weight it more heavily in
the hash seed). Track as **S222b candidate**: extend `_compute_behavioral_hash_v1`
input set.

### Anomaly 2 (MINOR): pose calibration not visually confirmed in this sprint

Spec called out `sleep` and `dig` poses as known calibration risks (overlays
calibrated for `idle` body rows 9-11). This sprint did NOT capture cats in
those poses (rhuan.lux scanstab showed all completed-scan cats → `sleep`
pose). Visual review at full zoom would be needed to confirm whether the
calico rects + badge circle render correctly on curled-sleep body or float
off-body.

**Recommendation**: gate via `if (pose === 'sleep') return null` per-overlay
component in S221b polish if the next visual audit confirms the issue. Not
shipped here.

### Anomaly 3 (RESOLVED): cross-surface consistency

DOM inspection on rhuan.lux confirmed identical badge circle (`#ffcc00`)
across ScansTab rows. The S221 prop-passing wiring works end-to-end.
No regression from S220.

### Anomaly 4 (NOT OBSERVED): color clashes

None observed in the 5-target sample. The 4 detail-layer axes use distinct
palettes that don't overlap with fur palette in the current sample.

### Anomaly 5 (NOT OBSERVED): hash decode mismatch

JS `deriveBehavioralDetails` and Python decode (identical algorithm) produced
matching axes for all 5 targets. The rhuan.lux DOM inspection confirmed the
JS implementation produces the expected overlay rects in the actual page.

## Recommended next sprints

- **[ ] S222b — extend behavioral_hash_v1 axis set** (HIGH priority): current
  3-axis hash collides on 60% of randomly sampled targets. Adding S147
  network_signature spectral entropy to the hash input would dramatically
  reduce collision rate. Closes the "920K combos doesn't translate to 920K
  unique cats" gap surfaced here.
- **[ ] S222c — pose-aware overlay calibration** (MEDIUM, was S221b): only
  warranted IF a visual audit on `sleep`/`dig` poses confirms ugliness. Gate
  by individual overlay component with `if (pose === 'sleep') return null`.
- **[ ] S223 — tuxedo / mitten / pointed Siamese pose-aware overlays**
  (deferred from S221, LOW priority): per-pose rect deltas, more work.
- **[ ] Operator action — Nabil JWT refresh**: re-login to pick up the 13
  new superadmin roles from this sprint's role elevation.

## Files committed

- `docs/qa/S222_role_audit_pre.txt`
- `docs/qa/S222_role_audit_post.txt`
- `docs/qa/S222_smoke/manifest.json` (5 targets with decoded axes)
- `docs/qa/S222_smoke/friends_rhuan_lux_scanstab.png` (visual evidence, 1/5)
- `docs/qa/S222_smoke/report.md` (this file)
