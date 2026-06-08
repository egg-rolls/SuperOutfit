#!/usr/bin/env python3
"""
点赞迁移评分系统 v2
改进：
  1. 剔除离群色卡（全黑/全白/超高饱和霓虹色）
  2. 稀疏高斯过程（Sparse GP）— 诱导点近似，O(nm²) 替代 O(n³)
"""

import colorsys
import json
import math
import os
import pickle
import random
import sys
from pathlib import Path

from paths import get_data_dir
SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = get_data_dir()
RAW_PALETTES = DATA_DIR / "raw_palettes.json"
SCORED_PALETTES = DATA_DIR / "scored_palettes.json"
TRANSFER_MODEL = DATA_DIR / "like_transfer_model.pkl"
FINAL_MODEL = DATA_DIR / "color_model_gp.pkl"
FEATURE_STATS = DATA_DIR / "feature_stats.json"

# ==================== 颜色工具 ====================

def hex_to_rgb(hex_str):
    h = hex_str.strip().lstrip("#")
    if len(h) == 3: h = "".join(c * 2 for c in h)
    if len(h) != 6 or not all(c in "0123456789abcdefABCDEF" for c in h):
        return (128, 128, 128)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

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

# ==================== 离群检测 ====================

def is_outlier(colors):
    """
    检测色卡是否为离群值：
    - 全黑（所有颜色明度 < 10%）
    - 全白（所有颜色明度 > 95%）
    - 超高饱和霓虹色（任一颜色饱和度 > 90 且明度 30-70）
    """
    hsls = [hex_to_hsl(c) for c in colors]
    
    # 全黑
    if all(l < 10 for _, _, l in hsls):
        return True, "all_black"
    
    # 全白
    if all(l > 95 for _, _, l in hsls):
        return True, "all_white"
    
    # 超高饱和霓虹色
    if any(s > 90 and 30 < l < 70 for _, s, l in hsls):
        return True, "ultra_saturation"
    
    return False, None

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
    
    hsl_list = [hex_to_hsl(h) for h in hex_list]
    chromatic = [(hsl, area) for hsl, area in zip(hsl_list, areas) if not is_achromatic(hsl)]

    features = []

    if chromatic:
        w_h = sum(h * a for (h,s,l), a in chromatic) / sum(a for _, a in chromatic)
        w_s = sum(s * a for (h,s,l), a in chromatic) / sum(a for _, a in chromatic)
        w_l = sum(l * a for (h,s,l), a in chromatic) / sum(a for _, a in chromatic)
    else:
        w_h, w_s, w_l = 0, 0, 50
    features.extend([w_h/360, w_s/100, w_l/100])

    all_h = [h for h,s,l in hsl_list]
    all_s = [s for h,s,l in hsl_list]
    all_l = [l for h,s,l in hsl_list]

    features.extend([sum(all_h)/len(all_h)/360, sum(all_s)/len(all_s)/100, sum(all_l)/len(all_l)/100])

    for vals, scale in [(all_h, 360), (all_s, 100), (all_l, 100)]:
        mean = sum(vals) / len(vals)
        std = (sum((v-mean)**2 for v in vals) / len(vals))**0.5
        features.extend([max(vals)/scale, min(vals)/scale, (max(vals)-min(vals))/scale, std/scale])

    hue_dists = [hue_distance(all_h[i], all_h[j]) for i in range(len(all_h)) for j in range(i+1, len(all_h))]
    if hue_dists:
        mean_d = sum(hue_dists) / len(hue_dists)
        std_d = (sum((d-mean_d)**2 for d in hue_dists) / len(hue_dists))**0.5
    else:
        mean_d, std_d = 0, 0
    features.extend([mean_d/180, max(hue_dists, default=0)/180, min(hue_dists, default=0)/180, std_d/180])

    features.append(len(chromatic) / max(len(hsl_list), 1))

    entropy = -sum(a * math.log(a + 1e-10) for a in areas if a > 0)
    max_entropy = math.log(len(areas)) if len(areas) > 1 else 1
    features.append(entropy / max(max_entropy, 1))

    features.append(len(hex_list) / 6.0)
    features.append((max(all_l) - min(all_l)) / 100 if all_l else 0)
    features.append((max(all_s) - min(all_s)) / 100 if all_s else 0)

    # OKLab 特征 (15 维)
    oklab_list = [hex_to_oklab(h) for h in hex_list]
    ok_L = [L for L,a,b in oklab_list]
    ok_a = [a for L,a,b in oklab_list]
    ok_b = [b for L,a,b in oklab_list]
    ok_chroma = [oklab_chroma(a, b) for a, b in zip(ok_a, ok_b)]
    ok_hue = [oklab_hue(a, b) for a, b in zip(ok_a, ok_b)]

    if chromatic:
        w_L = sum(L * a for L, a in zip(ok_L, areas)) / sum(areas)
        w_a = sum(a * w for a, w in zip(ok_a, areas)) / sum(areas)
        w_b = sum(b * w for b, w in zip(ok_b, areas)) / sum(areas)
    else:
        w_L, w_a, w_b = 0.5, 0, 0
    features.extend([w_L, w_a, w_b])

    features.extend([sum(ok_L)/len(ok_L), sum(ok_a)/len(ok_a), sum(ok_b)/len(ok_b)])

    features.extend([max(ok_L), min(ok_L), max(ok_L)-min(ok_L),
                     (sum((v-sum(ok_L)/len(ok_L))**2 for v in ok_L)/len(ok_L))**0.5])

    features.extend([max(ok_chroma), min(ok_chroma), max(ok_chroma)-min(ok_chroma),
                     (sum((v-sum(ok_chroma)/len(ok_chroma))**2 for v in ok_chroma)/len(ok_chroma))**0.5])

    ok_hue_dists = [hue_distance(ok_hue[i], ok_hue[j]) for i in range(len(ok_hue)) for j in range(i+1, len(ok_hue))]
    features.append((sum(ok_hue_dists)/len(ok_hue_dists) if ok_hue_dists else 0) / 180)

    return features

