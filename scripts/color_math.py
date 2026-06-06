#!/usr/bin/env python3
"""
SuperOutfit 色彩协调度数学计算
基于世界名画色卡统计 + HSL 色彩空间理论 + OKLab 感知色彩空间

用法：
  # 计算一组颜色的协调度
  python color_math.py --colors "#F5F0E8,#C4A97D,#1A1A1A"

  # 从衣物 ID 计算
  python color_math.py --items item_001,item_003,item_006

  # 分析底色
  python color_math.py --items item_001,item_003 --analyze-base
"""

import argparse
import colorsys
import json
import math
import os
import sys
import yaml
from pathlib import Path

DATA_DIR = Path(os.environ.get("SUPEROUTFIT_DATA", Path(__file__).resolve().parent.parent / "data"))
ITEMS_DIR = DATA_DIR / "items"

# ==================== 颜色转换 ====================

def hex_to_rgb(hex_str):
    """HEX → RGB (0-255)"""
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    if len(hex_str) != 6 or not all(c in "0123456789abcdefABCDEF" for c in hex_str):
        return (128, 128, 128)  # fallback gray
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hsl(r, g, b):
    """RGB → HSL (H: 0-360, S: 0-100, L: 0-100)"""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return round(h * 360, 1), round(s * 100, 1), round(l * 100, 1)

def hex_to_hsl(hex_str):
    """HEX → HSL"""
    return rgb_to_hsl(*hex_to_rgb(hex_str))

def hex_to_oklab(hex_str):
    """HEX → OKLab (Björn Ottosson's specification)"""
    r, g, b = hex_to_rgb(hex_str)

    def srgb_to_linear(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r_lin = srgb_to_linear(r)
    g_lin = srgb_to_linear(g)
    b_lin = srgb_to_linear(b)

    # linear RGB to LMS
    l = 0.4122214708 * r_lin + 0.5363325363 * g_lin + 0.0514459929 * b_lin
    m = 0.2119034982 * r_lin + 0.6806995451 * g_lin + 0.1073969566 * b_lin
    s = 0.0883024619 * r_lin + 0.2817188376 * g_lin + 0.6299787005 * b_lin

    # LMS cube root (handle negative values safely)
    l_ = abs(l) ** (1/3) if l >= 0 else -abs(l) ** (1/3)
    m_ = abs(m) ** (1/3) if m >= 0 else -abs(m) ** (1/3)
    s_ = abs(s) ** (1/3) if s >= 0 else -abs(s) ** (1/3)

    # LMS to OKLab
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, a, b

def oklab_chroma(L, a, b):
    """OKLab chroma (saturation-like measure)"""
    return (a**2 + b**2) ** 0.5

def oklab_hue(L, a, b):
    """OKLab hue angle in degrees (0-360)"""
    return math.degrees(math.atan2(b, a)) % 360

def is_achromatic(hsl):
    """判断是否无彩色（黑白灰）"""
    _, s, l = hsl
    return s < 5 or l < 3 or l > 97

# ==================== 色相关系计算 ====================

def hue_distance(h1, h2):
    """两个色相之间的最短距离（0-180°）"""
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)

def classify_harmony(h1, h2):
    """判断两个色相的关系"""
    if is_achromatic((h1, 0, 50)) or is_achromatic((h2, 0, 50)):
        return "achromatic", 1.0  # 无彩色和任何颜色都兼容

    dist = hue_distance(h1, h2)

    if dist <= 15:
        return "同色系", 1.0
    elif dist <= 30:
        return "类似色", 0.95
    elif dist <= 60:
        return "邻近色", 0.8
    elif 150 <= dist <= 210:
        return "互补色", 0.7
    elif 105 <= dist <= 135:
        return "三角配色", 0.75
    elif dist <= 90:
        return "对比色", 0.5
    else:
        return "分裂互补", 0.65

# ==================== 协调度计算 ====================

