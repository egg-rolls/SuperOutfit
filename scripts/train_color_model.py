#!/usr/bin/env python3
"""
SuperOutfit 色彩协调度数学模型训练

从真实色卡数据中提取特征，训练多项式回归模型。
模型可以处理变长颜色输入（2-6 个颜色），输出协调度分数。

改进：
- OKLab 感知色彩空间特征
- 高斯过程回归（Matérn 5/2 核）

用法：
  python train_color_model.py          # 训练模型
  python train_color_model.py --verify # 验证模型
"""

import colorsys
import json
import math
import os
import pickle
import sys
from pathlib import Path

from paths import get_data_dir
SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = get_data_dir()
RAW_PALETTES = DATA_DIR / "raw_palettes.json"
MODEL_PATH = DATA_DIR / "color_model.pkl"
MODEL_GP_PATH = DATA_DIR / "color_model_gp.pkl"
FEATURE_STATS = DATA_DIR / "feature_stats.json"

# ==================== 颜色工具 ====================

def hex_to_rgb(hex_str):
    """HEX → RGB (0-255)"""
    h = hex_str.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6 or not all(c in "0123456789abcdefABCDEF" for c in h):
        return (128, 128, 128)  # fallback gray
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def hex_to_hsl(hex_str):
    h = hex_str.strip().lstrip("#")
    r, g, b = int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255
    h_val, l, s = colorsys.rgb_to_hls(r, g, b)
    return h_val * 360, s * 100, l * 100

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
    return hsl[1] < 5 or hsl[2] < 3 or hsl[2] > 97

def hue_distance(h1, h2):
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)

# ==================== 特征提取 ====================

