#!/usr/bin/env python3
"""S284a — Build api/services/layer4/name_priors.json from name datasets.

Merges three sources into one artifact giving, per first name: real frequency
(where SSA/INSEE know it), gender + cross-source confidence, coverage, and source.
This script is the reproducible generator; it commits the DERIVED artifact, never
the raw sources (cache is gitignored).

SOURCES & LICENCES
  SSA (US baby names) — US public domain.
    canonical : https://www.ssa.gov/oact/babynames/names.zip  (name,sex,count per yob)
    NOTE: ssa.gov IP-blocks many datacenter egress IPs; this build falls back to a
          public-domain mirror of the same data (top-1000/yr, 1880-2008, `percent`).
    mirror    : https://raw.githubusercontent.com/hadley/data-baby-names/master/baby-names.csv
  INSEE (FR "Fichier des prénoms") — Licence Ouverte v2.0 (Etalab); attribution INSEE.
    canonical : https://www.insee.fr/fr/statistiques/fichier/2540004/nat2022_csv.zip
    NOTE: insee.fr is likewise blocked in this build env. INSEE is OPTIONAL here and
          DROP-IN: place the national CSV (SEXE;PREUSUEL;ANNAIS;NOMBRE, ';'-sep) at
          scripts/_name_data_cache/insee_nat.csv and re-run — freq_coverage gains "fr".
  WGND 2.0 (World Gender Name Dictionary) — CC0.
    Raffo, Julio, 2021, "WGND 2.0", https://doi.org/10.7910/DVN/MSEGSJ, Harvard Dataverse.
    file: wgnd_2_0_name-gender-code  (name,code,gender,wgt) — per-country, the
          non-Western coverage + the cross-country gender-conflict signal.
    dataverse datafile id 4750348.

DESIGN DECISIONS (locked, S284a)
  (1) Filter to ~50-100k entries: keep a name if it appears in >= WGND_MIN_COUNTRIES
      countries OR is present in SSA/INSEE. WGND >=3 countries lands ~66k.
  (2) Double key: accented key_raw AND an ascii fallback (NFKD strip). ascii_index
      maps key_ascii -> the highest-p_freq raw key (tie-break documented).
  (3) Gender ambiguity is honest: gender_conf = |2*frac_M_countries - 1| where
      frac_M is the fraction of WGND countries whose dominant gender is M. A name
      male in some countries and female in others (Andrea: M in IT/ES, F in US/most)
      lands below the S282 0.70 floor -> the entropy gender axis falls to unknown
      (governor 3: we don't guess).

FREQUENCY (this build): SSA-only (US). INSEE pending (drop-in). p_freq is the
  dominant-sex mean historical birth share, halved to approximate all-births
  prevalence. _meta.freq_coverage records which national frequencies contributed.

Run: python3 scripts/build_name_priors.py
"""
import csv
import json
import logging
import os
import sys
import unicodedata
import urllib.request
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("name_priors")

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "_name_data_cache")
OUT = os.path.join(HERE, "..", "api", "services", "layer4", "name_priors.json")

WGND_URL = "https://dataverse.harvard.edu/api/access/datafile/4750348?format=original"
SSA_MIRROR = "https://raw.githubusercontent.com/hadley/data-baby-names/master/baby-names.csv"
WGND_PATH = os.path.join(CACHE, "wgnd_code.csv")
SSA_PATH = os.path.join(CACHE, "ssa_hadley.csv")
INSEE_PATH = os.path.join(CACHE, "insee_nat.csv")   # optional drop-in

WGND_MIN_COUNTRIES = 3   # decision (1) — calibrated to land in [50k, 100k]
P_FREQ_CLIP = (1e-6, 0.2)


def _download(url, path, what):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        log.info("  [cache] %s (%s)", what, _mb(path))
        return
    log.info("  [fetch] %s -> %s", what, path)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 name-priors-build"})
        with urllib.request.urlopen(req, timeout=600) as r, open(path, "wb") as out:
            out.write(r.read())
    except Exception as e:
        log.error("FATAL: could not fetch %s (%s): %s", what, url, e)
        log.error("Drop the file manually into %s and re-run.", CACHE)
        sys.exit(1)


