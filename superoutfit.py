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
        ("版本", "v3.3.0"),
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
        version = Text("v3.3.0", style="#5db872")
        content = Text.assemble("\n  ", title, "\n  ", subtitle, "\n  ", version, "\n")
        console.print(Panel(content, border_style="#cc785c", box=box.ROUNDED, expand=False))
    except Exception:
        print("SuperOutfit v3.3.0")


# ==================== Main ====================

def print_rich_help():
    """打印自定义的 Rich 格式帮助信息"""
    try:
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        from rich import box

        # 命令分组
        groups = [
            ("衣橱管理", [
                ("add",    "添加衣物 (AI 生成 YAML)", "--file item.yaml [--wishlist]"),
                ("list",   "列出衣物",                "[--type X] [--season X] [--json]"),
                ("show",   "查看衣物详情",            "item_001 [--json]"),
                ("edit",   "编辑衣物",                "item_001 --file new.yaml"),
                ("delete", "删除衣物",                "item_001 [--wishlist]"),
            ]),
            ("穿着追踪", [
                ("wear add",   "记录今天穿了什么",  "--items item_001,item_002 [--date 2026-06-07]"),
                ("wear wash",  "标记衣物已清洗",    "--items item_001"),
                ("wear check", "查看需要清洗的衣物", "[--type 上衣]"),
                ("wear report","穿着统计报表",      "[--items item_001] [--json]"),
            ]),
            ("色彩分析", [
                ("color score",   "色彩和谐度评分",   '--colors "#F5F0E8,#111111"'),
                ("color inverse", "反向推导配色",     '--known "#F5F0E8" --target 75 --missing 1'),
            ]),
            ("数据管理", [
                ("data dir",    "查看/设置数据目录",  "\\[/path/to/data]"),
                ("data export", "导出数据为 zip",    "\\[-o output.zip]"),
                ("data import", "从 zip 导入数据",   "-f backup.zip \\[--merge]"),
            ]),
            ("系统工具", [
                ("weather",  "天气查询",        "[--city 大连]"),
                ("info",     "系统信息",        ""),
                ("gateway",  "启动/停止网关",   "[up|down|status] [--dev] [--port 32200]"),
                ("update",   "更新 SuperOutfit",""),
            ]),
        ]

        console.print()
        for group_name, commands in groups:
            table = Table(
                box=None, show_header=True, header_style="bold #cc785c",
                padding=(0, 2), show_edge=False,
                title=f"  {group_name}", title_style="bold",
            )
            table.add_column("命令", style="bold #cc785c", min_width=16)
            table.add_column("说明", min_width=24)
            table.add_column("参数", style="dim")

            for cmd, desc, args in commands:
                table.add_row(f"  spof {cmd}", desc, args)

            console.print(table)
            console.print()

        # 使用示例
        examples = Text()
        examples.append("  使用示例:\n", style="bold")
        examples.append("  spof gateway", style="bold #cc785c")
        examples.append("                    # 启动服务（API + 前端）\n", style="dim")
        examples.append("  spof list", style="bold #cc785c")
        examples.append("                       # 查看衣橱\n", style="dim")
        examples.append("  spof add --file item.yaml", style="bold #cc785c")
        examples.append("         # 添加衣物\n", style="dim")
        examples.append("  spof wear check", style="bold #cc785c")
        examples.append("                  # 查看需清洗的衣物\n", style="dim")
        examples.append("  spof color score --colors ", style="bold #cc785c")
        examples.append('"#F5F0E8,#111111"', style="#5db872")
        examples.append("  # 色彩评分\n", style="dim")
        examples.append("  spof data dir ~/my-data", style="bold #cc785c")
        examples.append("            # 设置数据目录\n", style="dim")

        console.print(Panel(examples, border_style="#e6dfd8", box=box.ROUNDED, expand=False))

        # 底部提示
        console.print()
        console.print("  [dim]--json    所有 list/show/report 命令支持 JSON 输出[/]")
        console.print("  [dim]--wishlist 衣橱命令切换到购物清单[/]")
        console.print("  [dim]-h       任何子命令查看详细帮助  spof wear -h[/]")
        console.print()

    except Exception:
        # fallback
        print("用法: spof <命令> [参数]")
        print("运行 spof -h 查看完整帮助")


