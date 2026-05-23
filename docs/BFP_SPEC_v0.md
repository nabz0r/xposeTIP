<!--
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 Nabil Ksontini
Behavioral Fingerprint Protocol — Specification v0 (working draft)
-->

# Behavioral Fingerprint Protocol — Specification v0

**Status**: Public working draft. Released for external review and external implementation feedback.
**Version**: 0.2.2
**Date**: 2026-05-23
**License**: Apache License 2.0
**Editor**: Nabil Ksontini

---

## 1. Status of This Document

This document is a public working draft of the **Behavioral Fingerprint Protocol** (BFP). It specifies a vendor-neutral representation of behavioral identity fingerprints derived from open-source intelligence sources. It is not a published standard. It is intended to capture, in normative form, the implicit protocol currently implemented by the xposeTIP reference implementation, and to serve as the basis for future public release.

This v0.2 draft is **code-agnostic on normalization functions and threshold values**: those are left to implementations. The protocol fixes the *structure* (axes, layers, vector format, similarity model, trust-layer mechanisms) but not the exact mathematics of any single axis.

The v0.2.x series is formalized across three editorial sessions: Session 1 (v0.2.0) established the trust layer mechanics in §15-17. Session 2 sub-A (v0.2.1) formalized the trust-layer terminology, conceptual model, conformance, subject-rights tiers, and component versioning. Session 2 sub-B (v0.2.2, this revision) adds per-axis implementation status flags (§5) and the behavioral hash specification (§9.3). Session 2 continues in v0.2.3 with the post-quantum cryptography stack (§13).

This draft is licensed under the Apache License, Version 2.0. Implementation and adoption feedback is welcome via the project repository.

---

## 2. Introduction

### 2.1 Purpose

Traditional indicators of compromise (IPs, file hashes, domains) lose value within hours or days. The identity behind digital activity persists. The Behavioral Fingerprint Protocol provides a vendor-neutral, interoperable representation of that persistent identity layer.

A **behavioral fingerprint** is a structured representation of an entity's observable behavior across multiple dimensions of digital identity. Two fingerprints can be compared to assess the probability that they represent the same underlying entity, even when surface indicators (usernames, email addresses, IP addresses) differ.

### 2.2 Scope

This specification defines:

- The conceptual model of a behavioral fingerprint as a confidence-weighted vector across 16 axes organized in 6 layers.
- Normative requirements for each axis (definition, drift behavior, empty-state semantics).
- The serialization format for fingerprints.
- The similarity computation between two fingerprints.
- A provenance model for fingerprint outputs.
- Conformance requirements for implementations.

This specification does **not** define:

- The specific signal sources that implementations must use (those are implementation-defined).
- The specific normalization function for any single axis (those are implementation-defined, subject to the constraints in §6).
- The threshold value for declaring two fingerprints "matched" (that is profile-defined; see §8).
- Storage or transport protocols beyond the serialization format.

### 2.3 Non-Goals

**BFP is not an identification protocol.** A high similarity score between two fingerprints is a probabilistic indicator, not a verified identity claim. Implementations and consumers MUST NOT treat BFP output as proof of identity for legal, financial, or adjudicative purposes without independent corroboration.

**BFP fingerprints are not unique identifiers.** The behavioral axes defined in §5, taken together, encode approximately 28 bits of Shannon entropy in current implementations. At planet-scale subject populations (≥4×10⁹ humans), every fingerprint bucket is occupied by millions of distinct subjects. A BFP fingerprint is therefore a **clustering primitive** — useful for narrowing a candidate set, computing similarity, and grouping related observations — and **not** a primitive sufficient for asserting "this fingerprint identifies subject X uniquely."

Unique identity in BFP arises only through **composition**:

- the behavioral fingerprint hash (§9.2) as a clustering anchor, plus
- a **subject binding signature** (§13) bound to the subject through a ceremony involving evidence outside the fingerprint axes (e.g., possession of a cryptographic key, control of a known identifier), plus
- optional **network-layer signals** (future versions; §14), which add substantially more entropy than the behavioral axes alone provide.

Implementations that derive identity decisions from a behavioral hash alone are non-conformant with the spirit of this specification and MUST NOT advertise such use as "BFP identification."

**BFP does not aggregate, surveil, or profile beyond the subject's own consent boundary**, in the sense defined in §12. The protocol's purpose is to return knowledge of the subject's own fingerprint *to the subject*, not to construct new surveillance capability. This is a non-goal stated in normative form: the protocol's specification deliberately omits primitives (e.g., cross-subject linking without explicit subject query, mass-population scoring) that would be required for surveillance applications.

---

## 3. Terminology and Conventions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119 and RFC 8174.

### 3.1 Definitions

#### Fingerprint-layer terms (v0.1+)

- **Entity**: the underlying subject (typically a natural person) whose behavior is being characterized. Used interchangeably with **Subject** in the trust-layer context.
- **Subject**: a natural person whose behavioral fingerprint is being computed. Subject is the trust-layer term; entity is the fingerprint-layer term. They refer to the same real-world person.
- **Observation**: data collected about an entity from one or more sources at a given point in time.
- **Axis**: a single normative dimension of behavioral identity, producing a scalar value and confidence.
- **Layer**: a grouping of axes that share a conceptual category (Surface, Forensic, Temporal, Linguistic, Relational, Adverse).
- **Fingerprint**: the complete confidence-weighted vector across all 16 axes for a given entity at a given observation time.
- **Implementation**: software that computes BFP fingerprints from observations.
- **Operator**: an entity (organization or individual) running an implementation. Operators are the parties with operational responsibility for emitted claims and anchored trust logs.
- **Reference implementation**: an implementation maintained by the BFP project itself (currently the xposeTIP project) serving as the canonical reference for protocol conformance testing.
- **Behavioral hash**: a clustering-primitive locality-sensitive hash (MinHash family) over selected invariant axes. Distinct from the fingerprint hash (§9.2), which is identity-typed. See §9.3 (specified in v0.2.2).
- **Conformant implementation**: an implementation satisfying the requirements of §11.

#### Trust-layer terms (v0.2+)

- **Trust boundary**: the scope within which claims are emitted and anchored. Per implementation, this typically corresponds to a tenant, workspace, or operator instance. Trust boundaries DO NOT share claim spaces or Merkle anchors; cross-boundary claim transfer requires explicit federation (out of scope for v0.x).
- **Trust log**: the totality of claims emitted within a trust boundary, ordered by emission time, periodically anchored via Merkle roots (§17).
- **Claim**: an atomic, content-addressable assertion about a subject made by an operator. The unit of the trust log. See §16.
- **Cross-verification source**: an independent source whose signal contributes to a claim's cross-verification count. See §15.
- **Anchor** (Merkle anchor): a Merkle root computed over the trust log within a trust boundary at a given point in time. See §17.
- **Merkle leaf**: the hash of a single claim's `claim_hash` field, padded with the domain-separation prefix `0x00`. See §17.4.
- **Merkle root**: the top-of-tree hash of the Merkle anchor.
- **Subject signature**: a cryptographic signature produced by the subject over an attestation. Post-quantum algorithm choice specified in §13 (specified in v0.2.3).
- **Operator signature**: a cryptographic signature produced by the operator over a claim or batch. Post-quantum algorithm choice specified in §13 (specified in v0.2.3).

---

## 4. Conceptual Model

### 4.1 The 6 Layers

BFP organizes axes into 6 layers, each capturing a distinct dimension of behavioral identity:

| Layer | Captures | Drift |
|---|---|---|
| **Surface** | What is publicly visible | Moderate, grows with activity |
| **Forensic** | Presence in formal/structured records | Monotonic non-decreasing |
| **Temporal** | How identity persists and evolves over time | Slow, monotonic |
| **Linguistic** | How the entity expresses itself | Very stable |
| **Relational** | Shape of the entity's social network | Stable |
| **Adverse** | Signals of evasion, risk, or threat | Stepwise (event-driven) |

Layers are organizational; they do not appear in the serialized fingerprint format. Each axis declares its layer.

### 4.2 The Fingerprint Vector

A BFP v0 fingerprint is a vector of 16 axis observations. Each axis observation is a tuple:

```
(value, confidence)
```

where:

- `value` ∈ [0.0, 1.0] is the normalized axis score for the entity.
- `confidence` ∈ [0.0, 1.0] reflects the strength of evidence supporting the value.

Both fields are REQUIRED for every axis in every fingerprint.

### 4.3 Confidence Semantics

