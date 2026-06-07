# AGENTS.md - SuperOutfit v3.2.1 开发指南

> 本文档指导工程师（包括 AI Agent）开发和维护 SuperOutfit 项目。

## 项目概述

SuperOutfit 是一个 AI 智能穿搭顾问系统，支持三种入口：

1. **CLI 命令行** — 统一的 `spof` 命令（推荐）
2. **MCP Server** — 通过 stdio 协议与 AI Agent 交互（12 个工具）
3. **FastAPI 后端** — REST API + 前端静态服务（端口 32200）
4. **Vue 前端** — Web 界面，由 API 直接服务

核心能力：
- **衣物管理** — YAML 文件存储，用户可直接在资源管理器浏览编辑
- **穿搭推荐** — AI 基于天气 + 衣橱 + 用户画像推荐搭配
- **色彩评分** — 基于 6400 组真实色卡训练的高斯过程数学模型
- **穿着追踪** — 记录穿着/洗涤历史，自动计算单次穿着成本
- **心愿单** — 独立管理想买的衣物，与正式衣橱隔离
- **主题系统** — 从色卡中提取 4 色切换全站主题，派生全部 CSS 变量

## v3.2 设计原则

1. **AI 写 YAML，spof 处理它** — 所有衣物数据通过 YAML 文件提交，没有 `--field` 参数
2. **`--wishlist` 切换目标** — 默认操作 `data/items/`，加 `--wishlist` 操作 `data/wishlist/`
3. **模糊搜索用 `search_files`** — 不自建搜索命令，复用文件搜索工具
4. **数据自包含** — 穿着日期 (`wear_dates`)、洗涤频率 (`wash_frequency`) 写入 item YAML
5. **批量操作** — `--items` 逗号分隔、`--type` 过滤类型

## 项目结构

```
D:\Application\SuperOutfit\
├── AGENTS.md               # 本文件 — 开发指南
├── SKILL.md                # Hermes Agent 指令文件
├── README.md               # 用户文档
├── CLI.md                  # CLI 命令速查
├── LICENSE                 # MIT
├── superoutfit.py          # CLI 入口（spof 命令）
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
│   │   ├── components/     # UI 组件
│   │   ├── views/          # 页面组件
│   │   └── services/       # API 服务层
│   ├── public/
│   │   ├── manifest.json   # PWA 配置
│   │   └── sw.js           # Service Worker
│   ├── vite.config.js      # Vite 配置 + API 代理
│   └── package.json
│
├── scripts/                # 核心脚本 + 工具
│   ├── wardrobe_ops.py     # 衣物 CRUD（add/list/show/edit/delete）
│   ├── wear_ops.py         # 穿着记录（add/wash/check/report）
│   ├── weather.py          # 天气查询（Open-Meteo 免费 API）
│   ├── scorer.py           # 搭配评分（6 维度，调用 color_math.py）
│   ├── color_math.py       # 色彩协调度计算（GP 模型 + HSL + OKLab）
│   ├── like_based_scoring.py # 特征提取 + 点赞迁移 + 7 级评分
│   ├── train_color_model.py # 色彩模型训练
│   ├── scrape_palettes.py  # 色卡爬虫
│   ├── scrape_wxsecai.py   # 色卡爬虫（色采）
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
│   ├── color_theory.md     # 色彩理论数学
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
    ├── preferences.yaml    # AI 学习偏好
    ├── items/              # 衣物详情 YAML（正式衣橱）
    ├── wishlist/           # 心愿单 YAML（想买的衣物）
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
│                      SuperOutfit v3.2.1                      │
├─────────────────────────────────────────────────────────────┤
│  CLI (superoutfit.py → spof)                                │
│  └─ 统一命令入口：add/list/show/edit/delete/wear/color/...   │
├─────────────────────────────────────────────────────────────┤
│  MCP Server (server.py)                                     │
│  └─ 12 个工具（天气/衣橱/推荐/评分/色彩）                      │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Backend (api/main.py, 端口 32200)                  │
│  └─ 12+ REST 端点 + 前端静态文件服务                          │
│  └─ 通过 subprocess 调用 scripts/ CLI 工具                   │
├─────────────────────────────────────────────────────────────┤
│  Vue 3 Frontend (frontend/dist/, 由 API 直接服务)             │
│  └─ 生产模式：构建后由 FastAPI 静态服务                        │
│  └─ 开发模式：Vite 热重载（独立端口，API端口+1）               │
├─────────────────────────────────────────────────────────────┤
│  Python Scripts (scripts/)                                  │
│  └─ wardrobe_ops.py / wear_ops.py / weather.py / scorer.py  │
└─────────────────────────────────────────────────────────────┘
```

### 启动命令

```bash
# CLI（推荐）
spof list
spof list --type 上衣 --season 夏
spof show item_001
spof wear report --items item_001

# Gateway 一键启动（推荐）
spof gateway                    # 启动 API + 前端（端口 32200）
spof gateway --dev              # 开发模式（前端热重载，独立端口）
spof gateway --no-frontend      # 仅 API 后端
spof gateway --no-mcp           # 不启动 MCP

# 手动启动后端（仅调试用）
uv run uvicorn api.main:app --host 0.0.0.0 --port 32200 --reload

# MCP Server（由 MCP 客户端自动启动）
python server.py
```

## CLI 命令概览（v3.2）

完整参考见 [CLI.md](CLI.md)。核心命令：

