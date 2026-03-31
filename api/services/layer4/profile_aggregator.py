"""Profile Aggregator — merge findings into a unified person profile."""
import logging
import re
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.finding import Finding
from api.models.identity import Identity
from api.models.target import Target
from api.services.layer4.source_scoring import get_source_reliability as _get_src_rel_mod
from api.services.layer4.username_validator import is_valid_username

logger = logging.getLogger(__name__)

# Avatar URL blacklist — platform logos, default images, not real profile photos
AVATAR_BLACKLIST_PATTERNS = [
    "telesco.pe",
    "cdn1.telesco.pe",
    "cdn2.telesco.pe",
    "cdn3.telesco.pe",
    "cdn4.telesco.pe",
    "telegram.org",
    "t.me/i/",
    "static.xx.fbcdn",
    "default_profile",
    "gravatar.com/avatar/00000000",
    "/default.",
    "placeholder",
    "no-avatar",
    "no_avatar",
    "anonymous",
]

# Bio blacklist — platform slogans extracted as user bios
BIO_BLACKLIST = [
    "fast. secure. powerful.",
    "a new era of messaging",
    "join the conversation",
    "share and stay in touch",
    "connect with friends",
    "see what's happening",
    "instant messaging",
    "cloud-based mobile",
    "linktree",
    "discover and stream music",
    "your next favorite track",
    # Telegram platform descriptions
    "telegram is a cloud-based",
    "telegram messenger",
    "pure instant messaging",
    "simple, fast, secure",
    "synced across all your devices",
    "sending messages",
    "telegram lets you",
    "powerful, fast, and secure",
]


def _is_valid_avatar(url):
    """Check if avatar URL is a real profile photo, not a platform logo."""
    if not url:
        return False
    url_lower = url.lower()
    return not any(pattern in url_lower for pattern in AVATAR_BLACKLIST_PATTERNS)


def _score_avatar(url: str) -> int:
    """Score avatar quality: 0=invalid, 1=generated/default, 2=unknown, 3=real platform photo."""
    if not url:
        return 0
    low = url.lower()
    # Gravatar identicons / generated defaults
    if 'd=identicon' in low or 'd=retro' in low or 'd=wavatar' in low:
        return 1
    # Platform default avatars
    if 'redditstatic.com/avatars/defaults' in low:
        return 1
    if 'simg-ssl.duolingo.com/avatar/default' in low:
        return 1
    # Protocol-relative URLs (//simg-ssl...) — typically low quality
    if url.startswith('//'):
        return 1
    # Real platform avatars — known high-quality sources
    if 'githubusercontent.com' in low:
        return 3
    if 'linktr.ee' in low:
        return 3
    if 'pbs.twimg.com' in low:
        return 3
    if 'googleusercontent.com' in low:
        return 3
    if 'fullcontact.com' in low:
        return 3
    # Everything else
    return 2


def _is_valid_bio(bio):
    """Check if bio is user-written, not a platform slogan."""
    if not bio:
        return False
    bio_lower = bio.strip().lower()
    return not any(bl in bio_lower for bl in BIO_BLACKLIST)


def _load_blacklist(session):
    """Load name blacklist from DB. Returns list of dicts."""
    try:
        from api.models.name_blacklist import NameBlacklist
        entries = session.execute(select(NameBlacklist)).scalars().all()
        return [{"pattern": e.pattern, "type": e.type} for e in entries]
    except Exception:
        logger.debug("Could not load name blacklist from DB, using hardcoded fallback")
        return []


def _is_valid_name_db(name_val, blacklist):
    """Validate name against DB blacklist."""
    if not name_val or len(name_val.strip()) < 3:
        return False
    val = name_val.strip()
    val_lower = val.lower()

    # Reject single-letter initials like "J.", "A Smith", or "J Smith"
    parts = val.split()
    if parts and (len(parts[0]) == 1 or (len(parts[0]) == 2 and parts[0].endswith("."))):
        return False
    # Reject single-letter last name initials like "Steffen H.", "John D."
    if len(parts) >= 2 and len(parts[-1].rstrip(".")) <= 1:
        return False

    for entry in blacklist:
        pattern = entry["pattern"].lower()
        rule_type = entry["type"]

        if rule_type == "exact" and val_lower == pattern:
            return False
        elif rule_type == "contains" and pattern in val_lower:
            return False
        elif rule_type == "regex":
            try:
                if re.match(entry["pattern"], val, re.IGNORECASE):
                    return False
            except re.error:
                pass

    return True