def extract_features(colors_with_areas):
    """
    从一组颜色中提取固定长度的特征向量

    输入: [(hex, area), ...]  area 为该颜色占全身比例 (0-1)
    输出: 特征向量 (list of float)

    特征设计 (27 原始 + 15 OKLab = 42 维):
    HSL 特征 (27维):
    - 每个颜色的 H, S, L（加权平均和简单平均）
    - 色相的最大/最小/跨度/标准差
    - 明度的最大/最小/跨度/标准差
    - 饱和度的最大/最小/跨度/标准差
    - 两两色相距离的统计
    - 有彩色数量
    - 面积分布熵
    - 明度对比度
    - 饱和度对比度

    OKLab 特征 (15维):
    - 加权平均 L, a, b
    - 简单平均 L, a, b
    - L 的 max/min/span/std
    - Chroma 的 max/min/span/std
    - OKLab hue 的 pairwise distance stats (mean only)
    """
    hex_list = [c[0] for c in colors_with_areas]
    areas = [c[1] for c in colors_with_areas]

    # 归一化面积
    total_area = sum(areas)
    if total_area > 0:
        areas = [a / total_area for a in areas]
    else:
        n = len(areas)
        areas = [1.0 / n] * n

    hsl_list = [hex_to_hsl(h) for h in hex_list]

    # 分离有彩色和无彩色
    chromatic = [(hsl, area) for hsl, area in zip(hsl_list, areas) if not is_achromatic(hsl)]
    achromatic_count = len(hsl_list) - len(chromatic)

    features = []

    # --- 1. 加权平均 HSL ---
    if chromatic:
        w_h = sum(h * a for (h, s, l), a in chromatic) / sum(a for _, a in chromatic)
        w_s = sum(s * a for (h, s, l), a in chromatic) / sum(a for _, a in chromatic)
        w_l = sum(l * a for (h, s, l), a in chromatic) / sum(a for _, a in chromatic)
    else:
        w_h, w_s, w_l = 0, 0, 50

    features.extend([w_h / 360, w_s / 100, w_l / 100])

    # --- 2. 简单平均 HSL ---
    all_h = [h for h, s, l in hsl_list]
    all_s = [s for h, s, l in hsl_list]
    all_l = [l for h, s, l in hsl_list]

    features.extend([
        sum(all_h) / len(all_h) / 360,
        sum(all_s) / len(all_s) / 100,
        sum(all_l) / len(all_l) / 100,
    ])

    # --- 3. H/S/L 的 max, min, span, std ---
    for vals, scale in [(all_h, 360), (all_s, 100), (all_l, 100)]:
        mean = sum(vals) / len(vals)
        std = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
        features.extend([
            max(vals) / scale,
            min(vals) / scale,
            (max(vals) - min(vals)) / scale,
            std / scale,
        ])

    # --- 4. 两两色相距离统计 ---
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

    # --- 5. 有彩色比例 ---
    features.append(len(chromatic) / max(len(hsl_list), 1))

    # --- 6. 面积分布熵 ---
    entropy = -sum(a * math.log(a + 1e-10) for a in areas if a > 0)
    max_entropy = math.log(len(areas)) if len(areas) > 1 else 1
    features.append(entropy / max(max_entropy, 1))

    # --- 7. 颜色数量（归一化） ---
    features.append(len(hex_list) / 6.0)

    # --- 8. 明度对比度 ---
    if all_l:
        l_contrast = (max(all_l) - min(all_l)) / 100
    else:
        l_contrast = 0
    features.append(l_contrast)

    # --- 9. 饱和度对比度 ---
    if all_s:
        s_contrast = (max(all_s) - min(all_s)) / 100
    else:
        s_contrast = 0
    features.append(s_contrast)

    # ==================== OKLab 特征 (新增) ====================
    oklab_list = [hex_to_oklab(h) for h in hex_list]
    ok_L = [L for L, a, b in oklab_list]
    ok_a = [a for L, a, b in oklab_list]
    ok_b = [b for L, a, b in oklab_list]
    ok_chroma = [oklab_chroma(L, a, b) for L, a, b in oklab_list]
    ok_hue = [oklab_hue(L, a, b) for L, a, b in oklab_list]

    # --- OKLab 加权平均 L, a, b ---
    chromatic_oklab = [(oklab_list[i], areas[i]) for i in range(len(hex_list)) if not is_achromatic(hsl_list[i])]
    if chromatic_oklab:
        total_w = sum(a for _, a in chromatic_oklab)
        w_ok_L = sum(L * a for (L, _, _), a in chromatic_oklab) / total_w
        w_ok_a = sum(a_val * a for (_, a_val, _), a in chromatic_oklab) / total_w
        w_ok_b = sum(b_val * a for (_, _, b_val), a in chromatic_oklab) / total_w
    else:
        w_ok_L, w_ok_a, w_ok_b = 0.5, 0.0, 0.0
    features.extend([w_ok_L, w_ok_a * 5, w_ok_b * 5])  # scale a,b for better normalization

    # --- OKLab 简单平均 L, a, b ---
    features.extend([
        sum(ok_L) / len(ok_L),
        sum(ok_a) / len(ok_a) * 5,
        sum(ok_b) / len(ok_b) * 5,
    ])

    # --- OKLab L 的 max/min/span/std ---
    ok_L_mean = sum(ok_L) / len(ok_L)
    ok_L_std = (sum((v - ok_L_mean)**2 for v in ok_L) / len(ok_L)) ** 0.5
    features.extend([max(ok_L), min(ok_L), max(ok_L) - min(ok_L), ok_L_std])

    # --- OKLab Chroma 的 max/min/span/std ---
    ok_c_mean = sum(ok_chroma) / len(ok_chroma)
    ok_c_std = (sum((v - ok_c_mean)**2 for v in ok_chroma) / len(ok_chroma)) ** 0.5
    features.extend([max(ok_chroma), min(ok_chroma), max(ok_chroma) - min(ok_chroma), ok_c_std])

    # --- OKLab Hue 两两距离统计 ---
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

# ==================== 理论评分（作为训练标签）====================

def theory_score(colors_with_areas):
    """用理论规则给色卡打分，作为模型训练的标签"""
    hex_list = [c[0] for c in colors_with_areas]
    hsl_list = [hex_to_hsl(h) for h in hex_list]

    chromatic = [hsl for hsl in hsl_list if not is_achromatic(hsl)]

    if len(chromatic) == 0:
        return 90  # 全无彩色

    # 色相关系分
    hue_dists = []
    for i in range(len(chromatic)):
        for j in range(i + 1, len(chromatic)):
            hue_dists.append(hue_distance(chromatic[i][0], chromatic[j][0]))

    avg_hue_dist = sum(hue_dists) / len(hue_dists) if hue_dists else 0

    if avg_hue_dist <= 20:
        hue_score = 95  # 同色系/类似色
    elif avg_hue_dist <= 40:
        hue_score = 85
    elif avg_hue_dist <= 60:
        hue_score = 70
    elif avg_hue_dist <= 120:
        hue_score = 55
    elif avg_hue_dist <= 150:
        hue_score = 65  # 分裂互补
    else:
        hue_score = 60  # 互补色

    # 明度对比分
    all_l = [l for h, s, l in hsl_list]
    l_span = max(all_l) - min(all_l)
    if 15 <= l_span <= 50:
        l_score = 90
    elif l_span < 15:
        l_score = 65
    else:
        l_score = 75

    # 饱和度协调分
    all_s = [s for h, s, l in chromatic]
    s_std = (sum((s - sum(all_s)/len(all_s)) ** 2 for s in all_s) / len(all_s)) ** 0.5 if all_s else 0
    if s_std <= 15:
        s_score = 90
    elif s_std <= 30:
        s_score = 75
    else:
        s_score = 55

    # 颜色数量分
    n = len(chromatic)
    if n <= 2:
        n_score = 90
    elif n == 3:
        n_score = 85
    else:
        n_score = 65

    score = hue_score * 0.40 + l_score * 0.25 + s_score * 0.20 + n_score * 0.15
    return round(min(max(score, 0), 100), 1)

