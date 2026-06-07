#!/usr/bin/env python3
"""
SuperOutfit 穿着管理
记录穿着、标记清洗、查看需清洗、穿着报表。
所有数据存储在 item YAML 中。

用法：
  python wear.py add --items item_001,item_002              # 记录今天穿了
  python wear.py add --items item_001 --date 2025-06-01     # 指定日期
  python wear.py wash --items item_001,item_002             # 标记已清洗
  python wear.py check [--type 上衣]                        # 需清洗的
  python wear.py report [--items item_001] [--type 下装]    # 穿着报表 + 性价比
"""

import argparse
import json
import sys
from datetime import datetime, date
from pathlib import Path

import yaml

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ITEMS_DIR = DATA_DIR / "items"


def load_items():
    """加载所有衣物"""
    if not ITEMS_DIR.exists():
        return []
    items = []
    for f in sorted(ITEMS_DIR.glob("*.yaml")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                item = yaml.safe_load(fp)
                if item:
                    item["_file"] = f.name
                    items.append(item)
        except:
            pass
    return items


def load_item(item_id):
    """加载单件"""
    path = ITEMS_DIR / f"{item_id}.yaml"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        item = yaml.safe_load(f)
        if item:
            item["_file"] = f"{item_id}.yaml"
        return item


def save_item(item):
    """保存单件"""
    path = ITEMS_DIR / item["_file"]
    data = {k: v for k, v in item.items() if not k.startswith("_")}
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def resolve_items(args):
    """解析目标衣物"""
    if args.items:
        ids = [s.strip() for s in args.items.split(",")]
        return [load_item(i) for i in ids if load_item(i)]
    elif args.type:
        return [i for i in load_items() if i.get("type") == args.type]
    return []


def cmd_add(args):
    """记录穿着"""
    targets = resolve_items(args)
    if not targets:
        print(json.dumps({"error": "没有匹配的衣物，需要 --items 或 --type"}))
        return

    wear_date = args.date or date.today().isoformat()
    try:
        datetime.strptime(wear_date, "%Y-%m-%d")
    except ValueError:
        print(json.dumps({"error": f"日期格式错误: {wear_date}"}))
        return

    updated = []
    for item in targets:
        item_id = item.get("id", item["_file"].replace(".yaml", ""))
        item["wear_count"] = item.get("wear_count", 0) + 1
        item["last_worn"] = wear_date

        wear_dates = item.get("wear_dates", [])
        if not isinstance(wear_dates, list):
            wear_dates = []
        wear_dates.append(wear_date)
        item["wear_dates"] = wear_dates

        # 自动计算 needs_wash
        wash_freq = item.get("wash_frequency", 0)
        if wash_freq > 0:
            wear_since_wash = item["wear_count"] - item.get("wash_count", 0)
            item["needs_wash"] = wear_since_wash >= wash_freq
        else:
            item["needs_wash"] = False

        save_item(item)
        updated.append({
            "id": item_id,
            "wear_count": item["wear_count"],
            "needs_wash": item.get("needs_wash", False)
        })

    print(json.dumps({"success": True, "date": wear_date, "count": len(updated), "items": updated}, ensure_ascii=False, indent=2))


def cmd_wash(args):
    """标记已清洗"""
    targets = resolve_items(args)
    if not targets:
        print(json.dumps({"error": "没有匹配的衣物，需要 --items 或 --type"}))
        return

    today = date.today().isoformat()
    updated = []

    for item in targets:
        item_id = item.get("id", item["_file"].replace(".yaml", ""))
        item["wash_count"] = item.get("wear_count", 0)
        item["last_washed"] = today
        item["needs_wash"] = False  # 清洗后重置
        save_item(item)
        updated.append({"id": item_id, "wash_count": item["wash_count"], "needs_wash": False})

    print(json.dumps({"success": True, "count": len(updated), "items": updated}, ensure_ascii=False, indent=2))


def cmd_check(args):
    """查看需要清洗的衣物"""
    items = load_items()
    if args.type:
        items = [i for i in items if i.get("type") == args.type]

    needs_wash = []
    for item in items:
        wash_freq = item.get("wash_frequency", 0)
        if wash_freq <= 0:
            continue

        wear_count = item.get("wear_count", 0)
        wash_count = item.get("wash_count", 0)
        wear_since_wash = wear_count - wash_count

        if wear_since_wash >= wash_freq:
            item_id = item.get("id", item["_file"].replace(".yaml", ""))
            needs_wash.append({
                "id": item_id,
                "type": item.get("type", ""),
                "sub_type": item.get("sub_type", ""),
                "wash_frequency": wash_freq,
                "wear_since_wash": wear_since_wash,
            })

    needs_wash.sort(key=lambda x: x["wear_since_wash"] - x["wash_frequency"], reverse=True)

    if args.json:
        print(json.dumps({"needs_wash": needs_wash, "total": len(needs_wash)}, ensure_ascii=False, indent=2))
    else:
        if not needs_wash:
            try:
                from output import empty_state
                empty_state("🧺", "没有需要清洗的衣物")
            except ImportError:
                print("没有需要清洗的衣物。")
            return
        try:
            from output import console
            from rich.table import Table
            from rich.text import Text
            from rich import box

            t = Table(box=box.SIMPLE_HEAD, border_style="#e6dfd8",
                      title=f"需要清洗 · {len(needs_wash)} 件", title_style="bold #cc785c")
            t.add_column("", width=3)
            t.add_column("ID", style="dim")
            t.add_column("类型")
            t.add_column("名称", style="bold")
            t.add_column("已穿", justify="right")
            t.add_column("建议", justify="right", style="dim")
            t.add_column("超出", justify="right")

            for i in needs_wash:
                over = i["wear_since_wash"] - i["wash_frequency"]
                if over >= 2:
                    urgency = Text("!!!", style="bold #c64545")
                elif over >= 1:
                    urgency = Text("!", style="bold #d4a017")
                else:
                    urgency = Text("·", style="dim")
                t.add_row(
                    urgency,
                    i["id"],
                    i["type"],
                    i["sub_type"],
                    str(i["wear_since_wash"]),
                    str(i["wash_frequency"]),
                    f"+{over}" if over > 0 else "0",
                )
            console.print()
            console.print(t)
            console.print()
        except ImportError:
            print(f"\n  需要清洗 ({len(needs_wash)} 件)")
            for i in needs_wash:
                over = i["wear_since_wash"] - i["wash_frequency"]
                tag = "!!!" if over >= 2 else ("!" if over >= 1 else "")
                print(f"  {tag} {i['id']:<12} {i['type']}/{i['sub_type']:<10} "
                      f"已穿{i['wear_since_wash']}次 (建议{i['wash_frequency']}次洗)")


def cmd_report(args):
    """穿着报表 + 性价比"""
    if args.items or args.type:
        # 单件/多件详情
        targets = resolve_items(args)
        if not targets:
            print(json.dumps({"error": "没有匹配的衣物"}))
            return

        reports = []
        for item in targets:
            item_id = item.get("id", item["_file"].replace(".yaml", ""))
            price = item.get("price", 0)
            wear_count = item.get("wear_count", 0)
            cost_per_wear = round(price / wear_count, 1) if wear_count > 0 and price > 0 else None

            reports.append({
                "id": item_id,
                "type": item.get("type", ""),
                "sub_type": item.get("sub_type", ""),
                "wear_count": wear_count,
                "last_worn": item.get("last_worn", ""),
                "price": price,
                "cost_per_wear": cost_per_wear,
                "wash_frequency": item.get("wash_frequency", 0),
                "wear_dates": item.get("wear_dates", [])[-5:],  # 最近5次
            })

        if args.json:
            print(json.dumps(reports, ensure_ascii=False, indent=2))
        else:
            try:
                from output import console, info_table
                from rich.panel import Panel
                from rich.table import Table as RichTable
                from rich import box

                for r in reports:
                    rows = [
                        ("ID", r["id"]),
                        ("类型", f"{r['type']} / {r['sub_type']}"),
                        ("穿着", f"{r['wear_count']} 次"),
                        ("最后", r["last_worn"] or "从未"),
                    ]
                    if r["price"]:
                        rows.append(("价格", f"¥{r['price']}"))
                        rows.append(("单次成本", f"¥{r['cost_per_wear']}" if r["cost_per_wear"] else "-"))
                    if r["wear_dates"]:
                        rows.append(("近期", ", ".join(r["wear_dates"])))

                    t = RichTable(box=None, show_header=False, padding=(0, 2))
                    t.add_column(style="dim", min_width=10)
                    t.add_column()
                    for label, value in rows:
                        t.add_row(label, str(value))
                    title = f"{r['type']} / {r['sub_type']}"
                    console.print(Panel(t, title=title, border_style="#cc785c", box=box.ROUNDED, expand=False))
                console.print()
            except ImportError:
                for r in reports:
                    print(f"\n  {r['id']} {r['type']}/{r['sub_type']}")
                    print(f"    穿着: {r['wear_count']}次  最后: {r['last_worn'] or '从未'}")
                    if r["price"]:
                        print(f"    价格: ¥{r['price']}  单次: ¥{r['cost_per_wear'] or '-'}")
                    if r["wear_dates"]:
                        print(f"    近期: {', '.join(r['wear_dates'])}")
    else:
        # 全局报表
        items = load_items()
        if not items:
            print("衣橱为空。")
            return

        total_wear = sum(i.get("wear_count", 0) for i in items)
        total_price = sum(i.get("price", 0) for i in items)

        most_worn = sorted(items, key=lambda x: x.get("wear_count", 0), reverse=True)
        valued = sorted(
            [{"id": i.get("id",""), "type": i.get("type",""), "sub_type": i.get("sub_type",""),
              "price": i.get("price",0), "wear_count": i.get("wear_count",0),
              "cpw": round(i.get("price",0)/i.get("wear_count",1), 1)}
             for i in items if i.get("price",0) > 0 and i.get("wear_count",0) > 0],
            key=lambda x: x["cpw"]
        )
        never_worn = [i for i in items if i.get("wear_count", 0) == 0]

        if args.json:
            print(json.dumps({
                "total_items": len(items),
                "total_wear": total_wear,
                "total_price": total_price,
                "avg_wear": round(total_wear / len(items), 1),
                "most_worn": [{"id": i.get("id",""), "count": i.get("wear_count",0)} for i in most_worn[:5]],
                "best_value": valued[:5],
                "never_worn": [i.get("id","") for i in never_worn],
            }, ensure_ascii=False, indent=2))
        else:
            try:
                from output import console, bar_chart, info_table
                from rich.table import Table
                from rich.text import Text
                from rich.panel import Panel
                from rich import box

                # 概览面板
                avg = round(total_wear / len(items), 1)
                overview = Table(box=None, show_header=False, padding=(0, 2))
                overview.add_column(style="dim", min_width=10)
                overview.add_column()
                overview.add_row("总件数", str(len(items)))
                overview.add_row("总穿着", f"{total_wear} 次")
                overview.add_row("均穿", f"{avg} 次/件")
                if total_price:
                    overview.add_row("总价值", f"¥{total_price}")
                console.print()
                console.print(Panel(overview, title="穿着报表", border_style="#cc785c", box=box.ROUNDED, expand=False))

                # 最常穿（带条形图）
                if most_worn and most_worn[0].get("wear_count", 0) > 0:
                    t = Table(box=box.SIMPLE_HEAD, border_style="#e6dfd8",
                              title="最常穿", title_style="bold #cc785c")
                    t.add_column("#", style="dim", width=3)
                    t.add_column("ID", style="dim")
                    t.add_column("名称")
                    t.add_column("条形图")
                    t.add_column("次数", justify="right")
                    for i, m in enumerate(most_worn[:5]):
                        wc = m.get("wear_count", 0)
                        if wc == 0: break
                        t.add_row(
                            str(i + 1),
                            m.get("id", ""),
                            f"{m.get('type', '')}/{m.get('sub_type', '')}",
                            bar_chart(wc),
                            str(wc),
                        )
                    console.print(t)

                # 性价比
                if valued:
                    t = Table(box=box.SIMPLE_HEAD, border_style="#e6dfd8",
                              title="性价比 TOP 5", title_style="bold #cc785c")
                    t.add_column("#", style="dim", width=3)
                    t.add_column("ID", style="dim")
                    t.add_column("名称")
                    t.add_column("价格", justify="right")
                    t.add_column("单次成本", justify="right", style="bold #5db872")
                    for i, v in enumerate(valued[:5]):
                        t.add_row(
                            str(i + 1),
                            v["id"],
                            f"{v['type']}/{v['sub_type']}",
                            f"¥{v['price']}",
                            f"¥{v['cpw']}/次",
                        )
                    console.print(t)

                # 从未穿着
                if never_worn:
                    names = [f"{n.get('id', '')} {n.get('type', '')}/{n.get('sub_type', '')}" for n in never_worn]
                    console.print(f"\n  [dim]从未穿着 ({len(never_worn)} 件):[/] [muted]{', '.join(names)}[/]")
                console.print()
            except ImportError:
                print(f"\n  穿着报表")
                print(f"  总件数: {len(items)}  总穿着: {total_wear}次  均穿: {round(total_wear/len(items),1)}次/件")
                if most_worn and most_worn[0].get("wear_count", 0) > 0:
                    print(f"\n  最常穿:")
                    for i, m in enumerate(most_worn[:5]):
                        wc = m.get("wear_count", 0)
                        if wc == 0: break
                        bar = "█" * min(wc, 20)
                        print(f"    {i+1}. {m.get('id','')} {m.get('type','')}/{m.get('sub_type','')} {bar} {wc}次")


def main():
    parser = argparse.ArgumentParser(description="SuperOutfit 穿着管理")
    parser.add_argument("action", choices=["add", "wash", "check", "report"])
    parser.add_argument("--items", help="衣物 ID (逗号分隔)")
    parser.add_argument("--type", help="按类型筛选")
    parser.add_argument("--date", help="穿着日期 YYYY-MM-DD")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    {"add": cmd_add, "wash": cmd_wash, "check": cmd_check, "report": cmd_report}[args.action](args)


if __name__ == "__main__":
    main()


# ==================== API 包装函数（返回 dict，不打印） ====================

def api_record(item_ids, date_str=None):
    targets = [load_item(i) for i in item_ids]
    targets = [t for t in targets if t]
    if not targets:
        return {"error": "没有匹配的衣物"}

    wear_date = date_str or date.today().isoformat()
    updated = []
    for item in targets:
        item_id = item.get("id", item["_file"].replace(".yaml", ""))
        item["wear_count"] = item.get("wear_count", 0) + 1
        item["last_worn"] = wear_date
        wear_dates = item.get("wear_dates", [])
        if not isinstance(wear_dates, list):
            wear_dates = []
        wear_dates.append(wear_date)
        item["wear_dates"] = wear_dates
        wash_freq = item.get("wash_frequency", 0)
        if wash_freq > 0:
            wear_since_wash = item["wear_count"] - item.get("wash_count", 0)
            item["needs_wash"] = wear_since_wash >= wash_freq
        else:
            item["needs_wash"] = False
        save_item(item)
        updated.append({"id": item_id, "wear_count": item["wear_count"], "needs_wash": item.get("needs_wash", False)})
    return {"success": True, "date": wear_date, "count": len(updated), "items": updated}

def api_wash(item_ids):
    targets = [load_item(i) for i in item_ids]
    targets = [t for t in targets if t]
    if not targets:
        return {"error": "没有匹配的衣物"}
    today = date.today().isoformat()
    updated = []
    for item in targets:
        item_id = item.get("id", item["_file"].replace(".yaml", ""))
        item["wash_count"] = item.get("wear_count", 0)
        item["last_washed"] = today
        item["needs_wash"] = False
        save_item(item)
        updated.append({"id": item_id, "wash_count": item["wash_count"], "needs_wash": False})
    return {"success": True, "count": len(updated), "items": updated}

def api_check(type_filter=None):
    items = load_items()
    if type_filter:
        items = [i for i in items if i.get("type") == type_filter]
    needs_wash = []
    for item in items:
        wash_freq = item.get("wash_frequency", 0)
        if wash_freq <= 0:
            continue
        wear_count = item.get("wear_count", 0)
        wash_count = item.get("wash_count", 0)
        if wear_count - wash_count >= wash_freq:
            item_id = item.get("id", item["_file"].replace(".yaml", ""))
            needs_wash.append({"id": item_id, "type": item.get("type", ""), "sub_type": item.get("sub_type", ""), "wear_since_wash": wear_count - wash_count, "wash_frequency": wash_freq})
    return {"needs_wash": needs_wash, "total": len(needs_wash)}
