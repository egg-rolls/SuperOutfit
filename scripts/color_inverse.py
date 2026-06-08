#!/usr/bin/env python3
"""
色彩反向推导工具

给定部分颜色和目标分数，推导应该补全的颜色。

用法：
  python color_inverse.py --known "#F5F0E8,#111111" --target 75 --missing 2
"""

import json
import math
import os
from pathlib import Path

from paths import get_data_dir
SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = get_data_dir()
SCORED_PALETTES = DATA_DIR / "scored_palettes.json"


def hex_to_hsl(hex_str):
    """HEX → HSL"""
    import colorsys
    h = hex_str.strip().lstrip("#")
    r, g, b = int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255
    h_val, l, s = colorsys.rgb_to_hls(r, g, b)
    return h_val * 360, s * 100, l * 100


def color_distance(hex1, hex2):
    """两个颜色的距离（简单欧氏距离）"""
    r1, g1, b1 = int(hex1[1:3], 16), int(hex1[3:5], 16), int(hex1[5:7], 16)
    r2, g2, b2 = int(hex2[1:3], 16), int(hex2[3:5], 16), int(hex2[5:7], 16)
    return math.sqrt((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2)


def contains_known_colors(palette_colors, known_colors, threshold=50):
    """检查色卡是否包含已知颜色（允许一定误差）"""
    for known in known_colors:
        found = False
        for palette_color in palette_colors:
            if color_distance(known, palette_color) < threshold:
                found = True
                break
        if not found:
            return False
    return True


def get_missing_colors(palette_colors, known_colors, threshold=50):
    """获取补全的颜色（排除已知颜色）"""
    missing = []
    for palette_color in palette_colors:
        is_known = False
        for known in known_colors:
            if color_distance(known, palette_color) < threshold:
                is_known = True
                break
        if not is_known:
            missing.append(palette_color)
    return missing


def search_palettes(known_colors, target_score, missing_count, tolerance=10):
    """
    搜索满足条件的色卡
    
    参数：
        known_colors: 已知颜色列表
        target_score: 目标分数
        missing_count: 需要补全的颜色数量
        tolerance: 分数容差
    
    返回：
        匹配的色卡列表
    """
    if not SCORED_PALETTES.exists():
        print(f"错误：找不到色卡数据 {SCORED_PALETTES}")
        return []
    
    with open(SCORED_PALETTES, "r", encoding="utf-8") as f:
        palettes = json.load(f)
    
    print(f"加载 {len(palettes)} 组色卡")
    
    # 筛选条件
    results = []
    for palette in palettes:
        colors = palette["colors"]
        score = palette["score"]
        
        # 1. 检查颜色数量（已知 + 补全 = 总数）
        if len(colors) != len(known_colors) + missing_count:
            continue
        
        # 2. 检查分数是否在目标范围内
        if abs(score - target_score) > tolerance:
            continue
        
        # 3. 检查是否包含已知颜色
        if not contains_known_colors(colors, known_colors):
            continue
        
        # 4. 获取补全的颜色
        missing = get_missing_colors(colors, known_colors)
        
        results.append({
            "colors": colors,
            "missing": missing,
            "score": score,
            "source": palette.get("source", "unknown"),
        })
    
    # 按分数接近程度排序
    results.sort(key=lambda x: abs(x["score"] - target_score))
    
    return results


def suggest_colors(known_colors, target_score, missing_count, top_n=5):
    """
    建议补全的颜色
    
    参数：
        known_colors: 已知颜色列表
        target_score: 目标分数
        missing_count: 需要补全的颜色数量
        top_n: 返回前 N 个建议
    
    返回：
        颜色建议列表
    """
    print(f"\n=== 色彩反向推导 ===")
    print(f"已知颜色：{known_colors}")
    print(f"目标分数：{target_score}")
    print(f"需要补全：{missing_count} 个颜色")
    
    # 搜索匹配的色卡
    results = search_palettes(known_colors, target_score, missing_count)
    
    if not results:
        print("\n未找到匹配的色卡，尝试扩大搜索范围...")
        results = search_palettes(known_colors, target_score, missing_count, tolerance=20)
    
    if not results:
        print("\n仍未找到匹配的色卡")
        return []
    
    print(f"\n找到 {len(results)} 组匹配的色卡")
    print(f"\n前 {min(top_n, len(results))} 个建议：")
    
    suggestions = []
    for i, result in enumerate(results[:top_n]):
        print(f"\n--- 建议 {i+1} ---")
        print(f"完整配色：{result['colors']}")
        print(f"补全颜色：{result['missing']}")
        print(f"分数：{result['score']:.1f}")
        print(f"来源：{result['source']}")
        
        suggestions.append({
            "missing": result["missing"],
            "score": result["score"],
            "full_palette": result["colors"],
        })
    
    return suggestions


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="色彩反向推导工具")
    parser.add_argument("--known", required=True, help="已知颜色（逗号分隔的 HEX）")
    parser.add_argument("--target", type=float, required=True, help="目标分数")
    parser.add_argument("--missing", type=int, required=True, help="需要补全的颜色数量")
    parser.add_argument("--top", type=int, default=5, help="返回前 N 个建议")
    
    args = parser.parse_args()
    
    known_colors = [c.strip() for c in args.known.split(",")]
    suggest_colors(known_colors, args.target, args.missing, args.top)
