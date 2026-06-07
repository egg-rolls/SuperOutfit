#!/usr/bin/env python3
"""
首次使用引导

引导用户完成初始配置。

用法：
  python init_guide.py
  python init_guide.py --quick  # 快速模式（使用默认值）
"""

import os
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("SUPEROUTFIT_DATA", SKILL_DIR / "data"))


def print_banner():
    """打印欢迎横幅"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🧥 SuperOutfit — AI 智能穿搭顾问                           ║
║                                                              ║
║   欢迎使用！让我们快速完成初始配置。                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def ask_question(prompt, default=None, options=None):
    """
    询问用户问题
    
    参数：
        prompt: 提示信息
        default: 默认值
        options: 选项列表
    """
    if options:
        print(f"\n{prompt}")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        
        while True:
            choice = input(f"\n请选择 [1-{len(options)}]: ").strip()
            if not choice and default:
                return default
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return options[idx]
            except ValueError:
                pass
            print(f"请输入 1-{len(options)} 之间的数字")
    else:
        if default:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "
        
        answer = input(prompt).strip()
        return answer if answer else default


def collect_user_info():
    """收集用户信息"""
    print("\n" + "="*60)
    print("📝 基本信息")
    print("="*60)
    
    name = ask_question("你的名字", default="用户")
    
    city = ask_question("你所在的城市", default="大连")
    
    height = ask_question("你的身高 (cm)", default="175")
    try:
        height = int(height)
    except ValueError:
        height = 175
    
    weight = ask_question("你的体重 (kg)", default="70")
    try:
        weight = int(weight)
    except ValueError:
        weight = 70
    
    print("\n" + "="*60)
    print("🎨 风格偏好")
    print("="*60)
    
    styles = ask_question(
        "你的穿衣风格（可多选）",
        options=["休闲", "商务", "运动", "简约", "复古", "工装", "日系", "韩系"]
    )
    
    print("\n" + "="*60)
    print("💰 预算设置")
    print("="*60)
    
    budget_top = ask_question("上衣预算 (元)", default="200")
    try:
        budget_top = int(budget_top)
    except ValueError:
        budget_top = 200
    
    budget_bottom = ask_question("下装预算 (元)", default="300")
    try:
        budget_bottom = int(budget_bottom)
    except ValueError:
        budget_bottom = 300
    
    budget_outer = ask_question("外套预算 (元)", default="500")
    try:
        budget_outer = int(budget_outer)
    except ValueError:
        budget_outer = 500
    
    return {
        "name": name,
        "city": city,
        "height": height,
        "weight": weight,
        "styles": [styles] if isinstance(styles, str) else styles,
        "budget": {
            "top": budget_top,
            "bottom": budget_bottom,
            "outer": budget_outer,
        },
    }


def create_profile(user_info):
    """创建用户配置文件"""
    import yaml
    
    profile_path = DATA_DIR / "profile.yaml"
    
    # 确保目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 创建配置
    profile = {
        "name": user_info["name"],
        "city": user_info["city"],
        "height": user_info["height"],
        "weight": user_info["weight"],
        "styles": user_info["styles"],
        "preferred_colors": ["黑白灰"],
        "budget": user_info["budget"],
    }
    
    # 写入文件
    with open(profile_path, "w", encoding="utf-8") as f:
        yaml.dump(profile, f, allow_unicode=True, default_flow_style=False)
    
    print(f"\n✅ 配置已保存：{profile_path}")
    
    return profile


def create_data_structure():
    """创建数据目录结构"""
    dirs = [
        DATA_DIR / "items",
        DATA_DIR / "images",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录：{d}")


def print_next_steps():
    """打印后续步骤"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎉 初始化完成！                                            ║
║                                                              ║
║   下一步：                                                   ║
║                                                              ║
║   1. 添加衣物到衣橱                                          ║
║      superoutfit wardrobe add                                ║
║                                                              ║
║   2. 查看今日推荐                                            ║
║      superoutfit recommend today                             ║
║                                                              ║
║   3. 查看衣橱统计                                            ║
║      superoutfit config stats                                ║
║                                                              ║
║   4. 查看帮助                                                ║
║      superoutfit --help                                      ║
║                                                              ║
║   更多命令：                                                 ║
║      superoutfit color show "#FF0000"  # 查看颜色信息         ║
║      superoutfit inverse --help       # 反向推导颜色          ║
║      superoutfit palette list         # 查看色卡              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="首次使用引导")
    parser.add_argument("--quick", action="store_true", help="快速模式（使用默认值）")
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.quick:
        # 快速模式：使用默认值
        user_info = {
            "name": "用户",
            "city": "大连",
            "height": 175,
            "weight": 70,
            "styles": ["休闲"],
            "budget": {
                "top": 200,
                "bottom": 300,
                "outer": 500,
            },
        }
        print("使用默认配置...")
    else:
        # 交互模式
        user_info = collect_user_info()
    
    # 创建数据结构
    create_data_structure()
    
    # 创建配置文件
    create_profile(user_info)
    
    # 打印后续步骤
    print_next_steps()


if __name__ == "__main__":
    main()