# --- Static geocoding tables (zero API calls) ---
COUNTRY_COORDS = {
    # Europe
    "albania": {"lat": 41.15, "lon": 20.17, "country": "Albania"},
    "andorra": {"lat": 42.51, "lon": 1.52, "country": "Andorra"},
    "armenia": {"lat": 40.07, "lon": 45.04, "country": "Armenia"},
    "austria": {"lat": 47.52, "lon": 14.55, "country": "Austria"},
    "azerbaijan": {"lat": 40.14, "lon": 47.58, "country": "Azerbaijan"},
    "belarus": {"lat": 53.71, "lon": 27.95, "country": "Belarus"},
    "belgium": {"lat": 50.50, "lon": 4.47, "country": "Belgium"},
    "bosnia and herzegovina": {"lat": 43.92, "lon": 17.68, "country": "Bosnia and Herzegovina"},
    "bulgaria": {"lat": 42.73, "lon": 25.49, "country": "Bulgaria"},
    "croatia": {"lat": 45.10, "lon": 15.20, "country": "Croatia"},
    "cyprus": {"lat": 35.13, "lon": 33.43, "country": "Cyprus"},
    "czech republic": {"lat": 49.82, "lon": 15.47, "country": "Czech Republic"},
    "czechia": {"lat": 49.82, "lon": 15.47, "country": "Czech Republic"},
    "denmark": {"lat": 56.26, "lon": 9.50, "country": "Denmark"},
    "estonia": {"lat": 58.60, "lon": 25.01, "country": "Estonia"},
    "finland": {"lat": 61.92, "lon": 25.75, "country": "Finland"},
    "france": {"lat": 46.23, "lon": 2.21, "country": "France"},
    "georgia": {"lat": 42.32, "lon": 43.36, "country": "Georgia"},
    "germany": {"lat": 51.17, "lon": 10.45, "country": "Germany"},
    "greece": {"lat": 39.07, "lon": 21.82, "country": "Greece"},
    "hungary": {"lat": 47.16, "lon": 19.50, "country": "Hungary"},
    "iceland": {"lat": 64.96, "lon": -19.02, "country": "Iceland"},
    "ireland": {"lat": 53.14, "lon": -7.69, "country": "Ireland"},
    "italy": {"lat": 41.87, "lon": 12.57, "country": "Italy"},
    "kosovo": {"lat": 42.60, "lon": 20.90, "country": "Kosovo"},
    "latvia": {"lat": 56.88, "lon": 24.60, "country": "Latvia"},
    "liechtenstein": {"lat": 47.17, "lon": 9.56, "country": "Liechtenstein"},
    "lithuania": {"lat": 55.17, "lon": 23.88, "country": "Lithuania"},
    "luxembourg": {"lat": 49.82, "lon": 6.13, "country": "Luxembourg"},
    "malta": {"lat": 35.94, "lon": 14.38, "country": "Malta"},
    "moldova": {"lat": 47.41, "lon": 28.37, "country": "Moldova"},
    "monaco": {"lat": 43.73, "lon": 7.42, "country": "Monaco"},
    "montenegro": {"lat": 42.71, "lon": 19.37, "country": "Montenegro"},
    "netherlands": {"lat": 52.13, "lon": 5.29, "country": "Netherlands"},
    "north macedonia": {"lat": 41.51, "lon": 21.75, "country": "North Macedonia"},
    "norway": {"lat": 60.47, "lon": 8.47, "country": "Norway"},
    "poland": {"lat": 51.92, "lon": 19.15, "country": "Poland"},
    "portugal": {"lat": 39.40, "lon": -8.22, "country": "Portugal"},
    "romania": {"lat": 45.94, "lon": 24.97, "country": "Romania"},
    "russia": {"lat": 61.52, "lon": 105.32, "country": "Russia"},
    "serbia": {"lat": 44.02, "lon": 21.01, "country": "Serbia"},
    "slovakia": {"lat": 48.67, "lon": 19.70, "country": "Slovakia"},
    "slovenia": {"lat": 46.15, "lon": 14.99, "country": "Slovenia"},
    "spain": {"lat": 40.46, "lon": -3.75, "country": "Spain"},
    "sweden": {"lat": 60.13, "lon": 18.64, "country": "Sweden"},
    "switzerland": {"lat": 46.82, "lon": 8.23, "country": "Switzerland"},
    "turkey": {"lat": 38.96, "lon": 35.24, "country": "Turkey"},
    "ukraine": {"lat": 48.38, "lon": 31.17, "country": "Ukraine"},
    "united kingdom": {"lat": 55.38, "lon": -3.44, "country": "United Kingdom"},
    # Americas
    "argentina": {"lat": -38.42, "lon": -63.62, "country": "Argentina"},
    "bolivia": {"lat": -16.29, "lon": -63.59, "country": "Bolivia"},
    "brazil": {"lat": -14.24, "lon": -51.93, "country": "Brazil"},
    "canada": {"lat": 56.13, "lon": -106.35, "country": "Canada"},
    "chile": {"lat": -35.68, "lon": -71.54, "country": "Chile"},
    "colombia": {"lat": 4.57, "lon": -74.30, "country": "Colombia"},
    "costa rica": {"lat": 9.75, "lon": -83.75, "country": "Costa Rica"},
    "cuba": {"lat": 21.52, "lon": -77.78, "country": "Cuba"},
    "dominican republic": {"lat": 18.74, "lon": -70.16, "country": "Dominican Republic"},
    "ecuador": {"lat": -1.83, "lon": -78.18, "country": "Ecuador"},
    "el salvador": {"lat": 13.79, "lon": -88.90, "country": "El Salvador"},
    "guatemala": {"lat": 15.78, "lon": -90.23, "country": "Guatemala"},
    "haiti": {"lat": 18.97, "lon": -72.29, "country": "Haiti"},
    "honduras": {"lat": 15.20, "lon": -86.24, "country": "Honduras"},
    "jamaica": {"lat": 18.11, "lon": -77.30, "country": "Jamaica"},
    "mexico": {"lat": 23.63, "lon": -102.55, "country": "Mexico"},
    "nicaragua": {"lat": 12.87, "lon": -85.21, "country": "Nicaragua"},
    "panama": {"lat": 8.54, "lon": -80.78, "country": "Panama"},
    "paraguay": {"lat": -23.44, "lon": -58.44, "country": "Paraguay"},
    "peru": {"lat": -9.19, "lon": -75.02, "country": "Peru"},
    "puerto rico": {"lat": 18.22, "lon": -66.59, "country": "Puerto Rico"},
    "trinidad and tobago": {"lat": 10.69, "lon": -61.22, "country": "Trinidad and Tobago"},
    "united states": {"lat": 37.09, "lon": -95.71, "country": "United States"},
    "uruguay": {"lat": -32.52, "lon": -55.77, "country": "Uruguay"},
    "venezuela": {"lat": 6.42, "lon": -66.59, "country": "Venezuela"},
    # Asia
    "afghanistan": {"lat": 33.94, "lon": 67.71, "country": "Afghanistan"},
    "bahrain": {"lat": 26.07, "lon": 50.56, "country": "Bahrain"},
    "bangladesh": {"lat": 23.69, "lon": 90.36, "country": "Bangladesh"},
    "brunei": {"lat": 4.54, "lon": 114.73, "country": "Brunei"},
    "cambodia": {"lat": 12.57, "lon": 104.99, "country": "Cambodia"},
    "china": {"lat": 35.86, "lon": 104.20, "country": "China"},
    "hong kong": {"lat": 22.32, "lon": 114.17, "country": "Hong Kong"},
    "india": {"lat": 20.59, "lon": 78.96, "country": "India"},
    "indonesia": {"lat": -0.79, "lon": 113.92, "country": "Indonesia"},
    "iran": {"lat": 32.43, "lon": 53.69, "country": "Iran"},
    "iraq": {"lat": 33.22, "lon": 43.68, "country": "Iraq"},
    "israel": {"lat": 31.05, "lon": 34.85, "country": "Israel"},
    "japan": {"lat": 36.20, "lon": 138.25, "country": "Japan"},
    "jordan": {"lat": 30.59, "lon": 36.24, "country": "Jordan"},
    "kazakhstan": {"lat": 48.02, "lon": 66.92, "country": "Kazakhstan"},
    "kuwait": {"lat": 29.31, "lon": 47.48, "country": "Kuwait"},
    "laos": {"lat": 19.86, "lon": 102.50, "country": "Laos"},
    "lebanon": {"lat": 33.85, "lon": 35.86, "country": "Lebanon"},
    "malaysia": {"lat": 4.21, "lon": 101.98, "country": "Malaysia"},
    "mongolia": {"lat": 46.86, "lon": 103.85, "country": "Mongolia"},
    "myanmar": {"lat": 21.92, "lon": 95.96, "country": "Myanmar"},
    "nepal": {"lat": 28.39, "lon": 84.12, "country": "Nepal"},
    "oman": {"lat": 21.47, "lon": 55.98, "country": "Oman"},
    "pakistan": {"lat": 30.38, "lon": 69.35, "country": "Pakistan"},
    "palestine": {"lat": 31.95, "lon": 35.23, "country": "Palestine"},
    "philippines": {"lat": 12.88, "lon": 121.77, "country": "Philippines"},
    "qatar": {"lat": 25.35, "lon": 51.18, "country": "Qatar"},
    "saudi arabia": {"lat": 23.89, "lon": 45.08, "country": "Saudi Arabia"},
    "singapore": {"lat": 1.35, "lon": 103.82, "country": "Singapore"},
    "south korea": {"lat": 35.91, "lon": 127.77, "country": "South Korea"},
    "sri lanka": {"lat": 7.87, "lon": 80.77, "country": "Sri Lanka"},
    "syria": {"lat": 34.80, "lon": 38.10, "country": "Syria"},
    "taiwan": {"lat": 23.70, "lon": 120.96, "country": "Taiwan"},
    "thailand": {"lat": 15.87, "lon": 100.99, "country": "Thailand"},
    "united arab emirates": {"lat": 23.42, "lon": 53.85, "country": "United Arab Emirates"},
    "uzbekistan": {"lat": 41.38, "lon": 64.59, "country": "Uzbekistan"},
    "vietnam": {"lat": 14.06, "lon": 108.28, "country": "Vietnam"},
    "yemen": {"lat": 15.55, "lon": 48.52, "country": "Yemen"},
    # Africa
    "algeria": {"lat": 28.03, "lon": 1.66, "country": "Algeria"},
    "angola": {"lat": -11.20, "lon": 17.87, "country": "Angola"},
    "cameroon": {"lat": 7.37, "lon": 12.35, "country": "Cameroon"},
    "egypt": {"lat": 26.82, "lon": 30.80, "country": "Egypt"},
    "ethiopia": {"lat": 9.15, "lon": 40.49, "country": "Ethiopia"},
    "ghana": {"lat": 7.95, "lon": -1.02, "country": "Ghana"},
    "ivory coast": {"lat": 7.54, "lon": -5.55, "country": "Ivory Coast"},
    "kenya": {"lat": -0.02, "lon": 37.91, "country": "Kenya"},
    "libya": {"lat": 26.34, "lon": 17.23, "country": "Libya"},
    "morocco": {"lat": 31.79, "lon": -7.09, "country": "Morocco"},
    "nigeria": {"lat": 9.08, "lon": 8.68, "country": "Nigeria"},
    "senegal": {"lat": 14.50, "lon": -14.45, "country": "Senegal"},
    "south africa": {"lat": -30.56, "lon": 22.94, "country": "South Africa"},
    "sudan": {"lat": 12.86, "lon": 30.22, "country": "Sudan"},
    "tanzania": {"lat": -6.37, "lon": 34.89, "country": "Tanzania"},
    "tunisia": {"lat": 33.89, "lon": 9.54, "country": "Tunisia"},
    "uganda": {"lat": 1.37, "lon": 32.29, "country": "Uganda"},
    # Oceania
    "australia": {"lat": -25.27, "lon": 133.78, "country": "Australia"},
    "fiji": {"lat": -17.71, "lon": 178.07, "country": "Fiji"},
    "new zealand": {"lat": -40.90, "lon": 174.89, "country": "New Zealand"},
}

