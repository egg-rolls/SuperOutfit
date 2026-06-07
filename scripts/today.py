#!/usr/bin/env python3
"""
今日穿搭推荐快捷命令

根据天气和衣橱数据，快速推荐今日穿搭。

用法：
  python today.py
  python today.py --city 大连
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("SUPEROUTFIT_DATA", SKILL_DIR / "data"))


def load_profile():
    """加载用户配置"""
    import yaml
    profile_path = DATA_DIR / "profile.yaml"
    if not profile_path.exists():
        return None
    with open(profile_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_wardrobe():
    """加载衣橱数据"""
    items_dir = DATA_DIR / "items"
    if not items_dir.exists():
        return []
    
    items = []
    for item_file in sorted(items_dir.glob("*.yaml")):
        import yaml
        with open(item_file, "r", encoding="utf-8") as f:
            item = yaml.safe_load(f)
            if item:
                item["id"] = item_file.stem
                items.append(item)
    return items


def get_weather(city="大连"):
    """获取天气信息"""
    try:
        from weather import get_weather as fetch_weather
        return fetch_weather(city)
    except Exception:
        return None


def recommend_outfit(items, weather=None, profile=None):
    """
    根据天气和衣橱推荐穿搭
    
    简单规则：
    1. 根据温度选择衣物厚度
    2. 根据天气选择是否需要外套
    3. 根据用户风格偏好筛选
    """
    if not items:
        return None
    
    # 获取当前温度
    temp = 20  # 默认温度
    if weather and "temp" in weather:
        temp = weather["temp"]
    
    # 根据温度筛选合适的衣物
    suitable_items = []
    for item in items:
        seasons = item.get("season", [])
        if isinstance(seasons, str):
            seasons = [s.strip() for s in seasons.split(",")]
        
        # 根据温度判断季节
        if temp < 10:
            season = "冬季"
        elif temp < 20:
            season = "秋季"
        elif temp < 28:
            season = "春季"
        else:
            season = "夏季"
        
        if season in seasons or "四季" in seasons:
            suitable_items.append(item)
    
    if not suitable_items:
        suitable_items = items
    
    # 按类型分组
    by_type = {}
    for item in suitable_items:
        item_type = item.get("type", "未知")
        if item_type not in by_type:
            by_type[item_type] = []
        by_type[item_type].append(item)
    
    # 推荐搭配
    recommendation = {
        "temp": temp,
        "weather": weather,
        "items": [],
        "colors": [],
    }
    
    def get_item_color(item):
        """获取衣物颜色"""
        colors = item.get("colors", {})
        if isinstance(colors, dict):
            return colors.get("primary_hex", "#808080")
        return "#808080"
    
    def get_item_color_name(item):
        """获取衣物颜色名称"""
        colors = item.get("colors", {})
        if isinstance(colors, dict):
            return colors.get("primary", "未知")
        return "未知"
    
    # 选择上衣
    tops = by_type.get("上衣", []) + by_type.get("T恤", []) + by_type.get("衬衫", [])
    if tops:
        import random
        top = random.choice(tops)
        recommendation["items"].append({
            "item": top,
            "hex": get_item_color(top),
            "color_name": get_item_color_name(top),
        })
        recommendation["colors"].append(get_item_color(top))
    
    # 选择下装
    bottoms = by_type.get("下装", []) + by_type.get("裤子", [])
    if bottoms:
        import random
        bottom = random.choice(bottoms)
        recommendation["items"].append({
            "item": bottom,
            "hex": get_item_color(bottom),
            "color_name": get_item_color_name(bottom),
        })
        recommendation["colors"].append(get_item_color(bottom))
    
    # 选择外套（如果温度低）
    if temp < 20:
        outers = by_type.get("外套", []) + by_type.get("夹克", [])
        if outers:
            import random
            outer = random.choice(outers)
            recommendation["items"].append({
                "item": outer,
                "hex": get_item_color(outer),
                "color_name": get_item_color_name(outer),
            })
            recommendation["colors"].append(get_item_color(outer))
    
    # 选择鞋子
    shoes = by_type.get("鞋子", []) + by_type.get("运动鞋", [])
    if shoes:
        import random
        shoe = random.choice(shoes)
        recommendation["items"].append({
            "item": shoe,
            "hex": get_item_color(shoe),
            "color_name": get_item_color_name(shoe),
        })
        recommendation["colors"].append(get_item_color(shoe))
    
    return recommendation


def format_recommendation(rec):
    """格式化推荐结果"""
    if not rec:
        return "暂无推荐，请先添加衣物到衣橱"
    
    lines = []
    lines.append(f"\n{'='*50}")
    lines.append(f"🧥 今日穿搭推荐")
    lines.append(f"{'='*50}")
    
    if rec.get("weather"):
        weather = rec["weather"]
        lines.append(f"\n🌤️  天气：{weather.get('desc', '未知')}  温度：{rec['temp']}°C")
    else:
        lines.append(f"\n🌤️  温度：{rec['temp']}°C")
    
    lines.append(f"\n👔 推荐搭配：")
    lines.append(f"{'─'*50}")
    
    for item_info in rec["items"]:
        item = item_info["item"]
        hex_color = item_info["hex"]
        color_name = item_info["color_name"]
        item_type = item.get("type", "未知")
        name = item.get("name", item.get("id", ""))
        
        # 颜色方块
        try:
            r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
            block = f"\033[48;2;{r};{g};{b}m    \033[0m"
        except:
            block = "    "
        
        lines.append(f"  {block} {item_type:<6} {color_name} ({hex_color})")
        if name:
            lines.append(f"            {name}")
    
    lines.append(f"{'─'*50}")
    
    # 颜色和谐度
    if len(rec["colors"]) >= 2:
        try:
            from color_math import score_color_harmony
            score = score_color_harmony(rec["colors"])
            lines.append(f"\n🎨 配色和谐度：{score:.1f} 分")
        except:
            pass
    
    return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="今日穿搭推荐")
    parser.add_argument("--city", default=None, help="城市名称（默认从配置读取）")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    # 加载配置
    profile = load_profile()
    city = args.city
    if not city and profile:
        city = profile.get("city", "大连")
    if not city:
        city = "大连"
    
    # 加载衣橱
    items = load_wardrobe()
    if not items:
        print("❌ 衣橱为空，请先添加衣物：")
        print("   superoutfit wardrobe add")
        return
    
    # 获取天气
    weather = get_weather(city)
    
    # 推荐穿搭
    rec = recommend_outfit(items, weather, profile)
    
    if args.json:
        # JSON 输出
        output = {
            "city": city,
            "temp": rec.get("temp"),
            "weather": rec.get("weather"),
            "items": [{
                "id": item.get("id"),
                "type": item.get("type"),
                "color": item.get("primary_color"),
                "hex": item.get("primary_hex"),
            } for item in rec.get("items", [])],
            "colors": rec.get("colors", []),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(format_recommendation(rec))


if __name__ == "__main__":
    main()
