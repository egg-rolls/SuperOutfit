#!/usr/bin/env python3
"""
色彩反向推导 — 贝叶斯优化版本

给定部分颜色和目标分数，用贝叶斯优化推导补全的颜色。

用法：
  python color_inverse_bayesian.py --known "#F5F0E8,#111111" --target 75 --missing 2
"""

import colorsys
import json
import math
import pickle
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from paths import get_data_dir
SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = get_data_dir()
MODEL_PATH = DATA_DIR / "color_model_gp.pkl"
FEATURE_STATS = DATA_DIR / "feature_stats.json"


# ==================== 颜色工具 ====================

def hex_to_rgb(hex_str):
    h = hex_str.strip().lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def hex_to_hsl(hex_str):
    r, g, b = hex_to_rgb(hex_str)
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    return h * 360, s * 100, l * 100


def hex_to_oklab(hex_str):
    r, g, b = hex_to_rgb(hex_str)
    def srgb_to_linear(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    rl, gl, bl = srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b)
    l_ = (0.4122214708*rl + 0.5363325363*gl + 0.0514459929*bl) ** (1/3)
    m_ = (0.2119034982*rl + 0.6806995451*gl + 0.1073969566*bl) ** (1/3)
    s_ = (0.0883024619*rl + 0.2817188376*gl + 0.6299787005*bl) ** (1/3)
    L = 0.2104542553*l_ + 0.7936177850*m_ - 0.0040720468*s_
    a = 1.9779984951*l_ - 2.4285922050*m_ + 0.4505937099*s_
    b_val = 0.0259040371*l_ + 0.7827717662*m_ - 0.8086757660*s_
    return L, a, b_val


def is_achromatic(hsl):
    return hsl[1] < 5 or hsl[2] < 3 or hsl[2] > 97


def hue_distance(h1, h2):
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


def oklab_chroma(a, b):
    return (a**2 + b**2) ** 0.5


def oklab_hue(a, b):
    return math.degrees(math.atan2(b, a)) % 360


# ==================== 特征提取（42 维）====================

