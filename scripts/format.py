#!/usr/bin/env python3
"""
输出格式化模块

提供表格和颜色格式化功能。

用法：
  from format import print_table, print_color_block, format_item
"""

import sys


def print_table(headers, rows, max_width=80):
    """
    打印表格
    
    参数：
        headers: 表头列表
        rows: 数据行列表
        max_width: 最大宽度
    """
    if not rows:
        print("（无数据）")
        return
    
    # 计算列宽
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # 限制总宽度
    total_width = sum(col_widths) + len(headers) * 3 + 1
    if total_width > max_width:
        # 按比例缩小
        ratio = max_width / total_width
        col_widths = [int(w * ratio) for w in col_widths]
    
    # 打印表头
    header_line = "│"
    for i, h in enumerate(headers):
        header_line += f" {h:<{col_widths[i]}} │"
    
    separator = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
    header_sep = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
    footer = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"
    
    print(separator)
    print(header_line)
    print(header_sep)
    
    # 打印数据行
    for row in rows:
        row_line = "│"
        for i, cell in enumerate(row):
            cell_str = str(cell)
            # 截断过长的内容
            if len(cell_str) > col_widths[i]:
                cell_str = cell_str[:col_widths[i]-1] + "…"
            row_line += f" {cell_str:<{col_widths[i]}} │"
        print(row_line)
    
    print(footer)


def print_color_block(hex_color, width=4, height=1):
    """
    打印彩色方块
    
    参数：
        hex_color: HEX 颜色值
        width: 方块宽度
        height: 方块高度
    """
    try:
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        for _ in range(height):
            print(f"\033[48;2;{r};{g};{b}m{' ' * width}\033[0m", end="")
    except:
        print(" " * width, end="")


def format_item(item):
    """
    格式化衣物信息
    
    参数：
        item: 衣物数据字典
    
    返回：
        格式化后的字符串
    """
    lines = []
    
    # 获取颜色信息
    colors = item.get("colors", {})
    if isinstance(colors, dict):
        primary_color = colors.get("primary", "未知")
        primary_hex = colors.get("primary_hex", "#808080")
    else:
        primary_color = "未知"
        primary_hex = "#808080"
    
    # 颜色方块
    try:
        r, g, b = int(primary_hex[1:3], 16), int(primary_hex[3:5], 16), int(primary_hex[5:7], 16)
        color_block = f"\033[48;2;{r};{g};{b}m    \033[0m"
    except:
        color_block = "    "
    
    # 基本信息
    lines.append(f"{color_block} {item.get('type', '未知'):<6} {primary_color} ({primary_hex})")
    
    # 详细信息
    if item.get("sub_type"):
        lines.append(f"          子类型：{item['sub_type']}")
    if item.get("material"):
        lines.append(f"          材质：{item['material']}")
    if item.get("fit"):
        lines.append(f"          版型：{item['fit']}")
    
    return "\n".join(lines)


def format_wardrobe_list(items):
    """
    格式化衣橱列表
    
    参数：
        items: 衣物列表
    
    返回：
        格式化后的字符串
    """
    if not items:
        return "衣橱为空，请先添加衣物：superoutfit wardrobe add"
    
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"👔 衣橱列表 ({len(items)} 件)")
    lines.append(f"{'='*60}")
    
    # 按类型分组
    by_type = {}
    for item in items:
        item_type = item.get("type", "未知")
        if item_type not in by_type:
            by_type[item_type] = []
        by_type[item_type].append(item)
    
    for item_type, type_items in by_type.items():
        lines.append(f"\n{item_type} ({len(type_items)} 件)")
        lines.append(f"{'─'*60}")
        
        for item in type_items:
            lines.append(format_item(item))
    
    return "\n".join(lines)


def format_score(score_data):
    """
    格式化评分结果
    
    参数：
        score_data: 评分数据
    
    返回：
        格式化后的字符串
    """
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"📊 搭配评分")
    lines.append(f"{'='*60}")
    
    # 总分
    total_score = score_data.get("total_score", 0)
    grade = score_data.get("grade", "N/A")
    lines.append(f"\n总分：{total_score:.1f} 分 ({grade})")
    
    # 各维度分数
    dimensions = score_data.get("dimensions", {})
    if dimensions:
        lines.append(f"\n各维度评分：")
        lines.append(f"{'─'*60}")
        
        for dim, score in dimensions.items():
            bar_length = int(score / 5)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            lines.append(f"  {dim:<12} {bar} {score:.1f}")
    
    # 颜色和谐度
    color_score = score_data.get("color_score")
    if color_score:
        lines.append(f"\n🎨 颜色和谐度：{color_score:.1f} 分")
    
    return "\n".join(lines)


def format_weather(weather_data):
    """
    格式化天气信息
    
    参数：
        weather_data: 天气数据
    
    返回：
        格式化后的字符串
    """
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"🌤️  天气信息")
    lines.append(f"{'='*60}")
    
    # 基本信息
    city = weather_data.get("city", "未知")
    temp = weather_data.get("temp", {})
    condition = weather_data.get("condition", "未知")
    
    lines.append(f"\n城市：{city}")
    lines.append(f"天气：{condition}")
    
    # 温度
    if isinstance(temp, dict):
        current = temp.get("current", 0)
        max_temp = temp.get("max", 0)
        min_temp = temp.get("min", 0)
        lines.append(f"温度：{current}°C（{min_temp}°C ~ {max_temp}°C）")
    else:
        lines.append(f"温度：{temp}°C")
    
    # 穿衣建议
    advice = weather_data.get("clothing_advice", "")
    if advice:
        lines.append(f"\n💡 穿衣建议：{advice}")
    
    return "\n".join(lines)


# ==================== 测试 ====================

if __name__ == "__main__":
    # 测试表格
    print("测试表格：")
    headers = ["ID", "类型", "颜色", "材质"]
    rows = [
        ["item_001", "上衣", "米白", "冰丝缎面"],
        ["item_002", "裤子", "黑色", "棉质"],
        ["item_003", "鞋子", "白色", "网面"],
    ]
    print_table(headers, rows)
    
    print("\n测试颜色方块：")
    colors = ["#F5F0E8", "#111111", "#FF0000", "#00FF00", "#0000FF"]
    for color in colors:
        print(f"{color}: ", end="")
        print_color_block(color)
        print()