# ==================== 模型训练 ====================

def train_model():
    """训练色彩协调度模型（线性回归 + 高斯过程回归）"""
    if not RAW_PALETTES.exists():
        print(f"错误：找不到色卡数据 {RAW_PALETTES}")
        print("请先运行 scrape_palettes.py 爬取色卡数据")
        return

    with open(RAW_PALETTES, "r", encoding="utf-8") as f:
        palettes = json.load(f)

    print(f"加载 {len(palettes)} 组色卡")

    # 提取特征和标签
    X = []  # 特征矩阵
    y = []  # 标签（理论分数）

    for palette in palettes:
        colors = palette["colors"]
        if len(colors) < 2:
            continue

        # 均匀分配面积（色卡没有面积信息）
        areas = [1.0 / len(colors)] * len(colors)
        colors_with_areas = list(zip(colors, areas))

        features = extract_features(colors_with_areas)
        score = theory_score(colors_with_areas)

        X.append(features)
        y.append(score)

    print(f"有效样本：{len(X)} 组")
    print(f"特征维度：{len(X[0])}")
    print(f"分数分布：min={min(y):.1f}, max={max(y):.1f}, mean={sum(y)/len(y):.1f}")

    # 归一化特征
    n_features = len(X[0])
    means = [sum(row[i] for row in X) / len(X) for i in range(n_features)]
    stds = []
    for i in range(n_features):
        var = sum((row[i] - means[i]) ** 2 for row in X) / len(X)
        stds.append(var ** 0.5 if var > 0 else 1.0)

    X_norm = [[(row[i] - means[i]) / stds[i] for i in range(n_features)] for row in X]

    # 保存特征统计
    stats = {"means": means, "stds": stds, "n_features": n_features}
    with open(FEATURE_STATS, "w", encoding="utf-8") as f:
        json.dump(stats, f)

    # ======== 线性回归（带正则化，防止过拟合）========
    lambda_reg = 1.0  # L2 正则化强度

    n = len(X_norm)
    d = n_features

    # X^T X
    XtX = [[0.0] * d for _ in range(d)]
    for i in range(d):
        for j in range(d):
            XtX[i][j] = sum(X_norm[k][i] * X_norm[k][j] for k in range(n))

    # 加正则化
    for i in range(d):
        XtX[i][i] += lambda_reg * n

    # X^T y
    Xty = [0.0] * d
    for i in range(d):
        Xty[i] = sum(X_norm[k][i] * y[k] for k in range(n))

    # 解线性方程组（高斯消元）
    weights = solve_linear(XtX, Xty)
    bias = sum(y) / len(y) - sum(w * m for w, m in zip(weights, means)) / len(means)

    # 计算训练误差
    predictions = [sum(w * X_norm[k][i] for i, w in enumerate(weights)) + bias for k in range(n)]
    mae = sum(abs(p - y[k]) for k, p in enumerate(predictions)) / n
    rmse = (sum((p - y[k]) ** 2 for k, p in enumerate(predictions)) / n) ** 0.5

    # 保存线性模型
    model = {
        "weights": weights,
        "bias": bias,
        "means": means,
        "stds": stds,
        "n_features": n_features,
        "training_samples": n,
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
    }

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    print(f"\n[线性回归] 模型已保存：{MODEL_PATH}")
    print(f"  训练样本：{n}")
    print(f"  特征维度：{d}")
    print(f"  MAE：{mae:.2f}")
    print(f"  RMSE：{rmse:.2f}")
    print(f"  权重：{[round(w, 4) for w in weights]}")
    print(f"  偏置：{bias:.4f}")

    # ======== 高斯过程回归 ========
    gp_mae, gp_rmse = train_gp_model(X_norm, y, means, stds, n_features, n)

    return {"linear_mae": mae, "linear_rmse": rmse, "gp_mae": gp_mae, "gp_rmse": gp_rmse}