def extract_features(colors):
    """提取 42 维特征"""
    hex_list = [c if isinstance(c, str) else c[0] for c in colors]
    if isinstance(colors[0], tuple):
        areas = [c[1] for c in colors]
    else:
        areas = [1.0 / len(colors)] * len(colors)

    total_area = sum(areas)
    if total_area > 0:
        areas = [a / total_area for a in areas]
    else:
        n = len(areas)
        areas = [1.0 / n] * n

    hsl_list = [hex_to_hsl(h) for h in hex_list]

    chromatic = [(hsl, area) for hsl, area in zip(hsl_list, areas) if not is_achromatic(hsl)]
    achromatic_count = len(hsl_list) - len(chromatic)

    features = []

    # 1. 加权平均 HSL
    if chromatic:
        w_h = sum(h * a for (h, s, l), a in chromatic) / sum(a for _, a in chromatic)
        w_s = sum(s * a for (h, s, l), a in chromatic) / sum(a for _, a in chromatic)
        w_l = sum(l * a for (h, s, l), a in chromatic) / sum(a for _, a in chromatic)
    else:
        w_h, w_s, w_l = 0, 0, 50
    features.extend([w_h / 360, w_s / 100, w_l / 100])

    # 2. 简单平均 HSL
    all_h = [h for h, s, l in hsl_list]
    all_s = [s for h, s, l in hsl_list]
    all_l = [l for h, s, l in hsl_list]
    features.extend([
        sum(all_h) / len(all_h) / 360,
        sum(all_s) / len(all_s) / 100,
        sum(all_l) / len(all_l) / 100,
    ])

    # 3. H/S/L 的 max, min, span, std
    for vals, scale in [(all_h, 360), (all_s, 100), (all_l, 100)]:
        mean = sum(vals) / len(vals)
        std = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
        features.extend([max(vals) / scale, min(vals) / scale, (max(vals) - min(vals)) / scale, std / scale])

    # 4. 两两色相距离统计
    hue_dists = []
    for i in range(len(all_h)):
        for j in range(i + 1, len(all_h)):
            hue_dists.append(hue_distance(all_h[i], all_h[j]))
    if hue_dists:
        mean_d = sum(hue_dists) / len(hue_dists)
        max_d = max(hue_dists)
        min_d = min(hue_dists)
        std_d = (sum((d - mean_d) ** 2 for d in hue_dists) / len(hue_dists)) ** 0.5
    else:
        mean_d, max_d, min_d, std_d = 0, 0, 0, 0
    features.extend([mean_d / 180, max_d / 180, min_d / 180, std_d / 180])

    # 5. 有彩色比例
    features.append(len(chromatic) / max(len(hsl_list), 1))

    # 6. 面积分布熵
    entropy = -sum(a * math.log(a + 1e-10) for a in areas if a > 0)
    max_entropy = math.log(len(areas)) if len(areas) > 1 else 1
    features.append(entropy / max(max_entropy, 1))

    # 7. 颜色数量（归一化）
    features.append(len(hex_list) / 6.0)

    # 8. 明度对比度
    if all_l:
        l_contrast = (max(all_l) - min(all_l)) / 100
    else:
        l_contrast = 0
    features.append(l_contrast)

    # 9. 饱和度对比度
    if all_s:
        s_contrast = (max(all_s) - min(all_s)) / 100
    else:
        s_contrast = 0
    features.append(s_contrast)

    # OKLab 特征
    oklab_list = [hex_to_oklab(h) for h in hex_list]
    ok_L = [L for L, a, b in oklab_list]
    ok_a = [a for L, a, b in oklab_list]
    ok_b = [b for L, a, b in oklab_list]
    ok_chroma = [oklab_chroma(a, b) for L, a, b in oklab_list]
    ok_hue = [oklab_hue(a, b) for L, a, b in oklab_list]

    # OKLab 加权平均 L, a, b
    chromatic_oklab = [(oklab_list[i], areas[i]) for i in range(len(hex_list)) if not is_achromatic(hsl_list[i])]
    if chromatic_oklab:
        total_w = sum(a for _, a in chromatic_oklab)
        w_ok_L = sum(L * a for (L, _, _), a in chromatic_oklab) / total_w
        w_ok_a = sum(a_val * a for (_, a_val, _), a in chromatic_oklab) / total_w
        w_ok_b = sum(b_val * a for (_, _, b_val), a in chromatic_oklab) / total_w
    else:
        w_ok_L, w_ok_a, w_ok_b = 0.5, 0.0, 0.0
    features.extend([w_ok_L, w_ok_a * 5, w_ok_b * 5])

    # OKLab 简单平均 L, a, b
    features.extend([sum(ok_L) / len(ok_L), sum(ok_a) / len(ok_a) * 5, sum(ok_b) / len(ok_b) * 5])

    # OKLab L 的 max/min/span/std
    ok_L_mean = sum(ok_L) / len(ok_L)
    ok_L_std = (sum((v - ok_L_mean)**2 for v in ok_L) / len(ok_L)) ** 0.5
    features.extend([max(ok_L), min(ok_L), max(ok_L) - min(ok_L), ok_L_std])

    # OKLab Chroma 的 max/min/span/std
    ok_c_mean = sum(ok_chroma) / len(ok_chroma)
    ok_c_std = (sum((v - ok_c_mean)**2 for v in ok_chroma) / len(ok_chroma)) ** 0.5
    features.extend([max(ok_chroma), min(ok_chroma), max(ok_chroma) - min(ok_chroma), ok_c_std])

    # OKLab Hue 两两距离统计
    ok_hue_dists = []
    for i in range(len(ok_hue)):
        for j in range(i + 1, len(ok_hue)):
            d = abs(ok_hue[i] - ok_hue[j]) % 360
            ok_hue_dists.append(min(d, 360 - d))
    if ok_hue_dists:
        ok_hue_mean_d = sum(ok_hue_dists) / len(ok_hue_dists)
    else:
        ok_hue_mean_d = 0
    features.append(ok_hue_mean_d / 180)

    return features


# ==================== 贝叶斯优化 ====================

def load_model():
    """加载 GP 模型和特征统计"""
    if not MODEL_PATH.exists():
        print(f"错误：找不到模型文件 {MODEL_PATH}")
        return None, None, None

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    with open(FEATURE_STATS, "r") as f:
        stats = json.load(f)

    return model["model"], stats["means"], stats["stds"]


def predict_score(colors_hex, gp, means, stds):
    """预测颜色组合的分数"""
    features = extract_features(colors_hex)
    n_features = len(features)
    features_norm = [(features[i] - means[i]) / stds[i] for i in range(n_features)]
    score = float(gp.predict(np.array([features_norm]))[0])
    return max(0, min(100, score))


def objective_function(unknown_rgb_flat, known_hex, gp, means, stds, target_score):
    """
    目标函数：GP 预测分数与目标分数的差距

    参数：
        unknown_rgb_flat: 未知颜色的 RGB 值（展平的一维数组）
        known_hex: 已知颜色的 HEX 列表
        gp: GP 模型
        means, stds: 特征统计
        target_score: 目标分数
    """
    # 把 RGB 转为 HEX
    n_missing = len(unknown_rgb_flat) // 3
    unknown_hex = []
    for i in range(n_missing):
        r = unknown_rgb_flat[i * 3]
        g = unknown_rgb_flat[i * 3 + 1]
        b = unknown_rgb_flat[i * 3 + 2]
        unknown_hex.append(rgb_to_hex(r, g, b))

    # 拼接所有颜色
    all_colors = known_hex + unknown_hex

    # 预测分数
    score = predict_score(all_colors, gp, means, stds)

    # 返回差距的平方
    return (score - target_score) ** 2


