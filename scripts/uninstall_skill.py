#!/usr/bin/env python3
"""
SuperOutfit Skill 卸载工具
清理 ~/.agents/skills/superoutfit 和 .agent-configs

用法：python scripts/uninstall_skill.py [--yes]
"""

import os
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENTS_HOME = Path.home() / ".agents"
SKILL_DIR = AGENTS_HOME / "skills" / "superoutfit"
AGENT_CONFIGS = PROJECT_ROOT / ".agent-configs"

class Colors:
    OK = "\033[92m"
    WARN = "\033[93m"
    FAIL = "\033[91m"
    INFO = "\033[94m"
    END = "\033[0m"

def print_ok(msg): print(f"  {Colors.OK}✓{Colors.END} {msg}")
def print_warn(msg): print(f"  {Colors.WARN}⚠{Colors.END} {msg}")
def print_info(msg): print(f"  {Colors.INFO}ℹ{Colors.END} {msg}")

def remove_dir(path, name, auto_yes=False):
    """删除目录"""
    print(f"\n  清理 {name}...")
    
    if not path.exists():
        print_info(f"{name} 不存在，跳过")
        return True
    
    print_info(f"目标: {path}")
    
    if not auto_yes:
        response = input(f"  确认删除？ (y/N): ").strip().lower()
        if response not in ('y', 'yes'):
            print_warn("已跳过")
            return True
    
    try:
        shutil.rmtree(path)
        print_ok(f"{name} 已删除")
        return True
    except Exception as e:
        print_warn(f"删除失败: {e}")
        return False

def main():
    auto_yes = '--yes' in sys.argv or '-y' in sys.argv
    
    print("\n" + "="*60)
    print("  SuperOutfit Skill 卸载工具")
    print("="*60)
    print("\n将清理以下内容:")
    print(f"  - {SKILL_DIR}")
    print(f"  - {AGENT_CONFIGS}")
    
    # 执行卸载
    print("\n[1/2] 清理 Skill 目录...")
    remove_dir(SKILL_DIR, "Skill 目录", auto_yes)
    
    print("\n[2/2] 清理配置文件...")
    remove_dir(AGENT_CONFIGS, ".agent-configs", auto_yes)
    
    # 打印总结
    print("\n" + "="*60)
    print("  SuperOutfit Skill 卸载完成")
    print("="*60)
    print("\n已清理:")
    
    if not SKILL_DIR.exists():
        print(f"  ✓ {SKILL_DIR}")
    else:
        print(f"  ✗ {SKILL_DIR} (保留)")
    
    if not AGENT_CONFIGS.exists():
        print(f"  ✓ {AGENT_CONFIGS}")
    else:
        print(f"  ✗ {AGENT_CONFIGS} (保留)")
    
    print("\n注意: 项目代码和依赖未删除")
    print("如需完全卸载，请手动删除项目目录")
    print()

if __name__ == "__main__":
    main()
