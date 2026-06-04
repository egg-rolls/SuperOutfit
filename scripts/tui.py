#!/usr/bin/env python3
"""
交互式 TUI 模式

提供菜单式交互界面。

用法：
  python tui.py
  superoutfit tui
"""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"


def clear_screen():
    """清屏"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """打印横幅"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🧥 SuperOutfit — AI 智能穿搭顾问                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def print_menu():
    """打印主菜单"""
    print("""
┌──────────────────────────────────────────────────────────────┐
│  主菜单                                                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 👔 衣橱管理                                              │
│  2. 🌤️  天气查询                                              │
│  3. 🎨 穿搭推荐                                              │
│  4. 📊 搭配评分                                              │
│  5. 🎯 色彩分析                                              │
│  6. 📈 衣橱统计                                              │
│  7. ⚙️  设置                                                 │
│  0. 退出                                                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
""")


def print_submenu(title, options):
    """打印子菜单"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    
    print(f"  0. 返回主菜单")
    print(f"{'='*60}")


def get_choice(prompt="请选择", max_val=7):
    """获取用户选择"""
    while True:
        try:
            choice = input(f"\n{prompt} [0-{max_val}]: ").strip()
            if not choice:
                continue
            choice = int(choice)
            if 0 <= choice <= max_val:
                return choice
            print(f"请输入 0-{max_val} 之间的数字")
        except ValueError:
            print("请输入数字")


def wardrobe_menu():
    """衣橱管理菜单"""
    while True:
        print_submenu("👔 衣橱管理", [
            "添加衣物",
            "查看衣橱",
            "查看衣物详情",
            "更新衣物",
            "删除衣物",
        ])
        
        choice = get_choice(max_val=5)
        
        if choice == 0:
            break
        elif choice == 1:
            # 添加衣物
            print("\n添加衣物功能需要使用命令行：")
            print("  superoutfit wardrobe add")
            input("\n按 Enter 继续...")
        elif choice == 2:
            # 查看衣橱
            sys.path.insert(0, str(SKILL_DIR / "scripts"))
            from wardrobe_ops import list_items
            list_items()
            input("\n按 Enter 继续...")
        elif choice == 3:
            # 查看详情
            item_id = input("\n请输入衣物 ID（如 item_001）: ").strip()
            if item_id:
                sys.path.insert(0, str(SKILL_DIR / "scripts"))
                from wardrobe_ops import show_item
                show_item(item_id)
            input("\n按 Enter 继续...")
        elif choice == 4:
            # 更新衣物
            print("\n更新衣物功能需要使用命令行：")
            print("  superoutfit wardrobe update --item-id <ID>")
            input("\n按 Enter 继续...")
        elif choice == 5:
            # 删除衣物
            item_id = input("\n请输入衣物 ID（如 item_001）: ").strip()
            if item_id:
                confirm = input(f"确认删除 {item_id}？(y/n): ").strip().lower()
                if confirm == 'y':
                    sys.path.insert(0, str(SKILL_DIR / "scripts"))
                    from wardrobe_ops import delete_item
                    delete_item(item_id)
            input("\n按 Enter 继续...")


def weather_menu():
    """天气查询菜单"""
    print("\n查询天气...")
    
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    from config import get_city
    from weather import query_weather
    
    city = get_city()
    print(f"城市：{city}")
    
    result = query_weather(city)
    
    # 格式化输出
    temp = result.get("temp", {})
    condition = result.get("condition", "未知")
    advice = result.get("clothing_advice", "")
    
    print(f"\n天气：{condition}")
    if isinstance(temp, dict):
        print(f"温度：{temp.get('current', 0)}°C")
    print(f"\n穿衣建议：{advice}")
    
    input("\n按 Enter 继续...")


def recommend_menu():
    """穿搭推荐菜单"""
    print("\n获取今日推荐...")
    
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    from today import main as today_main
    
    today_main()
    
    input("\n按 Enter 继续...")


def score_menu():
    """搭配评分菜单"""
    print("\n搭配评分功能需要使用命令行：")
    print("  superoutfit score --items item_001,item_003")
    input("\n按 Enter 继续...")


def color_menu():
    """色彩分析菜单"""
    while True:
        print_submenu("🎯 色彩分析", [
            "查看颜色信息",
            "颜色和谐度评分",
            "反向推导颜色",
        ])
        
        choice = get_choice(max_val=3)
        
        if choice == 0:
            break
        elif choice == 1:
            # 查看颜色信息
            hex_color = input("\n请输入 HEX 颜色值（如 #F5F0E8）: ").strip()
            if hex_color:
                sys.path.insert(0, str(SKILL_DIR / "scripts"))
                from color_show import print_color_info
                print_color_info(hex_color)
            input("\n按 Enter 继续...")
        elif choice == 2:
            # 颜色和谐度评分
            colors_input = input("\n请输入颜色（逗号分隔，如 #F5F0E8,#111111）: ").strip()
            if colors_input:
                colors = [c.strip() for c in colors_input.split(",")]
                sys.path.insert(0, str(SKILL_DIR / "scripts"))
                from color_math import score_color_harmony
                score = score_color_harmony(colors)
                print(f"\n颜色和谐度：{score:.1f} 分")
            input("\n按 Enter 继续...")
        elif choice == 3:
            # 反向推导颜色
            print("\n反向推导功能需要使用命令行：")
            print("  superoutfit inverse --known '#F5F0E8,#111111' --target 75 --missing 2")
            input("\n按 Enter 继续...")


def stats_menu():
    """衣橱统计菜单"""
    print("\n获取衣橱统计...")
    
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    from stats import main as stats_main
    
    stats_main()
    
    input("\n按 Enter 继续...")


def settings_menu():
    """设置菜单"""
    while True:
        print_submenu("⚙️  设置", [
            "查看配置",
            "修改配置",
            "初始化引导",
        ])
        
        choice = get_choice(max_val=3)
        
        if choice == 0:
            break
        elif choice == 1:
            # 查看配置
            sys.path.insert(0, str(SKILL_DIR / "scripts"))
            from config import load_config
            config = load_config()
            print("\n当前配置：")
            for key, value in config.items():
                print(f"  {key}: {value}")
            input("\n按 Enter 继续...")
        elif choice == 2:
            # 修改配置
            print("\n修改配置功能需要使用命令行：")
            print("  编辑 data/profile.yaml")
            input("\n按 Enter 继续...")
        elif choice == 3:
            # 初始化引导
            sys.path.insert(0, str(SKILL_DIR / "scripts"))
            from init_guide import main as init_main
            init_main()
            input("\n按 Enter 继续...")


def main():
    """主函数"""
    while True:
        clear_screen()
        print_banner()
        print_menu()
        
        choice = get_choice()
        
        if choice == 0:
            print("\n👋 再见！")
            break
        elif choice == 1:
            wardrobe_menu()
        elif choice == 2:
            weather_menu()
        elif choice == 3:
            recommend_menu()
        elif choice == 4:
            score_menu()
        elif choice == 5:
            color_menu()
        elif choice == 6:
            stats_menu()
        elif choice == 7:
            settings_menu()


if __name__ == "__main__":
    main()
