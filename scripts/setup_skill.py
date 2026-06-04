#!/usr/bin/env python3
"""
SuperOutfit Skill 快速设置工具
适用于任何 AI Agent (Hermes, OpenCode, Claude Code, Cursor 等)

用法：python scripts/setup_skill.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENTS_HOME = Path.home() / ".agents"
SKILL_DIR = AGENTS_HOME / "skills" / "superoutfit"

class Colors:
    OK = "\033[92m"
    WARN = "\033[93m"
    FAIL = "\033[91m"
    INFO = "\033[94m"
    END = "\033[0m"

def print_ok(msg): print(f"  {Colors.OK}✓{Colors.END} {msg}")
def print_warn(msg): print(f"  {Colors.WARN}⚠{Colors.END} {msg}")
def print_fail(msg): print(f"  {Colors.FAIL}✗{Colors.END} {msg}")
def print_info(msg): print(f"  {Colors.INFO}ℹ{Colors.END} {msg}")

def check_command(cmd, name):
    """检查命令是否可用"""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_python():
    """检查 Python 版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print_ok(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_fail(f"Python {version.major}.{version.minor} (需要 3.10+)")
        return False

def check_uv():
    """检查 uv"""
    if check_command("uv", "uv"):
        print_ok("uv 已安装")
        return True
    else:
        print_warn("uv 未安装 (可选，用于快速依赖管理)")
        return False

def check_node():
    """检查 Node.js"""
    if check_command("node", "node"):
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print_ok(f"Node.js {result.stdout.strip()}")
        return True
    else:
        print_warn("Node.js 未安装 (前端功能需要)")
        return False

def check_git():
    """检查 git"""
    if check_command("git", "git"):
        print_ok("git 已安装")
        return True
    else:
        print_warn("git 未安装 (版本管理需要)")
        return False

def install_dependencies():
    """安装 Python 依赖"""
    print("\n[2/4] 安装依赖...")
    
    # 检查是否在虚拟环境中
    in_venv = sys.prefix != sys.base_prefix
    
    if in_venv:
        print_info("已激活虚拟环境")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], 
                      cwd=PROJECT_ROOT, capture_output=True)
        print_ok("依赖已安装")
        return True
    
    # 尝试使用 uv
    if check_command("uv", "uv"):
        print_info("使用 uv 安装...")
        result = subprocess.run(["uv", "pip", "install", "-e", "."], 
                               cwd=PROJECT_ROOT, capture_output=True, text=True)
        if result.returncode == 0:
            print_ok("依赖已安装 (uv)")
            return True
    
    # 回退到 pip
    print_info("使用 pip 安装...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], 
                           cwd=PROJECT_ROOT, capture_output=True, text=True)
    if result.returncode == 0:
        print_ok("依赖已安装 (pip)")
        return True
    
    print_fail("依赖安装失败")
    return False

def install_skill():
    """安装 Skill 到通用位置"""
    print("\n[3/4] 安装 Skill...")
    
    skill_md = PROJECT_ROOT / "SKILL.md"
    refs_dir = PROJECT_ROOT / "references"
    
    if not skill_md.exists():
        print_fail("SKILL.md 不存在")
        return False
    
    # 创建目录
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    
    # 复制 SKILL.md
    shutil.copy2(skill_md, SKILL_DIR / "SKILL.md")
    print_ok(f"SKILL.md → {SKILL_DIR}")
    
    # 复制 references
    if refs_dir.exists():
        target_refs = SKILL_DIR / "references"
        if target_refs.exists():
            shutil.rmtree(target_refs)
        shutil.copytree(refs_dir, target_refs)
        ref_count = len(list(target_refs.glob("*.md")))
        print_ok(f"references/ ({ref_count} 个文件)")
    
    # 复制项目路径信息
    path_file = SKILL_DIR / "project.path"
    path_file.write_text(str(PROJECT_ROOT), encoding="utf-8")
    print_ok(f"项目路径: {path_file}")
    
    return True

def generate_mcp_config():
    """生成 MCP 配置"""
    print("\n[4/4] 生成 MCP 配置...")
    
    mcp_config = '''{
  "mcpServers": {
    "superoutfit": {
      "command": "python",
      "args": ["''' + str(PROJECT_ROOT / 'server.py').replace('\\', '\\\\') + '''"]
    }
  }
}'''
    
    mcp_file = SKILL_DIR / "mcp.json"
    mcp_file.write_text(mcp_config, encoding="utf-8")
    print_ok(f"MCP 配置: {mcp_file}")
    
    return True

def print_summary():
    """打印使用说明"""
    print("\n" + "="*60)
    print("  SuperOutfit Skill 设置完成")
    print("="*60)
    print(f"\nSkill 位置: {SKILL_DIR}")
    print("\n使用方式:")
    print("  1. 直接运行 CLI:")
    print("     spof help")
    print("     spof gateway up")
    print()
    print("  2. 在任何 Agent 中引用:")
    print("     '阅读 ~/.agents/skills/superoutfit/SKILL.md'")
    print()
    print("  3. MCP 配置:")
    print(f"     {SKILL_DIR / 'mcp.json'}")
    print()

def main():
    print("\n" + "="*60)
    print("  SuperOutfit Skill 快速设置")
    print("="*60)
    print("\n适用于任何 AI Agent (Hermes, OpenCode, Claude Code 等)")
    
    # 1. 检查环境
    print("\n[1/4] 检查环境...")
    check_python()
    check_uv()
    check_node()
    check_git()
    
    # 2. 安装依赖
    install_dependencies()
    
    # 3. 安装 skill
    install_skill()
    
    # 4. 生成 MCP 配置
    generate_mcp_config()
    
    # 5. 打印总结
    print_summary()

if __name__ == "__main__":
    main()
