#!/usr/bin/env python3
"""
配置管理模块

从 profile.yaml 加载用户配置，提供智能默认值。

用法：
  from config import load_config, get_default
"""

import os
import yaml
from pathlib import Path

from paths import get_data_dir
SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = get_data_dir()


def load_config():
    """加载用户配置"""
    profile_path = DATA_DIR / "profile.yaml"
    if not profile_path.exists():
        return get_default_config()
    
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f)
        
        if not profile:
            return get_default_config()
        
        return profile
    except Exception as e:
        print(f"警告：加载配置失败：{e}")
        return get_default_config()


def get_default_config():
    """获取默认配置（匹配 profile.yaml 结构）"""
    return {
        "name": "用户",
        "city": "大连",
        "height": 175,
        "weight": 70,
        "style": {
            "primary": ["休闲", "简约"],
            "secondary": [],
            "avoid": [],
        },
        "colors": {
            "love": [],
            "neutral": ["黑白灰"],
            "avoid": [],
        },
        "budget": {
            "top": 200,
            "bottom": 300,
            "outerwear": 500,
        },
    }


def get_default(key, fallback=None):
    """获取配置的默认值"""
    config = load_config()
    return config.get(key, fallback)


def get_city():
    """获取用户城市"""
    return get_default("city", "大连")


def get_styles():
    """获取用户风格偏好（兼容 style_preferences / style.primary / styles）"""
    config = load_config()
    # 优先级：style.primary > style_preferences > styles
    style = config.get("style", {})
    if isinstance(style, dict) and style.get("primary"):
        return style["primary"]
    if config.get("style_preferences"):
        return config["style_preferences"]
    return config.get("styles", ["休闲", "简约"])


def get_budget():
    """获取用户预算"""
    return get_default("budget", {"top": 200, "bottom": 300, "outer": 500})


def get_body_info():
    """获取用户身材信息"""
    config = load_config()
    return {
        "height": config.get("height", 175),
        "weight": config.get("weight", 70),
        "shoulder": config.get("shoulder"),
        "chest": config.get("chest"),
        "waist": config.get("waist"),
        "hip": config.get("hip"),
    }


# ==================== 测试 ====================

if __name__ == "__main__":
    config = load_config()
    print("用户配置：")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print(f"\n城市：{get_city()}")
    print(f"风格：{get_styles()}")
    print(f"预算：{get_budget()}")
    print(f"身材：{get_body_info()}")
