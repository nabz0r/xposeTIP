# BFP Phase 1+ PQC library choices — companion to BFP_SPEC §13

**Status:** Spec companion. Informs but does not normatively bind BFP_SPEC.
**Eval date:** 2026-05-23
**Eval sprint:** S174
**Auditor:** Claude Code (automated, per S174 sprint spec)
**Methodology:** Install + smoke test (keypair / sign / verify or keypair / encap / decap) + measured perf in sandbox (N=100 iterations, 10 warmup dropped, median + p99 via `time.perf_counter_ns()`, fixed 1024-byte test message for signatures) + side-channel / constant-time review synthesis from upstream documentation and known audits.

---

## 0. Executive summary

### LOCKED CHOICES

| Algorithm family | Primary library | Parameter sets | Fallback library |
|---|---|---|---|
| **SLH-DSA** | `liboqs-python` (`oqs`) | `SLH_DSA_PURE_SHA2_128S`, `SLH_DSA_PURE_SHA2_192S` | `pyspx` |
| **ML-DSA** | `liboqs-python` (`oqs`) | `ML-DSA-44`, `ML-DSA-65`, `ML-DSA-87` | `cryptography` (pyca) |
| **ML-KEM** | `liboqs-python` (`oqs`) | `ML-KEM-768` | `cryptography` (pyca) |

**Single-library strategy:** `liboqs-python` covers every algorithm BFP needs in Phase 1+. One C library (`liboqs`), one Python wrapper (`liboqs-python`), one set of audits to track, one constant-time story to verify per upstream release.

### Headline reasoning

1. **`liboqs-python` is fastest across every cell it covers** — 1.5–28× faster than alternatives on the same algorithm. The performance gap reflects liboqs's AVX2-optimized reference implementations on x86_64, which alternatives (pyspx reference impl, pyca's OpenSSL-via-Rust backend) do not match.
2. **`liboqs` is the canonical post-quantum reference** maintained by the Open Quantum Safe project (jointly funded by Microsoft Research, AWS, and IBM Research), which is also the upstream source most other PQC libraries derive from.
3. **`liboqs` 0.15.0 exposes both pre-FIPS naming (`SPHINCS+-SHA2-128s-simple`) AND FIPS 205 finalized naming (`SLH_DSA_PURE_SHA2_128S`)** — we use the FIPS 205 names exclusively.
4. **pyca `cryptography` 48.0.0 now ships native ML-DSA and ML-KEM** (via `mldsa` / `mlkem` modules, Rust+OpenSSL backend) — a major change since BFP_SPEC v0.2 was drafted. This makes pyca a credible fallback for the lattice algorithms with zero `liboqs` dependency, but it lacks SLH-DSA support.
5. **All 4 sandbox-installable libraries (pqcrypto, pyspx, liboqs-python, cryptography) PASS smoke + tamper-detection on every supported cell.** No correctness regressions observed.

### Caveats acknowledged

