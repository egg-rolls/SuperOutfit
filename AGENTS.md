# AGENTS.md - SuperOutfit 开发指南

> 本文档指导工程师（包括 AI Agent）开发和维护 SuperOutfit 项目。

## 项目概述

SuperOutfit 是一个 AI 智能穿搭顾问系统，以 Hermes Skill 形式运行。核心能力：

1. **衣物管理** — YAML 文件存储，用户可直接在资源管理器浏览编辑
2. **穿搭推荐** — AI 基于天气 + 衣橱 + 用户画像推荐搭配
3. **色彩评分** — 基于 6400 组真实色卡训练的高斯过程数学模型
4. **领域知识** — 12 个知识文件覆盖穿搭全栈（色彩/版型/风格/场合/叠穿/购买）

核心流程：

```
用户请求 → AI 读取 SKILL.md + 按需加载 references/
         → 调用 weather.py 获取天气
         → 调用 wardrobe_ops.py 读取衣橱
         → AI 推荐搭配
         → 调用 scorer.py → color_math.py → GP 模型评分
         → 输出推荐方案
```

## 项目结构

```
superoutfit/
├── AGENTS.md               # 本文件 — 开发指南
├── SKILL.md                # Hermes Agent 指令文件
├── README.md               # 用户文档
├── LICENSE                 # MIT
├── setup.py                # 首次安装脚本
├── build_ui.py             # 生成可视化 HTML
├── export.py               # 导出分享包
│
├── scripts/                # 核心脚本
│   ├── wardrobe_ops.py     # 衣物 CRUD（add/list/show/update/delete/stats/reindex/record/restore）
│   ├── weather.py          # 天气查询（Open-Meteo 免费 API）
│   ├── scorer.py           # 搭配评分（6 维度，调用 color_math.py）
│   ├── color_math.py       # 色彩协调度计算（GP 模型 + HSL + OKLab）
│   ├── train_color_model.py # 色彩模型训练（特征提取 + 线性回归 + GP）
│   ├── scrape_palettes.py  # 色卡爬虫（Color Hunt + Colormind + LOL Colors + Design Seeds）
│   └── scrape_wxsecai.py   # 色卡爬虫（色采 wxsecai.com / colorcollect.cn）
│
├── templates/              # 数据模板
│   ├── item_template.yaml  # 衣物模板（含 HEX 色值字段）
│   ├── profile_template.yaml
│   └── outfit_template.yaml
│
├── references/             # 穿搭领域知识（按需加载）
│   ├── color.md            # 色彩搭配规则
│   ├── color_theory.md     # 色彩理论数学（底色/色环/CMYK）
│   ├── color_pipeline.md   # 色彩模型数据管道技术文档
│   ├── silhouette.md       # 版型与身材匹配
│   ├── wardrobe.md         # 衣橱结构与日常流程
│   ├── layering.md         # 叠穿层次指南
│   ├── occasion.md         # 5 大场合穿搭指南
│   ├── style_archetypes.md # 7 种风格体系
│   ├── accessories.md      # 配饰指南
│   ├── shoes.md            # 鞋子指南
│   ├── buying.md           # 购买决策指南
│   ├── mistakes.md         # 常见雷区
│   ├── care.md             # 衣物养护
│   └── SOURCES.md          # 知识来源记录
│
└── data/                   # 用户数据（.gitignore 排除）
    ├── profile.yaml        # 用户画像
    ├── wardrobe_index.yaml # 衣物索引（自动生成）
    ├── history.yaml        # 穿搭历史
    ├── preferences.yaml    # AI 学习偏好
    ├── items/              # 衣物详情 YAML
    ├── outfits/            # 搭配方案
    ├── images/             # 衣物图片
    ├── archive/            # 已淘汰衣物
    ├── raw_palettes.json   # 色卡原始数据（6400 组）
    ├── color_model.pkl     # 线性回归模型
    ├── color_model_gp.pkl  # 高斯过程模型（当前使用）
    └── feature_stats.json  # 特征归一化统计
```

