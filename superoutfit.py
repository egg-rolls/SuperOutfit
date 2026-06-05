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
"""

import argparse
import subprocess
import sys
import os
import json
from pathlib import Path

# rich
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    console = Console()
except ImportError:
    class SimpleConsole:
        def print(self, *args, **kwargs):
            print(*args)
    console = SimpleConsole()

SCRIPT_DIR = Path(__file__).parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))


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
    """数据导入导出"""
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
    from pathlib import Path as P
    items_dir = P("data/items")
    wishlist_dir = P("data/wishlist")
    item_count = len(list(items_dir.glob("*.yaml"))) if items_dir.exists() else 0
    wish_count = len(list(wishlist_dir.glob("*.yaml"))) if wishlist_dir.exists() else 0
    print(f"SuperOutfit v3.2.0")
    print(f"  衣柜: {item_count} 件")
    print(f"  购物清单: {wish_count} 件")


def cmd_gateway(args):
    """网关管理"""
    gw_action = getattr(args, "gw_action", "up")
    if gw_action == "up":
        from gateway import Gateway, load_pid, is_process_running
        data = load_pid()
        if data and is_process_running(data["pid"]):
            print(f"Gateway 已在运行 (PID: {data['pid']})")
            return
        class A:
            port = args.port
            no_frontend = args.no_frontend
            no_mcp = args.no_mcp
            dev = args.dev
        Gateway(A()).run()

    elif gw_action == "down":
        from gateway import stop_gateway
        success, message = stop_gateway()
        print(message)

    elif gw_action == "status":
        from gateway import get_gateway_status
        status = get_gateway_status()
        if not status["running"]:
            print(f"Gateway: {status['message']}")
            return
        print(f"Gateway: 运行中 (PID: {status['pid']})")
        ports = status.get("ports", {})
        if ports.get("api"):
            print(f"  API: http://localhost:{ports['api']}")


# ==================== Infrastructure ====================

def cmd_tui(args):
    from tui import main as tui_main
    tui_main()


def cmd_init(args):
    from init_guide import main as init_main
    argv = []
    if args.quick:
        argv.append("--quick")
    sys.argv = ["init_guide.py"] + argv
    init_main()


def cmd_update(args):
    install_dir = Path(__file__).parent
    print("更新 SuperOutfit...")
    if not (install_dir / ".git").exists():
        print("不是 git 仓库")
        return
    result = subprocess.run(["git", "pull", "origin", "master"],
                            cwd=str(install_dir), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"更新失败: {result.stderr}")
        return
    print("已是最新" if "Already up to date" in result.stdout else "代码已更新")


def show_banner():
    try:
        title = Text("SPOF", style="bold magenta")
        subtitle = Text("AI 智能穿搭顾问", style="dim")
        version = Text("v3.2.0", style="green")
        content = Text.assemble("\n", "  ", title, "\n", "  ", subtitle, "\n", "  ", version, "\n")
        console.print(Panel(content, border_style="blue", expand=False))
    except:
        print("SuperOutfit v3.2.0")


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
    p_data = subparsers.add_parser("data", help="数据导入导出")
    p_data.add_argument("data_action", choices=["export", "import"])
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
    p_gw.add_argument("--port", type=int, default=32200)
    p_gw.add_argument("--no-frontend", action="store_true")
    p_gw.add_argument("--no-mcp", action="store_true")
    p_gw.add_argument("--dev", action="store_true")
    p_gw.set_defaults(func=cmd_gateway)

    # === infra ===
    p = subparsers.add_parser("tui", help="交互式 TUI")
    p.set_defaults(func=cmd_tui)

    p = subparsers.add_parser("init", help="首次使用引导")
    p.add_argument("--quick", action="store_true")
    p.set_defaults(func=cmd_init)

    p = subparsers.add_parser("update", help="更新 SuperOutfit")
    p.set_defaults(func=cmd_update)

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
