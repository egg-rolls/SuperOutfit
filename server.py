#!/usr/bin/env python3
"""
SuperOutfit MCP Server
通过 MCP 协议暴露穿搭工具，供任何 AI Agent 调用。

启动：python server.py
配置：在 Agent 的 MCP 配置中添加本 server
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"

def run_script(name, args=None):
    """运行脚本并返回输出"""
    cmd = [sys.executable, str(SCRIPTS / name)]
    if args:
        cmd.extend(args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout.strip()

def load_json_output(name, args=None):
    """运行脚本并解析 JSON 输出"""
    output = run_script(name, args)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"raw": output}

# ==================== MCP Tool Definitions ====================

TOOLS = [
    {
        "name": "wardrobe_list",
        "description": "列出衣橱中的衣物。支持按类型、风格、季节筛选。返回 JSON 格式的衣物列表。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "按类型筛选：上衣/裤子/外套/鞋子/配饰"},
                "style": {"type": "string", "description": "按风格筛选：通勤/简约/工装/..."},
                "season": {"type": "string", "description": "按季节筛选：春/夏/秋/冬"},
            },
        },
    },
    {
        "name": "wardrobe_add",
        "description": "添加衣物到衣橱。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "类型：上衣/裤子/外套/鞋子/配饰"},
                "sub_type": {"type": "string", "description": "子类型：T恤/衬衫/牛仔裤/..."},
                "primary_color": {"type": "string", "description": "主色名称"},
                "primary_hex": {"type": "string", "description": "主色 HEX 色值，如 #F5F0E8"},
                "material": {"type": "string", "description": "材质"},
                "fit": {"type": "string", "description": "版型：修身/常规/宽松"},
                "style": {"type": "string", "description": "风格标签，逗号分隔"},
                "season": {"type": "string", "description": "季节，逗号分隔"},
                "temp_range": {"type": "string", "description": "适穿温度，如 18~32"},
                "occasion": {"type": "string", "description": "场合，逗号分隔"},
                "brand": {"type": "string", "description": "品牌"},
                "price": {"type": "integer", "description": "价格"},
                "image": {"type": "string", "description": "图片文件名"},
            },
            "required": ["type", "sub_type", "primary_color"],
        },
    },
    {
        "name": "wardrobe_show",
        "description": "查看单件衣物详情。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "衣物 ID，如 item_001"},
            },
            "required": ["item_id"],
        },
    },
    {
        "name": "wardrobe_update",
        "description": "更新衣物属性。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "衣物 ID"},
                "wear_count": {"type": "integer", "description": "穿着次数"},
                "last_worn": {"type": "string", "description": "最后穿着日期"},
                "favorite": {"type": "boolean", "description": "是否收藏"},
            },
            "required": ["item_id"],
        },
    },
    {
        "name": "wardrobe_delete",
        "description": "删除衣物（移到归档，不丢失）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "衣物 ID"},
            },
            "required": ["item_id"],
        },
    },
    {
        "name": "wardrobe_stats",
        "description": "衣橱统计概览：总数、按类型分布、最常穿/最少穿。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "wardrobe_record",
        "description": "记录今天穿了什么，自动更新穿着次数。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "items": {"type": "string", "description": "衣物 ID，逗号分隔，如 item_001,item_003"},
                "occasion": {"type": "string", "description": "场合"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["items"],
        },
    },
    {
        "name": "weather_query",
        "description": "查询天气信息，返回温度、天气状况、穿衣建议。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称，如 大连、北京"},
                "date": {"type": "string", "description": "日期 YYYY-MM-DD（默认今天，支持未来7天）"},
            },
            "required": ["city"],
        },
    },
    {
        "name": "color_score",
        "description": "计算一组衣物的色彩协调度（0-100 分，SSS/SS/S/A/B/C/D 等级）。基于 5462 组真实色卡训练的高斯过程模型。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "衣物 ID 列表，如 [\"item_001\", \"item_003\", \"item_006\"]",
                },
                "hex_colors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "直接传入 HEX 色值列表，如 [\"#F5F0E8\", \"#C4A97D\"]",
                },
            },
        },
    },
    {
        "name": "outfit_score",
        "description": "搭配综合评分：颜色协调（25%）+ 风格一致（20%）+ 场合匹配（20%）+ 天气适配（15%）+ 穿着新鲜度（10%）+ 用户偏好（10%）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "衣物 ID 列表",
                },
                "occasion": {"type": "string", "description": "场合"},
                "temperature": {"type": "number", "description": "当前温度"},
            },
            "required": ["item_ids"],
        },
    },
    {
        "name": "profile_get",
        "description": "获取用户画像：身材、风格偏好、颜色偏好、预算。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "ui_build",
        "description": "生成可视化 HTML 仪表盘（衣橱 + 色卡库 + 知识库 + 推荐）。",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

# ==================== MCP Tool Handlers ====================

def handle_tool(name, args):
    if name == "wardrobe_list":
        cmd_args = ["--json"]
        if args.get("category"): cmd_args.extend(["--category", args["category"]])
        if args.get("style"): cmd_args.extend(["--style", args["style"]])
        if args.get("season"): cmd_args.extend(["--season", args["season"]])
        return load_json_output("wardrobe_ops.py", ["list"] + cmd_args)

    elif name == "wardrobe_add":
        cmd_args = ["add"]
        for key in ["type", "sub_type", "primary_color", "primary_hex", "material",
                     "fit", "style", "season", "temp_range", "occasion", "brand", "price", "image"]:
            val = args.get(key)
            if val is not None:
                flag = f"--{key.replace('_', '-')}"
                cmd_args.extend([flag, str(val)])
        return load_json_output("wardrobe_ops.py", cmd_args)

    elif name == "wardrobe_show":
        return load_json_output("wardrobe_ops.py", ["show", args["item_id"]])

    elif name == "wardrobe_update":
        cmd_args = ["update", args["item_id"]]
        for key in ["wear_count", "last_worn", "favorite"]:
            val = args.get(key)
            if val is not None:
                cmd_args.extend([f"--{key.replace('_', '-')}", str(val)])
        return load_json_output("wardrobe_ops.py", cmd_args)

    elif name == "wardrobe_delete":
        return load_json_output("wardrobe_ops.py", ["delete", args["item_id"]])

    elif name == "wardrobe_stats":
        return load_json_output("wardrobe_ops.py", ["stats", "--json"])

    elif name == "wardrobe_record":
        cmd_args = ["record", "--items", args["items"]]
        if args.get("occasion"): cmd_args.extend(["--occasion", args["occasion"]])
        if args.get("notes"): cmd_args.extend(["--notes", args["notes"]])
        return load_json_output("wardrobe_ops.py", cmd_args)

    elif name == "weather_query":
        cmd_args = ["--city", args["city"]]
        if args.get("date"): cmd_args.extend(["--date", args["date"]])
        return load_json_output("weather.py", cmd_args)

    elif name == "color_score":
        if args.get("item_ids"):
            return load_json_output("color_math.py", ["--items", ",".join(args["item_ids"])])
        elif args.get("hex_colors"):
            return load_json_output("color_math.py", ["--colors", ",".join(args["hex_colors"])])
        return {"error": "需要 item_ids 或 hex_colors"}

    elif name == "outfit_score":
        cmd_args = ["--items", ",".join(args["item_ids"])]
        if args.get("occasion"): cmd_args.extend(["--occasion", args["occasion"]])
        if args.get("temperature"): cmd_args.extend(["--temp", str(args["temperature"])])
        return load_json_output("scorer.py", cmd_args)

    elif name == "profile_get":
        profile_path = DATA / "profile.yaml"
        if profile_path.exists():
            import yaml
            with open(profile_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {"error": "profile.yaml 不存在"}

    elif name == "ui_build":
        output = run_script("../build_ui.py")
        return {"output": output}

    return {"error": f"Unknown tool: {name}"}

# ==================== MCP Server (stdio JSON-RPC) ====================

def main():
    """MCP stdio server - reads JSON-RPC from stdin, writes to stdout"""
    print("SuperOutfit MCP Server started", file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "superoutfit", "version": "2.0.0"},
                },
            }
        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS},
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            try:
                result = handle_tool(tool_name, tool_args)
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]},
                }
            except Exception as e:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True},
                }
        elif method == "notifications/initialized":
            continue
        else:
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        print(json.dumps(response), flush=True)

if __name__ == "__main__":
    main()
