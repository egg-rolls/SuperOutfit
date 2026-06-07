#!/usr/bin/env python3
"""
色卡爬虫 - 从多个来源爬取真实配色方案
Sources: Color Hunt, Colour Lovers, Colormind, LOL Colors
"""

import json
import os
import time
import re
import urllib.request
import urllib.parse
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("SUPEROUTFIT_DATA", SKILL_DIR / "data"))
RAW_PALETTES = DATA_DIR / "raw_palettes.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch_url(url, data=None, timeout=15, headers=None):
    """Fetch URL with error handling"""
    hdrs = dict(HEADERS)
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs)
    resp = urllib.request.urlopen(req, timeout=timeout)
    return resp.read().decode("utf-8")

# ============================================================
# Color Hunt (existing)
# ============================================================
def scrape_colorhunt(pages=50, sort="new", tags=""):
    """从 Color Hunt 爬取色卡"""
    url = "https://colorhunt.co/php/feed.php"
    palettes = []
    for step in range(pages):
        data = urllib.parse.urlencode({"step": step, "sort": sort, "tags": tags}).encode()
        try:
            raw = json.loads(fetch_url(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}))
            for item in raw:
                code = item.get("code", "")
                likes = int(item.get("likes", 0))
                colors = []
                for i in range(0, len(code), 6):
                    hex_val = "#" + code[i:i+6]
                    if len(hex_val) == 7 and all(c in "0123456789abcdef" for c in code[i:i+6].lower()):
                        colors.append(hex_val)
                if 2 <= len(colors) <= 6:
                    palettes.append({"colors": colors, "likes": likes, "source": "colorhunt"})
            print(f"  Page {step+1}/{pages}: +{len(raw)} palettes (total: {len(palettes)})")
        except Exception as e:
            print(f"  Page {step+1}: error - {e}")
        time.sleep(0.3)
    return palettes

# ============================================================
# Colour Lovers API (public, no auth needed)
# ============================================================
def scrape_colourlovers(pages=5, per_page=100):
    """从 Colour Lovers API 爬取色卡"""
    palettes = []
    for page in range(1, pages + 1):
        url = f"https://www.colourlovers.com/api/palettes/top?format=json&numResults={per_page}&resultOffset={(page-1)*per_page}"
        try:
            raw = json.loads(fetch_url(url))
            for item in raw:
                colors = ["#" + c.upper() for c in item.get("colors", [])]
                colors = [c for c in colors if re.match(r'^#[0-9A-F]{6}$', c)]
                if 2 <= len(colors) <= 6:
                    palettes.append({
                        "colors": colors,
                        "likes": int(item.get("numVotes", 0)),
                        "source": "colourlovers",
                    })
            print(f"  Colour Lovers page {page}/{pages}: +{len(raw)} (total: {len(palettes)})")
        except Exception as e:
            print(f"  Colour Lovers page {page}: error - {e}")
            break
        time.sleep(1)  # be polite
    return palettes

# ============================================================
# Colormind API
# ============================================================
def scrape_colormind(iterations=30):
    """从 Colormind API 爬取随机色卡"""
    palettes = []
    for i in range(iterations):
        url = "http://colormind.io/api/"
        data = json.dumps({"model": "default"}).encode()
        try:
            raw = json.loads(fetch_url(url, data=data, headers={"Content-Type": "application/json"}))
            result = raw.get("result", [])
            colors = []
            for rgb in result:
                if len(rgb) == 3:
                    hex_val = "#{:02X}{:02X}{:02X}".format(rgb[0], rgb[1], rgb[2])
                    colors.append(hex_val)
            if 2 <= len(colors) <= 6:
                palettes.append({"colors": colors, "likes": 0, "source": "colormind"})
            if (i+1) % 10 == 0:
                print(f"  Colormind: {i+1}/{iterations} (total: {len(palettes)})")
        except Exception as e:
            print(f"  Colormind iteration {i+1}: error - {e}")
        time.sleep(0.5)
    return palettes

