# SuperOutfit 更新日志

## v3.2.0 — 2026-06-05

### 核心变更：AI 驱动架构重构

从 20 个命令精简为 **6 个 AI 命令**，移除所有硬编码算法，采用"工具做 CRUD，AI 做决策"的设计原则。

### 新增

- **`spof wear`** — 穿着管理系统
  - `wear add --items item_001,item_002` — 记录穿着（支持批量）
  - `wear wash --items item_001` — 手动标记清洗（脏污等）
  - `wear check [--type X]` — 查看需要清洗的衣物
  - `wear report [--items X]` — 穿着报表 + 性价比排行
- **`--wishlist` 标志** — 同一套 CRUD 命令管理购物清单
  - `spof add --file item.yaml --wishlist` — 添加到购物清单
  - `spof list --wishlist` — 查看购物清单
  - 购物清单存储在 `data/wishlist/`，与衣柜共享 YAML 格式
- **Item YAML 新字段**
  - `wash_frequency` — 建议穿几次后清洗（如白T恤=1，牛仔裤=5）
  - `wash_count` — 上次清洗时的穿着次数
  - `last_washed` — 上次清洗日期
  - `wear_dates[]` — 每次穿着日期记录
- **`scripts/wear.py`** — 穿着管理核心模块
- **`scripts/data_manager.py`** — 数据导入导出模块
- **`data/wishlist/`** — 购物清单目录

### 变更

- **`spof` 替代 `superoutfit`** — 所有 CLI 命令前缀改为 `spof`
- **CRUD 命令简化**
  - `wardrobe add --type X --sub-type Y ...` → `spof add --file item.yaml`
  - `wardrobe update item_001 --wear-count 5` → `spof edit item_001 --file new.yaml`
  - AI 写好 YAML 文件，丢给 spof 处理，不用记一堆 `--field` 参数
- **`wardrobe_ops.py` 重写** — 支持 `--wishlist` 切换目标目录
- **`superoutfit.py` 重写** — 6 个命令 + 基础设施（gateway/tui/init/update）
- **色彩工具合并** — `color score` + `color inverse` 合入 `spof color`
- **系统管理合并** — `config` + `gateway` + `skill` + `knowledge` 合入 `spof system`
- **搜索改用 `search_files`** — 不再自建搜索命令，用 Hermes 内置 ripgrep

### 移除

- **`scripts/season.py`** — 季节标签直接通过 `spof edit` 修改 YAML
- **`scripts/search.py`** — 改用 `search_files` 模糊查找
- **`scripts/stats.py`** — 统计功能合入 `wear report`
- **`scripts/wishlist.py`** — 购物清单合入 `spof --wishlist`
- **移除的命令**：`wardrobe`、`recommend`、`score`、`inverse`（独立）、`palette`、`knowledge`、`config`、`season`、`wishlist`、`search`、`stats`
- **移除的硬编码算法**
  - 换季温度阈值（`DALIAN_SEASON_TEMP`）
  - 月份-季节映射（`DALIAN_SEASON_MONTHS`）
  - 基础衣橱模板（`ESSENTIAL_WARDROBE`）
  - 缺口分析算法
  - 推荐率计算模板

### 文档更新

- `README.md` — CLI 示例、穿着追踪/购物清单新章节
- `AGENTS.md` — 命令参考、设计原则、AI 工作流
- `CLI.md` — 完全重写，17 个命令/子命令完整文档
- `SKILL.md` — v3.2 命令参考 + --wishlist 说明
- `docs/INSTALL.md` — 快速开始示例

### 统计

```
12 files changed, +1569, -1921 (净减 352 行)
删除 4 个脚本，新增 2 个脚本，重写 2 个脚本
```

---

## v3.1.0 及更早

<details>
<summary>历史版本</summary>

### v3.1.0
- Rich 终端 UI（banner、面板）
- 数据导入导出 (`spof data export/import`)
- Gateway 统一服务管理

### v3.0.0
- 三入口架构：MCP Server + FastAPI 后端 + Vue 前端
- 色彩评分模型（5462 组色卡，Sparse GP）
- 穿搭知识库（12 篇领域知识）
- 主题系统（4 基础色派生 20+ CSS 变量）

</details>
