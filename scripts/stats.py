#!/usr/bin/env python3
"""
衣橱统计快捷命令

快速查看衣橱统计信息。

用法：
  python stats.py
  python stats.py --json
"""

import json
import sys
from collections import Counter
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"


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


def analyze_wardrobe(items):
    """分析衣橱数据"""
    if not items:
        return None
    
    stats = {
        "total": len(items),
        "by_type": Counter(),
        "by_color": Counter(),
        "by_season": Counter(),
        "by_style": Counter(),
        "colors": [],
    }
    
    for item in items:
        # 按类型统计
        item_type = item.get("type", "未知")
        stats["by_type"][item_type] += 1
        
        # 按颜色统计
        colors = item.get("colors", {})
        if isinstance(colors, dict):
            color = colors.get("primary", "未知")
            hex_color = colors.get("primary_hex")
        else:
            color = "未知"
            hex_color = None
        
        stats["by_color"][color] += 1
        
        # 收集颜色
        if hex_color:
            stats["colors"].append(hex_color)
        
        # 按季节统计
        seasons = item.get("season", [])
        if isinstance(seasons, str):
            seasons = [s.strip() for s in seasons.split(",")]
        for season in seasons:
            stats["by_season"][season] += 1
        
        # 按风格统计
        styles = item.get("style", [])
        if isinstance(styles, str):
            styles = [s.strip() for s in styles.split(",")]
        for style in styles:
            stats["by_style"][style] += 1
    
    return stats


def format_stats(stats):
    """格式化统计结果"""
    if not stats:
        return "衣橱为空，请先添加衣物：superoutfit wardrobe add"
    
    lines = []
    lines.append(f"\n{'='*50}")
    lines.append(f"📊 衣橱统计")
    lines.append(f"{'='*50}")
    
    lines.append(f"\n📦 总计：{stats['total']} 件衣物")
    
    # 按类型
    lines.append(f"\n👔 按类型：")
    lines.append(f"{'─'*50}")
    for type_name, count in stats["by_type"].most_common():
        bar = "█" * count
        lines.append(f"  {type_name:<8} {bar} {count}")
    
    # 按颜色
    lines.append(f"\n🎨 按颜色：")
    lines.append(f"{'─'*50}")
    for color, count in stats["by_color"].most_common(10):
        # 颜色方块
        hex_color = None
        for item in load_wardrobe():
            if item.get("primary_color") == color:
                hex_color = item.get("primary_hex")
                break
        
        if hex_color:
            try:
                r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
                block = f"\033[48;2;{r};{g};{b}m  \033[0m"
            except:
                block = "  "
        else:
            block = "  "
        
        bar = "█" * count
        lines.append(f"  {block} {color:<6} {bar} {count}")
    
    # 按季节
    lines.append(f"\n🌤️  按季节：")
    lines.append(f"{'─'*50}")
    for season, count in stats["by_season"].most_common():
        bar = "█" * count
        lines.append(f"  {season:<6} {bar} {count}")
    
    # 按风格
    if stats["by_style"]:
        lines.append(f"\n✨ 按风格：")
        lines.append(f"{'─'*50}")
        for style, count in stats["by_style"].most_common():
            bar = "█" * count
            lines.append(f"  {style:<8} {bar} {count}")
    
    # 配色分析
    if len(stats["colors"]) >= 2:
        lines.append(f"\n🎨 配色分析：")
        lines.append(f"{'─'*50}")
        
        try:
            from color_math import score_color_harmony
            score = score_color_harmony(stats["colors"][:5])  # 取前5个颜色
            lines.append(f"  整体配色和谐度：{score:.1f} 分")
        except:
            pass
        
        # 颜色多样性
        unique_colors = len(stats["by_color"])
        lines.append(f"  颜色种类：{unique_colors} 种")
        
        if unique_colors < 3:
            lines.append(f"  💡 建议：颜色较少，可以尝试添加一些有彩色")
        elif unique_colors > 8:
            lines.append(f"  💡 建议：颜色较多，可以尝试统一风格")
    
    return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="衣橱统计")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    # 加载衣橱
    items = load_wardrobe()
    
    # 分析统计
    stats = analyze_wardrobe(items)
    
    if args.json:
        # JSON 输出
        output = {
            "total": stats["total"] if stats else 0,
            "by_type": dict(stats["by_type"]) if stats else {},
            "by_color": dict(stats["by_color"]) if stats else {},
            "by_season": dict(stats["by_season"]) if stats else {},
            "by_style": dict(stats["by_style"]) if stats else {},
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(format_stats(stats))


if __name__ == "__main__":
    main()