def incremental_train_gp(new_X, new_y, max_samples=5000):
    """增量训练 GP 模型：加载现有模型 + 新数据 → 更新模型
    
    策略：合并旧训练数据 + 新数据，重新训练（使用旧超参数作为初始值）
    """
    import pickle
    import numpy as np
    from pathlib import Path
    
    GP_MODEL_PATH = Path(__file__).parent.parent / "data" / "gp_model.pkl"
    
    if not GP_MODEL_PATH.exists():
        print("❌ 未找到现有 GP 模型，请先运行完整训练")
        return None
    
    # 加载现有模型
    with open(GP_MODEL_PATH, "rb") as f:
        old_model = pickle.load(f)
    
    print("📊 增量训练 GP 模型...\n")
    print(f"  现有模型类型：{old_model['type']}")
    print(f"  现有训练样本：{old_model['training_samples']}")
    print(f"  新增样本数：{len(new_y)}")
    
    # 合并数据（如果旧模型有保存训练数据）
    if "X_train" in old_model and "y_train" in old_model:
        X_all = np.vstack([old_model["X_train"], np.array(new_X)])
        y_all = np.concatenate([old_model["y_train"], np.array(new_y)])
        print(f"  合并后总样本：{len(y_all)}")
    else:
        # 旧模型没有保存训练数据，只用新数据
        X_all = np.array(new_X)
        y_all = np.array(new_y)
        print(f"  ⚠ 旧模型未保存训练数据，仅使用新样本")
    
    # 子采样
    if len(X_all) > max_samples:
        import random
        random.seed(42)
        indices = random.sample(range(len(X_all)), max_samples)
        X_all = X_all[indices]
        y_all = y_all[indices]
        print(f"  子采样至 {max_samples} 样本")
    
    # 重新训练（使用旧模型的超参数作为初始值）
    try:
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import Matern
        
        # 使用旧模型的核参数（如果有）
        if hasattr(old_model.get("model"), "kernel_"):
            kernel = old_model["model"].kernel_
            print(f"  复用旧核参数：{kernel}")
        else:
            kernel = Matern(nu=2.5, length_scale=1.0)
        
        gp = GaussianProcessRegressor(
            kernel=kernel,
            alpha=1.0,
            n_restarts_optimizer=2,  # 增量训练时减少优化次数
            normalize_y=True,
            random_state=42,
        )
        gp.fit(X_all, y_all)
        
        y_pred, y_std = gp.predict(X_all, return_std=True)
        gp_mae = float(np.mean(np.abs(y_pred - y_all)))
        gp_rmse = float(np.sqrt(np.mean((y_pred - y_all) ** 2)))
        
        # 更新模型
        new_model = {
            "type": "sklearn",
            "model": gp,
            "means": old_model.get("means", []),
            "stds": old_model.get("stds", []),
            "n_features": old_model.get("n_features", X_all.shape[1]),
            "training_samples": len(y_all),
            "X_train": X_all,  # 保存训练数据用于下次增量
            "y_train": y_all,
            "mae": round(gp_mae, 2),
            "rmse": round(gp_rmse, 2),
        }
        
        # 保存
        with open(GP_MODEL_PATH, "wb") as f:
            pickle.dump(new_model, f)
        
        print(f"\n✅ 增量训练完成！")
        print(f"  总样本数：{len(y_all)}")
        print(f"  MAE：{gp_mae:.2f}")
        print(f"  RMSE：{gp_rmse:.2f}")
        
        return new_model
        
    except Exception as e:
        print(f"❌ 增量训练失败：{e}")
        return None


