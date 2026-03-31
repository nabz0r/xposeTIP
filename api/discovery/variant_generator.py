"""Username and name variant generators for Discovery Engine queries."""

_LEET_MAP = {"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t"}


def generate_username_variants(username: str) -> list[str]:
    """Generate plausible variants of a username. Max 5, excluding original."""
    if not username or len(username) < 3:
        return []

    original = username.lower()
    variants = set()

    # 1. Leet-speak reversal: nabz0r → nabzor
    deleet = original
    for leet, char in _LEET_MAP.items():
        deleet = deleet.replace(leet, char)
    if deleet != original:
        variants.add(deleet)

    # 2. Separator insertion at plausible split points
    for i in range(2, len(original) - 1):
        # Only insert if both sides are >= 2 chars
        left, right = original[:i], original[i:]
        if len(left) >= 2 and len(right) >= 2:
            for sep in ("_", ".", "-"):
                v = f"{left}{sep}{right}"
                if v != original:
                    variants.add(v)
            break  # Only first plausible split to avoid explosion

    # 3. Remove separators: nab_z0r → nabz0r (if has separators)
    stripped = original.replace("_", "").replace(".", "").replace("-", "")
    if stripped != original and len(stripped) >= 3:
        variants.add(stripped)

    # 4. Truncation (only if > 5 chars)
    if len(original) > 5:
        variants.add(original[:len(original) - 2])

    # 5. Common suffix
    variants.add(f"{original}_")

    # Remove original, filter short variants, cap at 5
    variants.discard(original)
    return sorted(v for v in variants if len(v) >= 4)[:5]


def generate_name_variants(first: str, last: str) -> list[str]:
    """Generate username-style variants from a resolved name. Max 5."""
    if not first or not last:
        return []

    f = first.lower().strip()
    l = last.lower().strip()

    if len(f) < 2 or len(l) < 2:
        return []

    variants = [
        f"{f}.{l}",
        f"{f}_{l}",
        f"{f}{l}",
        f"{f[0]}.{l}",
        f"{f}{l[0]}",
        f"{f[0]}{l}",
    ]

    return variants[:5]
