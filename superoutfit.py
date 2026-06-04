#!/usr/bin/env python3
"""
SuperOutfit CLI — AI 智能穿搭顾问命令行工具

Usage:
    superoutfit <command> <subcommand> [options]

Commands:
    wardrobe    衣橱管理（add/list/show/update/delete/stats/record/reindex）
    weather     天气查询
    recommend   穿搭推荐
    score       搭配评分
    color       色彩协调度
    inverse     反向推导颜色（给定部分颜色和目标分数，推导补全颜色）
    palette     色卡管理（list/score/train）
    knowledge   知识库（list/show/edit）
    config      配置查看
"""

import argparse
import sys
import os
import json
from pathlib import Path

# 确保 scripts/ 在导入路径中
SCRIPT_DIR = Path(__file__).parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))


def cmd_wardrobe(args):
    """衣橱管理"""
    from wardrobe_ops import main as wardrobe_main
    
    # 构造参数列表
    argv = [args.subcommand]
    
    if args.subcommand == "add":
        if args.type: argv.extend(["--type", args.type])
        if args.sub_type: argv.extend(["--sub-type", args.sub_type])
        if args.primary_color: argv.extend(["--primary-color", args.primary_color])
        if args.primary_hex: argv.extend(["--primary-hex", args.primary_hex])
        if args.secondary_color: argv.extend(["--secondary-color", args.secondary_color])
        if args.secondary_hex: argv.extend(["--secondary-hex", args.secondary_hex])
        if args.material: argv.extend(["--material", args.material])
        if args.fit: argv.extend(["--fit", args.fit])
        if args.style: argv.extend(["--style", args.style])
        if args.season: argv.extend(["--season", args.season])
        if args.temp_range: argv.extend(["--temp-range", args.temp_range])
        if args.occasion: argv.extend(["--occasion", args.occasion])
        if args.pair_with: argv.extend(["--pair-with", args.pair_with])
        if args.restrict: argv.extend(["--restrict", args.restrict])
        if args.image: argv.extend(["--image", args.image])
    
    elif args.subcommand == "list":
        if args.json: argv.append("--json")
        if args.category: argv.extend(["--category", args.category])
        if args.style: argv.extend(["--style", args.style])
        if args.season: argv.extend(["--season", args.season])
        if args.occasion: argv.extend(["--occasion", args.occasion])
    
    elif args.subcommand == "show":
        if args.item_id: argv.append(args.item_id)
    
    elif args.subcommand == "update":
        if args.item_id: argv.append(args.item_id)
        if args.wear_count is not None: argv.extend(["--wear-count", str(args.wear_count)])
        if args.favorite: argv.extend(["--favorite", args.favorite])
        if args.style: argv.extend(["--style", args.style])
    
    elif args.subcommand == "delete":
        if args.item_id: argv.append(args.item_id)
        if args.force: argv.append("--force")
    
    elif args.subcommand == "record":
        if args.items: argv.extend(["--items", args.items])
        if args.occasion: argv.extend(["--occasion", args.occasion])
        if args.weather: argv.extend(["--weather", args.weather])
        if args.temp: argv.extend(["--temp", str(args.temp)])
        if args.notes: argv.extend(["--notes", args.notes])
    
    elif args.subcommand == "restore":
        if args.item_id: argv.append(args.item_id)
    
    # 调用原有脚本
    sys.argv = ["wardrobe_ops.py"] + argv
    wardrobe_main()


def cmd_weather(args):
    """天气查询"""
    from weather import main as weather_main
    
    argv = []
    if args.city: argv.extend(["--city", args.city])
    if args.lat: argv.extend(["--lat", str(args.lat)])
    if args.lon: argv.extend(["--lon", str(args.lon)])
    
    sys.argv = ["weather.py"] + argv
    weather_main()


def cmd_recommend(args):
    """穿搭推荐"""
    # TODO: 实现智能推荐逻辑
    print("🚧 推荐功能开发中...")
    print("当前可使用 score 命令评估搭配方案：")
    print("  superoutfit score --items item_001,item_003 --occasion 通勤")


def cmd_score(args):
    """搭配评分"""
    from scorer import main as scorer_main
    
    argv = []
    if args.items: argv.extend(["--items", args.items])
    if args.occasion: argv.extend(["--occasion", args.occasion])
    if args.temp: argv.extend(["--temp", str(args.temp)])
    
    sys.argv = ["scorer.py"] + argv
    scorer_main()