# ============================================================
# Adobe Color - scrape from explore/public API
# ============================================================
def scrape_adobe_color(pages=3):
    """Try Adobe Color explore API"""
    palettes = []
    try:
        # Adobe has a public-facing API for trending palettes
        url = "https://color.adobe.com/api/v2/trends?locale=en_US&startIndex=0&maxNumber=100&filter=themes"
        raw = json.loads(fetch_url(url))
        for theme in raw.get("themes", []):
            colors = []
            for c in theme.get("colors", []):
                r, g, b = c.get("red", 0), c.get("green", 0), c.get("blue", 0)
                hex_val = "#{:02X}{:02X}{:02X}".format(int(r), int(g), int(b))
                colors.append(hex_val)
            if 2 <= len(colors) <= 6:
                palettes.append({"colors": colors, "likes": 0, "source": "adobe"})
        print(f"  Adobe Color: got {len(palettes)} palettes")
    except Exception as e:
        print(f"  Adobe Color: error - {e}")
    return palettes

# ============================================================
# LOL Colors
# ============================================================
def scrape_lolcolors():
    """Scrape hex codes from LOL Colors"""
    palettes = []
    try:
        html = fetch_url("https://www.lolcolors.com/")
        # Find hex color codes in the HTML
        hex_matches = re.findall(r'#([0-9A-Fa-f]{6})', html)
        # Group them into palettes (LOL Colors typically shows groups of 5)
        chunk_size = 5
        for i in range(0, len(hex_matches) - chunk_size + 1, chunk_size):
            chunk = hex_matches[i:i+chunk_size]
            colors = ["#" + c.upper() for c in chunk]
            if 2 <= len(colors) <= 6:
                palettes.append({"colors": colors, "likes": 0, "source": "lolcolors"})
        print(f"  LOL Colors: got {len(palettes)} palettes")
    except Exception as e:
        print(f"  LOL Colors: error - {e}")
    return palettes

# ============================================================
# Design Seeds
# ============================================================
def scrape_designseeds():
    """Scrape hex codes from Design Seeds"""
    palettes = []
    try:
        html = fetch_url("https://www.design-seeds.com/")
        hex_matches = re.findall(r'#([0-9A-Fa-f]{6})', html)
        chunk_size = 4
        for i in range(0, len(hex_matches) - chunk_size + 1, chunk_size):
            chunk = hex_matches[i:i+chunk_size]
            colors = ["#" + c.upper() for c in chunk]
            if 2 <= len(colors) <= 6:
                palettes.append({"colors": colors, "likes": 0, "source": "designseeds"})
        print(f"  Design Seeds: got {len(palettes)} palettes")
    except Exception as e:
        print(f"  Design Seeds: error - {e}")
    return palettes

# ============================================================
# Dedup and merge
# ============================================================
def dedup_palettes(palettes):
    """Deduplicate palettes by sorted color tuple"""
    seen = set()
    unique = []
    for p in palettes:
        key = tuple(sorted(c.upper() for c in p["colors"]))
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique

def load_existing():
    """Load existing palettes from disk"""
    if RAW_PALETTES.exists():
        with open(RAW_PALETTES, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_palettes(palettes):
    """Save palettes to disk"""
    palettes.sort(key=lambda x: x["likes"], reverse=True)
    with open(RAW_PALETTES, "w", encoding="utf-8") as f:
        json.dump(palettes, f, ensure_ascii=False, indent=2)

# ============================================================
# Main
# ============================================================
def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing
    existing = load_existing()
    existing_count = len(existing)
    print(f"=== 已有 {existing_count} 组色卡 ===\n")

    # Build dedup set from existing
    seen = set()
    for p in existing:
        seen.add(tuple(sorted(c.upper() for c in p["colors"])))

    all_new = []
    reports = []

    # 1. Colour Lovers
    print("--- Colour Lovers ---")
    try:
        cl = scrape_colourlovers(pages=3, per_page=100)
        new_cl = [p for p in cl if tuple(sorted(c.upper() for c in p["colors"])) not in seen]
        for p in new_cl:
            seen.add(tuple(sorted(c.upper() for c in p["colors"])))
        all_new.extend(new_cl)
        reports.append(("Colour Lovers", len(new_cl)))
        print(f"  => {len(new_cl)} new palettes\n")
    except Exception as e:
        reports.append(("Colour Lovers", f"FAILED: {e}"))
        print(f"  => FAILED: {e}\n")

    # 2. Colormind
    print("--- Colormind ---")
    try:
        cm = scrape_colormind(iterations=30)
        new_cm = [p for p in cm if tuple(sorted(c.upper() for c in p["colors"])) not in seen]
        for p in new_cm:
            seen.add(tuple(sorted(c.upper() for c in p["colors"])))
        all_new.extend(new_cm)
        reports.append(("Colormind", len(new_cm)))
        print(f"  => {len(new_cm)} new palettes\n")
    except Exception as e:
        reports.append(("Colormind", f"FAILED: {e}"))
        print(f"  => FAILED: {e}\n")

    # 3. Adobe Color
    print("--- Adobe Color ---")
    try:
        ad = scrape_adobe_color()
        new_ad = [p for p in ad if tuple(sorted(c.upper() for c in p["colors"])) not in seen]
        for p in new_ad:
            seen.add(tuple(sorted(c.upper() for c in p["colors"])))
        all_new.extend(new_ad)
        reports.append(("Adobe Color", len(new_ad)))
        print(f"  => {len(new_ad)} new palettes\n")
    except Exception as e:
        reports.append(("Adobe Color", f"FAILED: {e}"))
        print(f"  => FAILED: {e}\n")

    # 4. LOL Colors
    print("--- LOL Colors ---")
    try:
        lc = scrape_lolcolors()
        new_lc = [p for p in lc if tuple(sorted(c.upper() for c in p["colors"])) not in seen]
        for p in new_lc:
            seen.add(tuple(sorted(c.upper() for c in p["colors"])))
        all_new.extend(new_lc)
        reports.append(("LOL Colors", len(new_lc)))
        print(f"  => {len(new_lc)} new palettes\n")
    except Exception as e:
        reports.append(("LOL Colors", f"FAILED: {e}"))
        print(f"  => FAILED: {e}\n")

    # 5. Design Seeds
    print("--- Design Seeds ---")
    try:
        ds = scrape_designseeds()
        new_ds = [p for p in ds if tuple(sorted(c.upper() for c in p["colors"])) not in seen]
        for p in new_ds:
            seen.add(tuple(sorted(c.upper() for c in p["colors"])))
        all_new.extend(new_ds)
        reports.append(("Design Seeds", len(new_ds)))
        print(f"  => {len(new_ds)} new palettes\n")
    except Exception as e:
        reports.append(("Design Seeds", f"FAILED: {e}"))
        print(f"  => FAILED: {e}\n")

    # Merge and save
    combined = existing + all_new
    final = dedup_palettes(combined)
    save_palettes(final)

    # Report
    print("=" * 50)
    print("=== SCRAPE REPORT ===")
    print("=" * 50)
    for name, count in reports:
        status = count if isinstance(count, int) else count
        print(f"  {name}: +{status} palettes")
    print(f"\n  Existing: {existing_count}")
    print(f"  New added: {len(all_new)}")
    print(f"  Final total: {len(final)}")
    print(f"  Saved to: {RAW_PALETTES}")

    # Stats
    by_source = {}
    for p in final:
        src = p.get("source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1
    print(f"\n  By source:")
    for src, cnt in sorted(by_source.items()):
        print(f"    {src}: {cnt}")

    by_count = {}
    for p in final:
        n = len(p["colors"])
        by_count[n] = by_count.get(n, 0) + 1
    print(f"\n  By color count:")
    for n, cnt in sorted(by_count.items()):
        print(f"    {n} colors: {cnt}")

if __name__ == "__main__":
    main()
