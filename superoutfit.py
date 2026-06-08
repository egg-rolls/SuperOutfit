#!/usr/bin/env python3
"""
SuperOutfit CLI — AI 智能穿搭顾问

6 个 AI 命令:
    spof        衣橱/购物清单 CRUD（add/list/show/edit/delete）
    spof wear   穿着管理（add/wash/check/report）
    spof color  色彩工具（score/inverse）
    spof weather 天气查询
    spof data   数据导入导出
    spof info    系统信息
    spof gateway 网关管理（up/down/status）

基础设施:
    spof update    更新应用
    spof uninstall 卸载应用
    spof tui       交互模式
    spof init      首次引导
"""

import argparse
import subprocess
import sys
import os
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent / "scripts"
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# rich (Claude-style output)
try:
    from scripts.output import console, header, info_table, success, error, warn, info, kv_pairs
except ImportError:
    try:
        from output import console, header, info_table, success, error, warn, info, kv_pairs
    except ImportError:
        try:
            from rich.console import Console
            console = Console()
        except ImportError:
            class _Console:
                def print(self, *a, **kw): print(*[str(x) for x in a])
            console = _Console()
        def header(t, s=None): print(f"\n  {t}\n  {s or ''}")
        def info_table(r, title=None): [print(f"  {k}: {v}") for k, v in r]
        def success(m): print(f"  [OK] {m}")
        def error(m): print(f"  [ERR] {m}")
        def warn(m): print(f"  [!] {m}")
        def info(m): print(f"  - {m}")
        def kv_pairs(p): [print(f"  {k}: {v}") for k, v in p]


# ==================== AI Commands ====================

def cmd_spof(args):
    """衣橱/购物清单 CRUD"""
    from wardrobe_ops import main as wardrobe_main
    argv = [args.subcommand]
    if args.item_id:
        argv.append(args.item_id)
    if args.file:
        argv.extend(["--file", args.file])
    if args.type:
        argv.extend(["--type", args.type])
    if args.season:
        argv.extend(["--season", args.season])
    if args.wishlist:
        argv.append("--wishlist")
    if args.json:
        argv.append("--json")
    sys.argv = ["wardrobe_ops.py"] + argv
    wardrobe_main()


def cmd_wear(args):
    """穿着管理"""
    from wear import main as wear_main
    argv = [args.wear_action]
    if args.items:
        argv.extend(["--items", args.items])
    if args.type:
        argv.extend(["--type", args.type])
    if args.date:
        argv.extend(["--date", args.date])
    if args.json:
        argv.append("--json")
    sys.argv = ["wear.py"] + argv
    wear_main()


def cmd_color(args):
    """色彩工具"""
    if args.color_action == "score":
        from color_math import main as color_main
        argv = []
        if args.colors:
            argv.extend(["--colors", args.colors])
        sys.argv = ["color_math.py"] + argv
        color_main()

    elif args.color_action == "inverse":
        if args.method == "search":
            from color_inverse import suggest_colors
            known = [c.strip() for c in args.known.split(",")]
            suggest_colors(known, args.target, args.missing, args.top)
        else:
            from color_inverse_global import diverse_global_inverse
            known = [c.strip() for c in args.known.split(",")]
            diverse_global_inverse(known, args.target, args.missing, args.samples, args.maxiter)


def cmd_weather(args):
    """天气查询"""
    from weather import main as weather_main
    argv = []
    if args.city:
        argv.extend(["--city", args.city])
    if args.lat:
        argv.extend(["--lat", str(args.lat)])
    if args.lon:
        argv.extend(["--lon", str(args.lon)])
    sys.argv = ["weather.py"] + argv
    weather_main()


def cmd_data(args):
    """数据管理"""
    if args.data_action == "dir":
        # 显示或设置数据目录
        from paths import get_data_dir, set_data_dir
        if args.path:
            ok, msg = set_data_dir(args.path)
            if ok:
                success(f"数据目录已设置: {msg}")
            else:
                error(msg)
        else:
            current = get_data_dir()
            info(f"当前数据目录: {current}")
            info(f"配置文件: {Path.home() / '.superoutfit' / 'config.json'}")
        return

    from data_manager import export_data, import_data
    if args.data_action == "export":
        export_data(args.output)
    elif args.data_action == "import":
        if not args.file:
            print("需要 --file")
            return
        import_data(args.file, merge=args.merge, force=args.force)