def cmd_color(args):
    """色彩协调度"""
    from color_math import main as color_main
    
    argv = []
    if args.items: argv.extend(["--items", args.items])
    if args.colors: argv.extend(["--colors", args.colors])
    
    sys.argv = ["color_math.py"] + argv
    color_main()


def cmd_inverse(args):
    """反向推导颜色"""
    if args.method == "search":
        from color_inverse import suggest_colors
        known = [c.strip() for c in args.known.split(",")]
        suggest_colors(known, args.target, args.missing, args.top)
    else:
        from color_inverse_global import diverse_global_inverse
        known = [c.strip() for c in args.known.split(",")]
        diverse_global_inverse(known, args.target, args.missing, args.samples, args.maxiter)


def cmd_palette(args):
    """色卡管理"""
    if args.subcommand == "list":
        # 列出色卡
        scored_path = Path("data/scored_palettes.json")
        if not scored_path.exists():
            print("❌ 未找到已评分色卡，请先运行：superoutfit palette train")
            return
        
        with open(scored_path, "r", encoding="utf-8") as f:
            palettes = json.load(f)
        
        # 按分数排序
        palettes.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # 筛选
        if args.top:
            palettes = palettes[:args.top]
        if args.source:
            palettes = [p for p in palettes if p.get("source") == args.source]
        if args.min_score:
            palettes = [p for p in palettes if p.get("score", 0) >= args.min_score]
        
        print(f"📊 共 {len(palettes)} 组色卡\n")
        for i, p in enumerate(palettes[:20], 1):
            colors = " ".join(p.get("colors", []))
            score = p.get("score", 0)
            source = p.get("source", "")
            likes = p.get("likes", 0)
            grade = p.get("grade", "")
            
            # 色块预览
            preview = ""
            for c in p.get("colors", []):
                preview += f"  {c}"
            
            print(f"{i:3}. {grade:3} {score:5.1f}分 | {colors}{preview}")
            print(f"     来源: {source} | 点赞: {likes}")
    
    elif args.subcommand == "train":
        # 训练色彩模型
        print("🎨 开始训练色彩模型...")
        from like_based_scoring import main as train_main
        sys.argv = ["like_based_scoring.py"]
        train_main()
    
    elif args.subcommand == "scrape":
        # 爬取色卡
        print("🕷️ 开始爬取色卡...")
        from scrape_palettes import main as scrape_main
        sys.argv = ["scrape_palettes.py"]
        scrape_main()
        
        from scrape_wxsecai import main as scrape_wxsecai_main
        sys.argv = ["scrape_wxsecai.py"]
        scrape_wxsecai_main()


def cmd_knowledge(args):
    """知识库管理"""
    refs_dir = Path("references")
    
    if args.subcommand == "list":
        # 列出知识文件
        files = sorted(refs_dir.glob("*.md"))
        print(f"📚 共 {len(files)} 篇知识文档\n")
        for f in files:
            if f.name == "SOURCES.md":
                continue
            # 读取第一行作为标题
            with open(f, "r", encoding="utf-8") as fh:
                first_line = fh.readline().strip()
                title = first_line.lstrip("#").strip() if first_line else f.stem
            print(f"  {f.name:20} {title}")
    
    elif args.subcommand == "show":
        # 显示知识内容
        if not args.filename:
            print("❌ 请指定文件名，例如：superoutfit knowledge show color.md")
            return
        
        filepath = refs_dir / args.filename
        if not filepath.exists():
            print(f"❌ 文件不存在：{filepath}")
            return
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        if args.raw:
            print(content)
        else:
            # 简单渲染（去掉 markdown 语法）
            lines = content.split("\n")
            for line in lines:
                if line.startswith("#"):
                    print(f"\n{'='*60}")
                    print(line)
                    print(f"{'='*60}")
                elif line.startswith("- "):
                    print(f"  • {line[2:]}")
                elif line.startswith("```"):
                    continue
                else:
                    print(line)
    
    elif args.subcommand == "edit":
        # 编辑知识文件
        if not args.filename:
            print("❌ 请指定文件名，例如：superoutfit knowledge edit color.md")
            return
        
        filepath = refs_dir / args.filename
        if not filepath.exists():
            print(f"❌ 文件不存在：{filepath}")
            return
        
        # 使用默认编辑器打开
        editor = os.environ.get("EDITOR", "notepad" if os.name == "nt" else "vim")
        os.system(f'{editor} "{filepath}"')


