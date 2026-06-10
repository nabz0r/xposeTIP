"""S261 — Collision quarantine + coherence cap helpers.

Tactical, consumer-side guard against fabricated identities seeded from a
common-name / low-entropy email local-part. The classic failure (S261 spec):
`eric@plutontechnologies.com` enumerates 38 unrelated `@eric` handles into a
single high-confidence "Eric Setiawan" persona with garbage name pills.

Pure helpers — no DB, no pipeline, no scraper/axis/BFP touch. Reusable in the
systemic follow-ups (S-B corroboration, S-C domain resolver).
"""

import re

# Lowercase given names, multi-locale (EN/FR/DE/ES/IT). A bare local-part that
# IS one of these is a collision farm — username enumeration on it merges
# strangers. Curated prefilter, NOT entropy-perfect: it only decides *when to
# demand corroboration*, so a miss just falls back to current behavior (no
# over-suppression). Dictionary-word detection deferred to S-B.
COMMON_GIVEN_NAMES = frozenset({
    # EN — male
    "james", "john", "robert", "michael", "william", "david", "richard",
    "joseph", "thomas", "charles", "chris", "christopher", "daniel", "dan",
    "matthew", "matt", "anthony", "tony", "mark", "marc", "donald", "steven",
    "steve", "paul", "andrew", "andy", "josh", "joshua", "kevin", "brian",
    "george", "edward", "ed", "ronald", "tim", "timothy", "jason", "jeff",
    "jeffrey", "ryan", "jacob", "gary", "nick", "nicholas", "eric", "erik",
    "stephen", "jonathan", "jon", "larry", "justin", "scott", "brandon",
    "ben", "benjamin", "frank", "greg", "gregory", "sam", "samuel", "ray",
    "raymond", "patrick", "pat", "jack", "dennis", "jerry", "tyler", "aaron",
    "henry", "adam", "doug", "nathan", "nate", "zachary", "zach", "kyle",
    "noah", "liam", "lucas", "luke", "mason", "ethan", "logan", "aiden",
    "max", "mike", "tom", "joe", "bob", "bill", "dave", "rob", "phil",
    # EN — female
    "mary", "patricia", "jennifer", "jen", "linda", "elizabeth", "liz",
    "barbara", "susan", "sue", "jessica", "jess", "sarah", "karen", "nancy",
    "lisa", "betty", "margaret", "sandra", "ashley", "kimberly", "kim",
    "emily", "donna", "michelle", "carol", "amanda", "amy", "melissa",
    "deborah", "stephanie", "rebecca", "becky", "laura", "sharon", "cynthia",
    "kathleen", "amber", "anna", "anne", "ann", "samantha", "katherine",
    "kate", "katie", "christine", "debra", "rachel", "catherine", "emma",
    "olivia", "sophia", "sophie", "isabella", "mia", "charlotte", "amelia",
    "grace", "chloe", "ella", "lily", "hannah", "abby", "abigail", "megan",
    # FR
    "jean", "pierre", "luc", "louis", "henri", "andre", "rene", "claude",
    "michel", "alain", "bernard", "philippe", "patrice", "olivier",
    "nicolas", "julien", "guillaume", "antoine", "francois", "vincent",
    "thierry", "didier", "gilles", "yves", "herve", "fabien", "romain",
    "maxime", "hugo", "theo", "leo", "nathan", "raphael", "arthur", "jules",
    "marie", "sophie", "celine", "nathalie", "isabelle", "sandrine",
    "valerie", "veronique", "sylvie", "catherine", "florence", "aurelie",
    "elodie", "manon", "camille", "chloe", "ines", "jade", "lea", "louise",
    # DE
    "hans", "peter", "klaus", "wolfgang", "jurgen", "gunter", "dieter",
    "manfred", "helmut", "horst", "werner", "gerhard", "stefan", "thomas",
    "andreas", "frank", "uwe", "matthias", "markus", "lukas", "felix",
    "jonas", "leon", "finn", "elias", "paul", "ben", "luis", "anna", "lena",
    "lara", "sarah", "laura", "julia", "lisa", "lea", "nina", "marie",
    "sophie", "hannah", "emma", "mia", "lilly", "leonie", "katharina",
    # ES / IT
    "jose", "juan", "carlos", "antonio", "manuel", "francisco", "javier",
    "miguel", "angel", "rafael", "pablo", "diego", "alejandro", "sergio",
    "alberto", "fernando", "luis", "marco", "matteo", "lorenzo", "giuseppe",
    "giovanni", "francesco", "alessandro", "andrea", "stefano", "luca",
    "maria", "carmen", "ana", "isabel", "laura", "cristina", "marta",
    "lucia", "elena", "sofia", "giulia", "chiara", "francesca", "valentina",
    "alessia", "martina", "sara", "alice", "aurora", "beatrice",
    # generic / ambiguous short handles often used as given names
    "alex", "sasha", "robin", "jordan", "taylor", "morgan", "casey",
    "jamie", "drew", "lee", "ray", "kim", "jay", "cody", "dana",
})


def is_collision_prone_localpart(local: str) -> bool:
    """True if a bare local-part is too low-entropy to seed identity enumeration."""
    if not local:
        return False
    l = local.strip().lower()
    if len(l) < 4:               # very short handles collide on everything
        return True
    if l in COMMON_GIVEN_NAMES:  # common first name = collision farm
        return True
    return False


# Reject name strings carrying digits, possessives, or age slang — these are
# scrape artifacts, never real human names: "13y/o", "eric's", "user42".
_JUNK_NAME_RE = re.compile(r"\d|['’]s\b|\d+\s*y\s*/?\s*o", re.IGNORECASE)


def is_junk_name_token(name: str) -> bool:
    """Reject name strings carrying digits, possessives, or age slang (13y/o, eric's)."""
    if not name:
        return True
    return bool(_JUNK_NAME_RE.search(name))