def cmd_info(args):
    """系统信息"""
    from paths import get_data_dir
    data_dir = get_data_dir()
    items_dir = data_dir / "items"
    wishlist_dir = data_dir / "wishlist"
    item_count = len(list(items_dir.glob("*.yaml"))) if items_dir.exists() else 0
    wish_count = len(list(wishlist_dir.glob("*.yaml"))) if wishlist_dir.exists() else 0
    info_table([
        ("版本", "v3.2.1"),
        ("衣柜", f"{item_count} 件"),
        ("购物清单", f"{wish_count} 件"),
        ("数据目录", str(data_dir)),
    ], title="SuperOutfit")


def cmd_gateway(args):
    """网关管理"""
    gw_action = getattr(args, "gw_action", "up")
    if gw_action == "up":
        from gateway import Gateway, load_pid, is_process_running
        data = load_pid()
        if data and is_process_running(data["pid"]):
            warn(f"Gateway 已在运行 (PID: {data['pid']})")
            return
        class A:
            port = args.port
            no_frontend = args.no_frontend
            no_mcp = args.no_mcp
            dev = args.dev
        Gateway(A()).run()

    elif gw_action == "down":
        from gateway import stop_gateway
        ok, message = stop_gateway()
        if ok:
            success(message)
        else:
            error(message)

    elif gw_action == "status":
        from gateway import get_gateway_status
        status = get_gateway_status()
        if not status["running"]:
            info(status['message'])
            return
        ports = status.get("ports", {})
        rows = [
            ("状态", "[success]运行中[/]"),
            ("PID", str(status['pid'])),
        ]
        if ports.get("api"):
            rows.append(("API", f"http://localhost:{ports['api']}"))
        if ports.get("frontend"):
            rows.append(("Frontend", f"http://localhost:{ports['frontend']}"))
        info_table(rows, title="Gateway")


# ==================== Infrastructure ====================

def cmd_tui(args):
    from tui import main as tui_main
    tui_main()


def cmd_uninstall(args):
    """卸载 SuperOutfit"""
    import shutil
    install_dir = Path(__file__).parent.resolve()

    print("SuperOutfit 卸载程序\n")
    print(f"  安装目录: {install_dir}")

    # Ask keep data
    if args.keep_data:
        keep = True
    elif args.yes:
        keep = False
    else:
        ans = input("\n是否保留衣橱数据？(Y/n): ").strip().lower()
        keep = ans != "n"

    if keep:
        print("\n模式: 卸载程序，保留 data/ 目录")
    else:
        print("\n模式: 完全删除（包括数据）")
        if not args.yes:
            confirm = input("确认删除所有数据？(y/N): ").strip().lower()
            if confirm != "y":
                print("已取消")
                return

    # 1. Remove hermes skill
    skill_dir = Path.home() / "AppData" / "Local" / "hermes" / "skills" / "productivity" / "superoutfit"
    if skill_dir.exists():
        try:
            shutil.rmtree(skill_dir)
            print(f"  [OK] 已删除 Hermes skill")
        except Exception as e:
            print(f"  [!!] 删除 skill 失败: {e}")

    # 2. Remove installation
    if keep:
        # Remove everything except data/ and .git/
        removed = []
        for item in install_dir.iterdir():
            if item.name in ("data", ".git"):
                continue
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                removed.append(item.name)
            except Exception as e:
                print(f"  [!!] 删除 {item.name} 失败: {e}")
        print(f"  [OK] 已删除程序文件 ({len(removed)} 项)")
        print(f"  [OK] 已保留数据目录: {install_dir / 'data'}")
    else:
        try:
            shutil.rmtree(install_dir)
            print(f"  [OK] 已删除全部: {install_dir}")
        except Exception as e:
            print(f"  [!!] 删除失败: {e}")
            return

    # 3. Clean up PATH (Windows)
    if os.name == "nt":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
            try:
                path_val, _ = winreg.QueryValueEx(key, "Path")
                install_str = str(install_dir)
                new_path = ";".join(p for p in path_val.split(";") if install_str not in p)
                if new_path != path_val:
                    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                    print("  [OK] 已从 PATH 中移除")
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
        except Exception:
            pass

    print("\n卸载完成！")
    if keep:
        print(f"数据保留在: {install_dir / 'data'}")
        print("如需重新安装: git clone https://github.com/egg-rolls/SuperOutfit.git")


