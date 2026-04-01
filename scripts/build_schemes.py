#!/usr/bin/env python3
"""Fetch WezTerm color scheme data from the official docs and build color_schemes.json."""

import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import COLOR_SCHEMES

DATA_URL = "https://raw.githubusercontent.com/wez/wezterm/main/docs/colorschemes/data.json"
OUTPUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "color_schemes.json")


def main():
    print(f"Fetching scheme data from {DATA_URL}...")
    req = urllib.request.Request(DATA_URL, headers={"User-Agent": "wezconfigurator-build"})
    resp = urllib.request.urlopen(req, timeout=30)
    all_schemes = json.loads(resp.read().decode("utf-8"))
    print(f"  Got {len(all_schemes)} total schemes from WezTerm repo")

    # Build lookup: name -> colors (including aliases)
    lookup = {}
    for entry in all_schemes:
        meta = entry.get("metadata", {})
        colors = entry.get("colors", {})
        name = meta.get("name", "")
        if name and colors:
            lookup[name] = colors
        for alias in meta.get("aliases", []):
            if alias and colors:
                lookup[alias] = colors

    # Extract only the schemes we need
    wanted = set(COLOR_SCHEMES)
    result = {}
    missing = []

    for name in COLOR_SCHEMES:
        if name in lookup:
            c = lookup[name]
            scheme = {}
            for key in ("foreground", "background", "cursor_bg", "cursor_fg", "cursor_border",
                        "selection_bg", "selection_fg"):
                if key in c:
                    scheme[key] = c[key]
            if "ansi" in c:
                scheme["ansi"] = c["ansi"]
            if "brights" in c:
                scheme["brights"] = c["brights"]
            result[name] = scheme
        else:
            missing.append(name)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(result, f)

    print(f"\nDone! {len(result)} schemes saved to {OUTPUT}")
    print(f"File size: {os.path.getsize(OUTPUT) / 1024:.1f} KB")
    if missing:
        print(f"\n{len(missing)} schemes not found in WezTerm data:")
        for m in missing:
            print(f"  - {m}")


if __name__ == "__main__":
    main()
