# 色彩模型技术文档

本文档记录 SuperOutfit 色彩评分系统的完整数据管道，供开发者和 AI 继承和扩展。

## 架构总览

```
数据获取              训练                    预测
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
scrape_palettes.py    train_color_model.py    color_math.py
      ↓                     ↓                     ↓
raw_palettes.json     color_model.pkl      →  0-100 分数
(2046组真实色卡)       feature_stats.json      (支持变长输入)
```

## 数据源

### 当前数据
- **来源：** Color Hunt (colorhunt.co)
- **方式：** 爬取 `colorhunt.co/php/feed.php` API
- **规模：** 2046 组去重后的配色方案
- **格式：** 每组 4 个 HEX 色值 + 点赞数
- **存储：** `data/raw_palettes.json`

### 扩展数据源（待接入）
| 来源 | 规模 | 获取方式 | 说明 |
|------|------|----------|------|
| Adobe Color | ~10万组 | API / 爬取 | 社区上传的配色方案 |
| Coolors | ~5万组 | 爬取 | 热门生成器 |
| Design Seeds | ~2万组 | 爬取 | 自然灵感配色 |
| 名画色卡 | 自定义 | k-means 聚类 | 从画作中提取主色 |
| 中国传统色 | ~500色 | 公开数据集 | 故宫色卡等 |
| 日本传统色 | ~250色 | 公开数据集 | 和风配色 |

### 数据获取流程

```bash
# 1. 运行爬虫
python scripts/scrape_palettes.py

# 2. 数据保存在
data/raw_palettes.json
# 格式：[{ "colors": ["#hex1", "#hex2", ...], "likes": N, "source": "colorhunt" }]

# 3. 重新训练模型
python scripts/train_color_model.py

# 4. 模型自动保存在
data/color_model.pkl
data/feature_stats.json
```

## 特征工程

### 27 维特征向量

从颜色列表提取固定长度特征，支持变长输入（2-6 个颜色）：

| 编号 | 特征 | 说明 |
|------|------|------|
| 0-2 | 加权平均 HSL | 按面积加权的色相/饱和度/明度 |
| 3-5 | 简单平均 HSL | 不加权的色相/饱和度/明度 |
| 6-9 | 色相统计 | max/min/span/标准差 |
| 10-13 | 饱和度统计 | max/min/span/标准差 |
| 14-17 | 明度统计 | max/min/span/标准差 |
| 18-21 | 色相距离统计 | 两两距离的 mean/max/min/标准差 |
| 22 | 有彩色比例 | 有彩色占总颜色的比例 |
| 23 | 面积分布熵 | 面积分配的均匀程度 |
| 24 | 颜色数量 | 归一化的颜色数量 |
| 25 | 明度对比度 | 最亮与最暗的差 |
| 26 | 饱和度对比度 | 最饱和与最不饱和的差 |

### 待升级：OKLab 色彩空间

当前特征基于 HSL，存在感知不均匀性。升级方向：

- 将颜色转换为 OKLab 色彩空间再提取特征
- OKLab 等数值距离 = 等感知差异
- 预期提升 5-15%
- 实现：在 `_extract_features()` 中增加 OKLab 版本的特征

## 模型

### 当前模型：点赞迁移 + 高斯过程（GP）

```
核心思路：用人类点赞数据代替理论规则做训练标签

数据流：
  6400 组原始色卡
  → 剔除离群（全黑/全白/霓虹色 938 组）
  → 5462 组干净色卡
  → Color Hunt 1456 组有赞 → 百分位分数
  → Sparse GP 迁移模型（500 诱导点）→ 预测 4006 组无赞色卡
  → 全量 5462 组都有人类审美分数
  → Sparse GP 最终模型（500 诱导点，MAE 6.95）

特征维度：42（27 HSL + 15 OKLab）
特征来源：like_based_scoring.py::extract_features()（唯一实现）
GP 训练：5462 样本，500 诱导点，~10 秒
```

### 离群色卡过滤规则

```
全黑：所有颜色明度 < 10% → 剔除
全白：所有颜色明度 > 95% → 剔除
霓虹色：任一颜色饱和度 > 90 且明度 30-70 → 剔除
```