`confidence` is distinct from `value`. It expresses how reliable the value is, not how strong the underlying signal is. A high-value low-confidence axis means "we see this strongly but with thin evidence." A low-value high-confidence axis means "we have strong evidence that this signal is absent or weak."

Conformant implementations SHOULD calibrate confidence as follows:

- `0.0`: no observable signal for this axis.
- `0.0 < c < 0.3`: single source, low source reliability, or partial observation.
- `0.3 ≤ c < 0.7`: multiple sources or moderate reliability, partial cross-verification.
- `0.7 ≤ c ≤ 1.0`: multiple cross-verified sources, high reliability.

These bands are RECOMMENDED, not normative. The protocol does not mandate a specific calibration function.

### 4.4 Empty-State Semantics

When no signal is available for an axis, the axis MUST be emitted with `value = 0.0` and `confidence = 0.0`. Implementations MUST NOT omit axes from the serialized fingerprint. Implementations MUST NOT use sentinel values such as `null` or `-1` in place of `0.0`.

This ensures that:

- Fingerprint vectors are always of fixed length.
- Similarity computation (§7) handles empty axes uniformly via the confidence weight.
- Implementations have a consistent shape for downstream consumers.

### 4.5 Trust Layer Model

BFP defines two distinct conceptual layers. An implementation MAY conform to one or both. They have separate conformance requirements (§11).

**Layer 1: Fingerprint Computation** — produces a confidence-weighted vector across axes for an entity. Specified in §4-§9.

| Component | Section |
|---|---|
| Axes (16 dimensions) | §5 |
| Fingerprint vector | §4.2 |
| Confidence semantics | §4.3 |
| Normalization | §6 |
| Similarity computation | §7 |
| Profiles | §8 |
| Serialization + fingerprint hash | §9 |

A fingerprint-conformant implementation MAY operate without any trust-layer machinery. It produces fingerprints; it does not emit attested claims or anchor a trust log.

**Layer 2: Trust + Anchoring** — formalizes who attests to what about whom, with what corroboration, anchored in time. Specified in §13-§17.

| Component | Section |
|---|---|
| Subject + operator signatures (PQC) | §13 (v0.2.3) |
| Cross-verification | §15 |
| Claim log | §16 |
| Merkle anchor | §17 |

A trust-layer conformant implementation MUST also be fingerprint-conformant. The trust layer ANCHORS fingerprint-derived findings; it does not exist in isolation.

The two layers compose as:

```
                  ┌───────────────────────────────────────────┐
                  │  Layer 2: Trust + Anchoring               │
                  │                                           │
                  │  Cross-verification (§15)                 │
                  │     ↓                                     │
                  │  Claim emission (§16)                     │
                  │     ↓                                     │
                  │  Periodic Merkle anchor (§17)             │
                  │     ↓                                     │
                  │  Subject + operator signatures (§13)      │
                  └───────────────────────────────────────────┘
                                    ▲
                                    │ findings + scores
                                    │
                  ┌───────────────────────────────────────────┐
                  │  Layer 1: Fingerprint Computation         │
                  │                                           │
                  │  Observations → axes (§5)                 │
                  │     ↓                                     │
                  │  Normalization (§6) → fingerprint vector  │
                  │     ↓                                     │
                  │  Similarity (§7) under a profile (§8)     │
                  │     ↓                                     │
                  │  Fingerprint hash (§9.2)                  │
                  │  Behavioral hash (§9.3)                   │
                  └───────────────────────────────────────────┘
```

The separation matters because:

- An air-gapped fingerprint computer never emits attested claims; Layer 1 suffices.
- A multi-operator interoperable trust network requires Layer 2 for cross-attestation.
- Reference implementations SHOULD conform to both layers.

---

## 5. Axes

This section specifies each of the 16 axes. For each axis, the normative content is: layer, **status**, definition, empty-state, drift behavior, and constraints on the normalization function `F_axis`. The signal sources listed are informative — implementations MAY use other sources provided the definition is respected.

### 5.0 Axis Status Taxonomy

Each axis carries a **Status** flag indicating its implementation maturity within the BFP reference implementation:

- **LIVE** — axis is fully specified AND has a working reference implementation. Conformant implementations (§11.1) MUST compute and emit a meaningful value when signal is available. Empty-state semantics (§4.4) still apply when no signal is observed.
- **DRAFT** — axis is specified but the reference implementation does not yet compute it. Conformant implementations MAY emit `(0.0, 0.0)` for DRAFT axes without further computation. Future spec versions are expected to upgrade individual axes to LIVE as the reference implementation matures.

An axis moving from DRAFT to LIVE in a future spec version is a minor `bfp_version` bump (§14). Implementations targeting an older spec version MAY continue to emit `(0.0, 0.0)` for axes that were DRAFT in that version, even after a newer version flags them LIVE.

As of v0.2.2: **11 LIVE** axes, **5 DRAFT** axes (`account_hygiene`, `temporal_persistence`, `activity_rhythm`, `linguistic_signature`, `adversarial_indicators`).

### 5.1 Surface layer

#### 5.1.1 `account_count`

- **Layer**: Surface
- **Status**: LIVE
- **Definition**: Normalized count of distinct accounts confirmed to belong to the entity across all observed platforms.
- **Signal sources (informative)**: account enumeration scrapers, breach databases, social platform APIs, OAuth introspection.
- **F_account_count constraints**: monotonic non-decreasing in number of distinct confirmed accounts; F(0) = 0.0.
- **Drift**: monotonic non-decreasing during active periods; MAY decrease on confirmed account deletion.
- **Empty-state**: 0.0 / 0.0.

#### 5.1.2 `platform_diversity`

- **Layer**: Surface
- **Status**: LIVE
- **Definition**: Normalized measure of the diversity of platform types the entity is present on. Intended to be orthogonal to `account_count`: an entity with 1 account on each of 5 platforms SHOULD score higher than an entity with 5 accounts on the same platform.
- **Signal sources (informative)**: same sources as `account_count`, aggregated by platform type.
- **F_platform_diversity constraints**: monotonic non-decreasing in number of distinct platforms; SHOULD be entropy-like or otherwise reward distribution over count; F(empty) = 0.0.
- **Drift**: monotonic non-decreasing during active periods.
- **Empty-state**: 0.0 / 0.0.

#### 5.1.3 `geo_dispersion`

- **Layer**: Surface
- **Status**: LIVE
- **Definition**: Normalized measure of geographic spread of the entity's observable footprint.
- **Signal sources (informative)**: IP geolocation, profile location fields, platform regional metadata, timezone signals, language signals.
- **F_geo_dispersion constraints**: monotonic non-decreasing in number of distinct geographic regions (countries, cities) attested by independent signals; F(no geo signal) = 0.0.
- **Drift**: slow, both directions (relocations).
- **Empty-state**: 0.0 / 0.0.

#### 5.1.4 `media_presence`

- **Layer**: Surface
- **Status**: LIVE
- **Definition**: Normalized measure of the entity's mentions in news media, press, blogs, and public reporting. Distinct from `formal_records` (§5.2.5) which covers structured/governmental records.
- **Signal sources (informative)**: news aggregators, search engines, archive crawlers, public web content.
- **F_media_presence constraints**: monotonic non-decreasing in count of independent media mentions; SHOULD be log-scaled to avoid swamping by viral events; F(no mention) = 0.0.
- **Drift**: increases with notoriety; events can spike.
- **Empty-state**: 0.0 / 0.0.

### 5.2 Forensic layer

#### 5.2.1 `breach_incidents`

- **Layer**: Forensic
- **Status**: LIVE
- **Definition**: Normalized count of distinct breach incidents in which the entity's data is confirmed to appear.
- **Signal sources (informative)**: breach aggregators, leak databases.
- **F_breach_incidents constraints**: monotonic non-decreasing in distinct breach count; F(0) = 0.0.
- **Drift**: monotonic non-decreasing (breaches are permanent record).
- **Empty-state**: 0.0 / 0.0.
- **Notes**: orthogonal to `breach_severity` (§5.2.2). This axis counts incidents; severity is the other axis.

#### 5.2.2 `breach_severity`

- **Layer**: Forensic
- **Status**: LIVE
- **Definition**: Normalized measure of the severity and sensitivity of data exposed across all breaches in which the entity appears. Categories include password hashes, plaintext passwords, financial data, biometric data, personally identifying information.
- **Signal sources (informative)**: breach aggregators with data-type metadata, breach content samples.
- **F_breach_severity constraints**: monotonic non-decreasing in maximum sensitivity tier and in count of exposures at that tier; F(no breach) = 0.0.
- **Drift**: monotonic non-decreasing.
- **Empty-state**: 0.0 / 0.0.
- **Notes**: orthogonal to `breach_incidents`. An entity in 1 high-severity breach scores higher on `breach_severity` than an entity in 10 low-severity breaches, even though the latter scores higher on `breach_incidents`.