def color_pair_score(hsl1, hsl2):
    """两个颜色之间的协调度 (0-100)"""
    h1, s1, l1 = hsl1
    h2, s2, l2 = hsl2

    # 无彩色特殊处理
    if is_achromatic(hsl1) or is_achromatic(hsl2):
        # 无彩色和任何颜色都和谐
        # 但明度对比要够
        l_dist = abs(l1 - l2)
        if l_dist > 15:
            return 90
        else:
            return 75  # 明度太接近，模糊

    # 色相关系分
    relation, relation_weight = classify_harmony(h1, h2)
    hue_score = relation_weight * 100

    # 明度对比分（适度对比 = 好）
    l_dist = abs(l1 - l2)
    if 15 <= l_dist <= 50:
        light_score = 90  # 适度对比，有层次
    elif l_dist < 15:
        light_score = 60  # 太接近，模糊
    elif l_dist > 50:
        light_score = 80  # 强对比，有时太强
    else:
        light_score = 70

    # 饱和度协调分
    s_dist = abs(s1 - s2)
    if s_dist <= 20:
        sat_score = 90  # 饱和度接近，和谐
    elif s_dist <= 40:
        sat_score = 75  # 有差异但可接受
    else:
        sat_score = 55  # 饱和度差异大，需要注意

    # 加权平均
    score = hue_score * 0.50 + light_score * 0.30 + sat_score * 0.20
    return round(score, 1)

def outfit_color_score(hex_list):
    """
    一组颜色的综合协调度 (0-100)

    计算方式：
    1. 两两配对的平均协调度
    2. 底色一致性的加成
    3. 颜色数量的惩罚/加成
    """
    if len(hex_list) < 2:
        return 100.0

    hsl_list = [hex_to_hsl(h) for h in hex_list]

    # 分离有彩色和无彩色
    chromatic = [hsl for hsl in hsl_list if not is_achromatic(hsl)]
    achromatic_count = len(hsl_list) - len(chromatic)

    # 如果全是无彩色，直接满分
    if len(chromatic) == 0:
        return 95.0

    # 两两配对得分
    pair_scores = []
    for i in range(len(hsl_list)):
        for j in range(i + 1, len(hsl_list)):
            pair_scores.append(color_pair_score(hsl_list[i], hsl_list[j]))

    avg_pair = sum(pair_scores) / len(pair_scores) if pair_scores else 50

    # 底色一致性检查
    base_score = base_tone_score(chromatic)

    # 颜色数量评估
    color_count = len(chromatic)
    if color_count <= 2:
        count_score = 90  # 2色以内，简洁
    elif color_count == 3:
        count_score = 85  # 3色，经典
    elif color_count == 4:
        count_score = 70  # 4色，开始复杂
    else:
        count_score = 50  # 5色以上，风险高

    # 综合评分
    total = avg_pair * 0.50 + base_score * 0.30 + count_score * 0.20
    return round(min(total, 100), 1)

def base_tone_score(chromatic_hsl_list):
    """
    底色一致性评分 (0-100)

    原理：所有有彩色是否统一在一个"底色基调"内
    - 暖底色（H: 0-60, 300-360）→ 暖色系内和谐
    - 冷底色（H: 180-300）→ 冷色系内和谐
    - 中性底色（H: 60-180）→ 绿色系
    """
    if len(chromatic_hsl_list) < 2:
        return 100.0

    hues = [hsl[0] for hsl in chromatic_hsl_list]

    # 计算色相的平均距离
    total_dist = 0
    count = 0
    for i in range(len(hues)):
        for j in range(i + 1, len(hues)):
            total_dist += hue_distance(hues[i], hues[j])
            count += 1

    avg_dist = total_dist / count if count > 0 else 0

    # 色相平均距离越小，底色越统一
    if avg_dist <= 20:
        return 100  # 非常统一的底色
    elif avg_dist <= 40:
        return 90   # 底色基本统一
    elif avg_dist <= 60:
        return 75   # 有一定统一性
    elif avg_dist <= 90:
        return 55   # 底色不统一
    else:
        return 35   # 底色冲突

# ==================== 底色分析 ====================

def analyze_base_tone(hex_list):
    """分析一组颜色的底色倾向"""
    hsl_list = [hex_to_hsl(h) for h in hex_list if not is_achromatic(hex_to_hsl(h))]

    if not hsl_list:
        return {"base": "无彩色", "warm": 0, "cool": 0, "detail": "全是黑白灰"}

    hues = [hsl[0] for hsl in hsl_list]
    avg_hue = sum(hues) / len(hues)

    # 判断冷暖
    # 暖色：红(0-30) + 黄(30-60) + 红紫(300-360)
    # 冷色：青(180-240) + 蓝(240-300)
    # 中性：绿(60-180)
    warm_range = list(range(0, 61)) + list(range(300, 361))
    cool_range = list(range(180, 301))

    warm_count = sum(1 for h in hues if int(h) in warm_range)
    cool_count = sum(1 for h in hues if int(h) in cool_range)

    if warm_count > cool_count:
        base = "暖底色"
        safe_range = "0-60°, 300-360°（红/橙/黄/暖棕）"
    elif cool_count > warm_count:
        base = "冷底色"
        safe_range = "180-300°（青/蓝/紫/冷灰）"
    else:
        base = "中性底色"
        safe_range = "60-180°（绿/黄绿）"

    # 安全区计算
    safe_hue_min = int(avg_hue - 30) % 360
    safe_hue_max = int(avg_hue + 30) % 360

    return {
        "base": base,
        "avg_hue": round(avg_hue, 1),
        "warm_count": warm_count,
        "cool_count": cool_count,
        "safe_range": safe_range,
        "safe_hue_zone": f"{safe_hue_min}° - {safe_hue_max}°",
        "colors_analyzed": len(hsl_list),
    }

