#!/usr/bin/env python3
"""Download MaxMind GeoLite2-City database.

You need a free MaxMind account + license key:
  1. Sign up at https://www.maxmind.com/en/geolite2/signup
  2. Generate a license key at https://www.maxmind.com/en/accounts/current/license-key
  3. Set MAXMIND_LICENSE env var or pass as argument

Usage:
  MAXMIND_LICENSE=your_key python scripts/download_maxmind.py
  python scripts/download_maxmind.py YOUR_LICENSE_KEY
"""

import os
import sys
import tarfile
import urllib.request
import shutil

LICENSE = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("MAXMIND_LICENSE", "")
DB_DIR = "data/maxmind"
DB_PATH = os.path.join(DB_DIR, "GeoLite2-City.mmdb")

if not LICENSE:
    print(__doc__)
    sys.exit(1)

url = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={LICENSE}&suffix=tar.gz"

print(f"Downloading GeoLite2-City to {DB_DIR}/ ...")
os.makedirs(DB_DIR, exist_ok=True)

tar_path = os.path.join(DB_DIR, "GeoLite2-City.tar.gz")
urllib.request.urlretrieve(url, tar_path)

with tarfile.open(tar_path) as tar:
    for member in tar.getmembers():
        if member.name.endswith(".mmdb"):
            member.name = os.path.basename(member.name)
            tar.extract(member, DB_DIR)
            break

os.unlink(tar_path)
print(f"Done. Database saved to {DB_PATH}")