CITY_COORDS = {
    # US
    "san francisco": {"lat": 37.77, "lon": -122.42, "city": "San Francisco", "country": "United States"},
    "new york": {"lat": 40.71, "lon": -74.01, "city": "New York", "country": "United States"},
    "los angeles": {"lat": 34.05, "lon": -118.24, "city": "Los Angeles", "country": "United States"},
    "chicago": {"lat": 41.88, "lon": -87.63, "city": "Chicago", "country": "United States"},
    "seattle": {"lat": 47.61, "lon": -122.33, "city": "Seattle", "country": "United States"},
    "austin": {"lat": 30.27, "lon": -97.74, "city": "Austin", "country": "United States"},
    "boston": {"lat": 42.36, "lon": -71.06, "city": "Boston", "country": "United States"},
    "denver": {"lat": 39.74, "lon": -104.99, "city": "Denver", "country": "United States"},
    "portland": {"lat": 45.52, "lon": -122.68, "city": "Portland", "country": "United States"},
    "miami": {"lat": 25.76, "lon": -80.19, "city": "Miami", "country": "United States"},
    "atlanta": {"lat": 33.75, "lon": -84.39, "city": "Atlanta", "country": "United States"},
    "san jose": {"lat": 37.34, "lon": -121.89, "city": "San Jose", "country": "United States"},
    "mountain view": {"lat": 37.39, "lon": -122.08, "city": "Mountain View", "country": "United States"},
    "palo alto": {"lat": 37.44, "lon": -122.14, "city": "Palo Alto", "country": "United States"},
    "san diego": {"lat": 32.72, "lon": -117.16, "city": "San Diego", "country": "United States"},
    "philadelphia": {"lat": 39.95, "lon": -75.17, "city": "Philadelphia", "country": "United States"},
    "washington": {"lat": 38.91, "lon": -77.04, "city": "Washington", "country": "United States"},
    "minneapolis": {"lat": 44.98, "lon": -93.27, "city": "Minneapolis", "country": "United States"},
    "cedar rapids": {"lat": 41.98, "lon": -91.67, "city": "Cedar Rapids", "country": "United States"},
    "dallas": {"lat": 32.78, "lon": -96.80, "city": "Dallas", "country": "United States"},
    "houston": {"lat": 29.76, "lon": -95.37, "city": "Houston", "country": "United States"},
    "phoenix": {"lat": 33.45, "lon": -112.07, "city": "Phoenix", "country": "United States"},
    "raleigh": {"lat": 35.78, "lon": -78.64, "city": "Raleigh", "country": "United States"},
    "pittsburgh": {"lat": 40.44, "lon": -79.99, "city": "Pittsburgh", "country": "United States"},
    "detroit": {"lat": 42.33, "lon": -83.05, "city": "Detroit", "country": "United States"},
    "orlando": {"lat": 28.54, "lon": -81.38, "city": "Orlando", "country": "United States"},
    "florida": {"lat": 27.66, "lon": -81.52, "city": "Florida", "country": "United States"},
    # Europe
    "london": {"lat": 51.51, "lon": -0.13, "city": "London", "country": "United Kingdom"},
    "paris": {"lat": 48.86, "lon": 2.35, "city": "Paris", "country": "France"},
    "berlin": {"lat": 52.52, "lon": 13.41, "city": "Berlin", "country": "Germany"},
    "munich": {"lat": 48.14, "lon": 11.58, "city": "Munich", "country": "Germany"},
    "frankfurt": {"lat": 50.11, "lon": 8.68, "city": "Frankfurt", "country": "Germany"},
    "hamburg": {"lat": 53.55, "lon": 9.99, "city": "Hamburg", "country": "Germany"},
    "amsterdam": {"lat": 52.37, "lon": 4.90, "city": "Amsterdam", "country": "Netherlands"},
    "brussels": {"lat": 50.85, "lon": 4.35, "city": "Brussels", "country": "Belgium"},
    "luxembourg": {"lat": 49.61, "lon": 6.13, "city": "Luxembourg", "country": "Luxembourg"},
    "zurich": {"lat": 47.38, "lon": 8.54, "city": "Zurich", "country": "Switzerland"},
    "zürich": {"lat": 47.38, "lon": 8.54, "city": "Zurich", "country": "Switzerland"},
    "geneva": {"lat": 46.20, "lon": 6.14, "city": "Geneva", "country": "Switzerland"},
    "vienna": {"lat": 48.21, "lon": 16.37, "city": "Vienna", "country": "Austria"},
    "prague": {"lat": 50.08, "lon": 14.44, "city": "Prague", "country": "Czech Republic"},
    "warsaw": {"lat": 52.23, "lon": 21.01, "city": "Warsaw", "country": "Poland"},
    "budapest": {"lat": 47.50, "lon": 19.04, "city": "Budapest", "country": "Hungary"},
    "bucharest": {"lat": 44.43, "lon": 26.10, "city": "Bucharest", "country": "Romania"},
    "copenhagen": {"lat": 55.68, "lon": 12.57, "city": "Copenhagen", "country": "Denmark"},
    "stockholm": {"lat": 59.33, "lon": 18.07, "city": "Stockholm", "country": "Sweden"},
    "oslo": {"lat": 59.91, "lon": 10.75, "city": "Oslo", "country": "Norway"},
    "helsinki": {"lat": 60.17, "lon": 24.94, "city": "Helsinki", "country": "Finland"},
    "dublin": {"lat": 53.35, "lon": -6.26, "city": "Dublin", "country": "Ireland"},
    "lisbon": {"lat": 38.72, "lon": -9.14, "city": "Lisbon", "country": "Portugal"},
    "madrid": {"lat": 40.42, "lon": -3.70, "city": "Madrid", "country": "Spain"},
    "barcelona": {"lat": 41.39, "lon": 2.17, "city": "Barcelona", "country": "Spain"},
    "rome": {"lat": 41.90, "lon": 12.50, "city": "Rome", "country": "Italy"},
    "milan": {"lat": 45.46, "lon": 9.19, "city": "Milan", "country": "Italy"},
    "moscow": {"lat": 55.76, "lon": 37.62, "city": "Moscow", "country": "Russia"},
    "brighton": {"lat": 50.82, "lon": -0.14, "city": "Brighton", "country": "United Kingdom"},
    "manchester": {"lat": 53.48, "lon": -2.24, "city": "Manchester", "country": "United Kingdom"},
    "edinburgh": {"lat": 55.95, "lon": -3.19, "city": "Edinburgh", "country": "United Kingdom"},
    "vilnius": {"lat": 54.69, "lon": 25.28, "city": "Vilnius", "country": "Lithuania"},
    "tallinn": {"lat": 59.44, "lon": 24.75, "city": "Tallinn", "country": "Estonia"},
    "riga": {"lat": 56.95, "lon": 24.11, "city": "Riga", "country": "Latvia"},
    "athens": {"lat": 37.98, "lon": 23.73, "city": "Athens", "country": "Greece"},
    "istanbul": {"lat": 41.01, "lon": 28.98, "city": "Istanbul", "country": "Turkey"},
    "kyiv": {"lat": 50.45, "lon": 30.52, "city": "Kyiv", "country": "Ukraine"},
    "belgrade": {"lat": 44.79, "lon": 20.45, "city": "Belgrade", "country": "Serbia"},
    "zagreb": {"lat": 45.82, "lon": 15.98, "city": "Zagreb", "country": "Croatia"},
    # Canada
    "toronto": {"lat": 43.65, "lon": -79.38, "city": "Toronto", "country": "Canada"},
    "montreal": {"lat": 45.50, "lon": -73.57, "city": "Montreal", "country": "Canada"},
    "vancouver": {"lat": 49.28, "lon": -123.12, "city": "Vancouver", "country": "Canada"},
    "ottawa": {"lat": 45.42, "lon": -75.70, "city": "Ottawa", "country": "Canada"},
    "calgary": {"lat": 51.04, "lon": -114.07, "city": "Calgary", "country": "Canada"},
    # Asia
    "tokyo": {"lat": 35.68, "lon": 139.65, "city": "Tokyo", "country": "Japan"},
    "osaka": {"lat": 34.69, "lon": 135.50, "city": "Osaka", "country": "Japan"},
    "seoul": {"lat": 37.57, "lon": 126.98, "city": "Seoul", "country": "South Korea"},
    "beijing": {"lat": 39.90, "lon": 116.41, "city": "Beijing", "country": "China"},
    "shanghai": {"lat": 31.23, "lon": 121.47, "city": "Shanghai", "country": "China"},
    "shenzhen": {"lat": 22.54, "lon": 114.06, "city": "Shenzhen", "country": "China"},
    "hong kong": {"lat": 22.32, "lon": 114.17, "city": "Hong Kong", "country": "Hong Kong"},
    "taipei": {"lat": 25.03, "lon": 121.57, "city": "Taipei", "country": "Taiwan"},
    "singapore": {"lat": 1.35, "lon": 103.82, "city": "Singapore", "country": "Singapore"},
    "mumbai": {"lat": 19.08, "lon": 72.88, "city": "Mumbai", "country": "India"},
    "bangalore": {"lat": 12.97, "lon": 77.59, "city": "Bangalore", "country": "India"},
    "bengaluru": {"lat": 12.97, "lon": 77.59, "city": "Bangalore", "country": "India"},
    "delhi": {"lat": 28.70, "lon": 77.10, "city": "Delhi", "country": "India"},
    "new delhi": {"lat": 28.61, "lon": 77.21, "city": "New Delhi", "country": "India"},
    "hyderabad": {"lat": 17.39, "lon": 78.49, "city": "Hyderabad", "country": "India"},
    "pune": {"lat": 18.52, "lon": 73.86, "city": "Pune", "country": "India"},
    "chennai": {"lat": 13.08, "lon": 80.27, "city": "Chennai", "country": "India"},
    "kolkata": {"lat": 22.57, "lon": 88.36, "city": "Kolkata", "country": "India"},
    "dubai": {"lat": 25.20, "lon": 55.27, "city": "Dubai", "country": "United Arab Emirates"},
    "abu dhabi": {"lat": 24.45, "lon": 54.38, "city": "Abu Dhabi", "country": "United Arab Emirates"},
    "tel aviv": {"lat": 32.09, "lon": 34.78, "city": "Tel Aviv", "country": "Israel"},
    "riyadh": {"lat": 24.71, "lon": 46.68, "city": "Riyadh", "country": "Saudi Arabia"},
    "bangkok": {"lat": 13.76, "lon": 100.50, "city": "Bangkok", "country": "Thailand"},
    "jakarta": {"lat": -6.21, "lon": 106.85, "city": "Jakarta", "country": "Indonesia"},
    "kuala lumpur": {"lat": 3.14, "lon": 101.69, "city": "Kuala Lumpur", "country": "Malaysia"},
    "hanoi": {"lat": 21.03, "lon": 105.83, "city": "Hanoi", "country": "Vietnam"},
    "manila": {"lat": 14.60, "lon": 120.98, "city": "Manila", "country": "Philippines"},
    "karachi": {"lat": 24.86, "lon": 67.00, "city": "Karachi", "country": "Pakistan"},
    "dhaka": {"lat": 23.81, "lon": 90.41, "city": "Dhaka", "country": "Bangladesh"},
    # Oceania
    "sydney": {"lat": -33.87, "lon": 151.21, "city": "Sydney", "country": "Australia"},
    "melbourne": {"lat": -37.81, "lon": 144.96, "city": "Melbourne", "country": "Australia"},
    "brisbane": {"lat": -27.47, "lon": 153.03, "city": "Brisbane", "country": "Australia"},
    "perth": {"lat": -31.95, "lon": 115.86, "city": "Perth", "country": "Australia"},
    "auckland": {"lat": -36.85, "lon": 174.76, "city": "Auckland", "country": "New Zealand"},
    "wellington": {"lat": -41.29, "lon": 174.78, "city": "Wellington", "country": "New Zealand"},
    # South America
    "são paulo": {"lat": -23.55, "lon": -46.63, "city": "São Paulo", "country": "Brazil"},
    "sao paulo": {"lat": -23.55, "lon": -46.63, "city": "São Paulo", "country": "Brazil"},
    "rio de janeiro": {"lat": -22.91, "lon": -43.17, "city": "Rio de Janeiro", "country": "Brazil"},
    "buenos aires": {"lat": -34.60, "lon": -58.38, "city": "Buenos Aires", "country": "Argentina"},
    "santiago": {"lat": -33.45, "lon": -70.67, "city": "Santiago", "country": "Chile"},
    "bogota": {"lat": 4.71, "lon": -74.07, "city": "Bogotá", "country": "Colombia"},
    "lima": {"lat": -12.05, "lon": -77.04, "city": "Lima", "country": "Peru"},
    "mexico city": {"lat": 19.43, "lon": -99.13, "city": "Mexico City", "country": "Mexico"},
    # Africa
    "cairo": {"lat": 30.04, "lon": 31.24, "city": "Cairo", "country": "Egypt"},
    "lagos": {"lat": 6.52, "lon": 3.38, "city": "Lagos", "country": "Nigeria"},
    "nairobi": {"lat": -1.29, "lon": 36.82, "city": "Nairobi", "country": "Kenya"},
    "cape town": {"lat": -33.92, "lon": 18.42, "city": "Cape Town", "country": "South Africa"},
    "johannesburg": {"lat": -26.20, "lon": 28.05, "city": "Johannesburg", "country": "South Africa"},
    "casablanca": {"lat": 33.57, "lon": -7.59, "city": "Casablanca", "country": "Morocco"},
    "accra": {"lat": 5.60, "lon": -0.19, "city": "Accra", "country": "Ghana"},
    "addis ababa": {"lat": 9.03, "lon": 38.75, "city": "Addis Ababa", "country": "Ethiopia"},
}

