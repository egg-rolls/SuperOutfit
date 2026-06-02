#!/usr/bin/env python3
"""
SuperOutfit 首次安装脚本
用法：python setup.py

初始化空的 data/ 目录结构，用户可以立即开始添加衣物。
"""

import shutil
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
DATA_DIR = SKILL_DIR / "data"
TEMPLATES_DIR = SKILL_DIR / "templates"

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

    # Create directories
    for d in DIRS:
        path = DATA_DIR / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"  [dir]  data/{d}/")

    # Create initial files (only if not exist)
    for filename, content in INIT_FILES.items():
        path = DATA_DIR / filename
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            print(f"  [file] data/{filename}")
        else:
            print(f"  [skip] data/{filename} (已存在)")

    # Copy profile template (only if not exist)
    profile_dst = DATA_DIR / "profile.yaml"
    if not profile_dst.exists():
        profile_src = TEMPLATES_DIR / "profile_template.yaml"
        if profile_src.exists():
            shutil.copy2(profile_src, profile_dst)
            print(f"  [file] data/profile.yaml (从模板复制)")
        else:
            profile_dst.write_text("# 请填写你的用户画像\n", encoding="utf-8")
            print(f"  [file] data/profile.yaml (空文件)")
    else:
        print(f"  [skip] data/profile.yaml (已存在)")

    print(f"\n初始化完成！数据目录：{DATA_DIR}")
    print("\n下一步：")
    print("  1. 编辑 data/profile.yaml 填写你的个人信息")
    print("  2. 添加衣物：python scripts/wardrobe_ops.py add --help")
    print("  3. 或直接把衣物图片拖到 data/images/ 目录")

if __name__ == "__main__":
    main()