def _mb(path):
    return f"{os.path.getsize(path)/1e6:.1f} MB"


def acquire():
    """Ensure required sources are cached. WGND + SSA are mandatory (fail loud).
    INSEE is optional drop-in (Option-1 condition)."""
    os.makedirs(CACHE, exist_ok=True)
    log.info("Acquiring sources (cache=%s):", CACHE)
    _download(WGND_URL, WGND_PATH, "WGND 2.0 name-gender-code")
    _download(SSA_MIRROR, SSA_PATH, "SSA baby names (mirror)")
    if os.path.exists(INSEE_PATH) and os.path.getsize(INSEE_PATH) > 0:
        log.info("  [drop-in] INSEE present (%s)", _mb(INSEE_PATH))
        return True
    log.info("  [skip] INSEE absent — freq is SSA-only (drop %s to add FR)", INSEE_PATH)
    return False


# --- normalization (decision 2) ---
def normalize(name):
    raw = " ".join((name or "").strip().lower().split())
    ascii_ = unicodedata.normalize("NFKD", raw)
    ascii_ = "".join(c for c in ascii_ if not unicodedata.combining(c))
    return raw, ascii_


def _is_namelike(raw):
    if len(raw) < 2:
        return False
    if any(ch.isdigit() for ch in raw):
        return False
    if '"' in raw or raw.startswith("baby"):
        return False
    return True


# --- SSA (US frequency + gender lean) ---
def parse_ssa(path):
    """name_raw -> {p_freq, p_m}. hadley format: year,name,percent,sex(boy/girl)."""
    boy = defaultdict(float); girl = defaultdict(float)
    nb = defaultdict(int); ng = defaultdict(int)
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            raw, _ = normalize(row["name"])
            if not _is_namelike(raw):
                continue
            try:
                pct = float(row["percent"])
            except (TypeError, ValueError):
                continue
            if row["sex"] == "boy":
                boy[raw] += pct; nb[raw] += 1
            else:
                girl[raw] += pct; ng[raw] += 1
    out = {}
    for raw in set(boy) | set(girl):
        sb, sg = boy.get(raw, 0.0), girl.get(raw, 0.0)
        tot = sb + sg
        p_m = sb / tot if tot else 0.5
        # dominant-sex mean share, halved to approximate all-births prevalence
        if sb >= sg and nb.get(raw):
            mean = sb / nb[raw]
        elif ng.get(raw):
            mean = sg / ng[raw]
        else:
            mean = 0.0
        p_freq = max(P_FREQ_CLIP[0], min(P_FREQ_CLIP[1], mean * 0.5))
        out[raw] = {"p_freq": round(p_freq, 6), "p_m": round(p_m, 4)}
    return out


# --- INSEE (optional drop-in) ---
def parse_insee(path):
    """name_raw -> {nombre, p_m}. format SEXE;PREUSUEL;ANNAIS;NOMBRE (';'-sep)."""
    male = defaultdict(int); fem = defaultdict(int)
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        r = csv.reader(f, delimiter=";")
        header = next(r, None)
        for row in r:
            if len(row) < 4:
                continue
            sexe, preusuel, annais, nombre = row[0], row[1], row[2], row[3]
            if annais == "XXXX" or preusuel in ("_PRENOMS_RARES", "PRENOMS_RARES"):
                continue
            raw, _ = normalize(preusuel)
            if not _is_namelike(raw):
                continue
            try:
                n = int(nombre)
            except ValueError:
                continue
            (male if sexe.strip() == "1" else fem)[raw] += n
    total = sum(male.values()) + sum(fem.values()) or 1
    out = {}
    for raw in set(male) | set(fem):
        m, fv = male.get(raw, 0), fem.get(raw, 0)
        out[raw] = {"p_freq": round((m + fv) / total, 6),
                    "p_m": round(m / (m + fv), 4) if (m + fv) else 0.5}
    return out