_COUNTRY_CODE_MAP = {
    # Europe
    "al": "albania", "ad": "andorra", "am": "armenia", "at": "austria", "az": "azerbaijan",
    "by": "belarus", "be": "belgium", "ba": "bosnia and herzegovina", "bg": "bulgaria",
    "hr": "croatia", "cy": "cyprus", "cz": "czech republic", "dk": "denmark", "ee": "estonia",
    "fi": "finland", "fr": "france", "ge": "georgia", "de": "germany", "gr": "greece",
    "hu": "hungary", "is": "iceland", "ie": "ireland", "it": "italy", "xk": "kosovo",
    "lv": "latvia", "li": "liechtenstein", "lt": "lithuania", "lu": "luxembourg",
    "mt": "malta", "md": "moldova", "mc": "monaco", "me": "montenegro", "nl": "netherlands",
    "mk": "north macedonia", "no": "norway", "pl": "poland", "pt": "portugal", "ro": "romania",
    "ru": "russia", "rs": "serbia", "sk": "slovakia", "si": "slovenia", "es": "spain",
    "se": "sweden", "ch": "switzerland", "tr": "turkey", "ua": "ukraine",
    "gb": "united kingdom", "uk": "united kingdom",
    # Americas
    "ar": "argentina", "bo": "bolivia", "br": "brazil", "ca": "canada", "cl": "chile",
    "co": "colombia", "cr": "costa rica", "cu": "cuba", "do": "dominican republic",
    "ec": "ecuador", "sv": "el salvador", "gt": "guatemala", "ht": "haiti", "hn": "honduras",
    "jm": "jamaica", "mx": "mexico", "ni": "nicaragua", "pa": "panama", "py": "paraguay",
    "pe": "peru", "pr": "puerto rico", "tt": "trinidad and tobago",
    "us": "united states", "uy": "uruguay", "ve": "venezuela",
    # Asia
    "af": "afghanistan", "bh": "bahrain", "bd": "bangladesh", "bn": "brunei",
    "kh": "cambodia", "cn": "china", "hk": "hong kong", "in": "india", "id": "indonesia",
    "ir": "iran", "iq": "iraq", "il": "israel", "jp": "japan", "jo": "jordan",
    "kz": "kazakhstan", "kw": "kuwait", "la": "laos", "lb": "lebanon",
    "my": "malaysia", "mn": "mongolia", "mm": "myanmar", "np": "nepal",
    "om": "oman", "pk": "pakistan", "ps": "palestine", "ph": "philippines",
    "qa": "qatar", "sa": "saudi arabia", "sg": "singapore", "kr": "south korea",
    "lk": "sri lanka", "sy": "syria", "tw": "taiwan", "th": "thailand",
    "ae": "united arab emirates", "uz": "uzbekistan", "vn": "vietnam", "ye": "yemen",
    # Africa
    "dz": "algeria", "ao": "angola", "cm": "cameroon", "eg": "egypt", "et": "ethiopia",
    "gh": "ghana", "ci": "ivory coast", "ke": "kenya", "ly": "libya",
    "ma": "morocco", "ng": "nigeria", "sn": "senegal", "za": "south africa",
    "sd": "sudan", "tz": "tanzania", "tn": "tunisia", "ug": "uganda",
    # Oceania
    "au": "australia", "fj": "fiji", "nz": "new zealand",
}

_LOCATION_ALIASES = {
    # US
    "sf": "san francisco", "bay area": "san francisco", "silicon valley": "san jose",
    "nyc": "new york", "new york city": "new york", "la": "los angeles",
    "dc": "washington", "washington dc": "washington", "washington d.c.": "washington",
    "philly": "philadelphia", "atl": "atlanta", "pdx": "portland",
    "slc": "salt lake city",
    # Europe
    "münchen": "munich", "köln": "cologne", "wien": "vienna", "praha": "prague",
    "warszawa": "warsaw", "moskva": "moscow", "moskow": "moscow",
    "kiev": "kyiv", "lisboa": "lisbon", "roma": "rome", "milano": "milan",
    "köbenhavn": "copenhagen",
    # Asia
    "bombay": "mumbai", "madras": "chennai", "calcutta": "kolkata",
    "peking": "beijing", "saigon": "ho chi minh city",
    # Country aliases
    "usa": "united states", "u.s.a.": "united states", "u.s.": "united states",
    "the netherlands": "netherlands", "holland": "netherlands",
    "uae": "united arab emirates", "england": "united kingdom",
    "scotland": "united kingdom", "wales": "united kingdom",
    "korea": "south korea", "côte d'ivoire": "ivory coast",
    "brasil": "brazil", "deutschland": "germany", "españa": "spain", "italia": "italy",
}


def _normalize_location(loc_string):
    """Normalize location string with aliases before geocoding."""
    loc = loc_string.lower().strip()
    loc = loc.split(",")[0].strip()
    return _LOCATION_ALIASES.get(loc, loc)


def _synthesize_email_status(findings, target_id, session) -> dict:
    """Aggregate email status from all available sources."""
    status = {
        "deliverable": None, "reputation": None, "suspicious": False,
        "provider": None, "first_seen": None, "last_seen": None,
        "breach_count": 0, "credentials_leaked": False, "source": "synthesized",
    }

    # Priority 1: EmailRep data
    emailrep = next((f for f in findings if f.module == "emailrep" and f.category == "metadata"
                     and f.data and f.data.get("reputation")), None)
    if emailrep:
        d = emailrep.data
        status["deliverable"] = d.get("deliverable")
        status["reputation"] = d.get("reputation")
        status["suspicious"] = d.get("suspicious", False)
        status["first_seen"] = d.get("first_seen")
        status["last_seen"] = d.get("last_seen")
        status["source"] = "emailrep"

    # Priority 2: email_validator DNS
    if status["deliverable"] is None:
        ev = next((f for f in findings if f.module == "email_validator" and f.data), None)
        if ev and (ev.data.get("has_dns") or ev.data.get("format_valid")):
            status["deliverable"] = True

    # Provider detection from MX/DNS
    for f in findings:
        if f.module in ("email_validator", "dns_deep") and f.data:
            combined = str(f.data.get("records", [])).lower() + str(f.data.get("mx_records", [])).lower()
            if "microsoft" in combined or "outlook" in combined or "office365" in combined:
                status["provider"] = "Microsoft 365"
            elif "google" in combined or "aspmx" in combined:
                status["provider"] = "Google Workspace"
            elif "protonmail" in combined or "proton" in combined:
                status["provider"] = "ProtonMail"

    # Breach stats
    breach_findings = [f for f in findings if f.category == "breach"]
    status["breach_count"] = len(breach_findings)
    status["credentials_leaked"] = any(
        f.data and f.data.get("credentials_leaked") for f in breach_findings if f.data
    )

    # Timeline from non-domain findings
    if not status["first_seen"] or not status["last_seen"]:
        dates = []
        _SKIP = {"dns_deep", "whois_lookup", "domain_analyzer", "wayback_domain", "wayback_count", "rdap_domain"}
        for f in findings:
            if not f.data or f.module in _SKIP:
                continue
            for key in ("BreachDate", "breach_date", "created_at", "joined",
                        "first_seen", "last_seen", "signup_date", "member_since"):
                val = f.data.get(key)
                if val and isinstance(val, str) and len(val) >= 4:
                    try:
                        year = int(val[:4])
                        if 2000 <= year <= 2027:
                            dates.append(val)
                    except (ValueError, TypeError):
                        pass
        if dates:
            dates.sort()
            if not status["first_seen"]:
                status["first_seen"] = dates[0]
            if not status["last_seen"]:
                status["last_seen"] = dates[-1]

    return status


