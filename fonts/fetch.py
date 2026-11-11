#!/usr/bin/env python3
"""Download the free fonts the videos use (SIL Open Font License): Poppins + JetBrains Mono.

  python fonts/fetch.py
"""
from pathlib import Path

import requests

HERE = Path(__file__).parent
RAW = "https://raw.githubusercontent.com"
FILES = {
    "Poppins-Medium.ttf": f"{RAW}/google/fonts/main/ofl/poppins/Poppins-Medium.ttf",
    "Poppins-SemiBold.ttf": f"{RAW}/google/fonts/main/ofl/poppins/Poppins-SemiBold.ttf",
    "Poppins-Bold.ttf": f"{RAW}/google/fonts/main/ofl/poppins/Poppins-Bold.ttf",
    "Poppins-ExtraBold.ttf": f"{RAW}/google/fonts/main/ofl/poppins/Poppins-ExtraBold.ttf",
    "JetBrainsMono-Medium.ttf": f"{RAW}/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Medium.ttf",
    "JetBrainsMono-Bold.ttf": f"{RAW}/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Bold.ttf",
}

for name, url in FILES.items():
    if not (HERE / name).exists():
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        (HERE / name).write_bytes(r.content)
    print("ok", name)
