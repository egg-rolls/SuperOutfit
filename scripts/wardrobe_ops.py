#!/usr/bin/env python3
"""
SuperOutfit 统一衣橱 CRUD
一套命令管理衣柜和购物清单，用 --wishlist 切换目标。

用法：
  python wardrobe_ops.py add --file item.yaml              # 添加到衣柜
  python wardrobe_ops.py add --file item.yaml --wishlist   # 添加到购物清单
  python wardrobe_ops.py list [--type X] [--season X] [--wishlist] [--json]
  python wardrobe_ops.py show item_001 [--wishlist] [--json]
  python wardrobe_ops.py update item_001 --file item.yaml  # 覆盖更新
  python wardrobe_ops.py delete item_001 [--wishlist]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ITEMS_DIR = DATA_DIR / "items"
WISHLIST_DIR = DATA_DIR / "wishlist"


def get_target_dir(wishlist=False):
    """获取目标目录"""
    return WISHLIST_DIR if wishlist else ITEMS_DIR


def ensure_dirs():
    """确保目录存在"""
    ITEMS_DIR.mkdir(parents=True, exist_ok=True)
    WISHLIST_DIR.mkdir(parents=True, exist_ok=True)


def next_id(target_dir):
    """生成下一个 ID"""
    prefix = "wish" if target_dir == WISHLIST_DIR else "item"
    existing = sorted(target_dir.glob(f"{prefix}_*.yaml"))
    if not existing:
        return f"{prefix}_001"
    last = existing[-1].stem
    num = int(last.split("_")[1]) + 1
    return f"{prefix}_{num:03d}"


def load_item(item_id, target_dir):
    """加载单件衣物"""
    path = target_dir / f"{item_id}.yaml"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        item = yaml.safe_load(f)
        if item:
            item["_file"] = f"{item_id}.yaml"
        return item


def load_all(target_dir):
    """加载目标目录下所有衣物"""
    if not target_dir.exists():
        return []
    items = []
    for f in sorted(target_dir.glob("*.yaml")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                item = yaml.safe_load(fp)
                if item:
                    item["_file"] = f.name
                    items.append(item)
        except:
            pass
    return items


def save_item(item, target_dir):
    """保存单件衣物"""
    path = target_dir / item["_file"]
    data = {k: v for k, v in item.items() if not k.startswith("_")}
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


# ==================== Commands ====================

def cmd_add(args):
    """从 YAML 文件添加衣物"""
    ensure_dirs()
    target = get_target_dir(args.wishlist)

    if not args.file:
        print(json.dumps({"error": "需要 --file <path.yaml>"}))
        sys.exit(1)

    file_path = Path(args.file)
    if not file_path.exists():
        print(json.dumps({"error": f"文件不存在: {args.file}"}))
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        item = yaml.safe_load(f)

    if not item:
        print(json.dumps({"error": "YAML 文件为空"}))
        sys.exit(1)

    # 自动生成 ID（如果未指定）
    item_id = item.get("id") or next_id(target)
    item["id"] = item_id
    item["_file"] = f"{item_id}.yaml"

    # 初始化穿着相关字段（如果缺失）
    item.setdefault("wear_count", 0)
    item.setdefault("last_worn", "")
    item.setdefault("wash_count", 0)
    item.setdefault("wash_frequency", 0)
    item.setdefault("last_washed", "")
    item.setdefault("wear_dates", [])

    save_item(item, target)
    label = "购物清单" if args.wishlist else "衣柜"
    print(json.dumps({"success": True, "id": item_id, "target": label}))


def cmd_list(args):
    """列出衣物"""
    ensure_dirs()
    target = get_target_dir(args.wishlist)
    items = load_all(target)

    # 筛选
    if args.type:
        items = [i for i in items if i.get("type") == args.type]
    if args.season:
        items = [i for i in items if args.season in i.get("season", []) or "四季" in i.get("season", [])]

    if args.json:
        result = []
        for item in items:
            # 直接返回完整 YAML 数据，前端自动同步
            result.append(item)
        label = "wishlist" if args.wishlist else "wardrobe"
        print(json.dumps({"target": label, "items": result, "total": len(result)}, ensure_ascii=False, indent=2))
        return

    if not items:
        label = "购物清单" if args.wishlist else "衣柜"
        print(f"{label}为空。")
        return

    label = "购物清单" if args.wishlist else "衣柜"
    print(f"\n{'='*60}")
    print(f"  {label} ({len(items)} 件)")
    print(f"{'='*60}")

    for item in items:
        colors = item.get("colors", {})
        color = colors.get("primary", "") if isinstance(colors, dict) else ""
        season_str = ",".join(item.get("season", [])) if item.get("season") else ""
        fav = "★" if item.get("favorite") else ""

        print(f"  {item.get('id',''):<12} {item.get('type','')}/{item.get('sub_type',''):<10} "
              f"{color:<6} [{season_str}] 穿:{item.get('wear_count',0)} {fav}")
    print()


def cmd_show(args):
    """查看单件详情"""
    target = get_target_dir(args.wishlist)
    item = load_item(args.item_id, target)

    if not item:
        print(json.dumps({"error": f"未找到 {args.item_id}"}))
        sys.exit(1)

    if args.json:
        data = {k: v for k, v in item.items() if not k.startswith("_")}
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        data = {k: v for k, v in item.items() if not k.startswith("_")}
        print(yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False))


def cmd_update(args):
    """从 YAML 文件覆盖更新"""
    target = get_target_dir(args.wishlist)
    item = load_item(args.item_id, target)

    if not item:
        print(json.dumps({"error": f"未找到 {args.item_id}"}))
        sys.exit(1)

    if not args.file:
        print(json.dumps({"error": "需要 --file <path.yaml>"}))
        sys.exit(1)

    file_path = Path(args.file)
    if not file_path.exists():
        print(json.dumps({"error": f"文件不存在: {args.file}"}))
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        new_data = yaml.safe_load(f)

    if not new_data:
        print(json.dumps({"error": "YAML 文件为空"}))
        sys.exit(1)

    # 保留 ID 和内部字段
    new_data["id"] = item["id"]
    new_data["_file"] = item["_file"]
    # 保留穿着数据（除非新文件明确覆盖）
    for key in ["wear_count", "last_worn", "wash_count", "wash_frequency", "last_washed", "wear_dates"]:
        if key not in new_data:
            new_data[key] = item.get(key, 0 if "count" in key else ([] if "dates" in key else ""))

    save_item(new_data, target)
    print(json.dumps({"success": True, "id": item["id"]}))


def cmd_delete(args):
    """删除衣物"""
    target = get_target_dir(args.wishlist)
    path = target / f"{args.item_id}.yaml"

    if not path.exists():
        print(json.dumps({"error": f"未找到 {args.item_id}"}))
        sys.exit(1)

    path.unlink()
    label = "购物清单" if args.wishlist else "衣柜"
    print(json.dumps({"success": True, "id": args.item_id, "target": label}))


def main():
    parser = argparse.ArgumentParser(description="SuperOutfit 统一衣橱管理")
    parser.add_argument("command", choices=["add", "list", "show", "edit", "delete"])
    parser.add_argument("item_id", nargs="?", help="衣物 ID (show/update/delete)")
    parser.add_argument("--file", help="YAML 文件路径 (add/update)")
    parser.add_argument("--type", help="按类型筛选 (list)")
    parser.add_argument("--season", help="按季节筛选 (list)")
    parser.add_argument("--wishlist", action="store_true", help="操作购物清单而非衣柜")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "show": cmd_show,
        "edit": cmd_update,
        "delete": cmd_delete,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()


# ==================== API 包装函数（返回 dict，不打印） ====================

def api_list(type=None, season=None, wishlist=False):
    ensure_dirs()
    target = get_target_dir(wishlist)
    items = load_all(target)
    if type:
        items = [i for i in items if i.get("type") == type]
    if season:
        items = [i for i in items if season in i.get("season", []) or "四季" in i.get("season", [])]
    label = "wishlist" if wishlist else "wardrobe"
    return {"target": label, "items": items, "total": len(items)}

def api_show(item_id, wishlist=False):
    target = get_target_dir(wishlist)
    item = load_item(item_id, target)
    if not item:
        return None
    return {k: v for k, v in item.items() if not k.startswith("_")}

def api_add(item_dict, wishlist=False):
    ensure_dirs()
    target = get_target_dir(wishlist)
    item_id = item_dict.get("id") or next_id(target)
    item_dict["id"] = item_id
    item_dict["_file"] = f"{item_id}.yaml"
    item_dict.setdefault("wear_count", 0)
    item_dict.setdefault("last_worn", "")
    item_dict.setdefault("wash_count", 0)
    item_dict.setdefault("wash_frequency", 0)
    item_dict.setdefault("last_washed", "")
    item_dict.setdefault("wear_dates", [])
    save_item(item_dict, target)
    return {"success": True, "id": item_id}

def api_update(item_id, new_data, wishlist=False):
    target = get_target_dir(wishlist)
    item = load_item(item_id, target)
    if not item:
        return {"error": f"未找到 {item_id}"}
    new_data["id"] = item["id"]
    new_data["_file"] = item["_file"]
    for key in ["wear_count", "last_worn", "wash_count", "wash_frequency", "last_washed", "wear_dates"]:
        if key not in new_data:
            new_data[key] = item.get(key, 0 if "count" in key else ([] if "dates" in key else ""))
    save_item(new_data, target)
    return {"success": True, "id": item_id}

def api_delete(item_id, wishlist=False):
    target = get_target_dir(wishlist)
    path = target / f"{item_id}.yaml"
    if not path.exists():
        return {"error": f"未找到 {item_id}"}
    path.unlink()
    return {"success": True, "id": item_id}

def api_stats(wishlist=False):
    items = load_all(get_target_dir(wishlist))
    from collections import Counter
    type_counts = Counter(i.get("type", "未知") for i in items)
    season_counts = Counter(s for i in items for s in (i.get("season") or []))
    total_wears = sum(i.get("wear_count", 0) for i in items)
    return {
        "total": len(items),
        "by_type": dict(type_counts),
        "by_season": dict(season_counts),
        "total_wears": total_wears,
    }