def _geocode_location(loc_string):
    """Static geocoding — no API calls. Returns dict with lat/lon or None."""
    loc = _normalize_location(loc_string)

    # Try city match first (more specific)
    for city_key, coords in CITY_COORDS.items():
        if city_key in loc:
            return dict(coords)

    # Try country match
    for country_key, coords in COUNTRY_COORDS.items():
        if country_key in loc:
            return dict(coords)

    # Try 2-letter country code
    if len(loc) <= 3:
        country = _COUNTRY_CODE_MAP.get(loc)
        if country and country in COUNTRY_COORDS:
            return dict(COUNTRY_COORDS[country])

    return None


# Platform names that holehe/scrapers return as "name" — never real human names
_PLATFORM_NAMES_SET = {
    "spotify", "amazon", "reddit", "steam", "keybase", "github", "twitter",
    "facebook", "instagram", "tiktok", "freelancer", "replit", "eventbrite",
    "xvideos", "medium", "hackernews", "devto", "gitlab", "pinterest",
    "snapchat", "linkedin", "tumblr", "flickr", "twitch", "discord",
    "telegram", "whatsapp", "signal", "youtube", "netflix", "hulu",
    "apple", "google", "microsoft", "yahoo", "outlook", "protonmail",
    "gravatar", "wordpress", "blogger", "bitbucket", "stackoverflow",
    "lastpass", "1password", "bitwarden", "dashlane", "nordpass", "keepass",
    "office365", "office", "tutanota", "zoho", "mailchimp", "sendgrid",
    "proton", "icloud", "hotmail", "live", "msn", "aol", "gmx",
    "fiverr", "upwork", "toptal", "guru", "peopleperhour",
    "imgur", "disqus", "mastodon", "linktree", "aboutme", "about.me",
    "unknown", "user", "admin", "test", "null", "none", "default",
    "anonymous", "noreply", "info", "support", "contact", "hello",
    "webmaster", "postmaster", "root", "system", "bot", "service",
    "booking", "firefox", "chrome", "safari", "opera", "edge",
}

_TELEGRAM_SLOGANS = [
    "a new era of messaging", "fast. secure. powerful",
    "pure instant messaging", "cloud-based", "simple, fast, secure",
    "synced across all your devices", "sending messages",
    "telegram lets you", "powerful, fast, and secure",
    "telegram messenger", "telegram is a cloud-based",
]


def _clean_name_value(raw_name):
    """Clean a name before storing. Returns cleaned name or None if garbage."""
    if not raw_name or not isinstance(raw_name, str):
        return None

    name = raw_name.strip()

    # Strip emojis
    name = re.sub(r'[\U0001F000-\U0001FFFF\u200D\uFE0F]', '', name).strip()

    # Remove "on about.me", "on Snapchat", etc.
    name = re.sub(r'\s+on\s+\w+\.?\w*$', '', name, flags=re.IGNORECASE).strip()

    # Reject @xxx | Linktree, @xxx | Platform
    if name.startswith('@') or '|' in name:
        return None

    # Reject anything starting with "Telegram"
    if name.lower().startswith('telegram'):
        return None

    # Reject Telegram slogans
    if any(s in name.lower() for s in _TELEGRAM_SLOGANS):
        return None

    # Reject Cyrillic/CJK-only strings (likely wrong profile match)
    if re.match(r'^[\u0400-\u04FF\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]+$', name):
        return None

    # Reject very short
    if len(name) < 3:
        return None

    # Reject code/technical artifacts
    if re.match(r'^[a-z_]+$', name) and len(name) < 15:
        return None  # lowercase-only single word = username, not a name

    # Reject platform names
    if name.strip().lower() in _PLATFORM_NAMES_SET:
        return None

    # Reject "Contact @xxx" patterns
    if re.match(r'^contact\s+@', name, re.IGNORECASE):
        return None

    # Reject "xxx's profile" patterns (e.g. "stheis's profile" from letterboxd)
    if re.search(r"'s\s+profile$", name, re.IGNORECASE):
        return None

    return name


def _find_finding_for_name(findings, name_value, source_name):
    """Find the finding that produced this name value."""
    for f in findings:
        data = f.data or {}
        # Check extracted dict
        extracted = data.get("extracted")
        if isinstance(extracted, dict):
            for k, v in extracted.items():
                if v == name_value:
                    return f
        # Check direct name fields
        for key in ("name", "full_name", "display_name", "displayName"):
            if data.get(key) == name_value:
                return f
    return None