## 文件依赖链

```
scrape_palettes.py / scrape_wxsecai.py
  ↓ 输出
data/raw_palettes.json (6400 组色卡)
  ↓ 输入
train_color_model.py
  ↓ 输出
data/color_model_gp.pkl + data/color_model.pkl + data/feature_stats.json
  ↓ 加载
color_math.py (模型预测)
  ↓ 被调用
scorer.py (搭配评分)
  ↓ 被调用
SKILL.md 工作流中 AI 调用
```

## 色彩评分系统

### 架构

```
输入：可变长度的 HEX 色值列表 + 面积占比
  ↓
特征提取（42 维 = 27 HSL + 15 OKLab）
  ↓
高斯过程模型（Matérn 5/2 核，MAE 2.66）
  ↓
输出：0-100 协调度分数
```

### 关键文件

| 文件 | 职责 |
|------|------|
| `train_color_model.py` | 特征定义、模型训练、OKLab 转换 |
| `color_math.py` | 特征提取（与训练一致）、模型预测、CLI |
| `scorer.py` | 调用 color_math.py，整合 6 维度评分 |

### 数据源（6400 组色卡）

| 来源 | 数量 | 脚本 |
|------|------|------|
| Color Hunt | 2046 | scrape_palettes.py |
| 色采 (wxsecai) | 4171 | scrape_wxsecai.py |
| LOL Colors | 105 | scrape_palettes.py |
| Design Seeds | 48 | scrape_palettes.py |
| Colormind | 30 | scrape_palettes.py |

### 模型对比

| 模型 | MAE | RMSE | 训练样本 | 说明 |
|------|-----|------|----------|------|
| 线性回归 + L2 | 3.38 | 4.45 | 6400 | 旧模型（理论标签） |
| GP Matérn 5/2 | **6.95** | 12.68 | 5462（500 诱导点） | 当前使用（点赞标签 + 离群剔除 + Sparse GP） |

### 关键设计决策

1. **特征唯一实现** — `like_based_scoring.py::extract_features()` 是唯一的特征提取函数，`color_math.py` 通过导入调用，避免两份代码不一致
2. **点赞迁移** — 用 Color Hunt 的人类点赞训练迁移模型，给无赞色卡预测分数
3. **离群剔除** — 全黑/全白/霓虹色（饱和度>90）在训练前剔除，避免污染模型
4. **Sparse GP** — 用 K-Means 聚类选 500 个诱导点，训练速度提升 30 倍（~10 秒 vs ~5 分钟）

```bash
# 1. 爬取新色卡（可选）
python scripts/scrape_palettes.py
python scripts/scrape_wxsecai.py

# 2. 重训模型
python scripts/train_color_model.py

# 3. 验证
python scripts/train_color_model.py --verify
```

### 扩展色彩系统

- **添加数据源：** 在 scrape_palettes.py 中添加新爬取函数，输出格式统一为 `[{ "colors": ["#hex", ...], "likes": N, "source": "xxx" }]`
- **添加特征：** 同步修改 train_color_model.py 和 color_math.py 的 `_extract_features()`（必须一致）
- **升级模型：** 修改 train_color_model.py 的训练逻辑，保持输出格式兼容
- **详细文档：** 参见 `references/color_pipeline.md`

## 衣物数据格式

每件衣物是一个独立的 YAML 文件，含 HEX 色值：

```yaml
id: item_001
type: 上衣
sub_type: 短袖衬衫
colors:
  primary: 米白色
  primary_hex: "#F5F0E8"    # 色彩模型使用
  secondary: 无
  secondary_hex: ""
  tertiary: ""
  tertiary_hex: ""
  pattern: 纯色
material: 冰丝缎面
fit: 宽松落肩
style: [简约, 通勤, 轻商务, 休闲]
season: [春, 夏, 初秋]
temperature_range: "18~32"
occasion: [日常通勤, 外出逛街, 轻商务会面, 休闲约会]
wear_count: 0
last_worn: ""
pair_with: [休闲西裤, 直筒牛仔裤]
restrict: [厚重高领内搭]
favorite: false
image: item_001.jpg
```