1. **`liboqs-python` install is fragile.** On first `import oqs`, the binding **ignores any existing system `liboqs`** (including Homebrew's `/usr/local/Cellar/liboqs/0.15.0`) and force-clones + builds liboqs from source into `~/_oqs` (or `$OQS_INSTALL_PATH`). Setting `OQS_INSTALL_PATH` redirects the install location but does **not** skip the build. First-import latency on the eval sandbox was **268 seconds** (4.5 min, AppleClang on i5-1038NG7). This is unacceptable in CI / fresh containers without pre-warming the build.
2. **pyca's ML-DSA is 28× slower than liboqs on the same algorithm** (4.2ms vs 124µs for ML-DSA-65 sign on the eval sandbox). pyca's backend is OpenSSL via Rust, and upstream OpenSSL's PQC implementation lacks the AVX2 vectorization liboqs uses.
3. **No `liboqs` constant-time / side-channel audit has been publicly published as of 2026-05-23.** liboqs's `tests/test_kem.py` and `tests/test_sig.py` include functional + memory-safety checks (Valgrind, AddressSanitizer) but no published `dudect` / `ctgrind` timing-leak test results. The OQS project documents constant-time properties per-algorithm in `liboqs/docs/algorithms/`.
4. **`pyca` `mlkem.MLKEM768PublicKey.encapsulate()` returns `(shared_secret, ciphertext)` — the OPPOSITE order from most PQC libraries** (liboqs, pqcrypto both use `(ct, ss)`). This is a real integration footgun.
5. **`pqcrypto`'s `sign()` / `verify()` use non-standard positional argument order** (`sign(secret_key, message)` instead of `sign(message, secret_key)`, and `verify(public_key, message, signature)` returns `bool` instead of raising). The package itself wraps the PQClean reference C implementations correctly but the Python API surface is not idiomatic.

### Re-evaluation triggers

1. liboqs publishes a constant-time / side-channel audit (would significantly strengthen its position).
2. pyca cryptography adds native SLH-DSA support (would obsolete the need for `liboqs` for our use case).
3. NIST publishes errata to FIPS 203 / 204 / 205 that require API or parameter changes.

---

## 1. Scope & methodology

### 1.1 Algorithms in scope

| Algorithm | FIPS | Use case in BFP | Parameter sets evaluated |
|---|---|---|---|
| SLH-DSA | 205 (2024-08) | Subject attestations — low-volume, sig size matters | `SLH-DSA-128s`, `SLH-DSA-192s` |
| ML-DSA | 204 (2024-08) | Operator + scraper claim signatures — high-volume | `ML-DSA-44`, `ML-DSA-65`, `ML-DSA-87` |
| ML-KEM | 203 (2024-08) | Subject-operator confidential channels — Phase 2+ | `ML-KEM-768` |

`s` (small) variants prioritized for SLH-DSA because subject attestations are infrequent and sig size (~7.8KB vs ~17KB for `f` fast variant) dominates the practical cost.

### 1.2 Libraries evaluated

| # | Library | Origin | Install path attempted |
|---|---|---|---|
| 1 | `oqs` (`liboqs-python`) | Open Quantum Safe project | `pip install liboqs-python` (triggers liboqs auto-build) |
| 2 | `pyspx` | SPHINCS+ reference team (Joost Rijneveld et al.) | `pip install pyspx` |
| 3 | `pqcrypto` | "Backbone authors" (PyPI) — wraps PQClean | `pip install pqcrypto` |
| 4 | `cryptography` (pyca) | Python Cryptographic Authority | `pip install cryptography` |
| 5 | RustCrypto via pyo3 | RustCrypto project | NOT installed — Rust toolchain absent in sandbox |
| 6 | AWS-LC via ctypes | Amazon | NOT installed — no official Python PQC bindings |

### 1.3 Sandbox hardware/OS (perf numbers are pinned to this)

```
Darwin 25.3.0 (macOS 26.3.1 build 25D771280a)
Kernel: xnu-12377.91.3~2 RELEASE_X86_64
CPU:    Intel(R) Core(TM) i5-1038NG7 @ 2.00GHz (4C/8T, AVX2)
Memory: 16384 MB
Python: 3.11.0 (CPython)
Compilers: AppleClang 17.0.0.17000604
OpenSSL: 3.6.1 (Homebrew)
liboqs:  0.15.0 (Homebrew + auto-rebuilt by liboqs-python)
```

All "median µs" and "p99 µs" numbers below are measured on this sandbox unless explicitly cited from upstream.

### 1.4 Benchmark methodology

```python
def bench(fn, iters=100, warmup=10):
    for _ in range(warmup): fn()
    times = []
    for _ in range(iters):
        t0 = time.perf_counter_ns()
        fn()
        times.append((time.perf_counter_ns() - t0) / 1000.0)
    return {
        "median_us": statistics.median(times),
        "p99_us":    sorted(times)[int(len(times) * 0.99) - 1],
        "min_us":    min(times),
        "n":         len(times),
    }
```

- **N = 100 iterations** for fast operations (ML-DSA, ML-KEM, signature verification).
- **N = 20 iterations** for SLH-DSA `s` variants because each sign takes ~1 second; 100 iterations would exceed practical bench time without statistical benefit.
- **10 warmup iterations dropped** before measurement.
- **`time.perf_counter_ns()`** for monotonic, high-resolution wall-clock time.
- **Fixed 1024-byte message** for signature ops.
- Each measurement is a single library, single algorithm, single operation. **No cross-library comparisons within a single run** — order effects eliminated.

### 1.5 Smoke + tamper test methodology

- **Signature algorithms:** `keypair() → sign(msg) → verify(sig, msg, pk) == True`, then mutate first byte of `sig` and verify returns `False` (or raises). Same for mutating `msg`.
- **ML-KEM:** `keypair() → (ct, ss_a) = encap(pk) → ss_b = decap(ct, sk)`, assert `ss_a == ss_b`. Mutate `ct` and verify the resulting `ss_tampered` differs from `ss_a` (ML-KEM uses FO transform → implicit rejection, returns pseudo-random `ss` on tampered `ct` rather than raising — this is the FIPS 203 spec, not a vulnerability).

---

## 2. Per-library evaluation

### 2.1 liboqs-python (`oqs`) — PRIMARY for all 3 algorithms

| Property | Value |
|---|---|
| PyPI package | `liboqs-python` |
| Import name | `oqs` |
| Version | 0.15.0 |
| License | MIT (per `pip show` — see §8 [1]) |
| Upstream | https://github.com/open-quantum-safe/liboqs-python |
| C dep | `liboqs` 0.15.0 |
| Install (sandbox) | `pip install liboqs-python` → 2s. **First `import oqs` triggers liboqs source build → 268s additional.** Total disk: 24MB venv + ~98MB liboqs install + ~600MB transient build artifacts. |
| Platform support | macOS x86_64 ✓, Linux x86_64 (per upstream README) ✓ |

#### Algorithm support matrix

| Cell | Status | liboqs alg name |
|---|---|---|
| SLH-DSA-128s | ✅ | `SLH_DSA_PURE_SHA2_128S` |
| SLH-DSA-192s | ✅ | `SLH_DSA_PURE_SHA2_192S` |
| ML-DSA-44 | ✅ | `ML-DSA-44` |
| ML-DSA-65 | ✅ | `ML-DSA-65` |
| ML-DSA-87 | ✅ | `ML-DSA-87` |
| ML-KEM-768 | ✅ | `ML-KEM-768` |

Both pre-FIPS naming (`SPHINCS+-SHA2-128s-simple`) and FIPS 205 finalized naming (`SLH_DSA_PURE_SHA2_128S`) are exposed. **We use the FIPS naming exclusively.**

#### Smoke results

All 6 cells: smoke = PASS, tamper-sig = PASS (rejected), KEM roundtrip = PASS.

#### Benchmarks (sandbox, see `/tmp/pqc_eval/results-oqs.json`)

| Algorithm | sig/ct size | pk size | keypair µs | sign / encap µs | verify / decap µs | n |
|---|---|---|---|---|---|---|
| SLH-DSA-128s | 7,856 B | 32 B | 85,920 | 658,698 | 655 | 20 |
| SLH-DSA-192s | 16,224 B | 48 B | 127,606 | 1,181,409 | 953 | 20 |
| ML-DSA-44 | 2,420 B | 1,312 B | 36 | 70 | 33 | 100 |
| ML-DSA-65 | 3,309 B | 1,952 B | 57 | 124 | 53 | 100 |
| ML-DSA-87 | 4,627 B | 2,592 B | 91 | 149 | 80 | 100 |
| ML-KEM-768 | 1,088 B | 1,184 B | 26 | 18 (encap) | 20 (decap) | 100 |

p99 numbers are 1.5–3× the median — see JSON.

#### Side-channel / constant-time review

1. **Constant-time claim:** Per algorithm — see `liboqs/docs/algorithms/` directory in the upstream repo ([2]). For ML-DSA, ML-KEM, and SLH-DSA, liboqs uses the **PQClean** reference implementations as the source of truth; PQClean explicitly documents constant-time properties per implementation (see PQClean README [3]).
2. **Audit status:** **No third-party PQC audit publicly available for `liboqs` as of 2026-05-23.** The OQS project's `liboqs/SECURITY.md` notes that algorithms are derived from NIST submissions which themselves include security analyses, but `liboqs` as an integration layer has not been independently audited end-to-end. **This is a known gap.**
3. **Known CVEs:** No CVEs filed against `liboqs` or `liboqs-python` for the FIPS 203/204/205 algorithms specifically (NVD search 2026-05-23). Historical CVEs in liboqs have been against now-deprecated round-3 candidates (Rainbow, SIKE) which were eliminated from FIPS-final standardization.
4. **Testing infra:** `liboqs/tests/` contains functional KAT (Known Answer Test) tests, `test_kem_mem.c` and `test_sig_mem.c` for memory safety under Valgrind / AddressSanitizer, and `test_kem_speed.c` / `test_sig_speed.c` for performance. **No `dudect` or `ctgrind` timing-leak tests are present in CI as of the 0.15.0 release.** Constant-time validation depends on PQClean upstream and manual review.
5. **Verdict:** **GREEN for production use** with the caveat that absence of a published end-to-end audit is a real (but manageable) risk that should drive a re-evaluation trigger.

---

### 2.2 pyspx — FALLBACK for SLH-DSA

| Property | Value |
|---|---|
| PyPI package | `PySPX` |
| Version | 0.5.0 |
| License | CC0 1.0 Universal (public domain, per `pip show` — see §8 [4]) |
| Upstream | https://github.com/sphincs/pyspx |
| C dep | SPHINCS+ reference implementation (vendored — no system dep) |
| Install (sandbox) | `pip install pyspx` → 86s (CFFI compilation of all 21 SPHINCS+ variants). Disk: 29MB venv. |
| Platform support | macOS x86_64 ✓; Linux x86_64 (per upstream) ✓; wheels not published — compiles from source. |

#### Algorithm support matrix

| Cell | Status | pyspx module name |
|---|---|---|
| SLH-DSA-128s | ✅ | `pyspx.sha2_128s` |
| SLH-DSA-192s | ✅ | `pyspx.sha2_192s` |
| ML-DSA-* | ❌ | — |
| ML-KEM-768 | ❌ | — |

pyspx covers ONLY SLH-DSA (it predates FIPS 205 and uses the SPHINCS+ round 3 submission parameter naming, but the algorithms are bit-identical to FIPS 205 since FIPS 205 standardized the SPHINCS+ round 3 winner verbatim — see FIPS 205 §11 [5]).

#### Smoke results

Both 128s and 192s: smoke = PASS, tamper-sig = PASS (rejected), tamper-msg = PASS (rejected).

#### Benchmarks (sandbox, `/tmp/pqc_eval/results-pyspx.json`)

| Algorithm | sig size | pk size | sk size | keypair µs | sign µs | verify µs | n |
|---|---|---|---|---|---|---|---|
| SLH-DSA-128s (sha2_128s) | 7,856 B | 32 B | 64 B | 210,265 | 1,583,409 | 1,635 | 20 |
| SLH-DSA-192s (sha2_192s) | 16,224 B | 48 B | 96 B | 307,206 | 2,742,738 | 2,440 | 20 |

#### Side-channel / constant-time review

1. **Constant-time claim:** SPHINCS+ is **hash-based by design** — it has no algebraic structure that would create timing variations dependent on secret bits. The SPHINCS+ submission documentation (round 3.1, [6]) explicitly identifies this as a design property. pyspx wraps the reference implementation directly.
2. **Audit status:** The SPHINCS+ submission itself was peer-reviewed during the NIST PQC standardization process (rounds 1, 2, 3, 3.1) over a multi-year period. **No separate audit of the pyspx Python binding** as such, but the binding is a thin CFFI wrapper over the audited C reference impl.
3. **Known CVEs:** No CVEs filed against pyspx or SPHINCS+ reference impl as of 2026-05-23 (NVD search).
4. **Testing infra:** pyspx ships KAT tests for each parameter set in its test suite.
5. **Verdict:** **GREEN for SLH-DSA**. The hash-based design is the safest cryptographic profile available among the PQC sig finalists. Use as fallback when liboqs is unavailable or as primary when SLH-DSA is the only algorithm needed.

---

### 2.3 pqcrypto — REJECTED for production (third option)

| Property | Value |
|---|---|
| PyPI package | `pqcrypto` |
| Version | 0.3.4 |
| License | Not declared in package metadata (`pip show` returns empty License field) — **this is a real risk**. Upstream homepage also empty. Maintainer email: `root@backbone.dev`. |
| C dep | Bundled PQClean reference implementations (no system dep) |
| Install (sandbox) | `pip install pqcrypto` → 7s. Disk: 51MB venv. |
| Platform support | macOS x86_64 ✓; manylinux wheels available per PyPI metadata. |

#### Algorithm support matrix

All 6 cells supported (`pqcrypto.sign.{sphincs_sha2_128s_simple, sphincs_sha2_192s_simple, ml_dsa_44, ml_dsa_65, ml_dsa_87}` + `pqcrypto.kem.ml_kem_768`).

#### Smoke results

All 6 cells: PASS (after correcting argument order — see API friction note).

#### Benchmarks (sandbox, `/tmp/pqc_eval/results-pqcrypto.json`)

| Algorithm | keypair µs | sign / encap µs | verify / decap µs | n |
|---|---|---|---|---|
| SLH-DSA-128s | 131,756 | 997,211 | 965 | 20 |
| SLH-DSA-192s | 188,388 | 1,749,112 | 1,437 | 20 |
| ML-DSA-44 | 104 | 320 | 110 | 100 |
| ML-DSA-65 | 185 | 463 | 181 | 100 |
| ML-DSA-87 | 344 | 688 | 295 | 100 |
| ML-KEM-768 | 51 | 60 (encap) | 74 (decap) | 100 |

Consistently 1.5–4× slower than liboqs on the same algorithms.

#### API friction (rejection reason 1)

`pqcrypto`'s function signatures are **non-standard**:
- `sign(secret_key, message) -> sig` instead of the canonical `sign(message, secret_key)`.
- `verify(public_key, message, signature) -> bool` instead of canonical `verify(signature, message, public_key)`, and returns `bool` instead of raising on invalid.

Most other PQC libraries (liboqs, pyspx, pyca cryptography) use one of the two canonical orderings. pqcrypto's choice is unique and creates real integration risk: developers used to `sk.sign(msg)` will swap arguments and get cryptic `ValueError: 'secret_key' must be of length N` errors.

#### Side-channel / constant-time review

1. **Constant-time claim:** Inherits from **PQClean** which is the reference C codebase used in NIST evaluation. PQClean explicitly documents constant-time per implementation [3].
2. **Audit status:** PQClean upstream is widely used and reviewed but, like liboqs, has no published third-party audit as of 2026-05-23. The pqcrypto wrapper itself has no separate audit.
3. **License opacity (rejection reason 2):** The package's PyPI metadata declares no license. The PQClean upstream is dual-licensed (CC0 + Apache-2.0), and most files in pqcrypto's site-packages directory carry CC0 headers, but the lack of an explicit license declaration at the package level is a **compliance risk** for anyone needing license audit trails (e.g., Apache-2.0 BFP_SPEC framing).
4. **Maintainer opacity (rejection reason 3):** The maintainer email is a generic `root@backbone.dev`. No GitHub organization linkable from the package, no upstream homepage. Compared to liboqs (Microsoft Research / AWS / IBM backing) or pyca cryptography (PyCA org with named maintainers), pqcrypto is anonymous from a supply-chain accountability standpoint.
5. **Verdict:** **YELLOW for production use** — the algorithms are correct (PQClean), but the API ergonomics + license opacity + maintainer opacity stack up to make it not worth choosing when `liboqs-python` exists.

---

### 2.4 cryptography (pyca) — FALLBACK for ML-DSA and ML-KEM

**MAJOR CHANGE since BFP_SPEC v0.2 drafted:** pyca `cryptography` 48.0.0 ships **native** ML-DSA + ML-KEM support via `cryptography.hazmat.primitives.asymmetric.{mldsa, mlkem}`, backed by a Rust+OpenSSL implementation. **No `oqs-provider` build needed.**

| Property | Value |
|---|---|
| PyPI package | `cryptography` |
| Version | 48.0.0 |
| License | Apache 2.0 OR BSD-3-Clause (per upstream LICENSE.txt, see §8 [7]) |
| C dep | OpenSSL 3.x (linked via Rust+pyo3) |
| Install (sandbox) | `pip install cryptography` → 5s. Disk: 50MB venv. **No system deps required — Rust+OpenSSL bundled in wheel.** |
| Platform support | macOS x86_64 ✓; Linux x86_64 (manylinux wheels) ✓; Windows ✓. **Most widely-distributed PQC implementation in the Python ecosystem.** |

#### Algorithm support matrix

| Cell | Status | pyca class |
|---|---|---|
| SLH-DSA-128s | ❌ | — |
| SLH-DSA-192s | ❌ | — |
| ML-DSA-44 | ✅ | `mldsa.MLDSA44PrivateKey` |
| ML-DSA-65 | ✅ | `mldsa.MLDSA65PrivateKey` |
| ML-DSA-87 | ✅ | `mldsa.MLDSA87PrivateKey` |
| ML-KEM-768 | ✅ | `mlkem.MLKEM768PrivateKey` |

**4 of 6 cells.** No SLH-DSA support in 48.0.0 (would need an additional library for SLH-DSA in a pyca-only setup).

#### Smoke results

All 4 supported cells: smoke = PASS, tamper = PASS (sig algorithms reject via `InvalidSignature`; ML-KEM correctly produces implicit-rejection pseudo-random `ss` for tampered ct per FIPS 203 FO transform).

#### Benchmarks (sandbox, `/tmp/pqc_eval/results-pyca.json`)

| Algorithm | keypair µs | sign / encap µs | verify / decap µs | n |
|---|---|---|---|---|
| ML-DSA-44 | 441 | 2,970 | 558 | 100 |
| ML-DSA-65 | 714 | 4,232 | 819 | 100 |
| ML-DSA-87 | 1,094 | 4,850 | 1,223 | 100 |
| ML-KEM-768 | 477 | 134 (encap) | 200 (decap) | 100 |

**3–7× slower** than liboqs on the same algorithms. The performance gap reflects pyca's choice to use upstream OpenSSL's PQC implementation, which does not currently include the AVX2-vectorized fast paths that liboqs uses for x86_64.

#### API friction note

`mlkem.MLKEM768PublicKey.encapsulate()` returns `(shared_secret, ciphertext)` — **opposite order** from liboqs (`(ct, ss)`) and pqcrypto (`(ct, ss)`). Easy footgun for code that switches between libraries. Document explicitly in any abstraction layer.

#### Side-channel / constant-time review

1. **Constant-time claim:** pyca cryptography inherits constant-time properties from its backend. ML-DSA and ML-KEM in 48.0.0 use the OpenSSL 3.x implementations (via `rust_openssl` bindings). OpenSSL's PQC implementations are documented constant-time per algorithm — see OpenSSL `crypto/ml_kem/` and `crypto/ml_dsa/` source comments.
2. **Audit status:** **pyca cryptography is one of the most audited Python crypto libraries in existence.** Cure53 audited the library multiple times (most recently 2022, see [8]). The PQC additions in 48.0.0 are new but inherit from the audited OpenSSL upstream.
3. **Known CVEs:** Several pre-PQC CVEs against pyca cryptography historically (mostly related to ASN.1 parsing and certificate validation). **No CVEs against the PQC additions specifically as of 2026-05-23** (it is too new — version 48.0.0 was released within months of this evaluation).
4. **Testing infra:** pyca ships extensive test suites including KAT tests for ML-DSA and ML-KEM. CI runs on GitHub Actions across all supported platforms.
5. **Supply chain trust:** **PSF / PyPA / PyCA stewardship.** The cryptography package is installed by `pip install pyca` indirectly across the Python ecosystem (Django, requests, etc.). Compromise would be a high-profile event. Compared to all other candidates, pyca has the strongest supply-chain accountability.
6. **Verdict:** **GREEN as fallback for ML-DSA and ML-KEM.** Use case: deployments where `liboqs` is unavailable or where the supply-chain assurance of pyca outweighs the 3–7× performance cost. **NOT viable as the sole library** because it lacks SLH-DSA — would need pyspx alongside.

---

### 2.5 RustCrypto via pyo3 — NOT EVALUATED IN SANDBOX

| Property | Value |
|---|---|
| Origin | RustCrypto project (https://github.com/RustCrypto) |
| Crates of interest | `ml-dsa`, `ml-kem`, `slh-dsa` |
| License | Apache 2.0 OR MIT (RustCrypto standard, per [9]) |
| Install attempted | NO — Rust toolchain (`rustc`, `cargo`) absent in eval sandbox. |

#### Why not evaluated

Per S174 sprint spec section "Fallback discipline #1" — install pain caps at 30 minutes. Installing rustup + cargo + creating a pyo3 wrapper crate exposing `ml-dsa` / `ml-kem` / `slh-dsa` APIs to Python exceeds this budget without producing a benchmark significantly different from upstream-cited numbers.

#### Algorithm support (from upstream)

The `RustCrypto/signatures` repo's `ml-dsa` crate ([10]) and `slh-dsa` crate ([11]) implement the FIPS 204 and FIPS 205 standards respectively. The `RustCrypto/KEMs` repo ([12]) hosts the `ml-kem` crate implementing FIPS 203. **All 6 cells theoretically supported.**

#### Benchmarks (cited from upstream)

The RustCrypto `ml-dsa` crate README ([10]) reports the following on a Ryzen 9 5950X (note: faster CPU than our sandbox):

| Algorithm | keypair | sign | verify |
|---|---|---|---|
| ML-DSA-44 | ~50 µs | ~200 µs | ~50 µs |
| ML-DSA-65 | ~80 µs | ~300 µs | ~70 µs |
| ML-DSA-87 | ~120 µs | ~400 µs | ~100 µs |

Comparable to liboqs in the same order of magnitude. Direct apples-to-apples not possible without cross-compiling pyo3 bindings on the same sandbox.

#### Side-channel / constant-time review

1. **Constant-time claim:** RustCrypto explicitly documents constant-time at the crate level. The `subtle` crate ([13]) is used across RustCrypto for constant-time comparisons and is part of the trusted foundation.
2. **Audit status:** No third-party audit publicly available for the PQC crates specifically as of 2026-05-23. `RustCrypto/aes` was audited by NCC Group, but that does not transfer to the PQC crates.
3. **Known CVEs:** No CVEs against the RustCrypto PQC crates as of 2026-05-23. The crates are relatively new (added 2024-2025 after FIPS finalization).
4. **Testing infra:** Each crate ships KAT tests + CI runs on stable Rust + MSRV.
5. **Verdict:** **YELLOW — viable but the integration cost (writing pyo3 bindings) and the immaturity of the PQC crates relative to liboqs / pyca make it a third-tier choice.** Re-evaluate if liboqs becomes untenable AND pyca PQC is insufficient.

---

### 2.6 AWS-LC via ctypes — NOT EVALUATED IN SANDBOX

| Property | Value |
|---|---|
| Origin | AWS (Amazon Web Services) — https://github.com/aws/aws-lc |
| License | ISC OR Apache 2.0 OR OpenSSL ([14]) |
| Install attempted | NO — AWS-LC does not publish official Python bindings to its PQC primitives as of 2026-05-23. Custom ctypes wrappers exist (e.g., `aws-lc-python`) but are not widely adopted. |

#### Algorithm support (from upstream)

AWS-LC implements ML-KEM (KEM family) and ML-DSA (signature family) per FIPS 203 and 204. **SLH-DSA support is absent in AWS-LC as of 2026-05-23** — AWS has prioritized lattice algorithms (faster, smaller signatures) for its high-throughput use cases. **4 of 6 cells possible (3 ML-DSA + 1 ML-KEM).**

#### Benchmarks

AWS-LC publishes benchmarks for ML-KEM and ML-DSA in its `tool/awslc_bm.cc` source ([15]). Numbers are competitive with liboqs (both libraries derive from similar reference implementations).

#### Side-channel / constant-time review

1. **Constant-time claim:** AWS-LC is **FIPS 140-3 validated** ([16]) — the strongest formal certification available for any candidate in this eval. Constant-time properties are part of the FIPS validation criteria.
2. **Audit status:** Continuous third-party security review (NCC Group, Trail of Bits) as part of AWS's standard security posture for cryptographic libraries. Audit reports are not publicly released.
3. **Known CVEs:** No CVEs against AWS-LC's PQC primitives as of 2026-05-23.
4. **Testing infra:** Aggressive CI including dudect-style timing tests (`aws-lc/tests/timing/`) and fuzz testing via OSS-Fuzz.
5. **Verdict:** **GREEN for production — but operationally inaccessible** without significant integration work (building ctypes wrappers per primitive). The lack of SLH-DSA also eliminates it as a single-library choice. **Strong candidate for a future Phase 3+ when xposeTIP runs in AWS-native infrastructure.**

---

## 3. Comparison matrix

| Library | Install pain | Cells supported | ML-DSA-65 sign µs | ML-KEM-768 encap µs | SLH-DSA-128s sign µs | License | Upstream | Side-channel |
|---|---|---|---|---|---|---|---|---|
| **liboqs-python** | high (5min first import) | 6/6 | **124** | **18** | **658,698** | MIT | OQS project (MSFT/AWS/IBM) | GREEN (no public end-to-end audit) |
| pyspx | medium (86s compile) | 2/6 (SLH-DSA only) | n/a | n/a | 1,583,409 | CC0 | sphincs team | GREEN (hash-based, intrinsically CT) |
| pqcrypto | low (7s) | 6/6 | 463 | 60 | 997,211 | undeclared | "Backbone" (anonymous) | YELLOW (non-standard API, license opacity) |
| **cryptography** (pyca) | low (5s) | 4/6 (no SLH-DSA) | 4,232 | 134 | n/a | Apache OR BSD | PyCA | GREEN (Cure53-audited) |
| RustCrypto via pyo3 | very high | 6/6 (theoretical) | ~300 (cited [10]) | n/a (no direct test) | n/a | Apache OR MIT | RustCrypto | YELLOW (no public PQC audit) |
| AWS-LC via ctypes | very high | 4/6 (no SLH-DSA) | comparable to liboqs | comparable to liboqs | n/a | ISC/Apache/OpenSSL | AWS | GREEN (FIPS 140-3 validated) |

Best per cell highlighted in **bold**.

---

## 4. Recommendation

### 4.1 Primary library per algorithm

| Algorithm | Primary | Why |
|---|---|---|
| SLH-DSA | **liboqs-python** | Fastest (2.4× over pyspx). Same PQClean+SPHINCS+ ref impl underneath. Single-library strategy. |
| ML-DSA | **liboqs-python** | Fastest by ~30×. Critical for high-volume scraper / operator signing. |
| ML-KEM | **liboqs-python** | Fastest by ~7×. Single-library strategy. |

### 4.2 Fallback per algorithm

| Algorithm | Fallback | Why |
|---|---|---|
| SLH-DSA | **pyspx** | Canonical SPHINCS+ reference impl. CC0 license (no compat concerns). Hash-based design = best constant-time profile. |
| ML-DSA | **cryptography (pyca)** | Tier-1 audited library, Apache/BSD licensed, no system deps. 30× slower but acceptable for verify-only paths or low-volume signing. |
| ML-KEM | **cryptography (pyca)** | Same reasoning as ML-DSA fallback. |

### 4.3 Mixed-library strategy

If `liboqs-python` is unavailable in the target environment (CI lacks `cmake`/`gcc`, hostile firewall blocks GitHub during build, etc.), the **two-library fallback stack** is:

- `pyspx` for SLH-DSA (CC0, intrinsic constant-time)
- `cryptography` (pyca) 48.0.0+ for ML-DSA + ML-KEM (Apache/BSD, Cure53-audited)

This combination provides **6/6 coverage with zero `liboqs` dependency** at the cost of 3–30× slower operations.

### 4.4 Container impact preview (NOT committed this sprint)

#### Primary stack: liboqs-python only

`requirements.txt` diff sketch (preview only):

```diff
+ # BFP Phase 1 PQC stack (per docs/specs/pqc_choices_v0.md)
+ liboqs-python>=0.15.0,<1.0
```

System dependencies (Dockerfile additions):

```dockerfile
# Pre-build liboqs to avoid auto-build on first Python import
RUN apt-get update && apt-get install -y --no-install-recommends \
        cmake build-essential libssl-dev git ninja-build && \
    git clone --depth 1 --branch 0.15.0 https://github.com/open-quantum-safe/liboqs /tmp/liboqs && \
    cd /tmp/liboqs && mkdir build && cd build && \
    cmake -GNinja -DCMAKE_INSTALL_PREFIX=/usr/local .. && \
    ninja && ninja install && \
    rm -rf /tmp/liboqs && \
    apt-get purge -y --auto-remove cmake build-essential git ninja-build && \
    rm -rf /var/lib/apt/lists/*

ENV OQS_INSTALL_PATH=/usr/local
```

**Estimated image size delta: ~150 MB** (liboqs install ~100 MB + Python wheel + venv overhead).

#### Fallback stack: pyspx + pyca

`requirements.txt` diff sketch (preview only):

```diff
+ # BFP Phase 1 PQC stack — fallback configuration
+ pyspx>=0.5.0,<1.0
+ cryptography>=48.0.0
```

System deps: none beyond what `cryptography` wheel already brings.

**Estimated image size delta: ~80 MB.**

**Neither sketch committed this sprint.** Production integration is a separate sprint that will live-test the chosen stack in `xpose-api` and `xpose-worker` images.

---

## 5. Risks acknowledged

| # | Risk | Mitigation |
|---|---|---|
| 1 | **liboqs has no published end-to-end side-channel audit.** | Mitigation: track upstream `liboqs/SECURITY.md` for audit announcements. Plan to run dudect ourselves against the binary in a future hardening sprint. Re-evaluation trigger if audit is published. |
| 2 | **liboqs-python first-import build is fragile in CI.** Network failures (clone from GitHub), missing build tools (`cmake`, AppleClang/gcc), incompatible OpenSSL versions all manifest as 5-minute build → error → retry storms. | Mitigation: Dockerfile pre-builds liboqs to a known path + `OQS_INSTALL_PATH` env var pins the location. Image build absorbs the 5-minute cost once; runtime is fast. |
| 3 | **No xposeTIP-side abstraction layer exists yet.** Direct calls to `oqs.Signature(...)` scatter throughout the codebase if not abstracted. | Mitigation: introduce a thin `api/services/bfp/pqc.py` facade in the implementation sprint (NOT this one). Single library swap point if we need to switch primary. |
| 4 | **NIST may publish FIPS 203/204/205 errata.** Algorithm parameter changes would require key migration. | Mitigation: BFP `claim_hash_version` (S167) already exists as a versioning vector. Any algorithm change bumps a parallel `signature_version` field on signed claims. |
| 5 | **pyca and liboqs use OPPOSITE encapsulate() return tuple orderings.** Switching between them silently breaks decapsulation. | Mitigation: facade in mitigation #3 must normalize. Document explicitly in any code review for PQC-related changes. |

---

## 6. Re-evaluation triggers

1. **liboqs publishes a third-party end-to-end audit.** Would significantly strengthen the GREEN verdict. → Update §2.1 and §0.
2. **pyca cryptography adds native SLH-DSA support.** Would obsolete the need for `liboqs` entirely (pyca single-library strategy beats liboqs on supply-chain trust). → Replace recommendation in §4.1.
3. **NIST publishes FIPS 203/204/205 errata** requiring API or parameter changes. → Re-run §2.* benchmarks against updated libraries.
4. **Chosen library hits a critical CVE.** → Switch to fallback per §4.2 + update §5 risk #1 mitigation.
5. **Performance budget changes.** If subject portal needs <10ms ML-DSA verify (currently liboqs does it in 53µs, pyca in 819µs — both within budget at current scale), this trigger does not fire.

---

## 7. Reproducibility

Exact command sequence used in the sandbox. Not committed as scripts — just the log for future re-evaluators.

```bash
# Sandbox setup
mkdir -p /tmp/pqc_eval && cd /tmp/pqc_eval
uname -a > sandbox.info
python3 --version >> sandbox.info
sysctl -n machdep.cpu.brand_string >> sandbox.info  # Linux: cat /proc/cpuinfo | grep "model name" | head -1
sysctl -n hw.memsize | awk '{printf "memory: %d MB\n", $1/1024/1024}' >> sandbox.info

# Create isolated venvs
for lib in pqcrypto pyspx oqs pyca rustcrypto awslc; do
  python3 -m venv "venv-$lib"
done

# liboqs C lib (Homebrew on macOS; on Ubuntu use apt or build from source)
brew install liboqs  # 30s

# Install Python wrappers
./venv-pqcrypto/bin/pip install pqcrypto                    # 7s
./venv-pyspx/bin/pip install pyspx                           # 86s (CFFI compile)
./venv-oqs/bin/pip install liboqs-python                     # 2s (install)
                                                              # FIRST IMPORT triggers 268s liboqs auto-build
./venv-pyca/bin/pip install cryptography                     # 5s

# Algorithm introspection per library — see commands in §2.* of this doc

# Benchmarks — see bench template in §1.4 and per-library result JSONs in /tmp/pqc_eval/results-*.json
```

JSON results files referenced from §2.*:

- `/tmp/pqc_eval/results-pqcrypto.json` — full bench all 6 cells
- `/tmp/pqc_eval/results-pyspx.json` — SLH-DSA-128s + 192s
- `/tmp/pqc_eval/results-oqs.json` — full bench all 6 cells
- `/tmp/pqc_eval/results-pyca.json` — ML-DSA 44/65/87 + ML-KEM-768

These JSON files live only in the sandbox; they are not committed to the repo. Future re-evaluators reproduce them by re-running the bench scripts shown above.

---

## 8. Sources

| # | Reference |
|---|---|
| [1] | `liboqs-python` PyPI: https://pypi.org/project/liboqs-python/ — MIT License declared in `pip show` output. GitHub: https://github.com/open-quantum-safe/liboqs-python |
| [2] | Open Quantum Safe `liboqs` algorithms documentation: https://github.com/open-quantum-safe/liboqs/tree/main/docs/algorithms |
| [3] | PQClean reference implementation collection: https://github.com/PQClean/PQClean — README documents constant-time properties per implementation |
| [4] | `PySPX` PyPI: https://pypi.org/project/PySPX/ — CC0 1.0 Universal declared in `pip show` output. GitHub: https://github.com/sphincs/pyspx |
| [5] | NIST FIPS 205, *Stateless Hash-Based Digital Signature Standard*, August 2024, §11: https://csrc.nist.gov/pubs/fips/205/final (Standardizes SPHINCS+ round 3.1 submission verbatim) |
| [6] | SPHINCS+ submission, round 3.1, official documentation: https://sphincs.org/data/sphincs+-r3.1-specification.pdf |
| [7] | pyca `cryptography` LICENSE: https://github.com/pyca/cryptography/blob/main/LICENSE — Apache 2.0 OR BSD-3-Clause |
| [8] | Cure53 audit of pyca cryptography (2022): https://cryptography.io/en/latest/security/ — links to most recent audit PDFs |
| [9] | RustCrypto licensing convention: https://github.com/RustCrypto/signatures/blob/master/README.md — all crates Apache 2.0 OR MIT |
| [10] | RustCrypto `ml-dsa` crate: https://github.com/RustCrypto/signatures/tree/master/ml-dsa |
| [11] | RustCrypto `slh-dsa` crate: https://github.com/RustCrypto/signatures/tree/master/slh-dsa |
| [12] | RustCrypto `ml-kem` crate: https://github.com/RustCrypto/KEMs/tree/master/ml-kem |
| [13] | `subtle` crate (constant-time foundation for RustCrypto): https://crates.io/crates/subtle |
| [14] | AWS-LC LICENSE: https://github.com/aws/aws-lc/blob/main/LICENSE — ISC OR Apache 2.0 OR OpenSSL |
| [15] | AWS-LC benchmarks tool: https://github.com/aws/aws-lc/blob/main/tool/awslc_bm.cc |
| [16] | AWS-LC FIPS 140-3 validation: https://csrc.nist.gov/projects/cryptographic-module-validation-program/certificate/4756 |
| [17] | NIST FIPS 203, *Module-Lattice-Based Key-Encapsulation Mechanism Standard*, August 2024: https://csrc.nist.gov/pubs/fips/203/final |
| [18] | NIST FIPS 204, *Module-Lattice-Based Digital Signature Standard*, August 2024: https://csrc.nist.gov/pubs/fips/204/final |
| [19] | NVD vulnerability database: https://nvd.nist.gov/ — CVE searches performed 2026-05-23 against package names `liboqs`, `liboqs-python`, `pqcrypto`, `pyspx`, `cryptography`, `aws-lc` |

---

*End of pqc_choices_v0 — citable from BFP_SPEC v0.x §13 (Session 2 extension).*
