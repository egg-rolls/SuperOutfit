# SuperOutfit CLI v3.2 命令速查

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
spof system info
```

## 使用方式

```bash
spof <command> [subcommand] [options]
```

> v3.2 将命令前缀从 `superoutfit` 简化为 `spof`。

---

## 衣橱管理

### `spof add` — 添加衣物

```bash
spof add --file item.yaml                  # 添加到正式衣橱
spof add --file item.yaml --wishlist       # 添加到心愿单
```

- `--file`：YAML 文件路径（必填）
- `--wishlist`：目标切换为 `data/wishlist/`

AI 工作流：AI 生成 YAML 文件 → `spof add --file` 写入。

### `spof list` — 查看衣物列表

```bash
spof list                                  # 全部衣物
spof list --type 上衣                      # 按类型过滤
spof list --season 夏                      # 按季节过滤
spof list --wishlist                       # 查看心愿单
spof list --type 上衣 --season 夏 --json   # 组合过滤 + JSON 输出
```

| 参数 | 说明 |
|------|------|
| `--type X` | 按类型过滤（上衣/下装/鞋/配饰…） |
| `--season X` | 按季节过滤（春/夏/秋/冬/全季） |
| `--wishlist` | 查看心愿单而非正式衣橱 |
| `--json` | JSON 格式输出 |

### `spof show` — 查看衣物详情

```bash
spof show item_001                         # 详细信息
spof show item_001 --json                  # JSON 格式
spof show wish_001 --json                  # 心愿单物品
```

| 参数 | 说明 |
|------|------|
| `<item_id>` | 衣物 ID（必填） |
| `--json` | JSON 格式输出 |

### `spof edit` — 编辑衣物

```bash
spof edit item_001 --file updated.yaml     # 整文件覆盖
```

- `<item_id>`：要编辑的衣物 ID（必填）
- `--file`：新的 YAML 文件路径（必填，整文件覆盖）

> 注意：edit 是整文件覆盖，不是字段级更新。AI 先 `spof show item_001 --json` 获取当前数据，修改后写回新 YAML。

### `spof delete` — 删除衣物

```bash
spof delete item_001                       # 从正式衣橱删除
spof delete wish_001 --wishlist            # 从心愿单删除
```

| 参数 | 说明 |
|------|------|
| `<item_id>` | 衣物 ID（必填） |
| `--wishlist` | 从心愿单而非正式衣橱删除 |

---

## 穿着追踪

### `spof wear add` — 记录穿着

```bash
spof wear add --items item_001,item_002    # 记录今天穿着这些衣物
```

- `--items`：逗号分隔的衣物 ID 列表（必填）
- 自动在对应 YAML 中追加 `wear_dates` 条目，更新 `wear_count`

### `spof wear wash` — 标记已洗

```bash
spof wear wash --items item_001            # 标记已洗涤
spof wear wash --items item_001,item_003   # 批量标记
```

- `--items`：逗号分隔的衣物 ID 列表（必填）

### `spof wear check` — 需要洗涤的衣物

```bash
spof wear check                            # 全部类型
spof wear check --type 上衣                # 按类型过滤
```

| 参数 | 说明 |
|------|------|
| `--type X` | 按类型过滤 |

根据 `wash_frequency` 和 `wear_dates` 计算哪些衣物该洗了。

### `spof wear report` — 穿着报告

```bash
spof wear report                           # 全部衣物报告
spof wear report --items item_001,item_002 # 指定衣物
spof wear report --json                    # JSON 格式
```

| 参数 | 说明 |
|------|------|
| `--items X` | 逗号分隔的衣物 ID（可选，默认全部） |
| `--json` | JSON 格式输出 |

输出包含：穿着次数、单次穿着成本（cost-per-wear）、最近穿着日期等。

---

## 色彩分析

### `spof color score` — 色彩协调度评分

```bash
spof color score --colors '#F5F0E8,#111111'           # 2 色评分
spof color score --colors '#F5F0E8,#C4A97D,#111111'   # 3 色评分
```

- `--colors`：逗号分隔的 HEX 色值（必填）
- 输出 0-100 分数 + 7 级评级（SSS/SS/S/A/B/C/D）

### `spof color inverse` — 反向推导

```bash
spof color inverse --known '#F5F0E8' --target 75 --missing 1
spof color inverse --known '#F5F0E8,#111111' --target 80 --missing 2
```

| 参数 | 说明 |
|------|------|
| `--known X` | 已知颜色，逗号分隔的 HEX 色值（必填） |
| `--target N` | 目标协调度分数（必填） |
| `--missing N` | 需要补全的颜色数量（必填） |

根据已知颜色和目标分数，推导缺失颜色的最佳搭配。

---

## 天气查询

### `spof weather` — 查询天气

```bash
spof weather                               # 从配置读取城市
spof weather --city 大连                   # 指定城市
```

| 参数 | 说明 |
|------|------|
| `--city X` | 城市名称（可选，默认从配置读取） |

---

## 数据管理

### `spof data export` — 导出数据

```bash
spof data export                           # 导出全部数据
```

### `spof data import` — 导入数据

```bash
spof data import                           # 导入数据
```

---

## 系统管理

### `spof system info` — 系统信息

```bash
spof system info                           # 显示版本、数据路径、衣物数量等
```

### `spof system gateway` — 服务管理

```bash
spof system gateway up                     # 启动所有服务
spof system gateway down                   # 停止所有服务
spof system gateway status                 # 查看服务状态
```

### `spof update` — 更新应用

```bash
spof update                                # git pull 拉取最新代码
```

---

## 全局参数

| 参数 | 说明 |
|------|------|
| `--json` | JSON 格式输出（适用于 list/show/report） |
| `--wishlist` | 切换目标到心愿单（适用于 add/list/delete） |

---

## 命令总览

| 命令 | 说明 | 示例 |
|------|------|------|
| `spof add` | 添加衣物 | `spof add --file item.yaml` |
| `spof list` | 列出衣物 | `spof list --type 上衣` |
| `spof show` | 查看详情 | `spof show item_001` |
| `spof edit` | 编辑衣物 | `spof edit item_001 --file new.yaml` |
| `spof delete` | 删除衣物 | `spof delete item_001` |
| `spof wear add` | 记录穿着 | `spof wear add --items item_001` |
| `spof wear wash` | 标记已洗 | `spof wear wash --items item_001` |
| `spof wear check` | 需洗涤衣物 | `spof wear check --type 上衣` |
| `spof wear report` | 穿着报告 | `spof wear report --json` |
| `spof color score` | 色彩评分 | `spof color score --colors '#FFF,#000'` |
| `spof color inverse` | 反向推导 | `spof color inverse --known '#FFF' --target 75 --missing 1` |
| `spof weather` | 天气查询 | `spof weather --city 大连` |
| `spof data export` | 导出数据 | `spof data export` |
| `spof data import` | 导入数据 | `spof data import` |
| `spof system info` | 系统信息 | `spof system info` |
| `spof system gateway` | 服务管理 | `spof system gateway up` |
| `spof update` | 更新应用 | `spof update` |

---

## 示例工作流

### 1. 首次使用

```bash
# 一键安装
curl -fsSL https://raw.githubusercontent.com/egg-rolls/SuperOutfit/main/scripts/install.sh | bash

