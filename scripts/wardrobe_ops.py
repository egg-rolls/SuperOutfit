#!/usr/bin/env python3
"""
SuperOutfit 衣橱操作工具
用法：python wardrobe_ops.py <command> [options]
"""

import argparse
import json
import os
import sys
import yaml
from datetime import datetime, date
from pathlib import Path

# 数据目录
DATA_DIR = Path(os.environ.get("SUPEROUTFIT_DATA", Path(__file__).resolve().parent.parent / "data"))
ITEMS_DIR = DATA_DIR / "items"
IMAGES_DIR = DATA_DIR / "images"
ARCHIVE_DIR = DATA_DIR / "archive"
INDEX_FILE = DATA_DIR / "wardrobe_index.yaml"
HISTORY_FILE = DATA_DIR / "history.yaml"

def ensure_dirs():
    for d in [ITEMS_DIR, IMAGES_DIR, ARCHIVE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def next_item_id():
    """生成下一个衣物 ID"""
    existing = sorted(ITEMS_DIR.glob("item_*.yaml"))
    if not existing:
        return "item_001"
    last = existing[-1].stem  # item_XXX
    num = int(last.split("_")[1]) + 1
    return f"item_{num:03d}"

def next_outfit_id():
    """生成下一个搭配 ID"""
    outfits_dir = DATA_DIR / "outfits"
    outfits_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(outfits_dir.glob("outfit_*.yaml"))
    if not existing:
        return "outfit_001"
    last = existing[-1].stem
    num = int(last.split("_")[1]) + 1
    return f"outfit_{num:03d}"

def load_yaml(path):
    """安全加载 YAML"""
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    """保存 YAML"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

# ==================== Commands ====================

def cmd_add(args):
    """添加衣物"""
    ensure_dirs()
    item_id = args.id or next_item_id()
    
    item = {
        "id": item_id,
        "type": args.type or "",
        "sub_type": args.sub_type or "",
        "colors": {
            "primary": args.primary_color or "",
            "secondary": args.secondary_color or "",
            "pattern": args.pattern or "纯色",
        },
        "material": args.material or "",
        "fit": args.fit or "常规",
        "size": args.size or "",
        "brand": args.brand or "",
        "price": args.price or 0,
        "purchase_date": args.purchase_date or "",
        "condition": "完好",
        "wear_count": 0,
        "last_worn": "",
        "style": [s.strip() for s in args.style.split(",")] if args.style else [],
        "season": [s.strip() for s in args.season.split(",")] if args.season else [],
        "temperature_range": args.temp_range or "0~40",
        "occasion": [s.strip() for s in args.occasion.split(",")] if args.occasion else [],
        "layer": args.layer or "可单穿",
        "favorite": args.favorite or False,
        "tags": [s.strip() for s in args.tags.split(",")] if args.tags else [],
        "image": args.image or "",
        "pair_with": [],
        "restrict": [],
    }
    
    save_yaml(ITEMS_DIR / f"{item_id}.yaml", item)
    reindex()
    print(json.dumps({"success": True, "id": item_id, "message": f"已添加 {item_id}"}))

def cmd_list(args):
    """列出衣物"""
    ensure_dirs()
    items = []
    for f in sorted(ITEMS_DIR.glob("*.yaml")):
        item = load_yaml(f)
        if item:
            if args.category and item.get("type") != args.category:
                continue
            if args.style and args.style not in item.get("style", []):
                continue
            if args.season and args.season not in item.get("season", []):
                continue
            if args.occasion and args.occasion not in item.get("occasion", []):
                continue
            if args.favorites and not item.get("favorite"):
                continue
            items.append(item)
    
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return
    
    # 表格输出
    if not items:
        print("衣橱为空。")
        return
    
    print(f"{'ID':<12} {'类型':<6} {'子类型':<10} {'主色':<6} {'品牌':<10} {'风格':<20} {'穿着次数':<8} {'收藏'}")
    print("-" * 90)
    for item in items:
        styles = ",".join(item.get("style", []))[:18]
        fav = "★" if item.get("favorite") else ""
        print(f"{item['id']:<12} {item.get('type',''):<6} {item.get('sub_type',''):<10} "
              f"{item.get('colors',{}).get('primary',''):<6} {item.get('brand',''):<10} "
              f"{styles:<20} {item.get('wear_count',0):<8} {fav}")
    print(f"\n共 {len(items)} 件")

def cmd_show(args):
    """查看衣物详情"""
    path = ITEMS_DIR / f"{args.item_id}.yaml"
    item = load_yaml(path)
    if not item:
        print(json.dumps({"error": f"未找到 {args.item_id}"}))
        sys.exit(1)
    
    if args.json:
        print(json.dumps(item, ensure_ascii=False, indent=2))
    else:
        print(yaml.dump(item, allow_unicode=True, default_flow_style=False, sort_keys=False))

def cmd_update(args):
    """更新衣物属性"""
    path = ITEMS_DIR / f"{args.item_id}.yaml"
    item = load_yaml(path)
    if not item:
        print(json.dumps({"error": f"未找到 {args.item_id}"}))
        sys.exit(1)
    
    updated = []
    if args.type:
        item["type"] = args.type
        updated.append("type")
    if args.sub_type:
        item["sub_type"] = args.sub_type
        updated.append("sub_type")
    if args.primary_color:
        item.setdefault("colors", {})["primary"] = args.primary_color
        updated.append("primary_color")
    if args.material:
        item["material"] = args.material
        updated.append("material")
    if args.wear_count is not None:
        item["wear_count"] = args.wear_count
        updated.append("wear_count")
    if args.last_worn:
        item["last_worn"] = args.last_worn
        updated.append("last_worn")
    if args.favorite is not None:
        item["favorite"] = args.favorite
        updated.append("favorite")
    if args.style:
        item["style"] = [s.strip() for s in args.style.split(",")]
        updated.append("style")
    if args.condition:
        item["condition"] = args.condition
        updated.append("condition")
    
    save_yaml(path, item)
    reindex()
    print(json.dumps({"success": True, "id": args.item_id, "updated": updated}))

def cmd_delete(args):
    """删除衣物（移到 archive）"""
    src = ITEMS_DIR / f"{args.item_id}.yaml"
    if not src.exists():
        print(json.dumps({"error": f"未找到 {args.item_id}"}))
        sys.exit(1)
    
    # 移到归档
    dst = ARCHIVE_DIR / f"{args.item_id}.yaml"
    item = load_yaml(src)
    item["_archived_at"] = datetime.now().isoformat()
    save_yaml(dst, item)
    src.unlink()
    
    # 移动图片（如果存在）
    img = item.get("image", "")
    if img:
        img_src = IMAGES_DIR / img
        if img_src.exists():
            img_dst = ARCHIVE_DIR / img
            img_src.rename(img_dst)
    
    reindex()
    print(json.dumps({"success": True, "id": args.item_id, "message": "已移到归档"}))

def cmd_stats(args):
    """统计概览"""
    ensure_dirs()
    items = []
    for f in ITEMS_DIR.glob("*.yaml"):
        item = load_yaml(f)
        if item:
            items.append(item)
    
    if not items:
        print("衣橱为空。")
        return
    
    # 按类型统计
    by_type = {}
    total_value = 0
    total_wear = 0
    for item in items:
        t = item.get("type", "未分类")
        by_type[t] = by_type.get(t, 0) + 1
        total_value += item.get("price", 0)
        total_wear += item.get("wear_count", 0)
    
    # 最常穿 / 最少穿
    sorted_by_wear = sorted(items, key=lambda x: x.get("wear_count", 0), reverse=True)
    
    stats = {
        "total_items": len(items),
        "total_value": total_value,
        "total_wear_count": total_wear,
        "avg_wear_count": round(total_wear / len(items), 1) if items else 0,
        "by_type": by_type,
        "most_worn": sorted_by_wear[0]["id"] if sorted_by_wear else None,
        "least_worn": sorted_by_wear[-1]["id"] if sorted_by_wear else None,
        "favorites": sum(1 for i in items if i.get("favorite")),
    }
    
    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print(f"=== 衣橱概览 ===")
        print(f"总件数：{stats['total_items']}")
        print(f"总价值：¥{stats['total_value']}")
        print(f"总穿着：{stats['total_wear_count']} 次（平均 {stats['avg_wear_count']} 次/件）")
        print(f"收藏数：{stats['favorites']}")
        print(f"\n按类型：")
        for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
            print(f"  {t}: {count} 件")
        if sorted_by_wear:
            print(f"\n最常穿：{sorted_by_wear[0]['id']}（{sorted_by_wear[0].get('wear_count',0)} 次）")
            print(f"最少穿：{sorted_by_wear[-1]['id']}（{sorted_by_wear[-1].get('wear_count',0)} 次）")

def cmd_reindex(args=None):
    """重建索引"""
    reindex()
    print("索引已重建。")

def reindex():
    """重建 wardrobe_index.yaml"""
    ensure_dirs()
    items = []
    for f in sorted(ITEMS_DIR.glob("*.yaml")):
        item = load_yaml(f)
        if item:
            items.append(item)
    
    by_type = {}
    total_value = 0
    for item in items:
        t = item.get("type", "未分类")
        if t not in by_type:
            by_type[t] = {"count": 0, "items": [], "total_wear": 0}
        by_type[t]["count"] += 1
        by_type[t]["items"].append(item["id"])
        by_type[t]["total_wear"] += item.get("wear_count", 0)
    
    # 计算平均穿着次数
    for t in by_type:
        count = by_type[t]["count"]
        by_type[t]["avg_wear_count"] = round(by_type[t]["total_wear"] / count, 1) if count else 0
        del by_type[t]["total_wear"]
    
    sorted_by_wear = sorted(items, key=lambda x: x.get("wear_count", 0), reverse=True)
    sorted_by_date = sorted(items, key=lambda x: x.get("purchase_date", ""), reverse=True)
    
    index = {
        "total_items": len(items),
        "total_value": sum(i.get("price", 0) for i in items),
        "last_updated": datetime.now().isoformat(),
        "categories": by_type,
        "stats": {
            "most_worn": sorted_by_wear[0]["id"] if sorted_by_wear else None,
            "least_worn": sorted_by_wear[-1]["id"] if sorted_by_wear else None,
            "newest": sorted_by_date[0]["id"] if sorted_by_date else None,
        },
    }
    
    save_yaml(INDEX_FILE, index)

def cmd_record(args):
    """记录穿搭（今天穿了什么）"""
    ensure_dirs()
    item_ids = [s.strip() for s in args.items.split(",")]
    today = date.today().isoformat()
    
    updated = []
    for item_id in item_ids:
        path = ITEMS_DIR / f"{item_id}.yaml"
        item = load_yaml(path)
        if not item:
            print(f"警告：未找到 {item_id}，跳过")
            continue
        item["wear_count"] = item.get("wear_count", 0) + 1
        item["last_worn"] = today
        save_yaml(path, item)
        updated.append(item_id)
    
    # 追加到历史
    history = load_yaml(HISTORY_FILE) or {"records": []}
    history["records"].append({
        "date": today,
        "items": updated,
        "occasion": args.occasion or "",
        "notes": args.notes or "",
    })
    save_yaml(HISTORY_FILE, history)
    reindex()
    
    print(json.dumps({"success": True, "updated": updated, "date": today}))

def cmd_restore(args):
    """从归档恢复衣物"""
    src = ARCHIVE_DIR / f"{args.item_id}.yaml"
    if not src.exists():
        print(json.dumps({"error": f"归档中未找到 {args.item_id}"}))
        sys.exit(1)
    
    item = load_yaml(src)
    if "_archived_at" in item:
        del item["_archived_at"]
    
    dst = ITEMS_DIR / f"{args.item_id}.yaml"
    save_yaml(dst, item)
    src.unlink()
    
    # 恢复图片
    img = item.get("image", "")
    if img:
        img_src = ARCHIVE_DIR / img
        if img_src.exists():
            img_dst = IMAGES_DIR / img
            img_src.rename(img_dst)
    
    reindex()
    print(json.dumps({"success": True, "id": args.item_id, "message": "已从归档恢复"}))

# ==================== Main ====================

def main():
    parser = argparse.ArgumentParser(description="SuperOutfit 衣橱管理工具")
    sub = parser.add_subparsers(dest="command", help="命令")
    
    # add
    p_add = sub.add_parser("add", help="添加衣物")
    p_add.add_argument("--id", help="指定 ID（默认自动生成）")
    p_add.add_argument("--type", help="类型：上衣/裤子/外套/鞋子/配饰")
    p_add.add_argument("--sub-type", help="子类型：T恤/衬衫/...")
    p_add.add_argument("--primary-color", help="主色")
    p_add.add_argument("--secondary-color", help="副色/花纹")
    p_add.add_argument("--pattern", help="图案：纯色/条纹/格子/...")
    p_add.add_argument("--material", help="材质")
    p_add.add_argument("--fit", help="版型：修身/常规/宽松/...")
    p_add.add_argument("--size", help="尺码")
    p_add.add_argument("--brand", help="品牌")
    p_add.add_argument("--price", type=int, help="价格")
    p_add.add_argument("--purchase-date", help="购买日期")
    p_add.add_argument("--style", help="风格标签，逗号分隔")
    p_add.add_argument("--season", help="季节，逗号分隔")
    p_add.add_argument("--temp-range", help="适穿温度，如 15~25")
    p_add.add_argument("--occasion", help="场合，逗号分隔")
    p_add.add_argument("--layer", help="层次：内层/中间层/外层/可单穿")
    p_add.add_argument("--favorite", action="store_true", help="标记为收藏")
    p_add.add_argument("--tags", help="自定义标签，逗号分隔")
    p_add.add_argument("--image", help="图片文件名")
    
    # list
    p_list = sub.add_parser("list", help="列出衣物")
    p_list.add_argument("--json", action="store_true", help="JSON 输出")
    p_list.add_argument("--category", help="按类型筛选")
    p_list.add_argument("--style", help="按风格筛选")
    p_list.add_argument("--season", help="按季节筛选")
    p_list.add_argument("--occasion", help="按场合筛选")
    p_list.add_argument("--favorites", action="store_true", help="只看收藏")
    
    # show
    p_show = sub.add_parser("show", help="查看衣物详情")
    p_show.add_argument("item_id", help="衣物 ID")
    p_show.add_argument("--json", action="store_true", help="JSON 输出")
    
    # update
    p_update = sub.add_parser("update", help="更新衣物")
    p_update.add_argument("item_id", help="衣物 ID")
    p_update.add_argument("--type", help="类型")
    p_update.add_argument("--sub-type", help="子类型")
    p_update.add_argument("--primary-color", help="主色")
    p_update.add_argument("--material", help="材质")
    p_update.add_argument("--wear-count", type=int, help="穿着次数")
    p_update.add_argument("--last-worn", help="最后穿着日期")
    p_update.add_argument("--favorite", type=lambda x: x.lower() == "true", help="收藏状态")
    p_update.add_argument("--style", help="风格标签")
    p_update.add_argument("--condition", help="状态")
    
    # delete
    p_delete = sub.add_parser("delete", help="删除衣物（移到归档）")
    p_delete.add_argument("item_id", help="衣物 ID")
    
    # stats
    p_stats = sub.add_parser("stats", help="统计概览")
    p_stats.add_argument("--json", action="store_true", help="JSON 输出")
    
    # reindex
    sub.add_parser("reindex", help="重建索引")
    
    # record
    p_record = sub.add_parser("record", help="记录今天穿搭")
    p_record.add_argument("--items", required=True, help="衣物 ID，逗号分隔")
    p_record.add_argument("--occasion", help="场合")
    p_record.add_argument("--notes", help="备注")
    
    # restore
    p_restore = sub.add_parser("restore", help="从归档恢复衣物")
    p_restore.add_argument("item_id", help="衣物 ID")
    
    args = parser.parse_args()
    
    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "show": cmd_show,
        "update": cmd_update,
        "delete": cmd_delete,
        "stats": cmd_stats,
        "reindex": cmd_reindex,
        "record": cmd_record,
        "restore": cmd_restore,
    }
    
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