## 评分维度

scorer.py 的 6 个评分维度：

| 维度 | 权重 | 实现 |
|------|------|------|
| 颜色协调 | 25% | color_math.py GP 模型 |
| 风格一致 | 20% | 风格标签交集 |
| 场合匹配 | 20% | occasion 标签匹配 |
| 天气适配 | 15% | temperature_range 匹配 |
| 穿着新鲜度 | 10% | wear_count 反比 |
| 用户偏好 | 10% | profile 风格/颜色匹配 |

### 色彩等级（基于人类审美分布 P50=63）

| 等级 | 分数 | 含义 |
|------|------|------|
| SSS | ≥ 85 | 顶级，名画级配色（前 ~8%） |
| SS | ≥ 75 | 优秀，专业搭配师水准（前 ~20%） |
| S | ≥ 65 | 出色，有明确审美风格（前 ~35%） |
| A | ≥ 50 | 良好，和谐不出错（前 ~55%） |
| B | ≥ 35 | 一般，中规中矩（前 ~80%） |
| C | ≥ 20 | 偏弱，需要调整（前 ~93%） |
| D | < 20 | 差，明显不搭（后 ~7%） |

## 可视化 UI

```bash
python build_ui.py
# 输出：ui/outfit.html（自包含，含图片 base64，浏览器直接打开）
```

- 每次添加/修改衣物后需要重新运行
- 包含 4 个标签页：衣橱、画像、推荐、历史

## 知识体系

references/ 下的 12 个知识文件按决策点组织：

```
用户问"什么颜色配什么"     → color.md + color_theory.md
用户问"什么版型适合我"     → silhouette.md
用户问"怎么搭配"          → wardrobe.md + layering.md
用户问"某场合穿什么"       → occasion.md
用户问"什么风格适合"       → style_archetypes.md
用户问"配饰怎么搭"         → accessories.md
用户问"鞋子怎么选"         → shoes.md
用户问"该买什么"           → buying.md
用户问"搭配对不对"         → mistakes.md
用户问"怎么洗/保养"        → care.md
维护色彩模型              → color_pipeline.md
```

SKILL.md 指示 AI 按需加载，不全部注入以节省 token。

## 已知陷阱

### 色卡数据可能含无效 HEX
爬取的色卡数据可能包含空白、换行、非 HEX 字符。`hex_to_rgb()` 已加 strip + 验证，但新增数据源时需注意。

### GP 模型 O(n³) → Sparse GP O(nm²)
6400 全量 GP 训练约需 5 分钟。当前使用 Sparse GP（500 诱导点），训练 ~10 秒，精度损失 < 5%。数据量增长到 10000+ 时可增加诱导点数量。

### color_math.py 和 like_based_scoring.py 特征必须一致
`like_based_scoring.py::extract_features()` 是唯一的特征提取实现。`color_math.py` 通过 `from like_based_scoring import extract_features` 调用。不要在 color_math.py 中重新实现特征提取，否则 GP 预测会偏差巨大（已踩坑：OKLab a,b 通道乘了 5 导致分数偏差 15 分）。

### 评分维度权重是主观设定的
scorer.py 的 6 维度权重（0.25/0.20/0.20/0.15/0.10/0.10）是经验值，没有数据验证。未来可以用用户反馈数据来优化。

### data/ 目录被 .gitignore 排除
个人数据（衣物、画像、历史）不会被上传。但 raw_palettes.json 和模型文件也在 data/ 下，发布时需要通过 export.py 或 setup.py 处理。

## 提交规范

```bash
<type>(<scope>): <subject>
```

- `feat`: 新功能
- `fix`: Bug 修复
- `data`: 色卡数据更新
- `model`: 模型重训/升级
- `docs`: 文档更新
- `refactor`: 重构