def main():
    show_banner()

    parser = argparse.ArgumentParser(
        prog="spof",
        description="SuperOutfit AI 智能穿搭顾问",
        add_help=False,
    )

    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")
    parser.add_argument("-v", "--version", action="store_true", help="显示版本信息")
    subparsers = parser.add_subparsers(dest="command")

    # === 衣橱 CRUD ===
    p = subparsers.add_parser("add", help="添加衣物", description="从 YAML 文件添加衣物到衣橱或购物清单")
    p.add_argument("--file", required=True, help="YAML 文件路径")
    p.add_argument("--wishlist", action="store_true", help="添加到购物清单")
    p.set_defaults(func=lambda a: _crud("add", a))

    p = subparsers.add_parser("list", help="列出衣物", description="列出衣橱或购物清单中的所有衣物")
    p.add_argument("--type", help="按类型筛选 (上衣/下装/配饰)")
    p.add_argument("--season", help="按季节筛选 (春/夏/秋/冬)")
    p.add_argument("--wishlist", action="store_true", help="列出购物清单")
    p.add_argument("--json", action="store_true", help="JSON 格式输出")
    p.set_defaults(func=lambda a: _crud("list", a))

    p = subparsers.add_parser("show", help="查看衣物详情", description="查看单件衣物的完整信息")
    p.add_argument("item_id", help="衣物 ID (如 item_001)")
    p.add_argument("--wishlist", action="store_true", help="从购物清单查看")
    p.add_argument("--json", action="store_true", help="JSON 格式输出")
    p.set_defaults(func=lambda a: _crud("show", a))

    p = subparsers.add_parser("edit", help="编辑衣物", description="用新 YAML 文件覆盖更新衣物信息")
    p.add_argument("item_id", help="衣物 ID")
    p.add_argument("--file", required=True, help="新的 YAML 文件路径")
    p.add_argument("--wishlist", action="store_true", help="编辑购物清单中的衣物")
    p.set_defaults(func=lambda a: _crud("edit", a))

    p = subparsers.add_parser("delete", help="删除衣物", description="从衣橱或购物清单删除衣物")
    p.add_argument("item_id", help="衣物 ID")
    p.add_argument("--wishlist", action="store_true", help="从购物清单删除")
    p.set_defaults(func=lambda a: _crud("delete", a))

    # === 穿着管理 ===
    p_wear = subparsers.add_parser("wear", help="穿着管理", description="记录穿着、清洗、查看统计")
    p_wear.add_argument("wear_action", choices=["add", "wash", "check", "report"],
                        help="add=记录穿着 | wash=标记清洗 | check=需清洗 | report=统计报表")
    p_wear.add_argument("--items", help="衣物 ID (逗号分隔，如 item_001,item_002)")
    p_wear.add_argument("--type", help="按类型筛选")
    p_wear.add_argument("--date", help="日期 YYYY-MM-DD (默认今天)")
    p_wear.add_argument("--json", action="store_true", help="JSON 格式输出")
    p_wear.set_defaults(func=cmd_wear)

    # === 色彩工具 ===
    p_color = subparsers.add_parser("color", help="色彩分析", description="色彩和谐度评分与反向推导")
    p_color.add_argument("color_action", choices=["score", "inverse"],
                         help="score=评分 | inverse=反向推导")
    p_color.add_argument("--colors", help="HEX 色值 (逗号分隔)")
    p_color.add_argument("--known", help="已知颜色 HEX (逗号分隔)")
    p_color.add_argument("--target", type=float, help="目标分数 (0-100)")
    p_color.add_argument("--missing", type=int, help="需要补全的颜色数量")
    p_color.add_argument("--method", choices=["search", "global"], default="search")
    p_color.add_argument("--top", type=int, default=5)
    p_color.add_argument("--samples", type=int, default=3)
    p_color.add_argument("--maxiter", type=int, default=100)
    p_color.set_defaults(func=cmd_color)

    # === 天气 ===
    p_wt = subparsers.add_parser("weather", help="天气查询", description="查询天气信息 (Open-Meteo API)")
    p_wt.add_argument("--city", default="大连", help="城市名称 (默认: 大连)")
    p_wt.add_argument("--lat", type=float, help="纬度")
    p_wt.add_argument("--lon", type=float, help="经度")
    p_wt.set_defaults(func=cmd_weather)

    # === 数据管理 ===
    p_data = subparsers.add_parser("data", help="数据管理", description="数据目录配置、导入导出")
    p_data.add_argument("data_action", choices=["export", "import", "dir"],
                        help="dir=设置目录 | export=导出 | import=导入")
    p_data.add_argument("path", nargs="?", help="数据目录路径 (dir 操作)")
    p_data.add_argument("--output", "-o", help="导出文件路径")
    p_data.add_argument("--file", "-f", help="导入文件路径")
    p_data.add_argument("--merge", action="store_true", help="合并导入 (不覆盖)")
    p_data.add_argument("--force", action="store_true", help="强制导入 (覆盖)")
    p_data.set_defaults(func=cmd_data)

    # === 系统 ===
    p_info = subparsers.add_parser("info", help="系统信息", description="显示版本、数据目录、衣物统计")
    p_info.set_defaults(func=cmd_info)

    p_gw = subparsers.add_parser("gateway", aliases=["gw"], help="网关管理",
                                 description="启动/停止 API + 前端 + MCP 服务")
    p_gw.add_argument("gw_action", nargs="?", default="up",
                      choices=["up", "down", "status"],
                      help="up=启动 | down=停止 | status=状态 (默认: up)")
    p_gw.add_argument("--port", type=int, default=32200, help="API 端口 (默认: 32200)")
    p_gw.add_argument("--no-frontend", action="store_true", help="不启动前端")
    p_gw.add_argument("--no-mcp", action="store_true", help="不启动 MCP Server")
    p_gw.add_argument("--dev", action="store_true", help="开发模式 (前端热重载)")
    p_gw.set_defaults(func=cmd_gateway)

    p = subparsers.add_parser("tui", help="交互模式", description="菜单式交互界面")
    p.set_defaults(func=cmd_tui)

    p = subparsers.add_parser("init", help="初始化", description="首次使用引导配置")
    p.add_argument("--quick", action="store_true", help="快速模式 (使用默认值)")
    p.set_defaults(func=cmd_init)

    p = subparsers.add_parser("update", help="更新", description="从 GitHub 拉取最新代码并安装依赖")
    p.set_defaults(func=cmd_update)

    p = subparsers.add_parser("uninstall", help="卸载", description="卸载 SuperOutfit")
    p.add_argument("--keep-data", action="store_true", help="保留衣橱数据")
    p.add_argument("-y", "--yes", action="store_true", help="跳过确认")
    p.set_defaults(func=cmd_uninstall)

    args = parser.parse_args()

    if args.version:
        print("SuperOutfit v3.3.0")
        return

    if args.help or not args.command:
        print_rich_help()
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
