#!/usr/bin/env python3
"""
SuperOutfit 导出分享包
用法：python scripts/export.py

打包 skill 的可分享部分（不含个人数据），生成 zip 文件。
接收者解压后运行 uv sync 即可使用。
"""

import zipfile
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_NAME = f"superoutfit_{datetime.now().strftime('%Y%m%d')}.zip"

# 要包含的文件/目录
INCLUDE = [
    "SKILL.md",
    "README.md",
    "AGENTS.md",
    "CLI.md",
    "LICENSE",
    "pyproject.toml",
    "superoutfit.py",
    "server.py",
    "scripts/",
    "references/",
    "docs/",
    "api/",
]

# 要排除的模式
EXCLUDE = [
    "__pycache__",
    "*.pyc",
    ".git",
    ".venv",
    "node_modules",
    "superoutfit.egg-info",
]

def should_include(path: Path) -> bool:
    for pattern in EXCLUDE:
        if pattern in str(path):
            return False
    return True

def main():
    output_path = PROJECT_ROOT / OUTPUT_NAME
    
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for pattern in INCLUDE:
            target = PROJECT_ROOT / pattern
            if target.is_file():
                if should_include(target):
                    arcname = f"superoutfit/{target.relative_to(PROJECT_ROOT)}"
                    zf.write(target, arcname)
                    print(f"  + {arcname}")
            elif target.is_dir():
                for file in target.rglob("*"):
                    if file.is_file() and should_include(file):
                        arcname = f"superoutfit/{file.relative_to(PROJECT_ROOT)}"
                        zf.write(file, arcname)
                        print(f"  + {arcname}")
    
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ 导出完成：{output_path}")
    print(f"   大小：{size_mb:.1f} MB")
    print(f"\n接收者：解压 → cd superoutfit → uv sync → 开始使用")

if __name__ == "__main__":
    main()