# ==================== 点赞 → 百分位分数 ====================

def likes_to_percentile(palettes_with_likes):
    likes = [p["likes"] for p in palettes_with_likes]
    log_likes = [math.log1p(l) for l in likes]
    sorted_log = sorted(log_likes)
    n = len(sorted_log)
    scored = []
    for p, ll in zip(palettes_with_likes, log_likes):
        rank = sum(1 for x in sorted_log if x <= ll)
        p["score"] = round((rank / n) * 100, 1)
        scored.append(p)
    return scored

# ==================== 稀疏 GP（诱导点近似）====================

def sparse_gp_predict(gp_model, inducing_features, X_new):
    """
    稀疏 GP 预测：用诱导点的 GP 做近似
    预测时只计算新样本与诱导点之间的核矩阵，O(n_inducing²)
    """
    import numpy as np
    from sklearn.metrics.pairwise import rbf_kernel
    
    # 从全量 GP 中提取核参数
    kernel = gp_model.kernel_
    
    # 计算新样本与诱导点之间的核值
    K_inducing = kernel(X_new, inducing_features)
    
    # 用诱导点的 GP 做预测（简化版 FITC）
    # K(X_new, Z) @ K(Z, Z)^{-1} @ y
    K_zz = kernel(inducing_features, inducing_features)
    alpha = gp_model.alpha_  # K(X,X) + σI)^{-1} @ y
    
    # 简化：用诱导点子集的 alpha 近似
    n_inducing = len(inducing_features)
    n_train = len(alpha)
    
    # 用 K(X_new, Z) @ K(Z, Z)^{-1} @ y_Z 近似
    try:
        L = np.linalg.cholesky(K_zz + np.eye(n_inducing) * 1e-6)
        y_z = np.linalg.solve(L.T, np.linalg.solve(L, K_inducing.T @ np.ones(n_inducing) / n_inducing * n_train))
        y_pred = K_inducing @ np.linalg.solve(K_zz + np.eye(n_inducing) * 1e-6, 
                                                np.linalg.solve(K_zz + np.eye(n_inducing) * 1e-6, 
                                                                np.ones(n_inducing))) * np.mean(alpha * n_train)
    except:
        # fallback: 简单加权平均
        y_pred = K_inducing @ np.linalg.lstsq(K_zz + np.eye(n_inducing) * 1e-6, 
                                                np.ones(n_inducing), rcond=None)[0] * np.mean(gp_model.y_train_mean_ if hasattr(gp_model, 'y_train_mean_') else 50)
    
    return y_pred