def train_gp_model(X_norm, y, means, stds, n_features, n):
    """训练高斯过程回归模型（Matérn 5/2 核）"""
    # GP O(n³) 复杂度，超过 2000 样本需要子采样
    MAX_GP_SAMPLES = 10000
    if len(X_norm) > MAX_GP_SAMPLES:
        import random
        random.seed(42)
        indices = random.sample(range(len(X_norm)), MAX_GP_SAMPLES)
        X_gp = [X_norm[i] for i in indices]
        y_gp = [y[i] for i in indices]
        print(f"\n[高斯过程回归] 训练中（子采样 {MAX_GP_SAMPLES}/{len(X_norm)} 样本）...")
    else:
        X_gp = X_norm
        y_gp = y
        print(f"\n[高斯过程回归] 训练中...")

    gp_model = None

    # 尝试使用 sklearn
    try:
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import Matern
        import numpy as np

        X_np = np.array(X_gp)
        y_np = np.array(y_gp)

        kernel = Matern(nu=2.5, length_scale=1.0)
        gp = GaussianProcessRegressor(
            kernel=kernel,
            alpha=1.0,  # noise level
            n_restarts_optimizer=5,
            normalize_y=True,
            random_state=42,
        )
        gp.fit(X_np, y_np)

        y_pred, y_std = gp.predict(X_np, return_std=True)
        gp_mae = float(np.mean(np.abs(y_pred - y_np)))
        gp_rmse = float(np.sqrt(np.mean((y_pred - y_np) ** 2)))

        gp_model = {
            "type": "sklearn",
            "model": gp,
            "means": means,
            "stds": stds,
            "n_features": n_features,
            "training_samples": n,
            "X_train": X_np,  # 保存训练数据用于增量训练
            "y_train": y_np,
            "mae": round(gp_mae, 2),
            "rmse": round(gp_rmse, 2),
        }

        print(f"  使用 sklearn GaussianProcessRegressor")
        print(f"  核函数: Matérn(nu=2.5)")
        print(f"  MAE：{gp_mae:.2f}")
        print(f"  RMSE：{gp_rmse:.2f}")

    except ImportError:
        print("  sklearn 不可用，尝试安装...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn", "-q"])
            from sklearn.gaussian_process import GaussianProcessRegressor
            from sklearn.gaussian_process.kernels import Matern
            import numpy as np

            X_np = np.array(X_norm)
            y_np = np.array(y)

            kernel = Matern(nu=2.5, length_scale=1.0)
            gp = GaussianProcessRegressor(
                kernel=kernel,
                alpha=1.0,
                n_restarts_optimizer=5,
                normalize_y=True,
                random_state=42,
            )
            gp.fit(X_np, y_np)

            y_pred, y_std = gp.predict(X_np, return_std=True)
            gp_mae = float(np.mean(np.abs(y_pred - y_np)))
            gp_rmse = float(np.sqrt(np.mean((y_pred - y_np) ** 2)))

            gp_model = {
                "type": "sklearn",
                "model": gp,
                "means": means,
                "stds": stds,
                "n_features": n_features,
                "training_samples": n,
                "mae": round(gp_mae, 2),
                "rmse": round(gp_rmse, 2),
            }

            print(f"  已安装并使用 sklearn")
            print(f"  MAE：{gp_mae:.2f}")
            print(f"  RMSE：{gp_rmse:.2f}")

        except Exception as e:
            print(f"  sklearn 安装失败: {e}")
            print(f"  使用纯 Python 实现的简化 GP...")

    # 纯 Python fallback: 简化的 GP（使用 RBF 核，对小数据集子采样）
    if gp_model is None:
        gp_model, gp_mae, gp_rmse = _train_gp_pure_python(X_norm, y, means, stds, n_features, n)

    # 保存 GP 模型
    if gp_model["type"] == "sklearn":
        # sklearn 模型需要特殊处理
        save_data = {
            "type": "sklearn",
            "model": gp_model["model"],
            "means": means,
            "stds": stds,
            "n_features": n_features,
            "training_samples": n,
            "mae": gp_model["mae"],
            "rmse": gp_model["rmse"],
        }
    else:
        save_data = gp_model

    with open(MODEL_GP_PATH, "wb") as f:
        pickle.dump(save_data, f)

    print(f"  GP 模型已保存：{MODEL_GP_PATH}")
    return gp_model.get("mae", gp_mae if 'gp_mae' in dir() else 0), gp_model.get("rmse", gp_rmse if 'gp_rmse' in dir() else 0)


