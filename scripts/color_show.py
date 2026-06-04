#!/usr/bin/env python3
"""
颜色可视化工具

显示颜色的详细信息，包括 RGB、HSL、OKLab 等表示。

用法：
  python color_show.py "#F5F0E8"
  python color_show.py --list  # 显示常用颜色
"""

import colorsys
import math
import sys


# ==================== 颜色转换 ====================

def hex_to_rgb(hex_str):
    h = hex_str.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def hex_to_hsl(hex_str):
    r, g, b = hex_to_rgb(hex_str)
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    return h * 360, s * 100, l * 100


def hex_to_oklab(hex_str):
    r, g, b = hex_to_rgb(hex_str)
    def srgb_to_linear(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    rl, gl, bl = srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b)
    l_ = (0.4122214708*rl + 0.5363325363*gl + 0.0514459929*bl) ** (1/3)
    m_ = (0.2119034982*rl + 0.6806995451*gl + 0.1073969566*bl) ** (1/3)
    s_ = (0.0883024619*rl + 0.2817188376*gl + 0.6299787005*bl) ** (1/3)
    L = 0.2104542553*l_ + 0.7936177850*m_ - 0.0040720468*s_
    a = 1.9779984951*l_ - 2.4285922050*m_ + 0.4505937099*s_
    b_val = 0.0259040371*l_ + 0.7827717662*m_ - 0.8086757660*s_
    return L, a, b_val


def oklab_chroma(a, b):
    return (a**2 + b**2) ** 0.5


def oklab_hue(a, b):
    return math.degrees(math.atan2(b, a)) % 360


# ==================== 颜色分类 ====================

def classify_color(hex_str):
    """根据 HSL 对颜色进行分类"""
    h, s, l = hex_to_hsl(hex_str)
    
    # 无彩色
    if s < 5:
        if l < 15:
            return "黑色"
        elif l > 90:
            return "白色"
        else:
            return "灰色"
    
    # 有彩色
    if h < 15 or h >= 345:
        return "红色"
    elif h < 45:
        return "橙色"
    elif h < 75:
        return "黄色"
    elif h < 150:
        return "绿色"
    elif h < 195:
        return "青色"
    elif h < 255:
        return "蓝色"
    elif h < 285:
        return "紫色"
    elif h < 345:
        return "粉色"
    
    return "未知"


def get_color_name(hex_str):
    """获取颜色的中文名称"""
    # 常见颜色名称映射
    common_colors = {
        "#000000": "纯黑",
        "#111111": "深黑",
        "#1a1a1a": "炭黑",
        "#333333": "暗灰",
        "#666666": "中灰",
        "#808080": "灰色",
        "#999999": "浅灰",
        "#cccccc": "银灰",
        "#e0e0e0": "亮灰",
        "#f5f5f5": "烟白",
        "#ffffff": "纯白",
        "#ff0000": "纯红",
        "#00ff00": "纯绿",
        "#0000ff": "纯蓝",
        "#ffff00": "纯黄",
        "#ff00ff": "洋红",
        "#00ffff": "青色",
        "#f5f0e8": "米白",
        "#faf6f0": "象牙白",
        "#1a3a5c": "藏青",
        "#2c3e50": "深蓝灰",
        "#8b4513": "棕色",
        "#d2691e": "巧克力色",
        "#f4a460": "沙褐色",
        "#daa520": "金色",
        "#c4a97d": "卡其色",
        "#5a6b40": "军绿",
        "#228b22": "森林绿",
        "#800000": "栗色",
        "#8b0000": "深红",
        "#a52a2a": "褐色",
    }
    
    hex_lower = hex_str.lower()
    if hex_lower in common_colors:
        return common_colors[hex_lower]
    
    # 根据分类返回通用名称
    return classify_color(hex_str)


# ==================== 终端颜色输出 ====================

def print_color_block(hex_str, width=8, height=3):
    """在终端中打印彩色方块"""
    r, g, b = hex_to_rgb(hex_str)
    
    # 使用 ANSI 256 色或 24 位真彩色
    for _ in range(height):
        print(f"\033[48;2;{r};{g};{b}m{' ' * width}\033[0m")