def cmd_init(args):
    from init_guide import main as init_main
    argv = []
    if args.quick:
        argv.append("--quick")
    sys.argv = ["init_guide.py"] + argv
    init_main()


def cmd_update(args):
    install_dir = Path(__file__).parent
    print("更新 SuperOutfit...\n")
    if not (install_dir / ".git").exists():
        print("不是 git 仓库")
        return

    def git(*cmds):
        return subprocess.run(["git"] + list(cmds),
                              cwd=str(install_dir), capture_output=True,
                              encoding="utf-8", errors="replace")

    # Stash local changes (include untracked files like uv.lock)
    stash_result = git("stash", "push", "--include-untracked", "-m", "auto-stash before update")
    has_stash = "No local changes" not in stash_result.stdout

    # Clean untracked files that would block merge
    git("clean", "-fd", "scripts/")

    # 记录当前 commit
    old_head = git("rev-parse", "HEAD").stdout.strip()

    # Pull
    result = git("pull", "origin", "master")
    if result.stdout.strip():
        print(result.stdout.strip())

    # Pull 失败时，尝试 reset 到远程版本
    if result.returncode != 0:
        print(f"Pull 失败，尝试重置到远程版本...")
        git("fetch", "origin", "master")
        reset = git("reset", "--hard", "origin/master")
        if reset.returncode == 0:
            print("已重置到远程最新版本")
        else:
            print(f"更新失败: {reset.stderr}")
            if has_stash:
                git("stash", "pop")
            return

    # Try to restore stashed changes
    if has_stash:
        pop = git("stash", "pop")
        if pop.returncode != 0:
            print("本地修改与远程冲突，已丢弃本地修改（远程版本为准）")
            git("stash", "drop")

    new_head = git("rev-parse", "HEAD").stdout.strip()

    if old_head == new_head:
        print(f"已是最新 ({old_head[:7]})")
    else:
        print("代码已更新\n")
        # 显示新 commit 列表
        log = git("log", f"{old_head}..{new_head}", "--oneline", "--no-merges")
        if log.stdout.strip():
            for line in log.stdout.strip().split("\n"):
                print(f"  {line}")

    # 安装 Python 依赖
    print("检查 Python 依赖...")
    dep_ok = False

    # 方法 1: uv sync
    if not dep_ok:
        try:
            r = subprocess.run(["uv", "sync"], cwd=str(install_dir),
                               encoding="utf-8", errors="replace", shell=True)
            if r.returncode == 0:
                print("Python 依赖已同步 (uv)")
                dep_ok = True
        except FileNotFoundError:
            pass

    # 方法 2: pip install -e .
    if not dep_ok:
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", "."],
                cwd=str(install_dir),
                encoding="utf-8", errors="replace", shell=True
            )
            if r.returncode == 0:
                print("Python 依赖已安装 (pip)")
                dep_ok = True
        except Exception:
            pass

    # 方法 3: pip install --no-build-isolation -e .
    if not dep_ok:
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--no-build-isolation", "-e", "."],
                cwd=str(install_dir),
                encoding="utf-8", errors="replace", shell=True
            )
            if r.returncode == 0:
                print("Python 依赖已安装 (pip --no-build-isolation)")
                dep_ok = True
        except Exception:
            pass

    if not dep_ok:
        print("Python 依赖自动安装失败，请手动运行: pip install -e .")

    # 重新构建前端
    frontend_dir = install_dir / "frontend"
    if frontend_dir.exists() and (frontend_dir / "package.json").exists():
        print("构建前端...")
        try:
            subprocess.run(["npm", "install"], cwd=str(frontend_dir),
                           capture_output=True, shell=True)
            build = subprocess.run(["npm", "run", "build"], cwd=str(frontend_dir),
                                   capture_output=True, shell=True)
            if build.returncode == 0:
                print("前端构建完成")
            else:
                print("前端构建失败，请手动运行: cd frontend && npm run build")
        except FileNotFoundError:
            print("未找到 npm，请确保 Node.js 已安装")


