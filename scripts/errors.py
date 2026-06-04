#!/usr/bin/env python3
"""
错误处理模块

提供友好的错误提示和建议。

用法：
  from errors import friendly_error, suggest_fix
"""

import sys
from pathlib import Path


def friendly_error(error, context=None):
    """
    将错误转换为友好的提示信息
    
    参数：
        error: 异常对象或错误消息
        context: 上下文信息（如命令名、参数名等）
    """
    error_msg = str(error)
    
    # 常见错误模式
    patterns = [
        {
            "match": "No such file or directory",
            "message": "文件不存在",
            "suggestion": "请检查文件路径是否正确",
        },
        {
            "match": "Permission denied",
            "message": "权限不足",
            "suggestion": "请检查文件权限或使用管理员权限运行",
        },
        {
            "match": "ModuleNotFoundError",
            "message": "模块未找到",
            "suggestion": "请安装依赖：uv pip install -e .",
        },
        {
            "match": "ImportError",
            "message": "导入失败",
            "suggestion": "请检查 Python 环境和依赖",
        },
        {
            "match": "ValueError",
            "message": "值错误",
            "suggestion": "请检查输入参数是否正确",
        },
        {
            "match": "yaml.scanner.ScannerError",
            "message": "YAML 格式错误",
            "suggestion": "请检查 YAML 文件格式是否正确",
        },
        {
            "match": "json.decoder.JSONDecodeError",
            "message": "JSON 格式错误",
            "suggestion": "请检查 JSON 文件格式是否正确",
        },
    ]
    
    for pattern in patterns:
        if pattern["match"] in error_msg:
            print(f"\n❌ {pattern['message']}")
            if context:
                print(f"   上下文：{context}")
            print(f"   错误：{error_msg}")
            print(f"\n💡 建议：{pattern['suggestion']}")
            return
    
    # 默认错误处理
    print(f"\n❌ 错误：{error_msg}")
    if context:
        print(f"   上下文：{context}")


def suggest_fix(command, error_type=None):
    """
    根据命令和错误类型提供修复建议
    
    参数：
        command: 命令名称
        error_type: 错误类型
    """
    suggestions = {
        "wardrobe": {
            "empty": [
                "衣橱为空，请先添加衣物：",
                "  superoutfit wardrobe add --type 上衣 --primary-hex '#F5F0E8'",
            ],
            "not_found": [
                "未找到指定衣物，请检查 ID：",
                "  superoutfit wardrobe list  # 查看所有衣物",
            ],
        },
        "weather": {
            "city_not_found": [
                "未找到该城市，请检查城市名称：",
                "  superoutfit weather --list-cities  # 查看支持的城市",
            ],
            "network_error": [
                "网络连接失败，请检查网络：",
                "  1. 检查网络连接",
                "  2. 检查代理设置",
            ],
        },
        "color": {
            "invalid_hex": [
                "无效的 HEX 颜色值",
                "  格式：#RRGGBB（如 #FF0000）",
                "  短格式：#RGB（如 #F00）",
                "  查看颜色：superoutfit color show '#FF0000'",
            ],
            "no_colors": [
                "未指定颜色，请使用 --colors 参数：",
                "  superoutfit color --colors '#F5F0E8,#111111'",
            ],
        },
        "palette": {
            "not_found": [
                "未找到色卡数据，请先训练模型：",
                "  superoutfit palette train",
            ],
        },
        "knowledge": {
            "not_found": [
                "未找到知识文件，请检查文件名：",
                "  superoutfit knowledge list  # 查看所有知识文件",
            ],
        },
    }
    
    if command in suggestions:
        cmd_suggestions = suggestions[command]
        if error_type and error_type in cmd_suggestions:
            print(f"\n💡 建议：")
            for line in cmd_suggestions[error_type]:
                print(f"   {line}")
        else:
            # 显示所有可能的建议
            print(f"\n💡 可能的解决方案：")
            for err_type, lines in cmd_suggestions.items():
                print(f"\n   {err_type}:")
                for line in lines:
                    print(f"     {line}")


def handle_error(func):
    """
    错误处理装饰器
    
    用法：
        @handle_error
        def my_function():
            ...
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print("\n\n⚠️  操作已取消")
            sys.exit(0)
        except Exception as e:
            friendly_error(e)
            sys.exit(1)
    
    return wrapper


def validate_hex(hex_str):
    """
    验证 HEX 颜色值
    
    参数：
        hex_str: HEX 颜色字符串
    
    返回：
        (is_valid, error_message)
    """
    if not hex_str:
        return False, "未指定颜色"
    
    # 添加 # 前缀
    if not hex_str.startswith("#"):
        hex_str = "#" + hex_str
    
    # 检查长度
    if len(hex_str) not in [4, 7]:
        return False, f"无效的长度：{len(hex_str)}（应为 4 或 7）"
    
    # 检查字符
    valid_chars = set("0123456789abcdefABCDEF#")
    if not all(c in valid_chars for c in hex_str):
        return False, f"包含无效字符：{hex_str}"
    
    return True, None


def validate_item_id(item_id):
    """
    验证衣物 ID
    
    参数：
        item_id: 衣物 ID
    
    返回：
        (is_valid, error_message)
    """
    if not item_id:
        return False, "未指定衣物 ID"
    
    # 检查格式
    if not item_id.startswith("item_"):
        return False, f"无效的 ID 格式：{item_id}（应为 item_XXX）"
    
    # 检查是否存在
    items_dir = Path("data/items")
    if not (items_dir / f"{item_id}.yaml").exists():
        return False, f"衣物不存在：{item_id}"
    
    return True, None


# ==================== 测试 ====================

if __name__ == "__main__":
    # 测试错误处理
    print("测试错误处理：")
    
    try:
        raise FileNotFoundError("No such file or directory: test.txt")
    except Exception as e:
        friendly_error(e, "读取文件")
    
    print("\n" + "="*50)
    
    # 测试修复建议
    suggest_fix("color", "invalid_hex")
    
    print("\n" + "="*50)
    
    # 测试验证
    test_cases = [
        "#F5F0E8",
        "#F00",
        "invalid",
        "#GGGGGG",
        "",
    ]
    
    for test in test_cases:
        is_valid, error = validate_hex(test)
        print(f"\n'{test}': {'✓' if is_valid else '✗'} {error or ''}")
