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

def generate_agent_configs():
    """生成各 Agent 的配置示例"""
    print("\n[3/4] 生成 Agent 配置...")
    
    configs_dir = PROJECT_ROOT / ".agent-configs"
    configs_dir.mkdir(exist_ok=True)
    
    # MCP 配置 (适用于支持 MCP 的 Agent)
    mcp_config = '''{
  "mcpServers": {
    "superoutfit": {
      "command": "python",
      "args": ["''' + str(PROJECT_ROOT / 'server.py').replace('\\', '\\\\') + '''"]
    }
  }
}'''
    (configs_dir / "mcp.json").write_text(mcp_config, encoding="utf-8")
    print_ok(f"MCP 配置: {configs_dir / 'mcp.json'}")
    
    # Claude Code / Cursor 配置
    claude_config = '''# SuperOutfit Skill for Claude Code / Cursor

## 使用方式

1. 在项目根目录创建 `.cursorrules` 或 `.claude` 文件
2. 添加以下内容：

```
阅读并遵循 SKILL.md 中的指南
项目路径: ''' + str(PROJECT_ROOT) + '''
```

3. 或者直接在对话中说：
   "阅读 D:/Application/SuperOutfit/SKILL.md 并按照指南操作"
'''
    (configs_dir / "claude-code.md").write_text(claude_config, encoding="utf-8")
    print_ok(f"Claude Code 指南: {configs_dir / 'claude-code.md'}")
    
    # OpenCode 配置
    opencode_config = '''# SuperOutfit Skill for OpenCode

## 使用方式

1. 在项目根目录创建 `.opencode` 文件
2. 添加以下内容：

```
skill: D:/Application/SuperOutfit/SKILL.md
```

3. 或者直接在对话中说：
   "阅读 D:/Application/SuperOutfit/SKILL.md 并按照指南操作"
'''
    (configs_dir / "opencode.md").write_text(opencode_config, encoding="utf-8")
    print_ok(f"OpenCode 指南: {configs_dir / 'opencode.md'}")
    
    # 通用 Agent 配置
    generic_config = '''# SuperOutfit Skill - 通用 Agent 使用指南

## 项目信息
- 项目路径: ''' + str(PROJECT_ROOT) + '''
- 主入口: superoutfit.py (别名: spof)
- 文档: SKILL.md + references/

## 使用方式

### 方式 1: 直接引用 SKILL.md
在对话中告诉 Agent:
"阅读 D:/Application/SuperOutfit/SKILL.md 并按照指南操作"

### 方式 2: 使用 CLI
```bash
spof help          # 查看帮助
spof gateway up    # 启动服务
spof wardrobe list # 查看衣橱
```

### 方式 3: MCP 工具 (如果 Agent 支持)
参考 .agent-configs/mcp.json 配置

## 常用命令
- `spof setup` - 环境检查和依赖安装
- `spof gateway up/down/restart/status` - 服务管理
- `spof wardrobe add/list/show/stats` - 衣橱管理
- `spof recommend` - 穿搭推荐
- `spof score` - 搭配评分
- `spof color` - 色彩协调度
'''
    (configs_dir / "generic.md").write_text(generic_config, encoding="utf-8")
    print_ok(f"通用指南: {configs_dir / 'generic.md'}")
    
    return True

def print_summary():
    """打印使用说明"""
    print("\n[4/4] 完成！")
    print("\n" + "="*60)
    print("  SuperOutfit Skill 设置完成")
    print("="*60)
    print("\n适用于任何 AI Agent:")
    print("  - Hermes / Claude Code / OpenCode / Cursor 等")
    print("\n使用方式:")
    print("  1. 直接运行 CLI:")
    print("     spof help")
    print("     spof gateway up")
    print()
    print("  2. 在任何 Agent 中引用:")
    print("     '阅读 D:/Application/SuperOutfit/SKILL.md'")
    print()
    print("  3. 配置文件已生成:")
    print("     .agent-configs/mcp.json       (MCP 配置)")
    print("     .agent-configs/claude-code.md  (Claude Code 指南)")
    print("     .agent-configs/opencode.md     (OpenCode 指南)")
    print("     .agent-configs/generic.md      (通用指南)")
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
    
    # 3. 生成配置
    generate_agent_configs()
    
    # 4. 打印总结
    print_summary()

if __name__ == "__main__":
    main()