def print_color_info(hex_str):
    """打印颜色的详细信息"""
    r, g, b = hex_to_rgb(hex_str)
    h, s, l = hex_to_hsl(hex_str)
    ok_l, ok_a, ok_b = hex_to_oklab(hex_str)
    chroma = oklab_chroma(ok_a, ok_b)
    hue = oklab_hue(ok_a, ok_b)
    color_name = get_color_name(hex_str)
    
    print(f"\n颜色信息：{hex_str}")
    print("=" * 40)
    
    # 彩色方块
    print_color_block(hex_str)
    
    print(f"\n名称：{color_name}")
    print(f"分类：{classify_color(hex_str)}")
    
    print(f"\n--- RGB ---")
    print(f"  R: {r:3d}  G: {g:3d}  B: {b:3d}")
    
    print(f"\n--- HSL ---")
    print(f"  H: {h:6.1f}°  S: {s:5.1f}%  L: {l:5.1f}%")
    
    print(f"\n--- OKLab ---")
    print(f"  L: {ok_l:.3f}  a: {ok_a:.3f}  b: {ok_b:.3f}")
    print(f"  Chroma: {chroma:.3f}  Hue: {hue:.1f}°")
    
    # 明度等级
    if l < 20:
        lightness = "很暗"
    elif l < 40:
        lightness = "暗"
    elif l < 60:
        lightness = "中等"
    elif l < 80:
        lightness = "亮"
    else:
        lightness = "很亮"
    
    # 饱和度等级
    if s < 10:
        saturation = "无彩色"
    elif s < 30:
        saturation = "低饱和"
    elif s < 60:
        saturation = "中饱和"
    elif s < 80:
        saturation = "高饱和"
    else:
        saturation = "很高饱和"
    
    print(f"\n--- 描述 ---")
    print(f"  明度：{lightness} ({l:.0f}%)")
    print(f"  饱和度：{saturation} ({s:.0f}%)")


def print_common_colors():
    """显示常用颜色列表"""
    common_colors = [
        ("#000000", "纯黑"),
        ("#111111", "深黑"),
        ("#333333", "暗灰"),
        ("#666666", "中灰"),
        ("#999999", "浅灰"),
        ("#cccccc", "银灰"),
        ("#ffffff", "纯白"),
        ("#f5f0e8", "米白"),
        ("#ff0000", "纯红"),
        ("#00ff00", "纯绿"),
        ("#0000ff", "纯蓝"),
        ("#ffff00", "纯黄"),
        ("#1a3a5c", "藏青"),
        ("#8b4513", "棕色"),
        ("#c4a97d", "卡其"),
        ("#5a6b40", "军绿"),
        ("#800000", "栗色"),
    ]
    
    print("\n常用颜色参考：")
    print("=" * 60)
    print(f"{'HEX':<10} {'名称':<8} {'色块'}")
    print("-" * 60)
    
    for hex_str, name in common_colors:
        r, g, b = hex_to_rgb(hex_str)
        block = f"\033[48;2;{r};{g};{b}m    \033[0m"
        print(f"{hex_str:<10} {name:<8} {block}")


# ==================== 主函数 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="颜色可视化工具")
    parser.add_argument("color", nargs="?", help="HEX 颜色值（如 #F5F0E8）")
    parser.add_argument("--list", action="store_true", help="显示常用颜色列表")
    
    args = parser.parse_args()
    
    if args.list:
        print_common_colors()
        return
    
    if not args.color:
        parser.print_help()
        return
    
    # 验证 HEX 格式
    hex_str = args.color.strip()
    if not hex_str.startswith("#"):
        hex_str = "#" + hex_str
    
    if len(hex_str) not in [4, 7]:
        print(f"错误：'{args.color}' 不是有效的 HEX 颜色")
        print(f"\n💡 提示：")
        print(f"  - HEX 格式：#RRGGBB（如 #FF0000）")
        print(f"  - 短格式：#RGB（如 #F00）")
        return
    
    try:
        print_color_info(hex_str)
    except ValueError as e:
        print(f"错误：'{args.color}' 不是有效的 HEX 颜色")
        print(f"\n💡 提示：HEX 值应为 0-9 和 A-F 的组合")


if __name__ == "__main__":
    main()