# --- WGND (coverage + per-country gender consensus) — streamed by name block ---
def stream_wgnd(path, keep_extra):
    """Yields (key_raw, key_ascii, n_countries, gender, gender_conf) for names with
    >= WGND_MIN_COUNTRIES countries OR present in keep_extra. File is name-sorted,
    so each name's rows are contiguous → O(1) memory per name."""
    def finalize(name, per_country):
        raw, ascii_ = normalize(name)
        if not _is_namelike(raw):
            return None
        nc = len(per_country)
        if nc < WGND_MIN_COUNTRIES and raw not in keep_extra:
            return None
        m_votes = 0.0
        strong_m = strong_f = 0   # countries where the name is CLEARLY one gender
        for cc, (wm, wf) in per_country.items():
            tot = wm + wf
            pm = wm / tot if tot else 0.5
            m_votes += 1.0 if pm > 0.5 else (0.5 if pm == 0.5 else 0.0)
            if pm >= 0.7:
                strong_m += 1
            elif pm <= 0.3:
                strong_f += 1
        frac_m = m_votes / nc if nc else 0.5
        gender = "male" if frac_m > 0.5 else "female"
        # decision (3): a FLIP name — strongly male in >=2 countries AND strongly
        # female in >=2 — is locale-dependent → ambiguous, capped below the 0.70
        # floor regardless of which is the global majority (Andrea: M in IT/ES,
        # F in US/most). Governor-3: we refuse to guess the person's gender.
        if strong_m >= 2 and strong_f >= 2:
            mino, maj = min(strong_m, strong_f), max(strong_m, strong_f)
            conf = round(min(0.65, 1 - mino / (mino + maj)), 4)
        else:
            conf = round(abs(2 * frac_m - 1), 4)
        return raw, ascii_, nc, gender, conf

    cur_name = None
    per_country = defaultdict(lambda: [0.0, 0.0])  # cc -> [wgt_M, wgt_F]
    with open(path, newline="") as f:
        rdr = csv.reader(f)
        next(rdr, None)  # header
        for row in rdr:
            if len(row) < 4:
                continue
            name, code, gender, wgt = row[0], row[1], row[2], row[3]
            if name != cur_name:
                if cur_name is not None:
                    res = finalize(cur_name, per_country)
                    if res:
                        yield res
                cur_name = name
                per_country = defaultdict(lambda: [0.0, 0.0])
            try:
                w = float(wgt)
            except ValueError:
                w = 0.0
            if gender == "M":
                per_country[code][0] += w
            elif gender == "F":
                per_country[code][1] += w
        if cur_name is not None:
            res = finalize(cur_name, per_country)
            if res:
                yield res


