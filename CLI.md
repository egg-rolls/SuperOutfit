# SuperOutfit CLI 命令速查

## 安装

### 一键安装（推荐）

```bash
# Windows (PowerShell)
irm https://raw.githubusercontent.com/egg-rolls/SuperOutfit/master/scripts/install-simple.ps1 | iex

# macOS / Linux (Bash)
curl -fsSL https://raw.githubusercontent.com/egg-rolls/SuperOutfit/master/scripts/install.sh | bash
```

### 手动安装

```bash
git clone https://github.com/egg-rolls/SuperOutfit.git
cd SuperOutfit
uv venv
uv pip install -e .
superoutfit init --quick
```

## 使用方式

```bash
superoutfit <command> <subcommand> [options]
# 或
python -m superoutfit <command> <subcommand> [options]
```

---

## 命令列表

### Gateway (gateway / gw) — 服务管理

```bash
# 启动所有服务（API + 前端 + MCP）
superoutfit gateway

# 指定端口
superoutfit gateway --port 8000

# 不启动前端
superoutfit gateway --no-frontend

# 不启动 MCP
superoutfit gateway --no-mcp

# 开发模式（前端热重载）
superoutfit gateway --dev
```

### TUI (tui) — 交互模式

```bash
# 启动交互模式
superoutfit tui
```

### Init (init) — 首次使用引导

```bash
# 交互式引导
superoutfit init

# 快速初始化（使用默认值）
superoutfit init --quick
```

### 衣橱管理 (wardrobe / w)

```bash
# 添加衣物
superoutfit wardrobe add --type "上衣" --sub-type "T恤" --primary-color "黑色" --primary-hex "#000000"

# 查看衣橱
superoutfit wardrobe list
superoutfit wardrobe list --json
superoutfit wardrobe list --category "上衣"
superoutfit wardrobe list --style "通勤"

# 查看单件
superoutfit wardrobe show item_001

# 更新衣物
superoutfit wardrobe update item_001 --wear-count 5
superoutfit wardrobe update item_001 --favorite true

# 删除衣物（移到归档）
superoutfit wardrobe delete item_001
superoutfit wardrobe delete item_001 --force

# 统计信息
superoutfit wardrobe stats

# 记录穿着
superoutfit wardrobe record --items item_001,item_003 --occasion "通勤"

# 恢复归档衣物
superoutfit wardrobe restore item_001
```

### 天气查询 (weather / wt)

```bash
# 查询天气（从配置读取城市）
superoutfit weather

# 指定城市
superoutfit weather --city "大连"

# 指定坐标
superoutfit weather --lat 38.91 --lon 121.60

# 查看支持的城市
superoutfit weather --list-cities
```

### 穿搭推荐 (recommend / r)

```bash
# 今日推荐
superoutfit recommend today

# 指定城市
superoutfit recommend today --city "大连"
```

### 搭配评分 (score / s)

```bash
# 评分搭配
superoutfit score --items item_001,item_003,item_006 --occasion 通勤 --temp 22
```

### 色彩协调度 (color / c)

```bash
# 查看颜色详情
superoutfit color show "#F5F0E8"

# 查看常用颜色
superoutfit color show

# 按衣物 ID
superoutfit color --items item_001,item_003,item_006

# 按 HEX 色值
superoutfit color --colors "#F5F0E8,#C4A97D,#111111"
```

### 反向推导 (inverse / inv)

```bash
# 搜索法（快）
superoutfit inverse --known "#F5F0E8,#111111" --target 75 --missing 2 --method search

# 全局优化法（慢但可生成新颜色）
superoutfit inverse --known "#F5F0E8,#111111" --target 75 --missing 2 --method global

# 参数说明
# --known: 已知颜色（逗号分隔的 HEX）
# --target: 目标分数
# --missing: 需要补全的颜色数量
# --method: search（搜索色卡库）或 global（全局优化）
# --top: 搜索法返回前 N 个建议
# --samples: 全局法生成样本数量
# --maxiter: 全局法最大迭代次数
```

### 色卡管理 (palette / p)

```bash
# 列出色卡（按分数排序）
superoutfit palette list
superoutfit palette list --top 10
superoutfit palette list --source colorhunt
superoutfit palette list --min-score 80

# 训练色彩模型
superoutfit palette train

# 爬取新色卡
superoutfit palette scrape
```

### 知识库 (knowledge / k)

```bash
# 列出知识文档
superoutfit knowledge list

# 查看文档内容
superoutfit knowledge show color.md
superoutfit knowledge show color.md --raw  # 原始 Markdown

# 编辑文档
superoutfit knowledge edit color.md
```

### 配置查看 (config / cf)

```bash
# 查看用户配置
superoutfit config

# 衣橱统计
superoutfit config stats

# 衣橱统计（JSON 格式）
superoutfit config stats --json
```

### 版本信息

```bash
superoutfit --version
superoutfit -v
```

---

## 示例工作流

### 1. 首次设置

```bash
# 一键安装
curl -fsSL https://raw.githubusercontent.com/egg-rolls/SuperOutfit/main/scripts/install.sh | bash

# 首次使用引导
superoutfit init

# 或快速初始化
superoutfit init --quick
```

