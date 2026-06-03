#!/usr/bin/env python3
"""
SuperOutfit Skill 安装脚本
将 SKILL.md + references/ 复制到 Hermes skill 目录

用法：python scripts/install_skill.py
"""

import shutil
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
SKILL_DIR = HERMES_HOME / "skills" / "productivity" / "superoutfit"

def main():
    print("=== SuperOutfit Skill 安装 ===\n")

    # 确认源文件存在
    skill_md = PROJECT_ROOT / "SKILL.md"
    refs_dir = PROJECT_ROOT / "references"

    if not skill_md.exists():
        print(f"错误：找不到 {skill_md}")
        return

    # 创建目标目录
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    target_refs = SKILL_DIR / "references"

    # 复制 SKILL.md
    shutil.copy2(skill_md, SKILL_DIR / "SKILL.md")
    print(f"  + SKILL.md → {SKILL_DIR / 'SKILL.md'}")

    # 复制 references/
    if refs_dir.exists():
        if target_refs.exists():
            shutil.rmtree(target_refs)
        shutil.copytree(refs_dir, target_refs)
        ref_count = len(list(target_refs.glob("*.md")))
        print(f"  + references/ ({ref_count} 个文件) → {target_refs}")

    print(f"\n安装完成！")
    print(f"  Skill 目录：{SKILL_DIR}")
    print(f"\nHermes 用户运行：hermes curator pin superoutfit")
    print(f"其他 Agent：在项目目录中对 AI 说 '阅读 SKILL.md'")

    # 生成 MCP 配置示例
    mcp_config = f"""{{
  "mcpServers": {{
    "superoutfit": {{
      "command": "python",
      "args": ["{PROJECT_ROOT / 'server.py'}"]
    }}
  }}
}}"""
    
    mcp_example = PROJECT_ROOT / ".mcp.json.example"
    mcp_example.write_text(mcp_config, encoding="utf-8")
    print(f"\nMCP 配置示例已生成：{mcp_example}")
    print(f"复制到你的 Agent 配置目录即可使用 MCP 工具")

if __name__ == "__main__":
    main()