def show_banner():
    try:
        from rich.text import Text
        from rich.panel import Panel
        from rich import box
        title = Text("SPOF", style="bold #cc785c")
        subtitle = Text("AI 智能穿搭顾问", style="dim")
        version = Text("v3.2.1", style="#5db872")
        content = Text.assemble("\n  ", title, "\n  ", subtitle, "\n  ", version, "\n")
        console.print(Panel(content, border_style="#cc785c", box=box.ROUNDED, expand=False))
    except Exception:
        print("SuperOutfit v3.2.1")


# ==================== Main ====================

def main():
    show_banner()

    parser = argparse.ArgumentParser(
        prog="superoutfit",
        description="SuperOutfit AI 智能穿搭顾问",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  spof add --file item.yaml                    # 添加衣物
  spof add --file item.yaml --wishlist         # 添加到购物清单
  spof list --type 上衣 --season 夏             # 筛选
  spof show item_001                           # 查看详情
  spof edit item_001 --file new.yaml         # 编辑
  spof delete item_001                         # 删除
  spof wear add --items item_001,item_002      # 记录穿着
  spof wear check                              # 需清洗的
  spof wear report                             # 穿着报表
  spof color score --colors "#F5F0E8,#111111"  # 色彩和谐度
  spof color inverse --known "#F5F0E8" --target 75 --missing 1
  spof weather                                 # 天气
  spof data export                             # 导出数据
  spof info                                    # 系统信息
  spof gateway up                              # 启动网关
        """,
    )

    parser.add_argument("-v", "--version", action="store_true", help="版本信息")
    subparsers = parser.add_subparsers(dest="command")

    # === spof (衣橱 CRUD) ===
    p = subparsers.add_parser("add", help="添加衣物 (--wishlist=购物清单)")
    p.add_argument("--file", required=True, help="YAML 文件路径")
    p.add_argument("--wishlist", action="store_true", help="添加到购物清单")
    p.set_defaults(func=lambda a: _crud("add", a))

    p = subparsers.add_parser("list", help="列出衣物")
    p.add_argument("--type", help="按类型筛选")
    p.add_argument("--season", help="按季节筛选")
    p.add_argument("--wishlist", action="store_true", help="列出购物清单")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=lambda a: _crud("list", a))

    p = subparsers.add_parser("show", help="查看衣物详情")
    p.add_argument("item_id", help="衣物 ID")
    p.add_argument("--wishlist", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=lambda a: _crud("show", a))

    p = subparsers.add_parser("edit", help="编辑衣物")
    p.add_argument("item_id", help="衣物 ID")
    p.add_argument("--file", required=True, help="YAML 文件路径")
    p.add_argument("--wishlist", action="store_true")
    p.set_defaults(func=lambda a: _crud("edit", a))

    p = subparsers.add_parser("delete", help="删除衣物")
    p.add_argument("item_id", help="衣物 ID")
    p.add_argument("--wishlist", action="store_true")
    p.set_defaults(func=lambda a: _crud("delete", a))

    # === wear ===
    p_wear = subparsers.add_parser("wear", help="穿着管理")
    p_wear.add_argument("wear_action", choices=["add", "wash", "check", "report"])
    p_wear.add_argument("--items", help="衣物 ID (逗号分隔)")
    p_wear.add_argument("--type", help="按类型筛选")
    p_wear.add_argument("--date", help="日期 YYYY-MM-DD")
    p_wear.add_argument("--json", action="store_true")
    p_wear.set_defaults(func=cmd_wear)

    # === color ===
    p_color = subparsers.add_parser("color", help="色彩工具")
    p_color.add_argument("color_action", choices=["score", "inverse"])
    p_color.add_argument("--colors", help="HEX 色值 (逗号分隔)")
    p_color.add_argument("--known", help="已知颜色 (逗号分隔 HEX)")
    p_color.add_argument("--target", type=float, help="目标分数")
    p_color.add_argument("--missing", type=int, help="补全数量")
    p_color.add_argument("--method", choices=["search", "global"], default="search")
    p_color.add_argument("--top", type=int, default=5)
    p_color.add_argument("--samples", type=int, default=3)
    p_color.add_argument("--maxiter", type=int, default=100)
    p_color.set_defaults(func=cmd_color)

    # === weather ===
    p_wt = subparsers.add_parser("weather", help="天气查询")
    p_wt.add_argument("--city", default="大连")
    p_wt.add_argument("--lat", type=float)
    p_wt.add_argument("--lon", type=float)
    p_wt.set_defaults(func=cmd_weather)

    # === data ===
    p_data = subparsers.add_parser("data", help="数据管理（导入/导出/设置目录）")
    p_data.add_argument("data_action", choices=["export", "import", "dir"])
    p_data.add_argument("path", nargs="?", help="数据目录路径（dir 操作）")
    p_data.add_argument("--output", "-o")
    p_data.add_argument("--file", "-f")
    p_data.add_argument("--merge", action="store_true")
    p_data.add_argument("--force", action="store_true")
    p_data.set_defaults(func=cmd_data)

    # === info ===
    p_info = subparsers.add_parser("info", help="系统信息")
    p_info.set_defaults(func=cmd_info)

    # === gateway ===
    p_gw = subparsers.add_parser("gateway", aliases=["gw"], help="网关管理")
    p_gw.add_argument("gw_action", nargs="?", default="up",
                      choices=["up", "down", "status"])
    p_gw.add_argument("--port", type=int, default=32200, help="端口 (默认: 32200, API+前端同端口)")
    p_gw.add_argument("--no-frontend", action="store_true", help="不启动前端")
    p_gw.add_argument("--no-mcp", action="store_true", help="不启动 MCP")
    p_gw.add_argument("--dev", action="store_true", help="开发模式（前端热重载）")
    p_gw.set_defaults(func=cmd_gateway)

    # === infra ===
    p = subparsers.add_parser("tui", help="交互式 TUI")
    p.set_defaults(func=cmd_tui)

    p = subparsers.add_parser("init", help="首次使用引导")
    p.add_argument("--quick", action="store_true")
    p.set_defaults(func=cmd_init)

    p = subparsers.add_parser("update", help="更新 SuperOutfit")
    p.set_defaults(func=cmd_update)

    p = subparsers.add_parser("uninstall", help="卸载 SuperOutfit")
    p.add_argument("--keep-data", action="store_true", help="保留衣橱数据")
    p.add_argument("-y", "--yes", action="store_true", help="跳过确认")
    p.set_defaults(func=cmd_uninstall)

    args = parser.parse_args()

    if args.version:
        print("SuperOutfit v3.2.0")
        return

    if not args.command:
        parser.print_help()
        return

    args.func(args)


def _crud(command, args):
    """统一 CRUD 路由"""
    from wardrobe_ops import main as wardrobe_main
    argv = [command]
    if hasattr(args, "item_id") and args.item_id:
        argv.append(args.item_id)
    if hasattr(args, "file") and args.file:
        argv.extend(["--file", args.file])
    if hasattr(args, "type") and args.type:
        argv.extend(["--type", args.type])
    if hasattr(args, "season") and args.season:
        argv.extend(["--season", args.season])
    if hasattr(args, "wishlist") and args.wishlist:
        argv.append("--wishlist")
    if hasattr(args, "json") and args.json:
        argv.append("--json")
    sys.argv = ["wardrobe_ops.py"] + argv
    wardrobe_main()


if __name__ == "__main__":
    main()