def build():
    have_insee = acquire()

    log.info("Parsing SSA ...")
    ssa = parse_ssa(SSA_PATH)
    log.info("  SSA names: %d", len(ssa))

    insee = {}
    if have_insee:
        log.info("Parsing INSEE ...")
        insee = parse_insee(INSEE_PATH)
        log.info("  INSEE names: %d", len(insee))

    freq_keys = set(ssa) | set(insee)   # names that carry a national frequency

    log.info("Streaming WGND (keep >= %d countries OR in SSA/INSEE) ...", WGND_MIN_COUNTRIES)
    names = {}
    wgnd_kept = 0
    for raw, ascii_, nc, gender, conf in stream_wgnd(WGND_PATH, freq_keys):
        wgnd_kept += 1
        names[raw] = {
            "p_freq": None,
            "gender": gender, "gender_conf": conf,
            "coverage": ["wgnd"], "ascii": ascii_,
        }
    log.info("  WGND kept: %d", wgnd_kept)

    # fold in national frequencies + gender for SSA/INSEE names (add WGND-absent ones)
    def fold(src, label):
        for raw, d in src.items():
            _, ascii_ = normalize(raw)
            e = names.get(raw)
            if e is None:
                # SSA/INSEE-only name (not in WGND) — gender from the freq source lean
                e = {"p_freq": None, "gender": "male" if d["p_m"] > 0.5 else "female",
                     "gender_conf": round(abs(2 * d["p_m"] - 1), 4),
                     "coverage": [], "ascii": ascii_}
                names[raw] = e
            if label not in e["coverage"]:
                e["coverage"].append(label)
            # combine frequency: weighted by source size is overkill for SSA-only;
            # take max known prevalence across national sources (documented).
            pf = d["p_freq"]
            e["p_freq"] = pf if e["p_freq"] is None else max(e["p_freq"], pf)

    fold(ssa, "ssa")
    if insee:
        fold(insee, "insee")

    # coverage ordering: stable, sources present
    for e in names.values():
        e["coverage"] = [s for s in ("ssa", "insee", "wgnd") if s in e["coverage"]]

    # ascii_index (decision 2) — tie-break: highest p_freq, then most coverage, then raw
    ascii_index = {}
    best = {}
    for raw, e in names.items():
        a = e["ascii"]
        key = (e["p_freq"] or 0.0, len(e["coverage"]))
        if a not in best or key > best[a]:
            best[a] = key
            ascii_index[a] = raw

    freq_cov = ["us"] if ssa else []
    if insee:
        freq_cov.append("fr")

    with_freq = sum(1 for e in names.values() if e["p_freq"] is not None)
    with_gender = sum(1 for e in names.values() if e.get("gender"))
    ambiguous = sum(1 for e in names.values() if e.get("gender_conf", 1) < 0.70)

    meta = {
        "generated_by": "scripts/build_name_priors.py",
        "generated_at": os.environ.get("BUILD_TS", "unset"),
        "sources": {
            "ssa": {"license": "US public domain",
                    "url": "https://www.ssa.gov/oact/babynames/names.zip",
                    "acquired_via": "hadley/data-baby-names mirror (ssa.gov blocked in build env)"},
            "insee": {"license": "Licence Ouverte v2.0 (Etalab)",
                      "attribution": "INSEE — Fichier des prénoms",
                      "url": "https://www.insee.fr/fr/statistiques/fichier/2540004/nat2022_csv.zip",
                      "present": bool(insee)},
            "wgnd": {"license": "CC0", "doi": "10.7910/DVN/MSEGSJ",
                     "citation": "Raffo, Julio, 2021, WGND 2.0, Harvard Dataverse, V1"},
        },
        "entry_count": len(names),
        "freq_combine": "SSA-only (US), INSEE pending" if not insee else "max(SSA, INSEE) national prevalence",
        "freq_coverage": freq_cov,
        "wgnd_min_countries": WGND_MIN_COUNTRIES,
        "gender_conf_floor_note": "names below 0.70 are intentionally ambiguous (governor-3); "
                                  "conf = |2*frac_M_countries - 1| over WGND country dominant-gender votes",
    }

    artifact = {"_meta": meta, "names": names, "ascii_index": ascii_index}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(artifact, f, ensure_ascii=False, separators=(",", ":"))

    log.info("")
    log.info("=== name_priors.json written ===")
    log.info("  path        : %s (%s)", OUT, _mb(OUT))
    log.info("  entry_count : %d  (target [50000,100000])", len(names))
    if not (50000 <= len(names) <= 100000):
        log.warning("  !! entry_count OUTSIDE target window — adjust WGND_MIN_COUNTRIES")
    log.info("  with p_freq : %d (%.1f%%)", with_freq, 100 * with_freq / len(names))
    log.info("  with gender : %d (%.1f%%)", with_gender, 100 * with_gender / len(names))
    log.info("  ambiguous (<0.70 conf): %d (%.1f%%)", ambiguous, 100 * ambiguous / len(names))
    log.info("  freq_coverage: %s", freq_cov)
    log.info("  ascii_index : %d keys", len(ascii_index))


if __name__ == "__main__":
    build()
