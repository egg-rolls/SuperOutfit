#!/usr/bin/env python3
"""Scrape all color palettes from wxsecai.com / colorcollect.cn API."""

import json
import os
import sys
import time
import urllib.request

API_BASE = "https://api.colorcollect.cn/api/inspire_color_cards"

CATEGORIES = {
    8: "编辑推荐",
    5: "经典自然",
    12: "艺术配色",
    2: "西方油画",
    6: "故宫宝藏",
    13: "摄影配色",
    14: "影视配色",
    4: "万物万象",
    9: "神奇宝贝",
    7: "超级英雄",
    1: "应用配色",
    10: "采友分享",
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_FILE = os.path.join(PROJECT_DIR, "data", "raw_palettes.json")


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_colors(color_str):
    """Parse the color field which is a JSON string containing an array."""
    try:
        colors = json.loads(color_str)
        if isinstance(colors, list):
            valid = [c for c in colors if isinstance(c, str) and c.startswith("#") and len(c) == 7]
            if 2 <= len(valid) <= 6:
                return valid
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def scrape_category(cat_id, cat_name):
    """Scrape all palettes from a single category."""
    palettes = []
    page = 0
    while True:
        url = f"{API_BASE}/categories/{cat_id}/cards?page={page}"
        print(f"  Fetching page {page}...", end=" ")
        try:
            data = fetch_json(url)
        except Exception as e:
            print(f"Error: {e}")
            break

        if not data or (isinstance(data, list) and len(data) == 0):
            print("empty response, done.")
            break

        # data could be a list directly or wrapped in an object
        items = data if isinstance(data, list) else data.get("data", data)
        if not isinstance(items, list) or len(items) == 0:
            print("no items, done.")
            break

        count = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            colors = parse_colors(item.get("color", ""))
            if colors:
                palettes.append({
                    "colors": colors,
                    "likes": 0,
                    "source": "wxsecai",
                    "name": item.get("name", ""),
                    "category": cat_name,
                })
                count += 1

        print(f"got {count} valid palettes from {len(items)} items")
        page += 1
        time.sleep(0.3)

    return palettes


def main():
    # Load existing palettes
    existing = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        print(f"Loaded {len(existing)} existing palettes from {OUTPUT_FILE}")
    else:
        print(f"No existing file at {OUTPUT_FILE}, starting fresh")

    # Build dedup set from existing
    seen = set()
    for p in existing:
        key = tuple(sorted(p.get("colors", [])))
        if key:
            seen.add(key)

    all_new = []
    category_counts = {}

    for cat_id, cat_name in CATEGORIES.items():
        print(f"\nCategory {cat_id}: {cat_name}")
        palettes = scrape_category(cat_id, cat_name)
        category_counts[cat_name] = len(palettes)
        all_new.extend(palettes)

    # Deduplicate and merge
    added = 0
    for p in all_new:
        key = tuple(sorted(p["colors"]))
        if key not in seen:
            existing.append(p)
            seen.add(key)
            added += 1

    # Save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    # Report
    print("\n=== RESULTS ===")
    for cat_name, count in category_counts.items():
        print(f"  {cat_name}: {count} palettes scraped")
    print(f"\nTotal scraped from API: {len(all_new)}")
    print(f"New palettes added (after dedup): {added}")
    print(f"Total palettes now: {len(existing)}")


if __name__ == "__main__":
    main()
