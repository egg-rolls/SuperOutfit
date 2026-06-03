# AGENTS.md - SuperOutfit 开发指南

> 本文档指导工程师（包括 AI Agent）开发和维护 SuperOutfit 项目。

## 项目概述

SuperOutfit 是一个 AI 智能穿搭顾问系统，支持三种入口：

1. **CLI 命令行** — 统一的 `superoutfit` 命令（推荐）
2. **MCP Server** — 通过 stdio 协议与 AI Agent 交互（12 个工具）
3. **FastAPI 后端** — REST API，支持前端调用（端口 8001）
4. **Vue 前端** — Web 界面，Claude 设计风格（端口 5173）

核心能力：
- **衣物管理** — YAML 文件存储，用户可直接在资源管理器浏览编辑
- **穿搭推荐** — AI 基于天气 + 衣橱 + 用户画像推荐搭配
- **色彩评分** — 基于 6400 组真实色卡训练的高斯过程数学模型
- **主题系统** — 从色卡中提取 4 色切换全站主题，派生全部 CSS 变量

## 项目结构

```
D:\Application\SuperOutfit\
├── AGENTS.md               # 本文件 — 开发指南
├── SKILL.md                # Hermes Agent 指令文件
├── README.md               # 用户文档
├── LICENSE                 # MIT
├── superoutfit.py          # CLI 入口（统一命令）
├── server.py               # MCP Server
├── pyproject.toml          # Python 依赖 + CLI 入口点
│
├── api/                    # FastAPI 后端
│   └── main.py             # 12+ REST 端点，静态文件服务
│
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── App.vue         # 主应用（设计系统 + 主题逻辑）
│   │   ├── composables/    # 可复用逻辑（useWardrobe, useProfile, usePalettes, useRefs）
│   │   ├── components/     # UI 组件（AppHeader, TabNav, WardrobeCard, ItemModal, RefModal）
│   │   ├── views/          # 页面组件（WardrobeView, PalettesView, RefsView, ProfileView, RecommendView）
│   │   └── services/       # API 服务层
│   ├── public/
│   │   ├── manifest.json   # PWA 配置
│   │   └── sw.js           # Service Worker
│   ├── vite.config.js      # Vite 配置 + API 代理
│   └── package.json
│
├── scripts/                # 核心脚本 + 工具
│   ├── wardrobe_ops.py     # 衣物 CRUD（add/list/show/update/delete/stats/reindex/record/restore）
│   ├── weather.py          # 天气查询（Open-Meteo 免费 API）
│   ├── scorer.py           # 搭配评分（6 维度，调用 color_math.py）
│   ├── color_math.py       # 色彩协调度计算（GP 模型 + HSL + OKLab）
│   ├── like_based_scoring.py # 特征提取 + 点赞迁移 + 7 级评分
│   ├── train_color_model.py # 色彩模型训练（特征提取 + 线性回归 + GP）
│   ├── scrape_palettes.py  # 色卡爬虫（Color Hunt + Colormind + LOL Colors + Design Seeds）
│   ├── scrape_wxsecai.py   # 色卡爬虫（色采 wxsecai.com / colorcollect.cn）
│   ├── init_data.py        # 首次初始化数据目录
│   ├── export.py           # 导出分享包
│   ├── install_skill.py    # 从应用目录同步文档到 skill 目录
│   └── templates/          # 数据模板
│       ├── item_template.yaml
│       ├── profile_template.yaml
│       └── outfit_template.yaml
│
├── docs/                   # 项目文档
│   └── architecture.md     # 架构演进记录
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
    ├── scored_palettes.json # 5462 组已评分色卡
    ├── color_model_gp.pkl  # 高斯过程模型（当前使用）
    └── like_transfer_model.pkl # 点赞迁移模型
```

## 多平台架构

```
┌─────────────────────────────────────────────────────────────┐
│                       SuperOutfit                           │
├─────────────────────────────────────────────────────────────┤
│  CLI (superoutfit.py)                                       │
│  └─ 统一命令入口：wardrobe/weather/score/color/palette/...   │
├─────────────────────────────────────────────────────────────┤
│  MCP Server (server.py)                                     │
│  └─ 12 个工具（天气/衣橱/推荐/评分/色彩）                      │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Backend (api/main.py, 端口 8001)                   │
│  └─ 12+ REST 端点 + 静态文件服务                              │
│  └─ 通过 subprocess 调用 scripts/ CLI 工具                   │
├─────────────────────────────────────────────────────────────┤
│  Vue 3 Frontend (frontend/, 端口 5173)                      │
│  └─ Naive UI + @vicons/ionicons5                            │
│  └─ 4 个页面：衣橱、推荐、色卡、知识库                         │
│  └─ Claude 设计风格 + 主题切换                                │
├─────────────────────────────────────────────────────────────┤
│  Python Scripts (scripts/)                                  │
│  └─ wardrobe_ops.py / weather.py / scorer.py / color_math.py │
└─────────────────────────────────────────────────────────────┘
```

### 启动命令

```bash
# CLI（推荐）
superoutfit wardrobe list
superoutfit score --items item_001,item_003 --occasion 通勤

# 后端（端口 8001）
uv run uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload

# 前端（端口 5173，自动代理 API）
cd frontend && npm run dev

# MCP Server
python server.py
```

## 主题系统

### 设计原则

1. **4 个基础色** — 用户可配置（accent, canvas, dark, muted）
2. **全部派生** — 从 4 色自动计算 20+ CSS 变量
3. **对比度保护** — 文字色根据背景亮度自动计算（WCAG ≥ 4.5:1）
4. **色卡切换** — 点击色卡直接应用，>4 色时弹窗选择