# 查看系统信息
spof system info

# 启动服务
spof system gateway up
# 浏览器打开 http://localhost:32201
```

### 2. 添加衣物

```bash
# AI 生成 YAML，然后添加
spof add --file item_023.yaml

# 添加到心愿单
spof add --file wish_001.yaml --wishlist

# 查看衣橱
spof list
spof list --type 上衣 --season 夏
```

### 3. 穿着追踪

```bash
# 今天穿了这两件
spof wear add --items item_001,item_003

# 衣服该洗了
spof wear wash --items item_001

# 查看哪些该洗了
spof wear check

# 穿着报告
spof wear report --items item_001
```

### 4. 色彩分析

```bash
# 评估两色搭配
spof color score --colors '#F5F0E8,#111111'

# 已知一件米白，找最佳搭配色
spof color inverse --known '#F5F0E8' --target 75 --missing 1
```

### 5. 天气 + 推荐

```bash
# 查看天气
spof weather --city 大连

# 启动服务后通过前端或 AI 获取穿搭推荐
spof system gateway up
```

---

## 数据结构

```
data/
├── profile.yaml          # 用户画像
├── wardrobe_index.yaml   # 衣物索引（自动生成）
├── preferences.yaml      # AI 学习偏好
├── items/                # 正式衣橱（YAML 文件）
│   ├── item_001.yaml
│   ├── item_002.yaml
│   └── ...
├── wishlist/             # 心愿单（YAML 文件）
│   ├── wish_001.yaml
│   └── ...
├── images/               # 衣物图片
├── archive/              # 已淘汰衣物
└── *.pkl / *.json        # 色彩模型 + 色卡数据
```

所有数据都是 YAML 文件，可以直接在资源管理器中编辑。

---

## 常见问题

### Q: 命令找不到？

```bash
# 检查安装
uv pip list | grep superoutfit

# 重新安装
uv pip install -e .
```

### Q: 如何更新 CLI？

```bash
spof update
# 或手动：
git pull && uv pip install -e .
```

### Q: 数据在哪里？

衣物数据在 `data/items/`，心愿单在 `data/wishlist/`，均为 YAML 文件。

### Q: Gateway 启动失败？

```bash
# 检查端口占用
netstat -ano | findstr :32200  # Windows
lsof -i :32200                 # macOS/Linux

# 查看状态
spof system gateway status
```

### Q: --wishlist 和默认有什么区别？

`--wishlist` 将操作目标从 `data/items/`（正式衣橱）切换到 `data/wishlist/`（心愿单）。两个目录结构相同，互不干扰。