def cmd_config(args):
    """配置查看"""
    profile_path = Path("data/profile.yaml")
    
    if not profile_path.exists():
        print("❌ 未找到用户画像，请先创建 data/profile.yaml")
        return
    
    import yaml
    with open(profile_path, "r", encoding="utf-8") as f:
        profile = yaml.safe_load(f)
    
    print("⚙️  用户配置\n")
    print(f"  姓名: {profile.get('name', '未设置')}")
    print(f"  身高: {profile.get('height', '未设置')} cm")
    print(f"  体重: {profile.get('weight', '未设置')} kg")
    print(f"  肩宽: {profile.get('shoulder', '未设置')} cm")
    print(f"  胸围: {profile.get('chest', '未设置')} cm")
    print(f"  腰围: {profile.get('waist', '未设置')} cm")
    print(f"  臀围: {profile.get('hip', '未设置')} cm")
    print(f"  风格: {', '.join(profile.get('styles', []))}")
    print(f"  偏好颜色: {', '.join(profile.get('preferred_colors', []))}")
    print(f"  预算: 上衣 {profile.get('budget', {}).get('top', '?')} / 下装 {profile.get('budget', {}).get('bottom', '?')} / 外套 {profile.get('budget', {}).get('outer', '?')}")


def cmd_version(args):
    """版本信息"""
    print("SuperOutfit v3.0.0")
    print("AI 智能穿搭顾问 — MCP + CLI")
    print("https://github.com/egg-rolls/SuperOutfit")