#### 5.2.3 `email_security_posture`

- **Layer**: Forensic
- **Status**: LIVE
- **Definition**: Normalized measure of the security posture of the entity's email domain(s) at the protocol level — SPF, DMARC, DKIM, MX configuration, TLS.
- **Signal sources (informative)**: DNS lookups, mail server probes.
- **F_email_security_posture constraints**: monotonic non-decreasing in protocol-level hardening signals; F(domain unreachable) = 0.0 with confidence 0.0.
- **Drift**: discrete, changes when the domain operator updates configuration.
- **Empty-state**: 0.0 / 0.0.
- **Notes**: scoped to *domain-level* posture, not personal account hygiene (see `account_hygiene`).

#### 5.2.4 `account_hygiene`

- **Layer**: Forensic
- **Status**: DRAFT
- **Definition**: Normalized measure of the entity's personal security hygiene at the account level — password strength signals from breached passwords, password reuse across breaches, 2FA evidence where observable.
- **Signal sources (informative)**: breach contents, account-level metadata.
- **F_account_hygiene constraints**: monotonic non-increasing in count of weak-password signals, non-decreasing in 2FA evidence; F(no signal) = 0.0.
- **Drift**: bidirectional and user-influenced.
- **Empty-state**: 0.0 / 0.0.

#### 5.2.5 `formal_records`

- **Layer**: Forensic
- **Status**: LIVE
- **Definition**: Normalized measure of the entity's presence in formal/governmental/structured records — courts, corporate registries, sanctions lists, beneficial ownership databases, regulatory filings.
- **Signal sources (informative)**: court record APIs, gazettes, corporate registries, sanctions lists.
- **F_formal_records constraints**: monotonic non-decreasing in count of distinct formal record matches, weighted by record type severity; F(no record) = 0.0.
- **Drift**: monotonic non-decreasing.
- **Empty-state**: 0.0 / 0.0.

### 5.3 Temporal layer

#### 5.3.1 `email_age`

- **Layer**: Temporal
- **Status**: LIVE
- **Definition**: Normalized age of the entity's primary email account, as inferred from the earliest attested observation timestamp.
- **Signal sources (informative)**: breach dates, account creation timestamps, platform join dates.
- **F_email_age constraints**: monotonic non-decreasing in inferred age; SHOULD be bounded by domain launch date and a sanity cap; F(no temporal signal) = 0.0.
- **Drift**: monotonic increasing, linear with calendar time.
- **Empty-state**: 0.0 / 0.0.

#### 5.3.2 `temporal_persistence`

- **Layer**: Temporal
- **Status**: DRAFT
- **Definition**: Normalized measure of the entity's continuous activity over time across multiple platforms. Distinct from `email_age` (a point estimate of one account's birth) — this axis captures the *breadth and depth* of historical presence.
- **Signal sources (informative)**: account creation dates across platforms, activity timestamp distributions, archive depth.
- **F_temporal_persistence constraints**: monotonic non-decreasing in observed temporal span across platforms; SHOULD reward both age and continuity of activity; F(single point) = low but non-zero if at least one signal.
- **Drift**: slow monotonic.
- **Empty-state**: 0.0 / 0.0.

#### 5.3.3 `activity_rhythm`

- **Layer**: Temporal
- **Status**: DRAFT
- **Definition**: Normalized measure of the distinctiveness of the entity's temporal activity patterns — circadian, weekly, and seasonal cycles.
- **Signal sources (informative)**: activity timestamps clustered by hour/day/week.
- **F_activity_rhythm constraints**: SHOULD reflect pattern distinctiveness (deviation from uniform), not raw activity volume; F(insufficient timestamps) = 0.0.
- **Drift**: very stable.
- **Empty-state**: 0.0 / 0.0.

### 5.4 Linguistic layer

#### 5.4.1 `handle_persistence`

- **Layer**: Linguistic
- **Status**: LIVE
- **Definition**: Normalized measure of the entity's tendency to reuse the same or closely similar username/handle pattern across platforms.
- **Signal sources (informative)**: collected usernames across platforms, string similarity functions.
- **F_handle_persistence constraints**: monotonic non-decreasing in mean pairwise similarity of observed handles, weighted by number of observed handles; F(<2 handles) = 0.0.
- **Drift**: very stable.
- **Empty-state**: 0.0 / 0.0.

#### 5.4.2 `linguistic_signature`

- **Layer**: Linguistic
- **Status**: DRAFT
- **Definition**: Normalized measure of the distinctiveness and persistence of the entity's expressive style across collected text — stylometry, lexical diversity, syntactic patterns.
- **Signal sources (informative)**: collected posts, bios, comments, code commit messages.
- **F_linguistic_signature constraints**: SHOULD reflect the distinctiveness of observed stylistic patterns from population baseline; F(insufficient text) = 0.0.
- **Drift**: very stable, highest persistence among all axes.
- **Empty-state**: 0.0 / 0.0.

### 5.5 Relational layer

#### 5.5.1 `network_signature`

- **Layer**: Relational
- **Status**: LIVE
- **Definition**: Normalized measure derived from the structural properties of the entity's social network — centrality, clustering, neighborhood density.
- **Signal sources (informative)**: identity graph metrics computed from collected connections.
- **F_network_signature constraints**: SHOULD reflect distinctive structural properties of the entity's local graph; F(graph too sparse) = 0.0.
- **Drift**: stable.
- **Empty-state**: 0.0 / 0.0.

### 5.6 Adverse layer

#### 5.6.1 `adversarial_indicators`

- **Layer**: Adverse
- **Status**: DRAFT
- **Definition**: Normalized aggregation of signals indicating evasion behavior, threat actor presence, dark-web exposure, code-leaked credentials, or anti-OSINT patterns.
- **Signal sources (informative)**: dark-web monitors, code-leak detectors, threat-intel feeds, anti-OSINT behavior detectors.
- **F_adversarial_indicators constraints**: monotonic non-decreasing in count and severity of adverse signals; F(no adverse signal) = 0.0.
- **Drift**: stepwise, event-driven.
- **Empty-state**: 0.0 / 0.0.
- **Notes**: distinct from `formal_records`. `formal_records` is for *formal* adverse signals (sanctions, courts); `adversarial_indicators` is for *informal* adverse signals (dark web, code leaks, deliberate obfuscation).

---

## 6. Normalization Function Constraints

For each axis, the implementation defines `F_axis: InputDomain → [0.0, 1.0]`. All `F_axis` functions MUST satisfy:

1. `F_axis(empty observation) = 0.0`.
2. Output ∈ [0.0, 1.0].
3. Monotonicity in the natural underlying quantity, as specified per-axis in §5.
4. Deterministic given fixed inputs (no randomness, no time-dependent terms beyond observation time).

Implementations SHOULD document their `F_axis` choices. Implementations SHOULD prefer log-scaled normalizations for axes with naturally heavy-tailed inputs (counts, mentions).

Different implementations MAY use different `F_axis` functions, provided constraints 1–4 are met. As a consequence, fingerprints from different implementations are NOT directly comparable axis-by-axis without recalibration. Cross-implementation interoperability is a v1 goal.

---

## 7. Similarity Computation

### 7.1 Definition

Given two fingerprints A and B, the **confidence-weighted cosine similarity** is defined as:

```
                  Σ_i  w_i · v_A_i · v_B_i
sim(A, B) = ────────────────────────────────────────────────
            √( Σ_i w_i · v_A_i² ) · √( Σ_i w_i · v_B_i² )

where  w_i = min(c_A_i, c_B_i)
```

Indexing `i` runs over all 16 axes. `v_X_i` is the value of axis `i` in fingerprint X. `c_X_i` is the confidence of axis `i` in fingerprint X.

If the denominator is zero, `sim(A, B)` is undefined and implementations MUST return a sentinel indicating insufficient data for comparison (e.g., null), not a similarity value.

### 7.2 Properties

- `sim(A, A) = 1.0` for any A with at least one axis where `c_A_i · v_A_i > 0`.
- `sim(A, B) ∈ [0.0, 1.0]` (values are non-negative, so cosine cannot be negative).
- Axes with zero confidence in either A or B contribute zero to both numerator and denominator. Empty axes do not bias the result.

### 7.3 Threshold