# ==================== 主流程 ====================

def main():
    if not RAW_PALETTES.exists():
        print(f"错误：找不到 {RAW_PALETTES}")
        return
    
    with open(RAW_PALETTES, "r", encoding="utf-8") as f:
        palettes = json.load(f)
    
    print(f"=== 点赞迁移评分系统 v2 ===\n")
    print(f"加载 {len(palettes)} 组色卡")
    
    # 第零步：剔除离群色卡
    print(f"\n--- 第零步：剔除离群色卡 ---")
    clean = []
    outlier_count = {"all_black": 0, "all_white": 0, "ultra_saturation": 0}
    for p in palettes:
        is_out, reason = is_outlier(p["colors"])
        if is_out:
            outlier_count[reason] = outlier_count.get(reason, 0) + 1
        else:
            clean.append(p)
    
    print(f"  全黑：{outlier_count.get('all_black', 0)} 组")
    print(f"  全白：{outlier_count.get('all_white', 0)} 组")
    print(f"  超高饱和霓虹：{outlier_count.get('ultra_saturation', 0)} 组")
    print(f"  剔除总计：{len(palettes) - len(clean)} 组")
    print(f"  保留：{len(clean)} 组")
    
    # 分离有赞和无赞
    with_likes = [p for p in clean if p.get("likes", 0) > 0]
    without_likes = [p for p in clean if p.get("likes", 0) <= 0]
    
    print(f"  有赞：{len(with_likes)} 组")
    print(f"  无赞：{len(without_likes)} 组")
    
    # 第一步：点赞 → 百分位分数
    print(f"\n--- 第一步：点赞 → 百分位分数 ---")
    scored = likes_to_percentile(with_likes)
    print(f"  点赞范围：{min(p['likes'] for p in scored)} ~ {max(p['likes'] for p in scored)}")
    print(f"  分数范围：{min(p['score'] for p in scored):.1f} ~ {max(p['score'] for p in scored):.1f}")
    
    # 第二步：训练迁移模型
    print(f"\n--- 第二步：训练点赞预测模型 ---")
    X_labeled = []
    y_labeled = []
    for p in scored:
        if len(p["colors"]) >= 2:
            features = extract_features(p["colors"])
            X_labeled.append(features)
            y_labeled.append(p["score"])
    
    print(f"  有效样本：{len(X_labeled)}")
    
    # 归一化
    n_features = len(X_labeled[0])
    means = [sum(row[i] for row in X_labeled) / len(X_labeled) for i in range(n_features)]
    stds = []
    for i in range(n_features):
        var = sum((row[i] - means[i])**2 for row in X_labeled) / len(X_labeled)
        stds.append(var**0.5 if var > 0 else 1.0)
    X_norm = [[(row[i] - means[i]) / stds[i] for i in range(n_features)] for row in X_labeled]
    
    # Sparse GP：选诱导点
    N_INDUCING = 500
    try:
        from sklearn.cluster import KMeans
        import numpy as np
        
        X_np = np.array(X_norm)
        y_np = np.array(y_labeled)
        
        if len(X_norm) > N_INDUCING:
            print(f"  选择 {N_INDUCING} 个诱导点（K-Means 聚类）...")
            kmeans = KMeans(n_clusters=N_INDUCING, random_state=42, n_init=3)
            kmeans.fit(X_np)
            inducing_idx = []
            for center in kmeans.cluster_centers_:
                dists = np.sum((X_np - center) ** 2, axis=1)
                inducing_idx.append(np.argmin(dists))
            inducing_idx = list(set(inducing_idx))
            X_inducing = X_np[inducing_idx]
            y_inducing = y_np[inducing_idx]
        else:
            X_inducing = X_np
            y_inducing = y_np
            inducing_idx = list(range(len(X_norm)))
        
        print(f"  诱导点数量：{len(inducing_idx)}")
        
        # 在诱导点上训练 GP
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import Matern
        
        kernel = Matern(nu=2.5, length_scale=1.0)
        gp = GaussianProcessRegressor(kernel=kernel, alpha=1.0, n_restarts_optimizer=3,
                                       normalize_y=True, random_state=42)
        gp.fit(X_inducing, y_inducing)
        
        # 评估（在全量有赞数据上）
        y_pred = gp.predict(X_np)
        mae = float(np.mean(np.abs(y_pred - y_np)))
        rmse = float(np.sqrt(np.mean((y_pred - y_np)**2)))
        
        print(f"  迁移模型 MAE: {mae:.2f}, RMSE: {rmse:.2f}")
        
        # 保存迁移模型
        transfer_model = {
            "type": "sparse_gp",
            "model": gp,
            "inducing_idx": inducing_idx,
            "means": means,
            "stds": stds,
            "n_features": n_features,
            "mae": mae,
            "rmse": rmse,
        }
        with open(TRANSFER_MODEL, "wb") as f:
            pickle.dump(transfer_model, f)
        print(f"  迁移模型已保存")
        
    except Exception as e:
        print(f"  Sparse GP 失败：{e}")
        gp = None
    
    # 第三步：预测全量色卡分数
    print(f"\n--- 第三步：预测全量色卡分数 ---")
    all_scored = []
    for p in clean:
        if len(p["colors"]) < 2:
            continue
        features = extract_features(p["colors"])
        x_norm = [(features[i] - means[i]) / stds[i] for i in range(n_features)]
        
        if p.get("likes", 0) > 0:
            score = p.get("score", 50)
        elif gp is not None:
            x_np = np.array([x_norm])
            score = float(gp.predict(x_np)[0])
            score = max(0, min(100, score))
        else:
            score = 50
        
        all_scored.append({
            "colors": p["colors"],
            "score": round(score, 1),
            "likes": p.get("likes", 0),
            "source": p.get("source", "unknown"),
            "name": p.get("name", ""),
        })
    
    scores = [p["score"] for p in all_scored]
    print(f"  总计：{len(all_scored)} 组色卡已打分")
    print(f"  分数范围：{min(scores):.1f} ~ {max(scores):.1f}")
    print(f"  分数均值：{sum(scores)/len(scores):.1f}")
    
    by_source = {}
    for p in all_scored:
        src = p["source"]
        if src not in by_source:
            by_source[src] = []
        by_source[src].append(p["score"])
    print(f"\n  按来源统计：")
    for src, src_scores in sorted(by_source.items(), key=lambda x: -sum(x[1])/len(x[1])):
        print(f"    {src:<15} {len(src_scores):>5} 组  平均分: {sum(src_scores)/len(src_scores):.1f}")
    
    with open(SCORED_PALETTES, "w", encoding="utf-8") as f:
        json.dump(all_scored, f, ensure_ascii=False, indent=2)
    print(f"\n  已保存：{SCORED_PALETTES}")
    
    # 第四步：重训最终 Sparse GP
    print(f"\n--- 第四步：重训最终 Sparse GP ---")
    X_final = []
    y_final = []
    for p in all_scored:
        if len(p["colors"]) >= 2:
            features = extract_features(p["colors"])
            X_final.append(features)
            y_final.append(p["score"])
    
    f_means = [sum(row[i] for row in X_final) / len(X_final) for i in range(n_features)]
    f_stds = []
    for i in range(n_features):
        var = sum((row[i] - f_means[i])**2 for row in X_final) / len(X_final)
        f_stds.append(var**0.5 if var > 0 else 1.0)
    X_final_norm = [[(row[i] - f_means[i]) / f_stds[i] for i in range(n_features)] for row in X_final]
    
    try:
        X_fnp = np.array(X_final_norm)
        y_fnp = np.array(y_final)
        
        # 选诱导点
        if len(X_final_norm) > N_INDUCING:
            print(f"  选择 {N_INDUCING} 个诱导点...")
            kmeans = KMeans(n_clusters=N_INDUCING, random_state=42, n_init=3)
            kmeans.fit(X_fnp)
            final_inducing_idx = []
            for center in kmeans.cluster_centers_:
                dists = np.sum((X_fnp - center) ** 2, axis=1)
                final_inducing_idx.append(np.argmin(dists))
            final_inducing_idx = list(set(final_inducing_idx))
            X_final_inducing = X_fnp[final_inducing_idx]
            y_final_inducing = y_fnp[final_inducing_idx]
        else:
            X_final_inducing = X_fnp
            y_final_inducing = y_fnp
            final_inducing_idx = list(range(len(X_final_norm)))
        
        print(f"  诱导点数量：{len(final_inducing_idx)}")
        
        kernel = Matern(nu=2.5, length_scale=1.0)
        gp_final = GaussianProcessRegressor(kernel=kernel, alpha=1.0, n_restarts_optimizer=3,
                                             normalize_y=True, random_state=42)
        gp_final.fit(X_final_inducing, y_final_inducing)
        
        y_pred_final = gp_final.predict(X_fnp)
        mae_final = float(np.mean(np.abs(y_pred_final - y_fnp)))
        rmse_final = float(np.sqrt(np.mean((y_pred_final - y_fnp)**2)))
        
        print(f"  最终 Sparse GP MAE: {mae_final:.2f}, RMSE: {rmse_final:.2f}")
        print(f"  训练样本：{len(X_final)}（诱导点 {len(final_inducing_idx)}）")
        
        final_model = {
            "type": "sklearn",
            "model": gp_final,
            "means": f_means,
            "stds": f_stds,
            "n_features": n_features,
            "training_samples": len(X_final),
            "inducing_points": len(final_inducing_idx),
            "mae": round(mae_final, 2),
            "rmse": round(rmse_final, 2),
        }
        with open(FINAL_MODEL, "wb") as f:
            pickle.dump(final_model, f)
        
        with open(FEATURE_STATS, "w") as f:
            json.dump({"means": f_means, "stds": f_stds, "n_features": n_features}, f)
        
        print(f"  最终模型已保存：{FINAL_MODEL}")
        
        # 测试
        print(f"\n  测试用例：")
        test_cases = [
            ("米白+卡其+黑", ["#F5F0E8", "#C4A97D", "#111111"]),
            ("军绿+米白+深棕", ["#5a6b40", "#f5f0e8", "#4a3520"]),
            ("藏青+白+卡其", ["#1a3a5c", "#f8f8f8", "#c4a97d"]),
            ("全黑+银饰", ["#111111", "#1a1a1a", "#c0c0c0"]),
            ("酒红+黑+灰", ["#8b2525", "#1a1a1a", "#808080"]),
            ("蓝+红+黄撞色", ["#0000ff", "#ff0000", "#ffff00"]),
        ]
        for name, colors in test_cases:
            features = extract_features(colors)
            x_norm = [(features[i] - f_means[i]) / f_stds[i] for i in range(n_features)]
            pred = float(gp_final.predict(np.array([x_norm]))[0])
            pred = max(0, min(100, pred))
            print(f"    {name:<20} → {pred:.1f} 分")
        
    except Exception as e:
        print(f"  最终模型训练失败：{e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n=== 完成 ===")

if __name__ == "__main__":
    main()