# ==================== 数学模型预测评分 ====================

MODEL_PATH = DATA_DIR / "color_model.pkl"
MODEL_GP_PATH = DATA_DIR / "color_model_gp.pkl"
FEATURE_STATS = DATA_DIR / "feature_stats.json"

def _load_model():
    """加载训练好的线性模型"""
    if not MODEL_PATH.exists():
        return None
    import pickle
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

def _load_gp_model():
    """加载训练好的 GP 模型"""
    if not MODEL_GP_PATH.exists():
        return None
    import pickle
    with open(MODEL_GP_PATH, "rb") as f:
        return pickle.load(f)

def _extract_features(colors_with_areas):
    """从颜色列表提取特征向量 — 委托给 like_based_scoring.extract_features"""
    from like_based_scoring import extract_features
    hex_list = [c[0] for c in colors_with_areas]
    areas = [c[1] for c in colors_with_areas]
    return extract_features(list(zip(hex_list, areas)))

def model_predict_score(hex_list, areas=None):
    """
    用训练好的数学模型预测色彩协调度 (0-100)
    优先使用 GP 模型，降级到线性模型
    支持变长颜色输入 + 面积占比
    """
    if areas is None:
        areas = [1.0 / len(hex_list)] * len(hex_list)

    features = _extract_features(list(zip(hex_list, areas)))

    # 尝试 GP 模型
    gp_model = _load_gp_model()
    if gp_model is not None:
        return _predict_with_gp(gp_model, features)

    # 降级到线性模型
    model = _load_model()
    if model is None:
        return None
    return _predict_with_linear(model, features)


def model_predict_score_linear(hex_list, areas=None):
    """用线性模型预测（不使用 GP）"""
    model = _load_model()
    if model is None:
        return None
    if areas is None:
        areas = [1.0 / len(hex_list)] * len(hex_list)
    features = _extract_features(list(zip(hex_list, areas)))
    return _predict_with_linear(model, features)


def model_predict_score_gp(hex_list, areas=None):
    """用 GP 模型预测"""
    gp_model = _load_gp_model()
    if gp_model is None:
        return None
    if areas is None:
        areas = [1.0 / len(hex_list)] * len(hex_list)
    features = _extract_features(list(zip(hex_list, areas)))
    return _predict_with_gp(gp_model, features)


def _predict_with_linear(model, features):
    """用线性模型预测"""
    means = model["means"]
    stds = model["stds"]
    weights = model["weights"]
    bias = model["bias"]

    x_norm = [(features[i] - means[i]) / stds[i] for i in range(len(features))]
    score = sum(w * x for w, x in zip(weights, x_norm)) + bias
    return max(0, min(100, round(score, 1)))


def _predict_with_gp(gp_model, features):
    """用 GP 模型预测"""
    means = gp_model["means"]
    stds = gp_model["stds"]
    x_norm = [(features[i] - means[i]) / stds[i] for i in range(len(features))]

    if gp_model["type"] == "sklearn":
        import numpy as np
        X_np = np.array([x_norm])
        pred = gp_model["model"].predict(X_np)
        return max(0, min(100, round(float(pred[0]), 1)))
    else:
        # pure python
        X_train = gp_model["X_train"]
        alpha_vec = gp_model["alpha_vec"]
        length_scale = gp_model["length_scale"]

        def matern_52(x1, x2, ls):
            dist_sq = sum(((a - b) / ls) ** 2 for a, b in zip(x1, x2))
            dist = dist_sq ** 0.5
            sqrt5_dist = math.sqrt(5) * dist
            return (1 + sqrt5_dist + sqrt5_dist**2 / 3) * math.exp(-sqrt5_dist)

        k_star = [matern_52(x_norm, X_train[j], length_scale) for j in range(len(X_train))]
        pred = sum(a * ks for a, ks in zip(alpha_vec, k_star))
        return max(0, min(100, round(pred, 1)))