def _train_gp_pure_python(X_norm, y, means, stds, n_features, n):
    """纯 Python 实现的简化高斯过程（Matérn 5/2 核）"""
    import math

    def matern_52(x1, x2, length_scale=1.0):
        """Matérn 5/2 核函数"""
        dist_sq = sum(((a - b) / length_scale) ** 2 for a, b in zip(x1, x2))
        dist = dist_sq ** 0.5
        sqrt5_dist = math.sqrt(5) * dist
        return (1 + sqrt5_dist + sqrt5_dist**2 / 3) * math.exp(-sqrt5_dist)

    def rbf_kernel(x1, x2, length_scale=1.0):
        """RBF 核函数 (fallback)"""
        dist_sq = sum(((a - b) / length_scale) ** 2 for a, b in zip(x1, x2))
        return math.exp(-0.5 * dist_sq)

    # 对于大数据集，子采样训练点以保持计算可行
    max_train = 200
    if n > max_train:
        import random
        random.seed(42)
        indices = sorted(random.sample(range(n), max_train))
        X_sub = [X_norm[i] for i in indices]
        y_sub = [y[i] for i in indices]
        n_sub = max_train
    else:
        X_sub = X_norm
        y_sub = y
        n_sub = n

    print(f"  纯 Python GP: 训练点数={n_sub}, 特征维度={n_features}")

    # 计算核矩阵 K(X, X) + alpha * I
    alpha = 1.0
    length_scale = math.sqrt(n_features)  # heuristic

    K = [[0.0] * n_sub for _ in range(n_sub)]
    for i in range(n_sub):
        for j in range(i, n_sub):
            k_val = matern_52(X_sub[i], X_sub[j], length_scale)
            K[i][j] = k_val
            K[j][i] = k_val
        K[i][i] += alpha  # 加噪声

    # 解 K * alpha_vec = y  (使用 Cholesky 或直接求解)
    # 对于小矩阵，使用高斯消元
    alpha_vec = solve_linear([row[:] for row in K], y_sub[:])

    # 预测
    predictions = []
    for k in range(n):
        k_star = [matern_52(X_norm[k], X_sub[j], length_scale) for j in range(n_sub)]
        pred = sum(a * ks for a, ks in zip(alpha_vec, k_star))
        predictions.append(pred)

    gp_mae = sum(abs(p - y[k]) for k, p in enumerate(predictions)) / n
    gp_rmse = (sum((p - y[k]) ** 2 for k, p in enumerate(predictions)) / n) ** 0.5

    gp_model = {
        "type": "pure_python",
        "X_train": X_sub,
        "y_train": y_sub,
        "alpha_vec": alpha_vec,
        "length_scale": length_scale,
        "means": means,
        "stds": stds,
        "n_features": n_features,
        "training_samples": n,
        "mae": round(gp_mae, 2),
        "rmse": round(gp_rmse, 2),
    }

    print(f"  MAE：{gp_mae:.2f}")
    print(f"  RMSE：{gp_rmse:.2f}")

    return gp_model, gp_mae, gp_rmse


def solve_linear(A, b):
    """高斯消元法解线性方程组 Ax = b"""
    n = len(b)
    # 构造增广矩阵
    M = [A[i][:] + [b[i]] for i in range(n)]

    for col in range(n):
        # 选主元
        max_row = col
        for row in range(col + 1, n):
            if abs(M[row][col]) > abs(M[max_row][col]):
                max_row = row
        M[col], M[max_row] = M[max_row], M[col]

        # 消元
        pivot = M[col][col]
        if abs(pivot) < 1e-10:
            continue
        for row in range(col + 1, n):
            factor = M[row][col] / pivot
            for j in range(col, n + 1):
                M[row][j] -= factor * M[col][j]

    # 回代
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        if abs(M[i][i]) < 1e-10:
            x[i] = 0
            continue
        x[i] = M[i][n]
        for j in range(i + 1, n):
            x[i] -= M[i][j] * x[j]
        x[i] /= M[i][i]

    return x

# ==================== 验证 ====================