### 2. 启动服务

```bash
# 启动所有服务
superoutfit gateway

# 浏览器打开 http://localhost:8002
```

### 3. 添加衣物

```bash
# 添加一件白色 T 恤
superoutfit wardrobe add \
  --type "上衣" \
  --sub-type "圆领短袖T恤" \
  --primary-color "纯白色" \
  --primary-hex "#FFFFFF" \
  --material "纯棉" \
  --fit "标准" \
  --style "基础百搭,简约通勤,休闲" \
  --season "春,夏,初秋" \
  --temp-range "18~32" \
  --occasion "日常通勤,休闲约会"

# 查看衣橱
superoutfit wardrobe list
```

### 4. 评分搭配

```bash
# 查看搭配评分
superoutfit score --items item_001,item_004,item_006 --occasion 通勤

# 查看色彩协调度
superoutfit color --items item_001,item_004
```

### 5. 浏览色卡

```bash
# 查看高分色卡
superoutfit palette list --top 10 --min-score 80

# 从色卡获取灵感
superoutfit palette list --source colorhunt --top 5
```

### 6. 学习穿搭知识

```bash
# 查看有哪些知识文档
superoutfit knowledge list

# 学习色彩搭配
superoutfit knowledge show color.md

# 学习版型匹配
superoutfit knowledge show silhouette.md
```

### 7. 反向推导

```bash
# 已知米白+黑，目标 75 分，补全 2 个颜色
superoutfit inverse --known "#F5F0E8,#111111" --target 75 --missing 2
```

---

## 命令别名

| 全称 | 别名 |
|------|------|
| gateway | gw |
| wardrobe | w |
| weather | wt |
| recommend | r |
| score | s |
| color | c |
| inverse | inv |
| palette | p |
| knowledge | k |
| config | cf |

```bash
# 使用别名
superoutfit gw                   # 启动 Gateway
superoutfit w list               # 查看衣橱
superoutfit r today              # 今日推荐
superoutfit s --items item_001,item_003
superoutfit k list               # 查看知识库
superoutfit cf stats             # 衣橱统计
```

---

## 输出格式

### 衣橱列表

```
ID           类型     子类型        主色     品牌         风格                   穿着次数     收藏
------------------------------------------------------------------------------------------
item_001     上衣     短袖衬衫       米白色               简约,通勤,轻商务,休闲         0
item_002     上衣     长袖格纹衬衫     米白                美式休闲,复古,日常,叠穿        0
...
```

### 色卡列表

```
📊 共 5 组色卡

  1.     100.0分 | #fff5e4 #ffe3e1 #ffd1d1 #ff9494
     来源: colorhunt | 点赞: 41310
  2.      99.9分 | #f9f5f6 #f8e8ee #fdcedf #f2bed1
     来源: colorhunt | 点赞: 40717
...
```

### 知识库列表

```
📚 共 15 篇知识文档

  accessories.md       配饰指南
  buying.md            购买决策指南
  care.md              衣物养护指南
  color.md             色彩搭配规则
...
```

### 衣橱统计

```
==================================================
📊 衣橱统计
==================================================

📦 总计：9 件衣物

👔 按类型：
──────────────────────────────────────────────────
  上衣       ████ 4
  配饰       ████ 4
  下装       █ 1

🎨 按颜色：
──────────────────────────────────────────────────
  ██████ 米白     █████████ 9
  ██████ 黑色     █████████ 9
...

🌤️ 按季节：
──────────────────────────────────────────────────
  夏      ████ 4
  全季     ████ 4
  春      ███ 3
...
```

---

## 常见问题

### Q: 命令找不到？

```bash
# 方式 1：使用 python -m
python -m superoutfit --version

# 方式 2：检查安装
uv pip list | grep superoutfit

# 方式 3：重新安装
uv pip install -e .
```

### Q: 如何更新 CLI？

```bash
cd ~/.superoutfit  # 或安装目录
git pull
uv pip install -e .
```

### Q: 如何卸载？

```bash
# 删除安装目录
rm -rf ~/.superoutfit  # macOS/Linux
rm -rf %LOCALAPPDATA%\SuperOutfit  # Windows

# 或使用 pip
uv pip uninstall superoutfit
```

### Q: 数据在哪里？

```
data/
├── profile.yaml        # 用户画像
├── items/              # 衣物详情 YAML
├── images/             # 衣物图片
├── scored_palettes.json # 色卡数据
└── color_model_gp.pkl  # 色彩模型
```

所有数据都是 YAML 文件，可以直接在资源管理器中编辑。

### Q: Gateway 启动失败？

```bash
# 检查端口是否被占用
netstat -ano | findstr :8001  # Windows
lsof -i :8001                 # macOS/Linux

# 使用其他端口
superoutfit gateway --port 8000
```

### Q: 如何在后台运行 Gateway？

```bash
# macOS / Linux
nohup superoutfit gateway &

# Windows (PowerShell)
Start-Process -NoNewWindow superoutfit gateway
```