```bash
# ── 衣橱管理 ──
spof add --file item.yaml [--wishlist]        # 添加衣物
spof list [--type X] [--season X] [--wishlist] [--json]
spof show item_001 [--json]
spof edit item_001 --file new.yaml            # 整文件覆盖
spof delete item_001 [--wishlist]

# ── 穿着追踪 ──
spof wear add --items item_001,item_002       # 记录穿着
spof wear wash --items item_001               # 标记已洗
spof wear check [--type X]                    # 需要洗涤的衣物
spof wear report [--items X] [--json]         # 穿着报告 + 单次穿着成本

# ── 色彩分析 ──
spof color score --colors '#F5F0E8,#111111'   # 色彩协调度
spof color inverse --known '#F5F0E8' --target 75 --missing 1  # 反向推导

# ── 其他 ──
spof weather [--city X]
spof data export / import
spof info | gateway up/down/status
spof update                                   # git pull 更新
```

## MCP Server 配置

MCP Server 通过 stdio 协议与 AI Agent 交互。在 MCP 客户端配置中添加：

```json
{
  "mcpServers": {
    "superoutfit": {
      "command": "python",
      "args": ["D:\\Application\\SuperOutfit\\server.py"],
      "env": {
        "SUPEROUTFIT_DATA": "D:\\Application\\SuperOutfit\\data"
      }
    }
  }
}
```

### AI Agent 工作流（MCP）

1. **添加衣物** — AI 生成 YAML → 调用 `add_item` 工具
2. **查询衣橱** — 调用 `list_items`，支持类型/季节/风格过滤
3. **穿搭推荐** — 先查天气 → 再调 `recommend_outfit`
4. **色彩评分** — 调用 `color_score`，传入 HEX 色值列表
5. **记录穿着** — 调用 `record_wear`，传入衣物 ID 列表
6. **反向推导** — 调用 `color_inverse`，传入已知色 + 目标分数

### AI Agent 与 YAML 工作流（v3.2 核心）

v3.2 的核心理念：**AI 写 YAML，spof 处理它**。

```
用户: "帮我添加一件白色 T 恤"
  ↓
AI 生成 item_new.yaml:
  id: item_023
  type: 上衣
  sub_type: 圆领短袖T恤
  colors:
    primary: 纯白色
    primary_hex: "#FFFFFF"
  ...
  ↓
调用: spof add --file item_new.yaml
  ↓
spof 验证 → 写入 data/items/item_023.yaml → 更新索引
```

- 不需要 `--type "上衣" --sub-type "T恤"` 这样的参数
- 所有字段都在 YAML 中，一目了然
- 心愿单：`spof add --file item.yaml --wishlist`

## 衣物数据格式（v3.2）

每件衣物是一个独立的 YAML 文件。v3.2 新增 `wear_dates` 和 `wash_frequency` 字段：

```yaml
id: item_001
type: 上衣
sub_type: 短袖衬衫
colors:
  primary: 米白色
  primary_hex: "#F5F0E8"
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
wear_count: 5
wear_dates:                          # v3.2: 精确穿着日期
  - "2026-05-01"
  - "2026-05-08"
  - "2026-05-15"
  - "2026-05-22"
  - "2026-05-29"
wash_frequency: 3                    # v3.2: 每穿几次洗一次
last_worn: "2026-05-29"
pair_with: [休闲西裤, 直筒牛仔裤]
restrict: [厚重高领内搭]
favorite: false
image: item_001.jpg
```

### 心愿单 YAML

心愿单与正式衣橱格式相同，存储在 `data/wishlist/`：

```yaml
id: wish_001
type: 下装
sub_type: 高腰阔腿裤
colors:
  primary: 黑色
  primary_hex: "#111111"
price: 399
link: "https://example.com/product/123"
note: "等打折再买"
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

### CLI 用法

```bash
# 色彩协调度评分
spof color score --colors '#F5F0E8,#111111'

# 反向推导：已知米白，目标 75 分，补全 1 个颜色
spof color inverse --known '#F5F0E8' --target 75 --missing 1
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

references/ 下的知识文件按决策点组织：

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
6400 全量 GP 训练约需 5 分钟。当前使用 Sparse GP（500 诱导点），训练 ~10 秒，精度损失 < 5%。

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

### 8. v3.2: YAML 是唯一数据入口
不要通过 CLI 参数传递衣物字段（`--type`, `--sub-type` 等）。始终通过 `--file` 传入 YAML 文件。这样数据结构可以自由演进，CLI 不需要同步更新参数。

### 9. v3.2: --wishlist 切换目标目录
`--wishlist` 标志将数据目录从 `data/items/` 切换到 `data/wishlist/`。两个目录结构相同，但互不干扰。

### 10. v3.2.1: Gateway 子进程输出必须重定向到文件
`gateway.py` 启动子进程时**不能使用 `stdout=subprocess.PIPE`**。Windows 管道缓冲区仅 ~4KB，父进程不读取时，uvicorn 的日志输出会写满缓冲区并阻塞整个事件循环，导致服务器瘫痪。已改为写入 `.logs/{name}.log` 文件。如需查看子进程输出，读取日志文件而非 PIPE。

### 11. v3.2.1: WebSocket handler 必须清理外部连接
`api/main.py` 的 `/ws/recommend` 端点在客户端断开时，必须关闭到 Ollama 的 `http.client.HTTPConnection`。否则连接和线程泄漏，多次刷新后耗尽资源。使用 `try/finally` 确保连接关闭。