### 等级阈值（基于人类审美分布 P50=63）

```
SSS ≥ 85   顶级（前 ~8%）   名画级配色
SS  ≥ 75   优秀（前 ~20%）  专业搭配师水准
S   ≥ 65   出色（前 ~35%）  有明确审美风格
A   ≥ 50   良好（前 ~55%）  和谐不出错
B   ≥ 35   一般（前 ~80%）  中规中矩
C   ≥ 20   偏弱（前 ~93%）  需要调整
D   < 20   差（后 ~7%）     明显不搭
```

### 点赞迁移脚本

```bash
# 运行点赞迁移（一次性，数据更新后重跑）
python scripts/like_based_scoring.py

# 输出：
#   data/scored_palettes.json    6400 组色卡 + 分数
#   data/like_transfer_model.pkl 迁移模型
#   data/color_model_gp.pkl      最终 GP 模型
```

### OKLab 特征（15 维）

OKLab 色彩空间：等数值距离 = 等感知差异，比 HSL 更适合色彩计算。

| 编号 | 特征 | 说明 |
|------|------|------|
| 27-29 | OKLab 加权平均 L,a,b | 按面积加权的感知亮度/红绿/黄蓝 |
| 30-32 | OKLab 简单平均 L,a,b | 不加权 |
| 33-36 | OKLab L 统计 | max/min/span/标准差 |
| 37-40 | OKLab Chroma 统计 | 饱和度（感知）的统计 |
| 41 | OKLab Hue 距离 | 两两色相距离均值 |

### 数据来源

| 来源 | 数量 | 状态 |
|------|------|------|
| 色采 (wxsecai) | 4171 | ✅ |
| Color Hunt | 2046 | ✅ |
| LOL Colors | 105 | ✅ |
| Design Seeds | 48 | ✅ |
| Colormind | 30 | ✅ |
| Colour Lovers | - | ❌ 403 封锁 |
| Adobe Color | - | ❌ API 变更 |

### 重训模型的时机

- 新增 500+ 色卡数据后
- 添加新的数据源后
- 特征工程升级后（如加入 OKLab）
- 用户反馈评分不准时

```bash
# 重训命令
python scripts/train_color_model.py

# 验证命令
python scripts/train_color_model.py --verify
```

## 评分接口

### color_math.py

```bash
# 通过衣物 ID 评分
python scripts/color_math.py --items item_001,item_003,item_006

# 直接传 HEX 色值
python scripts/color_math.py --colors "#F5F0E8,#C4A97D,#111111"

# 带面积占比（主色50% + 辅助35% + 点缀15%）
python scripts/color_math.py --colors "#F5F0E8,#C4A97D,#111111" --areas "0.5,0.35,0.15"

# 详细分析
python scripts/color_math.py --items item_001,item_003 --detail
```

### scorer.py（集成调用）

scorer.py 自动调用 color_math.py 的模型评分，无需手动干预。

## 文件依赖关系

```
scrape_palettes.py
  ↓ 输出
data/raw_palettes.json
  ↓ 输入
train_color_model.py
  ↓ 输出
data/color_model.pkl + data/feature_stats.json
  ↓ 输入
color_math.py（预测时加载模型）
  ↓ 被调用
scorer.py（搭配评分时调用 color_math）
```

## 扩展指南

### 添加新的色卡数据源

1. 在 `scrape_palettes.py` 中添加新的爬取函数
2. 输出格式统一为 `[{ "colors": ["#hex", ...], "likes": N, "source": "xxx" }]`
3. 追加到 `data/raw_palettes.json`
4. 重新运行 `train_color_model.py`

### 添加新的特征

1. 在 `train_color_model.py` 的 `_extract_features()` 中添加
2. 同步更新 `color_math.py` 的 `_extract_features()`（必须一致）
3. 重新训练模型
4. `n_features` 会自动变化，模型文件会记录新的维度

### 升级模型算法

1. 在 `train_color_model.py` 中替换训练逻辑
2. 保持 `model.pkl` 的格式：`{ weights, bias, means, stds, n_features }`
3. 或者改为新格式，在 `color_math.py` 的 `_load_model()` 中适配
