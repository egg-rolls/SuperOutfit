#!/usr/bin/env python3
"""
SuperOutfit 首次安装脚本
用法：python scripts/init_data.py

初始化空的 data/ 目录结构，用户可以立即开始添加衣物。
"""

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATES_DIR = PROJECT_ROOT / "scripts" / "templates"

DIRS = [
    "items",
    "outfits",
    "images",
    "outfit_images",
    "archive",
]

INIT_FILES = {
    "wardrobe_index.yaml": """# 衣物索引（自动生成，请勿手动编辑）
total_items: 0
total_value: 0
last_updated: ""
categories: {}
stats:
  most_worn: null
  least_worn: null
  newest: null
""",
    "history.yaml": """# 穿搭历史
records: []
""",
    "preferences.yaml": """# AI 学习偏好（自动维护）
frequent_items: []
neglected_items: []
favorite_combos: []
avoided_combos: []
weekday_preferences: {}
weekend_preferences: {}
occasion_patterns: {}
learned_colors: []
seasonal_transition: {}
notes: []
updated_at: ""
""",
}

def main():
    print("=== SuperOutfit 初始化 ===\n")

    # 创建目录
    for d in DIRS:
        path = DATA_DIR / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"  [dir]  data/{d}/")

    # 创建初始文件
    for filename, content in INIT_FILES.items():
        path = DATA_DIR / filename
        if path.exists():
            print(f"  [skip] data/{filename} (已存在)")
        else:
            path.write_text(content, encoding="utf-8")
            print(f"  [new]  data/{filename}")

    # 复制模板
    for template in TEMPLATES_DIR.glob("*.yaml"):
        dest = DATA_DIR / template.name
        if not dest.exists():
            shutil.copy2(template, dest)
            print(f"  [copy] {template.name} → data/{template.name}")

    print(f"\n初始化完成！数据目录：{DATA_DIR}")
    print("\n下一步：")
    print("  1. 编辑 data/profile.yaml 填写你的个人信息")
    print("  2. 添加衣物：superoutfit wardrobe add --help")
    print("  3. 或直接把衣物图片拖到 data/images/ 目录")

if __name__ == "__main__":
    main()
