#!/usr/bin/env python3
"""
SuperOutfit 搭配评分工具
用法：python scorer.py --items item_001,item_020,item_040 [--occasion 办公] [--temp 22]

对一组衣物进行搭配评分，输出各维度分数和综合分。
"""

import argparse
import json
import os
import subprocess
import sys
import yaml
from pathlib import Path

DATA_DIR = Path(os.environ.get("SUPEROUTFIT_DATA", Path(__file__).resolve().parent.parent / "data"))
ITEMS_DIR = DATA_DIR / "items"
PROFILE_FILE = DATA_DIR / "profile.yaml"

# ==================== 评分规则 ====================

# 经典安全色系
SAFE_COLORS = {"白", "黑", "灰", "藏青", "深蓝", "米色", "卡其", "驼色", "深棕", "浅灰", "深灰"}

# 冲突色对
COLOR_CONFLICTS = [
    {"红", "绿"}, {"紫", "黄"}, {"橙", "蓝"},
    {"粉", "红"}, {"荧光绿", "任意"},
]

# 风格兼容矩阵（1.0 = 完美兼容，0.0 = 完全冲突）
STYLE_COMPAT = {
    ("简约", "通勤"): 1.0,
    ("简约", "日系"): 0.9,
    ("简约", "轻熟"): 0.85,
    ("通勤", "轻熟"): 0.95,
    ("通勤", "商务"): 1.0,
    ("运动", "正装"): 0.1,
    ("运动", "通勤"): 0.3,
    ("街头", "正装"): 0.2,
    ("街头", "通勤"): 0.3,
    ("街头", "简约"): 0.5,
    ("日系", "通勤"): 0.8,
    ("日系", "简约"): 0.9,
}

def load_item(item_id):
    """加载衣物"""
    path = ITEMS_DIR / f"{item_id}.yaml"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_profile():
    """加载用户画像"""
    if not PROFILE_FILE.exists():
        return None
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ==================== 评分维度 ====================

def color_score(items):
    """颜色协调性评分 (0-100) — 基于 HSL 数学模型"""
    try:
        from scripts.color_math import outfit_color_score_v2, get_item_hex_list
        hex_list = []
        for item in items:
            hex_list.extend(get_item_hex_list(item))
        if hex_list:
            return outfit_color_score_v2(hex_list)
    except Exception:
        pass
    # 降级到简单规则
    colors = set()
    for item in items:
        primary = item.get("colors", {}).get("primary", "")
        if primary:
            colors.add(primary)
    if not colors:
        return 50
    if colors.issubset(SAFE_COLORS):
        return 90
    for conflict in COLOR_CONFLICTS:
        if conflict.issubset(colors):
            return 20
    non_safe = colors - SAFE_COLORS
    if len(non_safe) <= 1:
        return 70
    return 50

def style_score(items):
    """风格一致性评分 (0-100)"""
    all_styles = set()
    for item in items:
        all_styles.update(item.get("style", []))
    
    if not all_styles:
        return 50
    
    # 检查风格冲突
    min_compat = 1.0
    style_list = list(all_styles)
    for i, s1 in enumerate(style_list):
        for s2 in style_list[i+1:]:
            compat = STYLE_COMPAT.get((s1, s2), STYLE_COMPAT.get((s2, s1), 0.7))
            min_compat = min(min_compat, compat)
    
    return min_compat * 100

def occasion_score(items, occasion):
    """场合匹配度 (0-100)"""
    if not occasion:
        return 50
    
    match_count = sum(1 for item in items if occasion in item.get("occasion", []))
    return (match_count / len(items)) * 100 if items else 0

def weather_score(items, temp):
    """天气适配度 (0-100)"""
    if temp is None:
        return 50
    
    match_count = 0
    for item in items:
        temp_range = item.get("temperature_range", "0~40")
        if isinstance(temp_range, str):
            try:
                parts = temp_range.replace("℃", "").replace("～", "~").split("~")
                low, high = int(parts[0].strip()), int(parts[1].strip())
            except (ValueError, IndexError):
                low, high = 0, 40
        else:
            low, high = 0, 40
        
        if low <= temp <= high:
            match_count += 1
    
    return (match_count / len(items)) * 100 if items else 0

def freshness_score(items):
    """穿搭新鲜度 (0-100) — 鼓励穿少穿的衣物"""
    if not items:
        return 50
    
    avg_wear = sum(item.get("wear_count", 0) for item in items) / len(items)
    
    if avg_wear < 3:
        return 100
    elif avg_wear < 10:
        return 70
    elif avg_wear < 20:
        return 40
    else:
        return 20

def preference_score(items, profile):
    """用户偏好匹配度 (0-100)"""
    if not profile:
        return 50
    
    loved_colors = set(profile.get("colors", {}).get("love", []))
    preferred_styles = set(profile.get("style", {}).get("primary", []))
    
    color_match = 0
    style_match = 0
    
    for item in items:
        item_color = item.get("colors", {}).get("primary", "")
        if item_color in loved_colors:
            color_match += 1
        
        item_styles = set(item.get("style", []))
        if item_styles.intersection(preferred_styles):
            style_match += 1
    
    color_pct = (color_match / len(items)) * 100 if items else 0
    style_pct = (style_match / len(items)) * 100 if items else 0
    
    return (color_pct + style_pct) / 2

# ==================== 综合评分 ====================

def score_outfit(item_ids, occasion=None, temp=None):
    """综合评分"""
    items = []
    missing = []
    for item_id in item_ids:
        item = load_item(item_id)
        if item:
            items.append(item)
        else:
            missing.append(item_id)
    
    if not items:
        return {"error": "没有找到任何有效衣物"}
    
    profile = load_profile()
    
    scores = {
        "color": round(color_score(items), 1),
        "style": round(style_score(items), 1),
        "occasion": round(occasion_score(items, occasion), 1),
        "weather": round(weather_score(items, temp), 1),
        "freshness": round(freshness_score(items), 1),
        "preference": round(preference_score(items, profile), 1),
    }
    
    weights = {
        "color": 0.25,
        "style": 0.20,
        "occasion": 0.20,
        "weather": 0.15,
        "freshness": 0.10,
        "preference": 0.10,
    }
    
    total = round(sum(scores[k] * weights[k] for k in scores), 1)
    
    # 等级
    if total >= 85:
        grade = "A"
        comment = "非常出色的搭配！"
    elif total >= 70:
        grade = "B"
        comment = "不错的搭配"
    elif total >= 55:
        grade = "C"
        comment = "中规中矩，可以优化"
    elif total >= 40:
        grade = "D"
        comment = "建议调整部分衣物"
    else:
        grade = "E"
        comment = "搭配存在明显问题"
    
    result = {
        "items": item_ids,
        "valid_items": [i["id"] for i in items],
        "missing_items": missing,
        "total_score": total,
        "grade": grade,
        "comment": comment,
        "scores": scores,
        "weights": weights,
        "occasion": occasion,
        "temperature": temp,
    }
    
    return result

def main():
    parser = argparse.ArgumentParser(description="SuperOutfit 搭配评分")
    parser.add_argument("--items", required=True, help="衣物 ID，逗号分隔")
    parser.add_argument("--occasion", help="场合")
    parser.add_argument("--temp", type=float, help="当前温度")
    
    args = parser.parse_args()
    item_ids = [s.strip() for s in args.items.split(",")]
    
    result = score_outfit(item_ids, args.occasion, args.temp)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