# ==================== 综合评分（理论 + 模型）====================

def outfit_color_score_v2(hex_list):
    """
    综合色彩协调度 (0-100)
    优先使用数学模型预测，降级到理论计算
    """
    if len(hex_list) < 2:
        return 100.0

    model_score = model_predict_score(hex_list)
    if model_score is not None:
        return model_score

    # 降级到理论计算
    return outfit_color_score(hex_list)

# ==================== 命令行接口 ====================

def load_item(item_id):
    path = ITEMS_DIR / f"{item_id}.yaml"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_item_hex_list(item):
    """从衣物提取所有 hex 色值"""
    colors = item.get("colors", {})
    hex_list = []
    for key in ["primary_hex", "secondary_hex", "tertiary_hex"]:
        val = colors.get(key)
        if val and val.startswith("#"):
            hex_list.append(val)
    return hex_list

def main():
    parser = argparse.ArgumentParser(description="SuperOutfit 色彩协调度计算")
    parser.add_argument("--colors", help="直接传入 HEX 色值，逗号分隔")
    parser.add_argument("--items", help="衣物 ID，逗号分隔")
    parser.add_argument("--analyze-base", action="store_true", help="分析底色")
    parser.add_argument("--detail", action="store_true", help="显示详细分析")

    args = parser.parse_args()

    hex_list = []

    if args.colors:
        hex_list = [c.strip() for c in args.colors.split(",")]
    elif args.items:
        item_ids = [s.strip() for s in args.items.split(",")]
        for item_id in item_ids:
            item = load_item(item_id)
            if item:
                item_hex = get_item_hex_list(item)
                hex_list.extend(item_hex)
            else:
                print(f"警告：未找到 {item_id}", file=sys.stderr)
    else:
        parser.print_help()
        return

    if not hex_list:
        print(json.dumps({"error": "没有有效的色值"}, ensure_ascii=False))
        return

    # 计算协调度（数学模型预测，优先 GP）
    score = outfit_color_score_v2(hex_list)
    theory = outfit_color_score(hex_list)
    linear_score = model_predict_score_linear(hex_list)
    gp_score = model_predict_score_gp(hex_list)

    result = {
        "colors": hex_list,
        "hsl_values": [hex_to_hsl(h) for h in hex_list],
        "harmony_score": score,
        "theory_score": theory,
        "linear_model_score": linear_score,
        "gp_model_score": gp_score,
        "model_available": linear_score is not None,
        "gp_available": gp_score is not None,
        "grade": "SSS" if score >= 85 else "SS" if score >= 75 else "S" if score >= 65 else "A" if score >= 50 else "B" if score >= 35 else "C" if score >= 20 else "D",
    }

    # 底色分析
    if args.analyze_base or args.detail:
        result["base_tone"] = analyze_base_tone(hex_list)

    # 详细分析
    if args.detail:
        pairs = []
        for i in range(len(hex_list)):
            for j in range(i + 1, len(hex_list)):
                hsl1 = hex_to_hsl(hex_list[i])
                hsl2 = hex_to_hsl(hex_list[j])
                relation, _ = classify_harmony(hsl1[0], hsl2[0])
                pair_score = color_pair_score(hsl1, hsl2)
                pairs.append({
                    "color1": hex_list[i],
                    "color2": hex_list[j],
                    "relation": relation,
                    "pair_score": pair_score,
                })
        result["pair_analysis"] = pairs

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()


# ==================== API 包装函数 ====================

def api_score(hex_list):
    if not hex_list:
        return {"error": "没有有效的色值"}
    score = outfit_color_score_v2(hex_list)
    theory = outfit_color_score(hex_list)
    linear_score = model_predict_score_linear(hex_list)
    gp_score = model_predict_score_gp(hex_list)
    return {
        "colors": hex_list,
        "harmony_score": score,
        "theory_score": theory,
        "linear_model_score": linear_score,
        "gp_model_score": gp_score,
        "model_available": linear_score is not None,
        "gp_available": gp_score is not None,
        "grade": "SSS" if score >= 85 else "SS" if score >= 75 else "S" if score >= 65 else "A" if score >= 50 else "B" if score >= 35 else "C" if score >= 20 else "D",
    }