def aggregate_profile(target_id, workspace_id, session: Session, graph_context=None, country_code=None) -> dict:
    """Build a unified profile from all findings for a target. Sync for Celery.

    If graph_context is provided, uses pre-computed node confidence map
    instead of querying identity nodes from DB.
    """
    # Deduplicate: keep latest finding per (module, title) — Python-side
    all_findings = session.execute(
        select(Finding).where(
            Finding.target_id == target_id,
            Finding.workspace_id == workspace_id,
            Finding.status == "active",
        )
    ).scalars().all()
    seen = {}
    for f in all_findings:
        key = (f.module, f.title)
        existing = seen.get(key)
        if existing is None or (f.created_at and (not existing.created_at or f.created_at > existing.created_at)):
            seen[key] = f
    findings = list(seen.values())

    profile = {
        "names": [],
        "avatars": [],
        "bio": None,
        "location": None,
        "company": None,
        "title": None,
        "age_range": None,
        "gender": None,
        "website": None,
        "social_profiles": [],
        "emails": [],
        "usernames": [],
        "breach_summary": {"count": 0, "sources": [], "credentials_leaked": False},
        "reputation": None,
        "email_security": {},
        "dns_provider": None,
        "email_provider": None,
        "geo_locations": [],
        "domains": [],
        "first_seen": None,
        "data_sources": [],
        "identity_estimation": {
            "gender": None,
            "gender_probability": None,
            "age": None,
            "age_sample_count": None,
            "nationalities": [],
        },
    }

    seen_names = set()
    seen_avatars = set()
    seen_socials = set()
    seen_emails = set()
    seen_usernames = set()
    breach_names = set()
    sources = set()

    for f in findings:
        data = f.data or {}
        # Scraper findings nest extracted fields under "extracted" key — flatten them
        if "extracted" in data and isinstance(data["extracted"], dict):
            for k, v in data["extracted"].items():
                if k not in data and v is not None:
                    data[k] = v
        source = data.get("source") or data.get("scraper") or f.module
        sources.add(source)

        # --- Names ---
        is_email_verified = getattr(f, "indicator_type", "") == "email"
        for name_key in ("name", "full_name", "display_name", "displayName"):
            # Axe 4: holehe "name" field = platform name, not person name
            if f.module == "holehe" and name_key == "name":
                continue
            raw = data.get(name_key, "")
            name = _clean_name_value(raw)
            if name is None and raw and raw.strip():
                logger.debug("Name rejected by _clean_name_value: %r (source=%s)", raw.strip(), source)
            if name and name not in seen_names:
                seen_names.add(name)
                profile["names"].append({"value": name, "source": source, "module": f.module, "email_verified": is_email_verified})
            elif name and name in seen_names:
                # Dedup upgrade: if new source is more reliable, update the entry
                new_rel = _get_src_rel_mod(f.module, scraper_name=source)
                for existing in profile["names"]:
                    if existing["value"] == name:
                        old_rel = _get_src_rel_mod(
                            existing.get("module", "scraper_engine"),
                            scraper_name=existing.get("source", ""),
                        )
                        if new_rel > old_rel:
                            existing["source"] = source
                            existing["module"] = f.module
                            existing["email_verified"] = is_email_verified
                        break

        # --- Avatars ---
        for avatar_key in ("avatar_url", "photo_url", "avatar", "picture", "profile_image", "image_url"):
            avatar = data.get(avatar_key, "")
            if avatar and avatar not in seen_avatars and _is_valid_avatar(avatar):
                seen_avatars.add(avatar)
                profile["avatars"].append({"url": avatar, "source": source})
        # Also check nested structures (profile_data, extracted, details)
        for nested_key in ("profile_data", "extracted", "details"):
            nested = data.get(nested_key)
            if isinstance(nested, dict):
                for avatar_key in ("avatar_url", "photo_url", "avatar", "picture", "profile_image", "image_url"):
                    avatar = nested.get(avatar_key, "")
                    if avatar and avatar not in seen_avatars and _is_valid_avatar(avatar):
                        seen_avatars.add(avatar)
                        profile["avatars"].append({"url": avatar, "source": source})

        # --- Bio ---
        for bio_key in ("bio", "about", "description"):
            bio = data.get(bio_key, "")
            if bio and not profile["bio"] and _is_valid_bio(bio):
                profile["bio"] = bio[:500]

        # --- Location ---
        # ONLY use profile-sourced locations, NOT geoip (server locations)
        if f.module not in ("geoip", "maxmind_geo") and f.category != "geolocation":
            for loc_key in ("location", "currentLocation"):
                loc = data.get(loc_key, "")
                if loc and not profile["location"]:
                    profile["location"] = loc

        # --- Company/Title ---
        if data.get("company") and not profile["company"]:
            profile["company"] = data["company"]
        if data.get("organization") and not profile["company"]:
            profile["company"] = data["organization"]
        if data.get("title") and not profile["title"]:
            profile["title"] = data["title"]

        # --- Age/Gender (FullContact) ---
        if data.get("age_range") and not profile["age_range"]:
            profile["age_range"] = data["age_range"]
        if data.get("gender") and not profile["gender"]:
            profile["gender"] = data["gender"]

        # --- Identity estimation (Genderize/Agify/Nationalize) ---
        if f.module == "scraper_engine":
            scraper_name = data.get("scraper", "")

            # Genderize
            if scraper_name == "genderize" and data.get("gender"):
                est = profile["identity_estimation"]
                if not est["gender"]:
                    est["gender"] = data["gender"]
                    try:
                        est["gender_probability"] = float(data.get("probability", 0))
                    except (TypeError, ValueError):
                        est["gender_probability"] = None

            # Agify
            if scraper_name == "agify" and data.get("age"):
                est = profile["identity_estimation"]
                if not est["age"]:
                    try:
                        est["age"] = int(data["age"])
                    except (TypeError, ValueError):
                        pass
                    try:
                        est["age_sample_count"] = int(data.get("sample_count", 0))
                    except (TypeError, ValueError):
                        pass

            # Nationalize
            if scraper_name == "nationalize" and data.get("top_country"):
                est = profile["identity_estimation"]
                if not est["nationalities"]:
                    nats = []
                    for prefix in ["top", "second", "third"]:
                        cc = data.get(f"{prefix}_country")
                        prob = data.get(f"{prefix}_probability")
                        if cc:
                            try:
                                nats.append({"country_code": cc, "probability": float(prob or 0)})
                            except (TypeError, ValueError):
                                nats.append({"country_code": cc, "probability": 0})
                    est["nationalities"] = nats

        # --- Website ---
        if data.get("blog") and not profile["website"]:
            profile["website"] = data["blog"]
        if data.get("website") and not profile["website"]:
            profile["website"] = data["website"]

        # --- Social profiles ---
        if f.category == "social_account":
            platform = (data.get("platform") or data.get("network") or data.get("service") or "").lower()
            url = f.url or data.get("url", "")
            username = data.get("username") or data.get("handle") or data.get("login") or ""

            # Normalize platform name
            platform_clean = platform.replace("_profile", "").replace("_scraper", "").replace("_search", "").strip()
            if not platform_clean and url:
                DOMAIN_PLATFORM = {
                    "twitter.com": "twitter", "x.com": "twitter", "instagram.com": "instagram",
                    "facebook.com": "facebook", "github.com": "github", "linkedin.com": "linkedin",
                    "pinterest.com": "pinterest", "reddit.com": "reddit", "youtube.com": "youtube",
                    "tiktok.com": "tiktok", "spotify.com": "spotify", "discord.com": "discord",
                    "steam": "steam", "keybase.io": "keybase", "medium.com": "medium",
                    "dev.to": "devto", "gitlab.com": "gitlab", "mastodon": "mastodon",
                    "stackoverflow.com": "stackoverflow", "imgur.com": "imgur",
                    "about.me": "aboutme", "linktree": "linktree", "disqus.com": "disqus",
                }
                for domain_key, pname in DOMAIN_PLATFORM.items():
                    if domain_key in url.lower():
                        platform_clean = pname
                        break

            key = platform_clean or url
            if key and key not in seen_socials:
                seen_socials.add(key)
                profile["social_profiles"].append({
                    "platform": platform_clean or platform,
                    "url": url,
                    "username": username,
                    "source": source,
                })

        # --- Alternate emails ---
        if data.get("alt_email"):
            alt = data["alt_email"]
            if alt not in seen_emails:
                seen_emails.add(alt)
                profile["emails"].append({"value": alt, "source": source})

        # --- Usernames ---
        for uname_key in ("username", "login", "handle", "preferredUsername"):
            uname = data.get(uname_key, "")
            if uname and uname not in seen_usernames and len(uname) >= 3 and is_valid_username(uname):
                seen_usernames.add(uname)
                profile["usernames"].append({"value": uname, "source": source})

        # --- Breaches (exclude "not configured" / "api key" info findings) ---
        if f.category == "breach":
            title_lower = (f.title or "").lower()
            if "not configured" not in title_lower and "api key" not in title_lower:
                breach_name = data.get("breach_name") or data.get("Name") or f.title
                if breach_name not in breach_names:
                    breach_names.add(breach_name)
                    profile["breach_summary"]["count"] += 1
                    profile["breach_summary"]["sources"].append(breach_name)
                if data.get("credentials_leaked"):
                    profile["breach_summary"]["credentials_leaked"] = True

        # --- Reputation (EmailRep) ---
        if data.get("reputation") and not profile["reputation"]:
            profile["reputation"] = {
                "level": data["reputation"],
                "suspicious": data.get("suspicious", False),
                "first_seen": data.get("first_seen"),
                "source": source,
            }

        # --- Email security ---
        if data.get("has_spf") is not None:
            profile["email_security"] = {
                "spf": data.get("has_spf"),
                "dmarc": data.get("has_dmarc"),
                "dkim": data.get("has_dkim"),
                "security_level": data.get("security_level", "unknown"),
                "source": source,
            }

        # --- DNS/Email provider ---
        if data.get("ns_provider") and not profile["dns_provider"]:
            profile["dns_provider"] = data["ns_provider"]
        if data.get("provider") and f.module == "dns_deep" and not profile["email_provider"]:
            profile["email_provider"] = data["provider"]

        # --- Geo locations ---
        if f.category == "geolocation":
            lat = data.get("latitude") or data.get("lat")
            lon = data.get("longitude") or data.get("lon")
            if lat and lon:
                profile["geo_locations"].append({
                    "lat": lat,
                    "lon": lon,
                    "city": data.get("city", ""),
                    "country": data.get("country", ""),
                    "source": source,
                })

        # --- First seen ---
        if data.get("first_seen") and not profile["first_seen"]:
            profile["first_seen"] = data["first_seen"]

    profile["data_sources"] = sorted(sources)
    profile["breach_summary"]["sources"] = profile["breach_summary"]["sources"][:20]

    # --- Harvest self-reported user locations from scraper findings ---
    user_locations = []
    seen_user_locs = set()

    for f in findings:
        source = f.module or ""
        data_raw = f.data or {}

        # Skip geoip — it's server location, not user location
        if source in ("geoip", "maxmind_geo"):
            continue

        # Check all possible location fields
        loc = None
        for key in ("location", "city", "country"):
            val = data_raw.get(key)
            if val and isinstance(val, str) and len(val.strip()) >= 2:
                loc = val.strip()
                break

        # Also check extracted dict
        if not loc:
            extracted = data_raw.get("extracted")
            if isinstance(extracted, dict):
                for key in ("location", "city", "country"):
                    val = extracted.get(key)
                    if val and isinstance(val, str) and len(val.strip()) >= 2:
                        loc = val.strip()
                        break

        if not loc:
            continue

        # Reject URLs, XML, very short codes
        if loc.startswith("http") or loc.startswith("<") or loc.startswith("]"):
            continue
        if "CDATA" in loc or "xml" in loc.lower():
            continue
        if len(loc) < 3 and loc.upper() not in _COUNTRY_CODE_MAP:
            continue

        loc_key = loc.lower().strip()
        if loc_key in seen_user_locs:
            continue
        seen_user_locs.add(loc_key)

        entry = {
            "location": loc,
            "source": source,
            "type": "self_reported",
            "confidence": _get_src_rel_mod(source),
        }
        # Static geocode
        coords = _geocode_location(loc)
        if coords:
            entry.update(coords)
        user_locations.append(entry)

    profile["user_locations"] = user_locations

    # --- Timezone inference from activity timestamps ---
    try:
        from api.services.layer4.analyzers.timezone_analyzer import analyze_timezone
        tz_result = analyze_timezone(findings)
        if tz_result and tz_result["confidence"] >= 0.3:
            profile["timezone"] = tz_result
            if not profile["location"] and tz_result.get("regions"):
                profile["timezone_geo_hint"] = tz_result["regions"][0]
        else:
            profile["timezone"] = None
    except Exception as e:
        logger.debug("Timezone analysis failed: %s", e)
        profile["timezone"] = None

    # --- Geographic consistency analysis ---
    try:
        from api.services.layer4.analyzers.geo_consistency import analyze_geo_consistency
        geo_result = analyze_geo_consistency(profile, findings, country_code=country_code)
        profile["geo_consistency"] = geo_result
    except Exception as e:
        logger.debug("Geo consistency analysis failed: %s", e)
        profile["geo_consistency"] = None

    # --- Email status synthesis ---
    try:
        profile["email_status"] = _synthesize_email_status(findings, target_id, session)
    except Exception as e:
        logger.debug("Email status synthesis failed: %s", e)
        profile["email_status"] = None

    # --- Profile confidence score ---
    name_sources = len(profile["names"])
    avatar_sources = len(profile["avatars"])
    total_sources = len(profile["data_sources"])

    name_confidence = min(1.0, name_sources * 0.25)
    avatar_confidence = min(1.0, avatar_sources * 0.33)
    data_confidence = min(1.0, total_sources / 10)

    name_values = [n["value"].lower().strip() for n in profile["names"]]
    most_common_count = max((name_values.count(v) for v in set(name_values)), default=0)
    cross_verified_bonus = min(0.2, most_common_count * 0.1)

    overall_confidence = min(1.0, (
        name_confidence * 0.30 +
        avatar_confidence * 0.15 +
        data_confidence * 0.40 +
        cross_verified_bonus +
        (0.15 if total_sources > 0 else 0.0)
    ))

    profile["confidence"] = {
        "overall": round(overall_confidence, 2),
        "name_sources": name_sources,
        "avatar_sources": avatar_sources,
        "total_sources": total_sources,
        "cross_verified": most_common_count > 1,
    }

    # Load identity nodes with propagated confidence (from PageRank)
    # Use graph_context if available, else load from DB (existing behavior)
    if graph_context:
        node_confidence_map = {
            v["value"].lower(): v["confidence"]
            for v in graph_context["node_map"].values()
            if v.get("value")
        }
    else:
        identities = session.execute(
            select(Identity).where(
                Identity.target_id == target_id,
                Identity.workspace_id == workspace_id,
            )
        ).scalars().all()
        node_confidence_map = {}
        for i in identities:
            if i.value:
                node_confidence_map[i.value.lower()] = i.confidence or 0.5

    # Load DB blacklist early (needed for field_confidence + name validation)
    db_blacklist = _load_blacklist(session)

    # --- Parse potential name from email prefix ---
    _email = session.execute(
        select(Target.email).where(Target.id == target_id, Target.workspace_id == workspace_id)
    ).scalar_one_or_none() or ""
    _prefix = _email.split("@")[0] if "@" in _email else _email
    _cleaned = re.sub(r"\d+", "", _prefix)
    _name_parts = [p for p in re.split(r"[._\-]", _cleaned) if len(p) >= 2]
    email_name_guess = {
        "first": _name_parts[0].capitalize() if len(_name_parts) >= 1 else None,
        "last": _name_parts[-1].capitalize() if len(_name_parts) >= 2 else None,
        "full": " ".join(p.capitalize() for p in _name_parts) if len(_name_parts) >= 2 else None,
    }

    # --- Per-field confidence ---
    field_confidence = {}

    # First name confidence — filter candidates through blacklist
    first_names = []
    for n in profile["names"]:
        parts = n["value"].strip().split()
        if parts:
            candidate = parts[0]
            if len(candidate) >= 2 and _is_valid_name_db(candidate, db_blacklist):
                first_names.append({"value": candidate, "source": n["source"]})

    if first_names:
        # Use propagated confidence from graph if available
        for fn in first_names:
            fn["graph_confidence"] = node_confidence_map.get(fn["value"].lower(), 0.3)

        # Boost names that appear in the top graph cluster
        if graph_context and graph_context.get("clusters"):
            top_cluster = graph_context["clusters"][0]
            top_cluster_nodes = set(top_cluster["nodes"])
            for fn in first_names:
                node_info = graph_context["node_map"].get(fn["value"].lower())
                if node_info and node_info["id"] in top_cluster_nodes:
                    fn["graph_confidence"] = fn.get("graph_confidence", 0) + 0.15

        # Best first name = highest graph confidence
        best = max(first_names, key=lambda fn: fn.get("graph_confidence", 0))
        fn_sources = set(fn["source"] for fn in first_names if fn["value"].lower() == best["value"].lower())
        match_count = sum(1 for fn in first_names if fn["value"].lower() == best["value"].lower())
        field_confidence["first_name"] = {
            "value": best["value"],
            "confidence": round(min(1.0, best["graph_confidence"] * 0.6 + len(fn_sources) * 0.15), 2),
            "sources": sorted(fn_sources),
            "source_count": len(fn_sources),
            "graph_confidence": round(best["graph_confidence"], 2),
        }
        # Boost if matches email pattern
        if email_name_guess["first"] and field_confidence["first_name"]["value"].lower() == email_name_guess["first"].lower():
            field_confidence["first_name"]["confidence"] = round(min(1.0, field_confidence["first_name"]["confidence"] + 0.20), 2)
            field_confidence["first_name"]["sources"].append("email_pattern_match")

    # Last name confidence — filter candidates through blacklist
    last_names = []
    for n in profile["names"]:
        parts = n["value"].strip().split()
        if len(parts) >= 2:
            candidate = parts[-1]
            if len(candidate) >= 2 and _is_valid_name_db(candidate, db_blacklist):
                last_names.append({"value": candidate, "source": n["source"]})

    if last_names:
        # Use propagated confidence from graph if available
        for ln in last_names:
            ln["graph_confidence"] = node_confidence_map.get(ln["value"].lower(), 0.3)

        # Boost names in top graph cluster
        if graph_context and graph_context.get("clusters"):
            top_cluster = graph_context["clusters"][0]
            top_cluster_nodes = set(top_cluster["nodes"])
            for ln in last_names:
                node_info = graph_context["node_map"].get(ln["value"].lower())
                if node_info and node_info["id"] in top_cluster_nodes:
                    ln["graph_confidence"] = ln.get("graph_confidence", 0) + 0.15

        best = max(last_names, key=lambda ln: ln.get("graph_confidence", 0))
        ln_sources = set(ln["source"] for ln in last_names if ln["value"].lower() == best["value"].lower())
        match_count = sum(1 for ln in last_names if ln["value"].lower() == best["value"].lower())
        field_confidence["last_name"] = {
            "value": best["value"],
            "confidence": round(min(1.0, best["graph_confidence"] * 0.6 + len(ln_sources) * 0.15), 2),
            "sources": sorted(ln_sources),
            "source_count": len(ln_sources),
            "graph_confidence": round(best["graph_confidence"], 2),
        }
        # Boost if matches email pattern
        if email_name_guess["last"] and field_confidence["last_name"]["value"].lower() == email_name_guess["last"].lower():
            field_confidence["last_name"]["confidence"] = round(min(1.0, field_confidence["last_name"]["confidence"] + 0.20), 2)
            field_confidence["last_name"]["sources"].append("email_pattern_match")

    # Gender confidence (from identity_estimation)
    est = profile.get("identity_estimation", {})
    if est.get("gender"):
        field_confidence["gender"] = {
            "value": est["gender"],
            "confidence": round(est.get("gender_probability", 0), 2),
            "sources": ["genderize.io"],
            "source_count": 1,
            "note": "Statistical estimation from first name",
        }

    # Age confidence
    if est.get("age"):
        sample = est.get("age_sample_count", 0) or 0
        field_confidence["age"] = {
            "value": f"~{est['age']}",
            "confidence": round(min(0.6, sample / 100000), 2),
            "sources": ["agify.io"],
            "source_count": 1,
            "note": f"Demographic estimate from {sample:,} samples",
        }

    # Location confidence
    if profile.get("location"):
        loc_sources = set()
        for f_item in findings:
            d = f_item.data or {}
            if "extracted" in d and isinstance(d["extracted"], dict):
                for k, v in d["extracted"].items():
                    if k not in d and v is not None:
                        d[k] = v
            for loc_key in ("location", "currentLocation"):
                if d.get(loc_key) == profile["location"]:
                    loc_sources.add(d.get("source") or d.get("scraper") or f_item.module)
        field_confidence["location"] = {
            "value": profile["location"],
            "confidence": round(min(1.0, len(loc_sources) * 0.35), 2),
            "sources": sorted(loc_sources),
            "source_count": len(loc_sources),
        }

    profile["field_confidence"] = field_confidence

    # Pick primary name with strict validation
    PLATFORM_NAMES = {
        # Social platforms
        "spotify", "amazon", "reddit", "steam", "keybase", "github", "twitter",
        "facebook", "instagram", "tiktok", "freelancer", "replit", "eventbrite",
        "xvideos", "medium", "hackernews", "devto", "gitlab", "pinterest",
        "snapchat", "linkedin", "tumblr", "flickr", "twitch", "discord",
        "telegram", "whatsapp", "signal", "youtube", "netflix", "hulu",
        "apple", "google", "microsoft", "yahoo", "outlook", "protonmail",
        "gravatar", "wordpress", "blogger", "bitbucket", "stackoverflow",
        # Password managers / security tools
        "lastpass", "1password", "bitwarden", "dashlane", "nordpass", "keepass",
        # Email services / providers
        "office365", "office", "tutanota", "zoho", "mailchimp", "sendgrid",
        "proton", "icloud", "hotmail", "live", "msn", "aol", "gmx",
        # Freelance / work platforms
        "fiverr", "upwork", "toptal", "guru", "peopleperhour",
        # New scraper platforms
        "imgur", "disqus", "mastodon", "linktree", "aboutme", "about.me",
        # Generic words that are never real names
        "unknown", "user", "admin", "test", "null", "none", "default",
        "anonymous", "noreply", "info", "support", "contact", "hello",
        "webmaster", "postmaster", "root", "system", "bot", "service",
    }
    REJECT_PATTERNS = {
        "account", "found", "not configured", "api key", "profile",
        "scraper", "scanner", "module", "error", "failed", "timeout",
        "not found", "no results", "unavailable", "blocked",
        "http://", "https://", ".com", ".org", ".net",
        # Telegram garbage
        "telegram", "a new era", "fast. secure", "instant messaging",
        "cloud-based", "synced across",
        # Platform descriptions
        "on about.me", "| linktree", "contact @",
        # Browsers / tools
        "firefox", "chrome", "safari", "opera", "edge",
        "booking",
    }

    def _is_valid_name(name_val):
        """Validate: must be a real human name, not a platform or finding title."""
        if not name_val or len(name_val.strip()) < 3:
            return False
        # Check DB blacklist first (if loaded)
        if db_blacklist and not _is_valid_name_db(name_val, db_blacklist):
            return False
        # Hardcoded fallback
        val = name_val.strip().lower()
        if val in PLATFORM_NAMES:
            return False
        if any(p in val for p in REJECT_PATTERNS):
            return False
        return True

    # Composite score name resolution: graph_confidence * 0.5 + source_reliability * 0.3 + count * 0.1
    _get_src_rel = _get_src_rel_mod

    # Count how many sources confirm each name
    name_counts = {}
    for n in profile["names"]:
        key = n["value"].strip().lower()
        name_counts[key] = name_counts.get(key, 0) + 1

    # Score each name candidate
    for n in profile["names"]:
        graph_conf = node_confidence_map.get(n["value"].strip().lower(), 0.3)
        name_module = n.get("module", n.get("source", ""))
        scraper_name = n.get("source", "")
        source_rel = _get_src_rel(name_module, scraper_name=scraper_name)
        count_bonus = name_counts.get(n["value"].strip().lower(), 1) * 0.1

        # Axe 3: source method penalty — username-guessed vs email-verified
        method_adj = 0.0
        src_finding = _find_finding_for_name(findings, n["value"], scraper_name)
        if src_finding:
            ind_type = getattr(src_finding, "indicator_type", None) or ""
            # Username-guessed: indicator_type is username or social_url
            if ind_type in ("username", "social_url"):
                method_adj = -0.15
            # Email-verified: indicator_type is email
            elif ind_type == "email":
                method_adj = 0.05

        n["composite_score"] = graph_conf * 0.5 + source_rel * 0.3 + count_bonus + method_adj

    # Filter through blacklist + validation, pick highest composite score
    valid_names = [n for n in profile["names"] if _is_valid_name(n["value"])]

    # Axe 2: Family name consensus — boost names whose surname matches dominant family name
    if len(valid_names) >= 3:
        surname_votes = {}
        for n in valid_names:
            parts = n["value"].strip().split()
            if len(parts) >= 2:
                surname = parts[-1].lower()
                if len(surname) >= 2:
                    surname_votes[surname] = surname_votes.get(surname, 0) + 1
        if surname_votes:
            dominant_surname = max(surname_votes, key=surname_votes.get)
            dominant_count = surname_votes[dominant_surname]
            if dominant_count >= 2:
                for n in valid_names:
                    parts = n["value"].strip().split()
                    if len(parts) >= 2 and parts[-1].lower() == dominant_surname:
                        n["composite_score"] = n.get("composite_score", 0) + 0.10

    # Email prefix first-letter bonus: "stheis@" → S matches "Sebastian" (+0.08)
    _email_prefix_lc = _prefix.lower() if _prefix else ""
    _email_first_char = _email_prefix_lc[0] if _email_prefix_lc else ""
    if _email_first_char:
        for n in valid_names:
            name_first = n["value"].strip()[0].lower() if n["value"].strip() else ""
            if name_first == _email_first_char:
                n["composite_score"] = n.get("composite_score", 0) + 0.08

    # === Email Pattern Intelligence ===
    # Detect corporate email patterns from sibling targets on the same domain
    from api.services.layer4.email_pattern_detector import (
        detect_domain_pattern, decompose_email, boost_names_with_pattern,
        detect_pattern_with_assertion,
    )

    _email_domain = _email.split("@")[-1].lower() if "@" in _email else ""
    _email_pattern_info = None
    _email_decomp = None

    if _email_domain:
        _email_pattern_info = detect_domain_pattern(_email_domain, session)
        if _email_pattern_info:
            _email_decomp = decompose_email(_email, _email_pattern_info)
            if _email_decomp:
                logger.info(
                    "EMAIL_PATTERN: %s → surname='%s' first='%s' (pattern=%s, conf=%.2f)",
                    _email, _email_decomp.get("surname", "?"),
                    _email_decomp.get("first_initial", _email_decomp.get("first_name", "?")),
                    _email_decomp.get("pattern", "?"),
                    _email_decomp.get("confidence", 0),
                )
                valid_names = boost_names_with_pattern(valid_names, _email_decomp)

    # Operator-confirmed pattern: if operator has asserted a name, confirm the pattern
    _target_for_pattern = session.execute(
        select(Target).where(Target.id == target_id, Target.workspace_id == workspace_id)
    ).scalar_one_or_none()
    if _target_for_pattern:
        _op_pattern = detect_pattern_with_assertion(
            _email,
            getattr(_target_for_pattern, 'user_first_name', None),
            getattr(_target_for_pattern, 'user_last_name', None),
        )
        if _op_pattern:
            profile["email_pattern_confirmed"] = _op_pattern

    # Store pattern info in profile for frontend display
    if _email_pattern_info:
        profile["email_pattern"] = _email_pattern_info
    if _email_decomp:
        profile["email_decomposition"] = _email_decomp
        if not any(n.get("email_pattern_match") for n in valid_names):
            # No name matched — store surname hint
            profile["email_derived_surname"] = _email_decomp.get("surname", "").title()
            profile["email_derived_first_initial"] = _email_decomp.get("first_initial", "").upper()

    # Tier separation: email-verified names vs username-guessed names
    verified_names = [n for n in valid_names if n.get("email_verified")]
    guessed_names = [n for n in valid_names if not n.get("email_verified")]

    primary_name = None
    if verified_names:
        # Prefer email-verified names — these are confirmed for this email
        best = max(verified_names, key=lambda n: n.get("composite_score", 0))
        primary_name = best["value"].strip()
    elif guessed_names:
        # Fallback: consensus by family name among username-guessed names
        family_groups = {}
        for n in guessed_names:
            parts = n["value"].strip().split()
            if len(parts) >= 2:
                family = parts[-1].lower()
                family_groups.setdefault(family, []).append(n)

        if family_groups:
            best_family = max(family_groups, key=lambda fam: len(family_groups[fam]))
            candidates = family_groups[best_family]
            best = max(candidates, key=lambda n: n.get("composite_score", 0))
            primary_name = best["value"].strip()
        else:
            best = max(guessed_names, key=lambda n: n.get("composite_score", 0))
            primary_name = best["value"].strip()
    # Fallback: use email guess if no name found from scanners
    if not primary_name and email_name_guess["full"]:
        if _is_valid_name(email_name_guess["full"]):
            primary_name = email_name_guess["full"]
            profile["names"].append({"value": email_name_guess["full"], "source": "email_pattern"})
            profile["confidence"]["overall"] = max(profile.get("confidence", {}).get("overall", 0), 0.25)
    profile["primary_name"] = primary_name

    # Save auto-resolved name BEFORE potential operator override
    profile["_auto_resolved_name"] = primary_name

    # === OPERATOR ASSERTION CHECK ===
    # If operator has asserted a name, it becomes primary with confidence=1.0
    target = session.execute(
        select(Target).where(Target.id == target_id, Target.workspace_id == workspace_id)
    ).scalar_one_or_none()
    if target:
        user_first = getattr(target, 'user_first_name', None)
        user_last = getattr(target, 'user_last_name', None)
        if user_first or user_last:
            asserted_name = ' '.join(p for p in [user_first, user_last] if p)
            profile["primary_name"] = asserted_name
            profile["primary_name_source"] = "operator"
            profile["primary_name_confidence"] = 1.0

            # Demote auto-resolved name to alias if different
            auto_name = profile.get("_auto_resolved_name")
            if auto_name and auto_name.lower() != asserted_name.lower():
                aliases = profile.get("name_aliases", [])
                if auto_name not in aliases:
                    aliases.append(auto_name)
                profile["name_aliases"] = aliases

            logger.info("Using operator-asserted name: '%s' (auto-resolved was: '%s')",
                        asserted_name, profile.get("_auto_resolved_name"))
        else:
            profile["primary_name_source"] = "auto"

    # Pick primary avatar: quality score first, then source priority as tiebreaker
    AVATAR_SOURCE_PRIORITY = {
        "gravatar": 10, "google_audit": 9, "github_deep": 8, "fullcontact": 7,
        "social_enricher": 6, "epieos": 5, "keybase": 5,
        "linkedin": 7, "twitter": 4, "facebook": 3,
        "steam": 1, "roblox": 1, "xbox": 1, "discord": 1,
        "scraper_engine": 2,
    }
    primary_avatar = None
    best_score = (-1, -1)  # (quality, source_priority)
    for a in profile["avatars"]:
        url = a.get("url")
        if not url or not _is_valid_avatar(url):
            continue
        quality = _score_avatar(url)
        src_prio = AVATAR_SOURCE_PRIORITY.get(a.get("source", ""), 0)
        if (quality, src_prio) > best_score:
            best_score = (quality, src_prio)
            primary_avatar = url

    # Quality gate: only promote to target.avatar_url if quality >= 2
    # Score 0-1 = invalid/generated defaults → pixel art avatar fallback
    avatar_quality = best_score[0] if best_score != (-1, -1) else 0
    if avatar_quality < 2:
        primary_avatar = None
    profile["primary_avatar"] = primary_avatar
    profile["primary_avatar_quality"] = avatar_quality  # expose for frontend badge

    # Store on target
    target = session.execute(
        select(Target).where(Target.id == target_id, Target.workspace_id == workspace_id)
    ).scalar_one_or_none()
    if target:
        target.profile_data = profile
        # Operator-asserted name always wins for display_name
        has_operator_name = (getattr(target, 'user_first_name', None) or
                             getattr(target, 'user_last_name', None))
        if has_operator_name:
            # Rebuild from user fields — pipeline NEVER overwrites operator assertion
            target.display_name = ' '.join(
                p for p in [target.user_first_name, target.user_last_name] if p
            )
        elif profile.get("primary_name_source") == "operator":
            target.display_name = profile["primary_name"]
        elif profile["primary_name"]:
            # Always update display_name from auto-resolved name on rescan
            # (previous value may be stale from an earlier, less accurate scan)
            target.display_name = profile["primary_name"]
        # Avatar: only set if quality >= 2, otherwise clear to trigger pixel art fallback
        if profile["primary_avatar"]:
            target.avatar_url = profile["primary_avatar"]
        else:
            target.avatar_url = None  # force GenerativeAvatar fallback
        session.commit()

    logger.info("Profile aggregated for target %s: %d sources, %d social profiles, %d breaches",
                target_id, len(sources), len(profile["social_profiles"]), profile["breach_summary"]["count"])
    return profile