def verify():
    """验证模型"""
    if not MODEL_PATH.exists():
        print("模型不存在，请先训练")
        return

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    print(f"线性回归模型信息：")
    print(f"  训练样本：{model['training_samples']}")
    print(f"  特征维度：{model['n_features']}")
    print(f"  MAE：{model['mae']}")
    print(f"  RMSE：{model['rmse']}")

    # 加载 GP 模型
    gp_available = MODEL_GP_PATH.exists()
    if gp_available:
        with open(MODEL_GP_PATH, "rb") as f:
            gp_model = pickle.load(f)
        print(f"\n高斯过程回归模型信息：")
        print(f"  类型：{gp_model['type']}")
        print(f"  训练样本：{gp_model['training_samples']}")
        print(f"  特征维度：{gp_model['n_features']}")
        print(f"  MAE：{gp_model['mae']}")
        print(f"  RMSE：{gp_model['rmse']}")

    # 测试几个经典配色
    test_cases = [
        ("米白+卡其+黑", ["#F5F0E8", "#C4A97D", "#111111"]),
        ("军绿+米白+深棕", ["#5a6b40", "#f5f0e8", "#4a3520"]),
        ("藏青+白+卡其", ["#1a3a5c", "#f8f8f8", "#c4a97d"]),
        ("全黑+银饰", ["#111111", "#1a1a1a", "#c0c0c0"]),
        ("酒红+黑+灰", ["#8b2525", "#1a1a1a", "#808080"]),
        ("蓝+红+黄（撞色）", ["#0000ff", "#ff0000", "#ffff00"]),
    ]

    print(f"\n测试用例：")
    header = f"  {'名称':<20} {'线性预测':>8} {'理论值':>8}",
    if gp_available:
        header = f"  {'名称':<20} {'线性预测':>8} {'GP预测':>8} {'理论值':>8}"
    print(header if isinstance(header, str) else header[0])

    for name, colors in test_cases:
        areas = [1.0 / len(colors)] * len(colors)
        linear_score = predict(model, list(zip(colors, areas)))
        theory = theory_score(list(zip(colors, areas)))
        if gp_available:
            gp_score = predict_gp(gp_model, list(zip(colors, areas)))
            print(f"  {name:<20} {linear_score:8.1f} {gp_score:8.1f} {theory:8.1f}")
        else:
            print(f"  {name:<20} {linear_score:8.1f} {theory:8.1f}")

    # 比较摘要
    if gp_available:
        print(f"\n===== 模型比较 =====")
        print(f"  线性回归:  MAE={model['mae']:.2f}  RMSE={model['rmse']:.2f}")
        print(f"  高斯过程:  MAE={gp_model['mae']:.2f}  RMSE={gp_model['rmse']:.2f}")
        if gp_model['mae'] < model['mae']:
            print(f"  → 高斯过程 MAE 更优 (降低 {model['mae'] - gp_model['mae']:.2f})")
        else:
            print(f"  → 线性回归 MAE 更优 (降低 {gp_model['mae'] - model['mae']:.2f})")


def predict(model, colors_with_areas):
    """用线性模型预测分数"""
    features = extract_features(colors_with_areas)
    means = model["means"]
    stds = model["stds"]
    weights = model["weights"]
    bias = model["bias"]

    x_norm = [(features[i] - means[i]) / stds[i] for i in range(len(features))]
    score = sum(w * x for w, x in zip(weights, x_norm)) + bias
    return max(0, min(100, round(score, 1)))


def predict_gp(gp_model, colors_with_areas):
    """用 GP 模型预测分数"""
    features = extract_features(colors_with_areas)
    means = gp_model["means"]
    stds = gp_model["stds"]

    x_norm = [(features[i] - means[i]) / stds[i] for i in range(len(features))]

    if gp_model["type"] == "sklearn":
        import numpy as np
        X_np = np.array([x_norm])
        pred, std = gp_model["model"].predict(X_np, return_std=True)
        return max(0, min(100, round(float(pred[0]), 1)))
    else:
        # pure python
        import math
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


if __name__ == "__main__":
    if "--verify" in sys.argv:
        verify()
    elif "--incremental" in sys.argv:
        # 增量训练模式：python train_color_model.py --incremental <new_data.csv>
        if len(sys.argv) < 3:
            print("用法：python train_color_model.py --incremental <new_data.csv>")
            print("  CSV 格式：hex1,hex2,hex3,area1,area2,area3,score")
            sys.exit(1)
        
        import csv
        csv_path = sys.argv[2]
        new_X = []
        new_y = []
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 解析特征和分数
                from color_math import extract_features
                colors = [
                    (row["hex1"], float(row.get("area1", 0.33))),
                    (row["hex2"], float(row.get("area2", 0.33))),
                    (row["hex3"], float(row.get("area3", 0.34))),
                ]
                features = extract_features(colors)
                new_X.append(features)
                new_y.append(float(row["score"]))
        
        incremental_train_gp(new_X, new_y)
    else:
        train_model()
        print("\n")
        verify()