def main():
    parser = argparse.ArgumentParser(
        prog="superoutfit",
        description="🧥 SuperOutfit — AI 智能穿搭顾问",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  superoutfit wardrobe add --type "上衣" --color "#F5F0E8"
  superoutfit wardrobe list --category "上衣"
  superoutfit weather --city "大连"
  superoutfit score --items item_001,item_003 --occasion 通勤
  superoutfit color --colors "#F5F0E8,#C4A97D,#111111"
  superoutfit inverse --known "#F5F0E8,#111111" --target 75 --missing 2
  superoutfit palette list --top 10
  superoutfit knowledge show color.md
  superoutfit config
        """
    )
    
    parser.add_argument("-v", "--version", action="store_true", help="显示版本信息")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # === wardrobe ===
    p_wardrobe = subparsers.add_parser("wardrobe", aliases=["w"], help="衣橱管理")
    p_wardrobe.add_argument("subcommand", choices=["add", "list", "show", "update", "delete", "stats", "record", "reindex", "restore"],
                           help="子命令")
    p_wardrobe.add_argument("--item-id", help="衣物 ID")
    p_wardrobe.add_argument("--type", help="衣物类型")
    p_wardrobe.add_argument("--sub-type", help="子类型")
    p_wardrobe.add_argument("--primary-color", help="主色")
    p_wardrobe.add_argument("--primary-hex", help="主色 HEX")
    p_wardrobe.add_argument("--secondary-color", help="次色")
    p_wardrobe.add_argument("--secondary-hex", help="次色 HEX")
    p_wardrobe.add_argument("--material", help="材质")
    p_wardrobe.add_argument("--fit", help="版型")
    p_wardrobe.add_argument("--style", help="风格（逗号分隔）")
    p_wardrobe.add_argument("--season", help="季节（逗号分隔）")
    p_wardrobe.add_argument("--temp-range", help="温度范围")
    p_wardrobe.add_argument("--occasion", help="场合（逗号分隔）")
    p_wardrobe.add_argument("--pair-with", help="搭配建议")
    p_wardrobe.add_argument("--restrict", help="限制搭配")
    p_wardrobe.add_argument("--image", help="图片文件")
    p_wardrobe.add_argument("--wear-count", type=int, help="穿着次数")
    p_wardrobe.add_argument("--favorite", choices=["true", "false"], help="是否收藏")
    p_wardrobe.add_argument("--items", help="衣物 ID 列表（逗号分隔）")
    p_wardrobe.add_argument("--notes", help="备注")
    p_wardrobe.add_argument("--weather", help="天气")
    p_wardrobe.add_argument("--temp", type=int, help="温度")
    p_wardrobe.add_argument("--json", action="store_true", help="JSON 输出")
    p_wardrobe.add_argument("--category", help="分类筛选")
    p_wardrobe.add_argument("--force", action="store_true", help="强制删除")
    p_wardrobe.set_defaults(func=cmd_wardrobe)
    
    # === weather ===
    p_weather = subparsers.add_parser("weather", aliases=["wt"], help="天气查询")
    p_weather.add_argument("--city", default="大连", help="城市名称")
    p_weather.add_argument("--lat", type=float, help="纬度")
    p_weather.add_argument("--lon", type=float, help="经度")
    p_weather.set_defaults(func=cmd_weather)
    
    # === recommend ===
    p_recommend = subparsers.add_parser("recommend", aliases=["r"], help="穿搭推荐")
    p_recommend.add_argument("--items", help="指定衣物 ID")
    p_recommend.add_argument("--occasion", help="场合")
    p_recommend.add_argument("--city", default="大连", help="城市")
    p_recommend.set_defaults(func=cmd_recommend)
    
    # === score ===
    p_score = subparsers.add_parser("score", aliases=["s"], help="搭配评分")
    p_score.add_argument("--items", required=True, help="衣物 ID 列表（逗号分隔）")
    p_score.add_argument("--occasion", default="日常", help="场合")
    p_score.add_argument("--temp", type=int, help="温度")
    p_score.set_defaults(func=cmd_score)
    
    # === color ===
    p_color = subparsers.add_parser("color", aliases=["c"], help="色彩协调度")
    p_color.add_argument("--items", help="衣物 ID 列表（逗号分隔）")
    p_color.add_argument("--colors", help="HEX 色值列表（逗号分隔）")
    p_color.set_defaults(func=cmd_color)
    
    # === inverse ===
    p_inverse = subparsers.add_parser("inverse", aliases=["inv"], help="反向推导颜色")
    p_inverse.add_argument("--known", required=True, help="已知颜色（逗号分隔的 HEX）")
    p_inverse.add_argument("--target", type=float, required=True, help="目标分数")
    p_inverse.add_argument("--missing", type=int, required=True, help="需要补全的颜色数量")
    p_inverse.add_argument("--method", choices=["search", "global"], default="search", 
                           help="方法：search=搜索色卡库（快），global=全局优化（慢但可生成新颜色）")
    p_inverse.add_argument("--top", type=int, default=5, help="搜索法：返回前 N 个建议")
    p_inverse.add_argument("--samples", type=int, default=3, help="全局法：生成样本数量")
    p_inverse.add_argument("--maxiter", type=int, default=100, help="全局法：最大迭代次数")
    p_inverse.set_defaults(func=cmd_inverse)
    
    # === palette ===
    p_palette = subparsers.add_parser("palette", aliases=["p"], help="色卡管理")
    p_palette.add_argument("subcommand", choices=["list", "train", "scrape"], help="子命令")
    p_palette.add_argument("--top", type=int, help="显示前 N 个")
    p_palette.add_argument("--source", help="按来源筛选")
    p_palette.add_argument("--min-score", type=float, help="最低分数")
    p_palette.set_defaults(func=cmd_palette)
    
    # === knowledge ===
    p_knowledge = subparsers.add_parser("knowledge", aliases=["k"], help="知识库管理")
    p_knowledge.add_argument("subcommand", choices=["list", "show", "edit"], help="子命令")
    p_knowledge.add_argument("filename", nargs="?", help="文件名")
    p_knowledge.add_argument("--raw", action="store_true", help="原始 Markdown")
    p_knowledge.set_defaults(func=cmd_knowledge)
    
    # === config ===
    p_config = subparsers.add_parser("config", aliases=["cf"], help="配置查看")
    p_config.set_defaults(func=cmd_config)
    
    args = parser.parse_args()
    
    if args.version:
        cmd_version(args)
        return
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
def cmd_inverse(args):
    """反向推导颜色"""
    from scripts.color_inverse import suggest_colors
    known = [c.strip() for c in args.known.split(",")]
    suggest_colors(known, args.target, args.missing, args.top)

