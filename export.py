#!/usr/bin/env python3
"""
SuperOutfit 导出分享包
用法：python export.py

打包 skill 的可分享部分（不含个人数据），生成 zip 文件。
接收者解压后运行 python setup.py 即可使用。
"""

import zipfile
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path(__file__).resolve().parent
OUTPUT_NAME = f"superoutfit_{datetime.now().strftime('%Y%m%d')}.zip"

# 要包含的文件/目录
INCLUDE = [
    "SKILL.md",
    "README.md",
    "setup.py",
    "export.py",
    "scripts/",
    "templates/",
]

# 要排除的模式
EXCLUDE = [
    "__pycache__",
    "*.pyc",
    ".git",
]

def should_include(path: Path) -> bool:
    for pattern in EXCLUDE:
        if pattern in str(path):
            return False
    return True

def main():
    output_path = SKILL_DIR.parent / OUTPUT_NAME
    
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for pattern in INCLUDE:
            target = SKILL_DIR / pattern
            if target.is_file():
                if should_include(target):
                    arcname = f"superoutfit/{target.relative_to(SKILL_DIR)}"
                    zf.write(target, arcname)
                    print(f"  + {arcname}")
            elif target.is_dir():
                for f in target.rglob("*"):
                    if f.is_file() and should_include(f):
                        arcname = f"superoutfit/{f.relative_to(SKILL_DIR)}"
                        zf.write(f, arcname)
                        print(f"  + {arcname}")
        
        # Add empty data directory structure
        data_dirs = ["data/items", "data/outfits", "data/images", 
                     "data/outfit_images", "data/archive"]
        for d in data_dirs:
            arcname = f"superoutfit/{d}/.gitkeep"
            zf.writestr(arcname, "")
            print(f"  + {arcname}")
    
    print(f"\n导出完成：{output_path}")
    print(f"大小：{output_path.stat().st_size / 1024:.1f} KB")
    print(f"\n接收者使用方式：")
    print(f"  1. 解压到 ~/.hermes/skills/productivity/superoutfit/")
    print(f"  2. 运行 python setup.py")
    print(f"  3. 编辑 data/profile.yaml 填写个人信息")

if __name__ == "__main__":
    main()