def bayesian_inverse(known_hex, target_score, missing_count, n_restarts=10):
    """
    贝叶斯优化反向推导

    参数：
        known_hex: 已知颜色的 HEX 列表
        target_score: 目标分数
        missing_count: 需要补全的颜色数量
        n_restarts: 优化重启次数
    """
    print(f"\n=== 贝叶斯优化反向推导 ===")
    print(f"已知颜色：{known_hex}")
    print(f"目标分数：{target_score}")
    print(f"需要补全：{missing_count} 个颜色")

    # 加载模型
    gp, means, stds = load_model()
    if gp is None:
        return []

    print(f"模型已加载")

    # 优化变量：未知颜色的 RGB 值（每个颜色 3 维）
    n_vars = missing_count * 3

    # 边界：RGB 值在 [0, 255] 范围内
    bounds = [(0, 255)] * n_vars

    # 多次随机重启
    best_result = None
    best_score = float("inf")

    print(f"\n开始优化（{n_restarts} 次重启）...")

    for i in range(n_restarts):
        # 随机初始点
        x0 = np.random.uniform(0, 255, n_vars)

        # 优化
        result = minimize(
            objective_function,
            x0,
            args=(known_hex, gp, means, stds, target_score),
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 100}
        )

        if result.fun < best_score:
            best_score = result.fun
            best_result = result

        if i % 5 == 0:
            print(f"  重启 {i+1}/{n_restarts}，当前最佳差距：{math.sqrt(best_score):.2f}")

    # 提取结果
    unknown_rgb = best_result.x
    n_missing = len(unknown_rgb) // 3
    unknown_hex = []
    for i in range(n_missing):
        r = int(np.clip(unknown_rgb[i * 3], 0, 255))
        g = int(np.clip(unknown_rgb[i * 3 + 1], 0, 255))
        b = int(np.clip(unknown_rgb[i * 3 + 2], 0, 255))
        unknown_hex.append(rgb_to_hex(r, g, b))

    # 预测最终分数
    all_colors = known_hex + unknown_hex
    final_score = predict_score(all_colors, gp, means, stds)

    print(f"\n优化完成！")
    print(f"补全颜色：{unknown_hex}")
    print(f"预测分数：{final_score:.1f}（目标：{target_score}）")
    print(f"差距：{abs(final_score - target_score):.1f}")

    return [{
        "missing": unknown_hex,
        "score": final_score,
        "full_palette": all_colors,
        "gap": abs(final_score - target_score),
    }]


# ==================== 多样化采样 ====================

def diverse_bayesian_inverse(known_hex, target_score, missing_count, n_samples=5):
    """
    多样化贝叶斯优化：生成多个不同的建议

    通过多次优化，使用不同的初始点，得到多个不同的结果。
    """
    print(f"\n=== 多样化贝叶斯优化 ===")

    all_results = []
    seen_colors = set()

    for i in range(n_samples):
        print(f"\n--- 样本 {i+1}/{n_samples} ---")
        results = bayesian_inverse(known_hex, target_score, missing_count, n_restarts=5)

        if results:
            result = results[0]
            # 检查是否已经见过类似的颜色
            color_key = tuple(sorted(result["missing"]))
            if color_key not in seen_colors:
                seen_colors.add(color_key)
                all_results.append(result)

    # 按差距排序
    all_results.sort(key=lambda x: x["gap"])

    print(f"\n生成 {len(all_results)} 个不同的建议：")
    for i, result in enumerate(all_results):
        print(f"\n建议 {i+1}：")
        print(f"  补全颜色：{result['missing']}")
        print(f"  预测分数：{result['score']:.1f}")
        print(f"  差距：{result['gap']:.1f}")

    return all_results


# ==================== 主函数 ====================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="色彩反向推导 — 贝叶斯优化版本")
    parser.add_argument("--known", required=True, help="已知颜色（逗号分隔的 HEX）")
    parser.add_argument("--target", type=float, required=True, help="目标分数")
    parser.add_argument("--missing", type=int, required=True, help="需要补全的颜色数量")
    parser.add_argument("--samples", type=int, default=3, help="生成样本数量")
    parser.add_argument("--restarts", type=int, default=10, help="每次优化的重启次数")

    args = parser.parse_args()

    known_colors = [c.strip() for c in args.known.split(",")]
    diverse_bayesian_inverse(known_colors, args.target, args.missing, args.samples)


if __name__ == "__main__":
    main()