This specification does NOT mandate a similarity threshold for declaring two fingerprints "matched." Threshold selection is a **profile** decision (see §8). Implementations MUST document their threshold and the calibration procedure used to select it.

---

## 8. Profiles

A **profile** is a named tuple of similarity configuration choices applied on top of this protocol. A profile fixes:

- A threshold for the similarity score above which two fingerprints are considered "matched."
- Optional per-axis weight overrides (subject to constraints to be defined in v1).
- Optional minimum-confidence guards.

The reference implementation publishes a default profile named `bfp-cosine-default-v0` with:

- Threshold: 0.7 (subject to empirical recalibration as the data flywheel matures).
- No per-axis weight overrides.
- No minimum-confidence guard beyond the §7.1 denominator check.

Implementations MUST declare which profile they use when emitting similarity results.

---

## 9. Serialization Format

### 9.1 Fingerprint JSON Schema

A serialized fingerprint MUST conform to the following structure (abbreviated; full JSON Schema in v1):

```json
{
  "bfp_version": "0.1.0",
  "entity_ref": "<implementation-defined opaque identifier>",
  "observed_at": "<RFC 3339 timestamp>",
  "axes": {
    "account_count":            { "value": 0.0, "confidence": 0.0 },
    "platform_diversity":       { "value": 0.0, "confidence": 0.0 },
    "geo_dispersion":           { "value": 0.0, "confidence": 0.0 },
    "media_presence":           { "value": 0.0, "confidence": 0.0 },
    "breach_incidents":         { "value": 0.0, "confidence": 0.0 },
    "breach_severity":          { "value": 0.0, "confidence": 0.0 },
    "email_security_posture":   { "value": 0.0, "confidence": 0.0 },
    "account_hygiene":          { "value": 0.0, "confidence": 0.0 },
    "formal_records":           { "value": 0.0, "confidence": 0.0 },
    "email_age":                { "value": 0.0, "confidence": 0.0 },
    "temporal_persistence":     { "value": 0.0, "confidence": 0.0 },
    "activity_rhythm":          { "value": 0.0, "confidence": 0.0 },
    "handle_persistence":       { "value": 0.0, "confidence": 0.0 },
    "linguistic_signature":     { "value": 0.0, "confidence": 0.0 },
    "network_signature":        { "value": 0.0, "confidence": 0.0 },
    "adversarial_indicators":   { "value": 0.0, "confidence": 0.0 }
  },
  "provenance": { /* see §10 */ }
}
```

All 16 axes MUST be present in the `axes` object. Axis order in serialization is not significant; the canonical ordering for hashing (§9.2) is alphabetical by axis name.

### 9.2 Fingerprint Hash

The fingerprint hash is computed as `SHA-256` of the UTF-8 encoded canonical JSON serialization of:

```json
{
  "bfp_version": "<version>",
  "axes_values": {
    "<axis_1_alphabetical>": <value>,
    "<axis_2_alphabetical>": <value>,
    ...
  }
}
```

Only `value` fields are hashed; `confidence` is excluded from the hash. Two fingerprints with identical values but different confidences hash identically. This is intentional: confidence is diagnostic, not definitional. The same entity observed with weaker evidence yields the same fingerprint identity.

Values MUST be serialized with 6-decimal precision (`%.6f`) to ensure cross-implementation hash stability.

### 9.3 Behavioral Hash

The **behavioral hash** is a locality-sensitive clustering primitive computed alongside the fingerprint. It is DISTINCT from the fingerprint hash (§9.2) in purpose, algorithm, and stability properties.

#### 9.3.1 Purpose

The fingerprint hash (§9.2) is an **identity hash**: two fingerprints with identical axis values produce identical hashes; any change in any value changes the hash. Use case: "are these the same fingerprint."

The behavioral hash (§9.3) is a **clustering hash**: two fingerprints with similar behavioral patterns produce hashes with high Jaccard similarity; small changes in the underlying behavior produce small changes in the hash. Use case: "are these likely the same subject across observation windows."

Implementations MAY compute both hashes per fingerprint. Each addresses a distinct downstream consumer.

#### 9.3.2 Selected Axes (normative)

The behavioral hash MUST be computed over EXACTLY these three axes, in this order:

1. `media_presence` (§5.1.4)
2. `geo_dispersion` (§5.1.3)
3. `breach_severity` (§5.2.2)

These three were selected by invariance analysis (see non-normative note below): they are the most stable axes per-subject (low intra-subject drift) AND the most discriminating across population (high inter-subject variance). Other axes either drift too much per-subject (would destabilize behavioral clustering across observation windows) or are too low-variance across the population (would not discriminate between subjects).

Implementations MUST NOT substitute other axes. Implementations MUST NOT add additional axes. Locking this selection is what makes the behavioral hash comparable across operators.

*Non-normative note: the reference implementation selected these axes by running `scripts/bfp_invariance_diag.py` over its 223-subject corpus (S165, May 2026). Subjects with ≥2 fingerprint snapshots were measured for per-axis stability (mean absolute delta, coefficient of variation, range) AND for population discrimination (across-population stdev, distinct bucket count). The three axes named here had the best joint stability-and-discrimination profile.*

#### 9.3.3 Bucket Encoding (normative)

Each axis value (a float in `[0.0, 1.0]`) MUST be discretized into one of 20 buckets using:

```
bucket_id = min(int(value * 20), 19)
```

Conformant implementations MUST clamp the input to `[0.0, 1.0]` before bucketing (values outside this range indicate an upstream bug; the protocol fixes the safe behavior).

Each (axis, bucket) pair MUST be encoded as the ASCII byte string:

```
"{axis_name}:{bucket_id}"
```

where `axis_name` is the canonical axis name from §5 (e.g. `media_presence`, NOT a renamed or aliased form) and `bucket_id` is the decimal integer in `[0, 19]` without leading zeros.

Example: for `media_presence` value `0.47`, `bucket_id = 9`, element = `b"media_presence:9"`.

#### 9.3.4 MinHash Parameters (normative)

The behavioral hash MUST be computed as a MinHash signature with:

| Parameter | Value | Rationale |
|---|---|---|
| Number of permutations | **128** | matches `datasketch` library default; signature length 128 × 8 bytes = 1024 bytes |
| Seed | **42** | deterministic permutation generation across implementations |
| Hash family | MinHash with linear permutations `h_i(x) = ((a_i × x + b_i) mod p)` where `p` is the Mersenne prime `2^61 − 1`, and `(a_i, b_i)` pairs are derived from `seed=42` | matches `datasketch` v1.x internal algorithm |

