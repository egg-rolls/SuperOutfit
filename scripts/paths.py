"""
SuperOutfit 路径管理

统一解析数据目录路径。优先级：
1. ~/.superoutfit/config.json 中的 data_dir
2. SUPEROUTFIT_DATA 环境变量
3. 默认路径（脚本所在目录的 data/）

用法：
  from paths import get_data_dir, set_data_dir, get_config
"""

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = Path.home() / ".superoutfit"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_config() -> dict:
    """读取配置文件"""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_config(config: dict):
    """保存配置文件"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def get_data_dir() -> Path:
    """获取数据目录（优先级：配置文件 > 环境变量 > 默认路径）"""
    config = get_config()
    if "data_dir" in config:
        p = Path(config["data_dir"])
        if p.exists():
            return p

    env = os.environ.get("SUPEROUTFIT_DATA")
    if env:
        p = Path(env)
        if p.exists():
            return p

    return PROJECT_ROOT / "data"


def set_data_dir(path: str) -> tuple[bool, str]:
    """设置数据目录

    Returns:
        (success, message)
    """
    p = Path(path).resolve()
    if not p.exists():
        try:
            p.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return False, f"无法创建目录: {e}"

    # 验证目录结构
    items_dir = p / "items"
    if not items_dir.exists():
        items_dir.mkdir(exist_ok=True)

    config = get_config()
    config["data_dir"] = str(p)
    save_config(config)
    return True, str(p)


def get_image_dir() -> Path:
    """获取图片目录"""
    return get_data_dir() / "images"