### CSS 变量层级

```
用户可配置（4 个）:
  --user-accent    → 按钮、强调色
  --canvas         → 页面背景
  --dark           → 深色表面（头部、深色卡片）
  --user-muted     → 辅助文字

派生自 dark:
  --surface-dark-elevated    → 深色提升面
  --surface-dark-soft        → 深色软面

派生自 canvas:
  --surface-soft             → 浅色软面
  --surface-card             → 卡片背景
  --surface-cream-strong     → 强调浅色
  --hairline                 → 边框线
  --hairline-soft            → 软边框

派生自文字色（基于 canvas 对比度）:
  --ink                      → 主文字
  --body                     → 正文
  --body-strong              → 强调正文
  --muted-soft               → 柔和辅助

派生自 accent:
  --primary-active           → 按钮按下
  --primary-disabled         → 禁用按钮

特殊文字（基于各自背景对比度）:
  --on-primary               → accent 上的文字
  --on-dark                  → dark 上的文字
  --on-dark-soft             → dark-soft 上的文字
```

### 实现文件

| 文件 | 职责 |
|------|------|
| `frontend/src/App.vue` | `applyTheme()` 函数，设置所有 CSS 变量 |
| `frontend/src/views/PalettesView.vue` | `generateTheme()` 函数，计算派生颜色 |

### 已知陷阱

#### 主题派生颜色必须完整更新
`applyTheme()` 必须设置所有 20+ CSS 变量，否则未更新的变量会保持硬编码值。
例如：`--surface-dark-elevated` 如果不更新，会一直是 `#252520`（黑色），导致深色背景上的文字看不见。

#### 文字色必须根据背景计算
不能固定 `--ink: #1a1a1a`（深色），因为当 `--canvas` 是深色时，深色文字看不见。
必须用 `pickTextColor(bg)` 根据背景亮度动态计算：
```javascript
function pickTextColor(bg) {
  const lum = getLuminance(bg)
  return lum > 0.4 ? '#1a1a1a' : '#f5f0e8'
}
```

#### 4 色色卡直接应用
色卡正好 4 色时直接应用，<4 色填充默认，>4 色弹窗选择。
不要对 4 色色卡弹窗，用户期望直接切换。

## 文件依赖链

```
scrape_palettes.py / scrape_wxsecai.py
  ↓ 输出
data/raw_palettes.json (6400 组色卡)
  ↓ 输入
train_color_model.py
  ↓ 输出
data/color_model_gp.pkl + data/like_transfer_model.pkl
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
高斯过程模型（Matérn 5/2 核，500 诱导点）
  ↓
输出：0-100 协调度分数 → 7 级评分（SSS/SS/S/A/B/C/D）
```

### 关键文件

| 文件 | 职责 |
|------|------|
| `train_color_model.py` | 特征定义、模型训练、OKLab 转换 |
| `like_based_scoring.py` | **唯一特征提取实现**、点赞迁移、7 级评分 |
| `color_math.py` | 特征提取（通过导入调用）、模型预测、CLI |
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

### 评分等级（基于人类审美分布 P50=63.4）

| 等级 | 分数 | 含义 |
|------|------|------|
| SSS | ≥ 85 | 顶级，名画级配色（前 ~8%） |
| SS | ≥ 75 | 优秀，专业搭配师水准（前 ~20%） |
| S | ≥ 65 | 出色，有明确审美风格（前 ~35%） |
| A | ≥ 50 | 良好，和谐不出错（前 ~55%） |
| B | ≥ 35 | 一般，中规中矩（前 ~80%） |
| C | ≥ 20 | 偏弱，需要调整（前 ~93%） |
| D | < 20 | 差，明显不搭（后 ~7%） |

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

## Git 提交规范

```bash
<type>(<scope>): <subject>
```

- `feat`: 新功能
- `fix`: Bug 修复
- `refactor`: 重构（不改变功能）
- `ui`: UI/样式调整
- `data`: 色卡数据更新
- `model`: 模型重训/升级
- `docs`: 文档更新
- `chore`: 杂项（.gitignore 等）

## 已知陷阱

### 1. 特征提取不一致
`like_based_scoring.py::extract_features()` 是唯一的特征提取实现。`color_math.py` 通过 `from like_based_scoring import extract_features` 调用。不要在 color_math.py 中重新实现特征提取，否则 GP 预测会偏差巨大（已踩坑：OKLab a,b 通道乘了 5 导致分数偏差 15 分）。

### 2. GP 模型 O(n³) → Sparse GP O(nm²)
6400 全量 GP 训练约需 5 分钟。当前使用 Sparse GP（500 诱导点），训练 ~10 秒，精度损失 < 5%。数据量增长到 10000+ 时可增加诱导点数量。

### 3. data/ 目录被 .gitignore 排除
个人数据（衣物、画像、历史）不会被上传。但 raw_palettes.json 和模型文件也在 data/ 下，发布时需要通过 export.py 或 setup.py 处理。

### 4. 主题派生颜色必须完整更新
`applyTheme()` 必须设置所有 20+ CSS 变量。遗漏任何一个变量会导致该变量保持硬编码值，与主题不一致。

### 5. 文字色必须动态计算
不能固定文字颜色，必须根据背景亮度用 `pickTextColor()` 计算，否则深色主题下文字看不见。

### 6. 色卡 <4 色时填充默认值
色卡不足 4 色时用默认值填充（accent → canvas → dark → muted），不弹窗。

### 7. Git push 需要代理
GitHub 连接超时，需要配置代理（端口 7892）才能 push。