The 128 (a_i, b_i) coefficient pairs MUST be generated identically across implementations. The canonical reference algorithm is the one implemented in [`datasketch`](https://github.com/ekzhu/datasketch) version `>=1.6, <2.0`. Implementations not using the `datasketch` library MUST reproduce its MinHash variant exactly to maintain cross-operator hash comparability.

*Non-normative note: a fully library-independent algorithmic specification of the MinHash variant used here is anticipated for a future spec version, removing the implicit `datasketch` lock-in. Currently, interop requires either using `datasketch` directly or porting its algorithm.*

#### 9.3.5 Set Semantics (normative)

The set of elements input to the MinHash is unordered. Implementations MUST NOT depend on insertion order to affect the output hash.

The set MAY contain fewer than 3 elements if one or more of the three required axes has no value available for the subject. Specifically:

- If an axis value is `None` / `null` / missing: that axis MUST be omitted from the element set. Implementations MUST NOT substitute `0.0` (this would bias the hash toward a non-meaningful bucket).
- If the resulting set contains zero elements (all three axes missing): the behavioral hash MUST be the empty string `""`. Implementations MUST persist this as `NULL` or an equivalent null marker in storage.

#### 9.3.6 Output Format (normative)

The behavioral hash MUST be serialized as the lowercase hexadecimal string of the MinHash signature byte representation:

- 128 permutations × 8 bytes per `uint64` hash = **1024 bytes**
- Hex-encoded length: **2048 ASCII characters**

Byte order: the native little-endian representation of `uint64` values, concatenated in permutation index order (i.e. the byte representation of `numpy.ndarray.tobytes()` for the default `numpy.uint64` dtype).

#### 9.3.7 Composition Property (informative)

The behavioral hash is a **clustering primitive, not a uniqueness identifier**.

Entropy budget: the three selected axes collectively contain approximately 28 bits of Shannon entropy across the protocol's defined `[0.0, 1.0]` × 20-bucket discretization. With K=3 axes, the address space is effectively 6.68 bits ≈ 103 distinct cell combinations. At population scale (e.g. 4.5 × 10^9 subjects), this means tens of millions of subjects per cell. The behavioral hash by itself CANNOT establish unique identity.

Uniqueness arises from COMPOSITION:

```
unique_identity = behavioral_hash + subject_binding_signature + network_layer_signals
```

where `subject_binding_signature` is a §13-defined PQC signature by the subject over an attestation, and `network_layer_signals` are out-of-band identifiers (network address, device fingerprint, etc.) that the protocol does not specify but allows implementations to compose with.

Implementations exposing the behavioral hash to downstream consumers SHOULD document this composition property and SHOULD NOT present the behavioral hash alone as an identity claim.

#### 9.3.8 Versioning

The behavioral hash carries an independent version field `behavioral_hash_version` (see §14.1).

The current version is `behavioral_hash_version = 1`, corresponding to the parameters in §9.3.2-§9.3.6. Any change to:
- The selected axes (§9.3.2)
- The bucket count or formula (§9.3.3)
- The element encoding (§9.3.3)
- The MinHash parameters (§9.3.4)
- The set semantics or empty handling (§9.3.5)
- The output format (§9.3.6)

REQUIRES bumping `behavioral_hash_version`. Existing behavioral hashes at the old version remain interpretable; implementations MUST NOT silently recompute them under a new version.

#### 9.3.9 Conformance

A fingerprint-layer conformant implementation (§11.1) MAY compute and emit the behavioral hash alongside fingerprint emission. The behavioral hash is RECOMMENDED for implementations supporting cross-operator subject clustering or similarity matching.

A trust-layer conformant implementation (§11.2) MAY use the behavioral hash as part of its claim emission or cross-verification logic (e.g. to detect "same subject seen by independent sources") but is not REQUIRED to.

---

## 10. Provenance

This v0 specification defines a minimal provenance stub. A fuller provenance model is a v1 goal.

A `provenance` object MUST include:

```json
{
  "implementation": "<implementation identifier and version>",
  "computed_at": "<RFC 3339 timestamp>",
  "source_count": <integer>,
  "axes_populated": <integer between 0 and 16>
}
```

Where:

- `implementation` identifies the implementation that produced the fingerprint.
- `computed_at` is the timestamp of computation (distinct from `observed_at` at the fingerprint root, which is the timestamp of the observation window).
- `source_count` is the number of distinct sources contributing signals to this fingerprint.
- `axes_populated` is the count of axes for which `confidence > 0`.

Future v1 extensions will add signed provenance, per-source attribution, and reproducibility metadata.

---

## 11. Conformance

BFP defines two layers of conformance (see §4.5 Trust Layer Model). An implementation declares which layer(s) it conforms to. Most fingerprint conformance requirements (§11.1) are unchanged from v0.1. The trust-layer conformance (§11.2) is new in v0.2.

### 11.1 Fingerprint Layer Conformance

A **fingerprint-layer conformant BFP v0 implementation** MUST:

1. Compute and emit all 16 axes specified in §5, with both `value` and `confidence` fields for each.
2. Emit `value` and `confidence` in [0.0, 1.0].
3. Emit `(0.0, 0.0)` for axes with no observable signal.
4. Implement at least the similarity computation specified in §7.
5. Declare which profile (§8) is in use when emitting similarity results.
6. Conform to the serialization format in §9.
7. Provide the provenance stub specified in §10.

A fingerprint-layer conformant implementation MAY:

- Emit `(0.0, 0.0)` for any axis flagged DRAFT in §5 without further computation. As of v0.2.2 the DRAFT axes are: `account_hygiene`, `temporal_persistence`, `activity_rhythm`, `linguistic_signature`, `adversarial_indicators` (5 axes).
- Implement additional similarity profiles beyond `bfp-cosine-default-v0`.
- Add implementation-specific fields outside the `axes` and `provenance` objects, prefixed with `x_` (extension fields).
- Compute and emit the behavioral hash specified in §9.3 alongside fingerprint emission (RECOMMENDED for implementations supporting cross-operator subject clustering).

### 11.2 Trust Layer Conformance

A **trust-layer conformant BFP v0 implementation** MUST ALSO be fingerprint-layer conformant per §11.1, AND MUST:

1. Implement cross-verification per §15: recompute on finding emission, persist `cross_verification_count` and `cross_verification_sources` for every (subject, indicator) tuple.
2. Emit claims per §16 obeying the locked emission rule (`cross_verification_count >= 1` AND non-null `indicator_type` AND non-null `indicator_value`).
3. Compute and persist Merkle anchors per §17 at least on operator demand (explicit batch trigger). Implementations SHOULD also support a regular cadence (Celery beat or equivalent).
4. Provide a means for an independent verifier to re-derive a Merkle root from raw `claim_hash` values stored in the trust log, returning byte-for-byte equality with the stored root or surfacing the divergence.
5. Preserve the append-only property of the claim log: either via application-level discipline (no UPDATE / DELETE on `claims`) or via DB-level enforcement (triggers, REVOKE). Application-level discipline is acceptable for v0.x; DB-level enforcement is RECOMMENDED for production deployments.
6. Scope all claims and anchors to a single trust boundary (§3). Cross-boundary claim transfer is out of scope for v0.x.

A trust-layer conformant implementation MAY:

- Emit `subject_signature` and `operator_signature` per §13 (REQUIRED for cross-trust-boundary claim transfer when that is specified in a future version; OPTIONAL in v0.x).
- Implement inclusion proofs for claims (§17.12 — out of scope for v0.2, anticipated for v0.3+).
- Implement claim supersession when evidence about a past claim evolves (out of scope for v0.2, anticipated for v1+).
- Provide subject-rights tiers per §12.1.

A fingerprint-conformant implementation MAY operate without any trust-layer machinery; in that case, §11.2 does not apply.

---

## 12. Privacy and Ethics Considerations

BFP enables the construction of detailed behavioral profiles from public data. Implementations and operators MUST consider:

- **Data minimization**: implementations SHOULD collect only the signals needed to compute the axes.
- **Subject rights**: where legally applicable, subjects SHOULD have the right to request fingerprint disclosure and challenge inaccurate inferences. See §12.1 for the normative tier structure.
- **Adversarial misuse**: BFP can be used to deanonymize or surveil. Implementations SHOULD include safeguards against bulk profiling of non-targeted populations and against use for harassment, doxxing, or unlawful surveillance.
- **Confidence honesty**: implementations MUST NOT inflate `confidence` for marketing or scoring purposes. Calibration SHOULD be documented and auditable.
- **Reproducibility**: implementations SHOULD make their normalization choices documented enough that a fingerprint can be re-derived from the same input data.

Implementations targeting use in due diligence, employment screening, insurance underwriting, or any high-stakes domain MUST be auditable and SHOULD be subject to independent calibration review.

### 12.1 Subject-Rights Tiers

The protocol defines four normative tiers of subject-facing rights plus one constrained mechanism for record alteration. Operators MAY implement any subset of the tiers. The tiers themselves are normative as a STRUCTURE — pricing, packaging, and commercial framing are OPERATIONAL concerns explicitly outside the protocol. Different operators MAY price the same tier differently or offer it free.

**Tier 1 — Read.** Subjects SHOULD be able to request and receive the current fingerprint computed about them within the operator's trust boundary. RECOMMENDED for all conformant operators without compensation.

**Tier 2 — Guidance.** Subjects SHOULD be able to request a human-readable explanation of which axes drive their fingerprint and what observable changes (account closures, public-records corrections, etc.) would reduce specific exposure scores. RECOMMENDED for all conformant operators without compensation.

**Tier 3 — Monitoring.** Subjects MAY subscribe to active monitoring of changes to their fingerprint within the operator's trust boundary, with notifications on significant deltas. Operators MAY charge for this tier or offer it bundled.

**Tier 4 — Managed Remediation.** Subjects MAY commission an operator to actively reduce specific exposure on their behalf (e.g., coordinating removal requests with databrokers, social platforms, or public registries within applicable legal frameworks). Operators MAY charge for this tier.

**Takedown — Legal Soupape.** A subject's right to have specific findings or claims removed from an operator's trust log is constrained to legally-defined channels: court orders, GDPR Article 8 sub-13 (data of minors), expungement orders, witness-protection requirements, and equivalent statutory mechanisms in the operator's jurisdiction. The protocol DOES NOT define a discretionary takedown mechanism. This is intentional: discretionary takedown would erode the append-only property of the trust log (§16.7) and enable gaming.

The normative content of §12.1 is the EXISTENCE of these tiers as a structure. Pricing, packaging, exact mechanics, and which tiers an operator chooses to offer are operational concerns outside the protocol.

---

## 13. Security Considerations

- **Adversarial input**: implementations MUST treat input data as untrusted. Adversaries may inject signals intended to manipulate axis values.
- **Fingerprint forgery**: an adversary with knowledge of `F_axis` functions MAY attempt to construct synthetic identities that produce target fingerprints. Implementations SHOULD treat low-source-count fingerprints with reduced confidence.
- **Side channels**: similarity scores can themselves leak information about the corpus. Implementations exposing similarity APIs SHOULD apply rate limiting and access controls.

---

## 14. Versioning

This is v0.2.2. The versioning policy for `bfp_version` itself is:

- **0.x.y**: pre-stable. Breaking changes permitted between minor versions. Not for external interoperability claims.
- **1.0.0**: first stable version. Breaking changes between major versions only.
- **Major version bumps**: changes to the axis set, layer model, similarity formula structure, or serialization format MUST bump the major version.
- **Minor version bumps**: additions to provenance, profiles, conformance, trust-layer mechanics, or non-normative clarifications.
- **Patch version bumps**: editorial corrections, no semantic changes.

A fingerprint serialization includes `bfp_version` to allow consumers to handle multiple versions.

### 14.1 Component Versioning

Beyond `bfp_version`, the protocol defines several component-specific version fields that evolve independently. Each component version is bumped on changes to that component's algorithm or canonical encoding, independent of the overall `bfp_version`.

| Component | Field name | Scope | Defined in | Bump rule |
|---|---|---|---|---|
| Claim canonical encoding | `claim_hash_version` | Per-claim | §16.3 | Major bump on canonical JSON encoding change. Minor bump on field additions that preserve canonical hash of pre-existing claims. |
| Merkle root algorithm | `root_version` | Per-anchor snapshot | §17.8 | Major bump on algorithm change (e.g., SHA3-256 → BLAKE3, leaf/internal hash structure change, ordering change). |
| Behavioral hash algorithm | `behavioral_hash_version` | Per-subject | §9.3 (v0.2.2) | Major bump on MinHash parameter change (number of permutations, axis selection, bucket count). |
| Signature algorithm | `signature_version` | Per-signature | §13 (v0.2.3) | Major bump on PQC algorithm or parameter set change. |

These component versions are decoupled from `bfp_version`. A `bfp_version=0.2.1` implementation MAY use `claim_hash_version=1` AND `root_version=1`. When future versions introduce new component algorithms, OLD components MUST remain interpretable in their original version: implementations MUST NOT silently rebuild past anchors under a new `root_version` (doing so would invalidate the tamper-evidence property — see §17.10).

Component version transitions are coordinated via the `bfp_version` minor bump that introduces the new component version. The minor bump itself does NOT obsolete old component versions; both old and new MUST be readable.

---

## 15. Cross-Verification

### 15.1 Definition

**Cross-verification** is the protocol's seed trust signal. For a given subject and a given (claim-type, claim-value) tuple, the **cross-verification count** is the number of distinct sources (§15.2) that have independently reported that exact tuple, excluding the source under consideration.

Cross-verification is computed at the level of an individual (subject, claim-type, claim-value) tuple. It is **not** a property of the fingerprint vector defined in §5, and it is **not** a property of any single axis.

### 15.2 Source Identity

A **source** is a named, deterministic process that produces observations from a bounded input domain. Examples include: a named scraper module, a named lookup API integration, a named manual reviewer, a named partner feed.

Conformant implementations:

- MUST assign each source a stable identifier (a "source ID") that does not change across observations of the same source.
- MUST NOT assign the same source ID to two processes that draw from different input domains. (Renaming a wrapper around an external service does not create a new source.)
- SHOULD encode in the source ID enough information for an auditor to attribute the observation to its origin (e.g., `hibp_api`, `email_validator`, `holehe_v2`).

A source that is split into multiple sub-process instances (e.g., parallel workers of the same scraper) MUST share the same source ID. Two parallel workers of `hibp_api` do not count as two cross-verifications.

### 15.3 Scope: Subject-Scoped, Not Population-Scoped

The cross-verification count for tuple `(subject_S, claim_type_T, claim_value_V)` is computed by counting the distinct sources that have reported `(claim_type_T, claim_value_V)` **for subject_S**, less any source whose own observation is the one under consideration.

Cross-verification MUST NOT be computed by counting sources that report `(claim_type_T, claim_value_V)` across the whole subject population. That would conflate independent subjects who happen to share an identifier (a common email-on-shared-domain, a generic username) and would produce a misleading trust signal.

*Non-normative note: this is why a username "john" detected by 100 sources across 100 subjects yields a cross-verification count of 0 for each subject, not 99.*

### 15.4 Self-Exclusion

The source under consideration MUST NOT count itself in its own cross-verification. For a finding emitted by source `S_a` reporting tuple `(S, T, V)`, the cross-verification count is `len({S_b, S_c, ...})` where each `S_x` is a distinct source other than `S_a` that has also reported `(S, T, V)`.

### 15.5 Source Idempotence

A source that emits the same `(subject, claim-type, claim-value)` tuple multiple times (e.g., across re-scans, across re-tries, across observation windows) MUST contribute **exactly one** to the cross-verification count of any other source observing the same tuple. Cross-verification counts the **set** of distinct sources, not the multiset of observations.

### 15.6 Snapshot Semantics

The cross-verification count and the ordered list of contributing source IDs (the **cross-verification sources**) are properties of an observation at a moment in time. They MAY change as new sources observe the same tuple, or as sources are retired from a deployment.

When a cross-verification count is used as input to a claim (§16), the count and sources MUST be captured as a **snapshot at the time of claim emission**. Subsequent changes to the live count do not retroactively change the emitted claim's snapshot.

### 15.7 Cross-Verification Sources Ordering

The list of source IDs contributing to a cross-verification count MUST be serialized in lexicographic ascending order whenever the list is used as input to a hash function or to a canonical encoding. This ordering requirement is what makes claim hashes (§16.3) deterministic across implementations.

### 15.8 Conformance

A conformant implementation:

- MUST compute cross-verification counts subject-scoped (§15.3).
- MUST exclude the self-source from its own count (§15.4).
- MUST treat repeated observations from one source as a single contribution (§15.5).
- MUST capture count and sources as snapshots at claim emission (§15.6).
- MUST sort source IDs lexicographically when serializing for hashing (§15.7).
- SHOULD persist computed cross-verification counts rather than recompute at every query (performance and consistency).
- SHOULD expose cross-verification metadata (count + sources) on the observation record itself, not only at the claim layer.

*Non-normative note: in the xposeTIP reference implementation, cross-verification counts are persisted on the `findings` table as `cross_verification_count` (Integer, indexed) and `cross_verification_sources` (JSONB array). The columns are written transactionally with new finding inserts. As of v1.6.0, 48.0% of stored findings have a cross-verification count of ≥1.*

---

## 16. Claim Log

### 16.1 Definition

A **claim** is the protocol's atomic unit of corroborated fact about a subject. A claim asserts:

> "Subject `S` has property `T` with value `V`, corroborated by `N` independent sources at time `E`."

The complete set of claims for a given operator constitutes the **claim log**: an append-only, content-addressable record of all corroborated observations the operator has made.

### 16.2 Claim Structure

A conformant claim MUST contain at minimum the following fields:

| Field | Type | Semantics |
|---|---|---|
| `subject_id` | string | Stable identifier of the subject within the operator's domain. |
| `claim_type` | string | Classifier of the asserted property (e.g., `email`, `username`, `phone`, `ip`, `domain`). Implementation-defined vocabulary; SHOULD use the same vocabulary across an operator. |
| `claim_value` | string | The asserted value of `claim_type` for `subject_id`. |
| `cross_verification_count` | integer ≥ 0 | Number of distinct sources corroborating `(claim_type, claim_value)` for `subject_id`, per §15. |
| `cross_verification_sources` | array of string | Lexicographically sorted source IDs (§15.7) contributing to the count. |
| `verified_at_emission` | boolean | Snapshot of any implementation-defined `verified` flag at the time of emission. MAY always be `false` in implementations that do not maintain such a flag. |
| `emitted_at` | string (RFC 3339 timestamp, UTC, microsecond precision recommended) | The moment the claim entered the log. |
| `claim_hash` | string (lowercase hex) | SHA-3-256 of the canonical encoding (§16.3). |
| `claim_hash_version` | integer | Hash algorithm version, currently `1` for SHA-3-256 over the canonical encoding defined in §16.3. |

Conformant implementations MAY add fields beyond the above (e.g., implementation-specific provenance pointers, evidence references, supplementary metadata) but MUST NOT change the semantics of the listed fields.

Two fields are **reserved** for the trust anchor layer defined in §17:

| Field | Type | Set by |
|---|---|---|
| `merkle_position` | integer ≥ 0 | The Merkle anchor builder (§17). Null until the first anchor is constructed. |
| `inclusion_proof` | array of string (RESERVED) | Sibling hashes for inclusion proof. Reserved for a future version of this specification. |

Two fields are **reserved** for cryptographic signatures (post-quantum, §13):

| Field | Type | Set by |
|---|---|---|
| `subject_signature` | string (RESERVED) | A SPHINCS+ / SLH-DSA signature by the subject's binding key over the canonical encoding. Reserved for a future version. |
| `operator_signature` | string (RESERVED) | An ML-DSA signature by the operator's signing key over the canonical encoding. Reserved for a future version. |

### 16.3 Canonical Encoding

The **canonical encoding** of a claim is the byte sequence used as input to the hash function in §16.4. The canonical encoding MUST be the UTF-8 byte representation of a JSON object containing **exactly** the following fields, in the following structure:

```
{
  "claim_hash_version": <int>,
  "claim_type": <string>,
  "claim_value": <string>,
  "cross_verification_count": <int>,
  "cross_verification_sources": [<sorted strings>],
  "emitted_at": <RFC 3339 string>,
  "subject_id": <string>,
  "verified_at_emission": <bool>
}
```

The JSON serialization MUST satisfy all of the following:

- Object keys serialized in lexicographic ascending order ("sort_keys").
- No whitespace separators between tokens; the key/value separator is `:`, the item separator is `,`.
- String values escaped per RFC 8259 (JSON).
- Booleans serialized as `true` / `false` (no quoting).
- Integers serialized in decimal without leading zeros.
- `cross_verification_sources` array members sorted lexicographically ascending (per §15.7).

The reference encoding produced by Python's `json.dumps(obj, sort_keys=True, separators=(",", ":"))` is conformant.

### 16.4 Hash Function

The `claim_hash` field MUST be the lowercase hexadecimal representation of `SHA3-256(canonical_encoding)`, where SHA3-256 is the 256-bit instance of the SHA-3 family defined in FIPS 202.

Implementations MUST NOT substitute SHA-256, BLAKE2, BLAKE3, or any other hash function while maintaining `claim_hash_version = 1`. A future version of this specification MAY introduce additional hash algorithms by reserving new `claim_hash_version` values.

### 16.5 Emission Rule

A claim MUST be emitted to the log if and only if **both** of the following are true:

- The triple `(subject_id, claim_type, claim_value)` is fully populated (no field is null or empty), and
- The observation has `cross_verification_count ≥ 1`.

Observations that do not satisfy these conditions MUST NOT enter the log.

*Non-normative rationale: requiring cross-verification ≥ 1 ensures that every claim in the log carries an independent corroboration signal. Emitting on single-source observations would dilute the trust substrate with material that has no independent witness.*

### 16.6 Uniqueness and Deduplication

The log MUST enforce uniqueness on the tuple `(subject_id, claim_type, claim_value)`. A second attempt to emit a claim for an already-present tuple MUST NOT produce a new log entry. Conformant implementations:

- MUST silently swallow the duplicate (no error to the caller).
- MUST NOT overwrite the existing claim's `claim_hash`, `emitted_at`, `cross_verification_count`, `cross_verification_sources`, or any reserved field with values derived from the second attempt.

*Non-normative note: this means the log preserves the FIRST observation's snapshot for any given (subject, type, value) tuple. Re-corroboration by additional sources after the first emission does not retroactively change the stored count. This is a deliberate design choice — a claim's hash is a commitment to its emission-time evidence, not a running tally. Evidence evolution is addressed in §16.8.*

### 16.7 Append-Only Property

Once a claim has entered the log, it MUST NOT be modified or removed. Specifically:

- Implementations MUST NOT provide an API or interface for updating any claim field after emission.
- Implementations MUST NOT provide an API or interface for deleting an emitted claim.
- Garbage-collection or storage-tier migration that preserves the claim's bytes verbatim is permissible.

Conformant implementations SHOULD enforce the append-only property at the storage layer (e.g., database triggers blocking UPDATE/DELETE, restricted database roles, immutable storage backends) when the operational threat model warrants it. At minimum, conformant implementations MUST enforce the property by convention in application code and MUST document the boundary of enforcement.

*Non-normative note: the xposeTIP reference implementation at v1.6.0 enforces this property by convention in application code only. A `UNIQUE (subject_id, claim_type, claim_value)` constraint blocks the most common accidental mutation path. Hardened DB-level enforcement is anticipated for a future hardening sprint.*

### 16.8 Evidence Evolution

When subsequent observations contradict, refine, or otherwise update the evidence underlying a previously-emitted claim, the log MUST NOT modify the original claim. Future versions of this specification will define one or more of:

- A **supersession chain** mechanism, by which a newer claim explicitly supersedes an older one while preserving both in the log.
- A **retraction record** mechanism, by which the operator marks a claim as retracted via a new log entry that references the retracted claim's hash.

Until that mechanism is specified, conformant implementations MAY use auxiliary tables or logs to record evidence-evolution metadata, but MUST NOT mutate the claim log itself.

### 16.9 Conformance

A conformant implementation:

- MUST persist all fields specified in §16.2 for every emitted claim.
- MUST compute `claim_hash` per §16.3 and §16.4.
- MUST enforce the emission rule in §16.5.
- MUST enforce uniqueness per §16.6.
- MUST treat the log as append-only per §16.7.
- MUST NOT mutate emitted claims to reflect post-emission evidence changes (§16.8).
- SHOULD expose the canonical encoding via a query interface so external verifiers can recompute `claim_hash` independently.

*Non-normative note: in the xposeTIP reference implementation, claims are persisted in the `bfp_claims` table. As of v1.6.0, 1,107 claims have been emitted across 15 workspaces, with claim types distributed across `ip`, `username`, `email`, `domain`, `first_name`, and `social_url`. Each claim has been verified to be reproducible from its stored fields via the canonical encoding.*

---

## 17. Merkle Anchor

### 17.1 Definition

A **Merkle anchor** is a single fixed-length cryptographic commitment to the entire content of a claim log at a specific moment in time. The anchor is the root hash of a binary Merkle tree built over the claim hashes (§16.4) in canonical order.

The Merkle anchor provides the **tamper-evidence** property: any modification to a stored claim (mutation, deletion, reordering) changes the anchor. An external party in possession of a previous anchor can therefore detect any post-emission modification of the claim log without re-fetching the log itself.

### 17.2 Scope

Each Merkle anchor MUST be computed within a single **trust boundary**, defined by the operator. Two distinct trust boundaries (e.g., two organizational units, two product environments, two operator instances) MUST NOT be combined into a single anchor. Cross-boundary aggregation, when needed, is the role of a future federation protocol (out of scope for v0.2).

*Non-normative note: in the xposeTIP reference implementation, the trust boundary is the workspace. Each workspace has an independent anchor history.*

### 17.3 Canonical Leaf Ordering

Within a trust boundary, claims MUST be ordered for anchor construction by:

1. `emitted_at` ascending (oldest first), with
2. `claim_hash` ascending (lexicographic on hex) as deterministic tiebreaker when two claims share an `emitted_at` value.

The 0-indexed position of a claim in this canonical ordering is the claim's `merkle_position` (§16.2).

### 17.4 Leaf Hash

The leaf hash of a claim is computed as:

```
leaf_hash = SHA3-256( 0x00 || raw_claim_hash )
```

where:

- `0x00` is a single byte with value zero, the leaf domain-separation prefix (per RFC 6962 §2.1, adapted to SHA-3-256).
- `raw_claim_hash` is the 32-byte raw decoding of the claim's `claim_hash` field (§16.4), i.e., the inverse of the hexadecimal encoding.
- `||` denotes byte concatenation.
- `SHA3-256` is the 256-bit instance of SHA-3 defined in FIPS 202.

The leaf hash is 32 bytes (256 bits).

### 17.5 Internal Node Hash

The hash of an internal tree node is computed from its two child hashes as:

```
internal_hash = SHA3-256( 0x01 || left_child_hash || right_child_hash )
```

where:

- `0x01` is a single byte with value one, the internal-node domain-separation prefix (per RFC 6962 §2.1, adapted to SHA-3-256).
- `left_child_hash` and `right_child_hash` are each 32-byte values from the level below.

Domain separation between leaves (`0x00`) and internal nodes (`0x01`) is REQUIRED and serves to prevent second-preimage attacks at level boundaries (e.g., constructing a leaf whose hash collides with an internal node).

### 17.6 Odd-Leaf Promotion

When constructing the tree level-by-level, if a level contains an odd number of nodes, the **unpaired** (final) node at that level MUST be promoted unchanged to the next level up.

Implementations MUST NOT duplicate the unpaired node, hash it with itself, or treat it as a sibling of a zero-padded peer. Duplication of the last node is the antipattern documented in CVE-2012-2459, which permits two distinct sets of leaves to produce the same root hash and therefore breaks the anchor's commitment property.

### 17.7 Empty-Tree Semantics

A trust boundary that contains zero claims MUST NOT have a recorded Merkle anchor. Implementations MUST NOT record a sentinel value (e.g., the hash of the empty string) as a root for an empty tree.

A trust boundary that contains exactly one claim has a Merkle root equal to that claim's leaf hash (per §17.4); the tree has a single leaf and zero internal nodes.

### 17.8 Anchor Snapshots

Each rebuild of the Merkle tree over a given trust boundary MUST produce a **new anchor snapshot** recording at minimum:

| Field | Type | Semantics |
|---|---|---|
| `trust_boundary_id` | string | Identifier of the trust boundary (e.g., workspace ID). |
| `root_hash` | string (lowercase hex) | The 64-character hex representation of the tree's root hash. |
| `num_leaves` | integer ≥ 1 | The number of claims included in this anchor. |
| `anchor_version` | integer | The version of the anchor algorithm. Currently `1`, denoting SHA3-256 + RFC-6962-style domain separation + the ordering of §17.3. |
| `computed_at` | string (RFC 3339 timestamp, UTC) | The moment the rebuild ran. |

Anchor snapshots MUST be append-only with the same semantics as the claim log itself (§16.7): once recorded, an anchor snapshot MUST NOT be modified or removed.

When the underlying claim log has not changed between two rebuilds, the resulting anchors MUST have identical `root_hash` values. Stability of the root across rebuilds is itself a tamper-evidence signal: an unexpected change in `root_hash` between two anchors of identical `num_leaves` indicates that a claim has been mutated.

### 17.9 Rebuild Frequency

This specification does not mandate any specific rebuild frequency. Conformant implementations:

- MUST be able to rebuild the anchor on demand.
- MAY rebuild on every claim emission, periodically (e.g., scheduled job), or only when explicitly requested.
- SHOULD record at least one anchor snapshot whenever the claim log within a trust boundary has changed since the previous snapshot.

*Non-normative note: the xposeTIP reference implementation at v1.6.0 rebuilds anchors on explicit invocation only (batch script). A scheduled rebuild trigger is anticipated as a near-term enhancement.*

### 17.10 Independent Verification

A conformant implementation MUST provide a means for an external party in possession of:

- the canonical claim list of a trust boundary (e.g., via §16.9's query interface), and
- the claimed `root_hash` and `num_leaves` for that boundary,

to **independently recompute the root hash** and compare it to the claimed value. Mismatch detection is the operational core of the tamper-evidence property.

Implementations SHOULD ship a standalone verification utility that consumes the claim list and the claimed anchor as inputs, recomputes the root, and reports match or mismatch.

*Non-normative note: in the xposeTIP reference implementation, this utility is `scripts/verify_bfp_merkle.py`. Empirical tamper detection has been demonstrated: corruption of one hexadecimal character in a single claim's stored hash causes the recomputed root to diverge from the stored anchor and the utility to report failure.*

### 17.11 Conformance

A conformant implementation:

- MUST compute leaf hashes per §17.4.
- MUST compute internal node hashes per §17.5.
- MUST promote unpaired nodes unchanged per §17.6.
- MUST NOT record an anchor for an empty trust boundary (§17.7).
- MUST record anchors as append-only snapshots per §17.8.
- MUST provide independent verification per §17.10.
- SHOULD persist `merkle_position` on each claim after each rebuild for efficient inclusion-proof generation in future versions.

### 17.12 Out of Scope for v0.2

The following are anticipated for future versions of this specification and are intentionally not specified here:

- **Inclusion proofs**: the algorithm for producing and verifying that a specific claim is included in a given anchor without revealing the rest of the log.
- **Consistency proofs**: the algorithm for proving that one anchor is an append-only extension of another (i.e., older claims have not been mutated between two anchor snapshots).
- **Signed Tree Heads (STH)**: a cryptographically signed envelope around an anchor, enabling third parties to attest to anchor authenticity. Requires the post-quantum signature stack of §13.
- **Anchor gossip and federation**: the protocol by which independent operators exchange anchors to provide mutual surveillance of each other's claim logs.

*Non-normative note: these are the mechanisms by which Certificate Transparency achieves its full security model. BFP v0.2 ships the anchor construction; the auxiliary mechanisms are roadmap.*

---

## Appendix A: Legacy Axis Name Aliases

For one release following adoption of this specification, the reference implementation SHALL accept and emit deprecation-warned legacy axis names. Mappings:

| Legacy name | Canonical name (v0) |
|---|---|
| `accounts` | `account_count` |
| `platforms` | `platform_diversity` |
| `username_reuse` | `handle_persistence` |
| `breaches` | `breach_incidents` |
| `data_leaked` | `breach_severity` |
| `geo_spread` | `geo_dispersion` |
| `email_age` | `email_age` (unchanged) |
| `security` | **SPLIT** — no direct alias. Consumers SHOULD migrate to `email_security_posture` and `account_hygiene`. Legacy emit MAY synthesize as `mean(email_security_posture, account_hygiene)` with deprecation warning. |
| `public_exposure` | **SPLIT** — no direct alias. Consumers SHOULD migrate to `media_presence` and `formal_records`. Legacy emit MAY synthesize as `mean(media_presence, formal_records)` with deprecation warning. |

After the one-release deprecation window, the legacy names MUST be removed.

---

## Appendix B: Open Items for v1

The following items are intentionally deferred from v0.x. They are anchored here to track scope toward v1.0.

### Fingerprint-layer open items

- Full signed provenance model with per-source attribution.
- Cross-implementation calibration procedure for `F_axis` functions.
- Standardized profiles beyond `bfp-cosine-default-v0`.
- Per-axis weight tuning with normative constraints.
- Stylometric pipeline for `linguistic_signature`.
- Activity-pattern extraction for `activity_rhythm`.
- Conformance test suite (fingerprint-layer).
- Reference test vectors for the fingerprint hash (§9.2) and behavioral hash (§9.3).

### Trust-layer open items

- PQC integration in claim emission: subject and operator signatures wired into the claim emitter, populating the `subject_signature` and `operator_signature` fields already reserved in the claim structure (§16.2).
- Subject portal: a normative interface specification for the Read (§12.1 Tier 1) and Guidance (§12.1 Tier 2) tiers.
- Monitoring tier infrastructure: delta computation, change-significance thresholds, notification dispatch.
- Managed Remediation workflow: scrubbing, coordination with databrokers, takedown request packaging within legal-soupape constraints.
- Inclusion-proof generation for claims (currently §17.12 lists this as out-of-scope for v0.2; v0.3+ target).
- Claim supersession mechanism: defines what happens when evidence about a past claim evolves (typo correction, refutation, etc.) while preserving append-only of the original (§16.8).
- Multi-operator trust-boundary federation: cross-operator claim transfer and audit semantics.
- Independent end-to-end audit of the chosen PQC library's constant-time properties (cited as risk #1 in `docs/specs/pqc_choices_v0.md` §5).
- Conformance test suite (trust-layer).

### Cross-cutting open items

- Mapping to common data-subject-rights frameworks (GDPR, CCPA, PIPEDA, etc.) at the level of §12.1 tiers.
- Threat model for adversarial fingerprint manipulation and trust-log gaming.
- Versioning interaction matrix for the four component versions in §14.1 (which combinations are forward-compatible, which require migration).

### Items moved out of "deferred" as of v0.2.1

- ~~Graph signature computation for `network_signature`~~ — shipped in S147 of the reference implementation; axis is now in production use. Spec section §5.5.x will be flagged STABLE in v0.2.2.
- ~~Basic trust layer mechanics~~ — shipped across S166-S170 of the reference implementation; specified in §13-§17 of this document.

---

*End of BFP v0.2.2 public working draft.*
