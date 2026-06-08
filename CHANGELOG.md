# SuperOutfit 更新日志

## v3.3.0 — 2026-06-07

### 新增：可配置数据目录 + CLI 美化 + 性能优化

**数据目录配置：**
- `spof data dir [path]` — 查看/设置数据目录
- 配置存储在 `~/.superoutfit/config.json`
- 所有脚本统一使用 `paths.get_data_dir()` 解析路径
- 优先级：配置文件 > 环境变量 > 默认路径

**CLI 输出美化（Rich）：**
- 新增 `scripts/output.py` — Claude 暖色调输出工具库
- `spof info` — Panel + Table 展示系统信息
- `spof list` — Rich Table 带彩色圆点
- `spof show` — Panel 详情卡片
- `spof wear check` — Table + urgency 颜色标记
- `spof wear report` — Panel + Table + 条形图
- `spof weather` — Panel 天气卡片
- `spof color score` — Panel + 色条 + 等级徽章
- `spof scorer` — Panel + 维度评分表
- `spof gateway` — Rich 状态表格

**前端架构升级：**
- 迁移到 Pinia 状态管理（5 个 store）
- 移除 naive-ui、@vicons/ionicons5、vue-router（减 ~3MB）
- v-show → v-if 视图按需挂载
- 图片懒加载（loading="lazy"）
- API 层添加 GET 请求缓存（30s TTL）+ 请求去重
- 移除 WebSocket/Ollama 聊天功能（本应用是 AI 工具，不内置 AI 调用）
- 移除 backdrop-filter: blur（性能优化）
- CSS transition: all → 具体属性 + contain: content

**后端性能优化：**
- GP/线性模型缓存（模块级变量，加载一次复用）
- 衣橱数据 mtime 缓存（目录未变直接返回）
- 天气 API 30 分钟 TTL 缓存
- 参考文档列表返回 excerpt 预览（前 200 字符）
- wear_count 从 wear_dates 派生（数据一致性）
- 路径穿越防护（reference 端点）

**后端可靠性：**
- bare except: pass → 具体异常 + stderr 警告
- api_update 不再修改调用方 dict
- palettes_list 文件缺失时返回空列表
- resolve_items 单次 load_item 调用
- spof update 自动安装依赖 + pull 失败自动 reset

**文档更新：**
- 新增 MCP_SETUP.md — AI 自动配置 MCP 连接指南
- SKILL.md 添加完整 Item YAML 规范 + 视觉分析指南
- AGENTS.md 更新命令参考、数据目录配置、设计决策

## v3.2.1 — 2026-06-07

### 修复：Gateway 刷新瘫痪问题

多次刷新前端导致 Gateway 服务器完全卡死，无法响应任何请求。

**根因分析：**
1. `gateway.py` 启动 uvicorn 子进程时使用 `stdout=subprocess.PIPE`，但父进程从不读取管道。Windows 管道缓冲区仅 ~4KB，前端每次刷新触发 5-6 个并发请求的日志输出，缓冲区写满后 uvicorn 的写入阻塞，整个异步事件循环冻结。
2. `/ws/recommend` WebSocket handler 在客户端断开时未关闭到 Ollama 的 HTTP 连接，导致连接和线程泄漏。
3. Vite 代理端口硬编码为 32201，但 API 默认端口为 32200，dev 模式下代理指向错误端口。

**修复内容：**
- **`gateway.py`** — 子进程输出重定向到 `.logs/{name}.log` 文件，彻底消除 PIPE 缓冲区死锁；前端端口从 API 端口+1 开始分配，确保端口分配顺序正确；修复 Windows 控制台 GBK 编码导致的 Unicode 报错
- **`api/main.py`** — WebSocket handler 添加 `try/finally` 确保 Ollama 连接在客户端断开时被关闭
- **`frontend/vite.config.js`** — 代理目标从 `32201` 改为 `32200`（API 默认端口）
- **`.gitignore`** — 添加 `.logs/` 目录

**测试结果：**
- 6 个端点并发请求：6/6 成功
- 3 轮 x 6 并发请求（模拟多次 F5）：18/18 成功
- Gateway 正常启停，无残留进程

### 版本号统一

修复各文件版本号不一致的问题：
- `pyproject.toml`: 3.1.0 → 3.2.1
- `api/main.py`: 3.0.0 → 3.2.1
- `README.md`: 3.2.0 → 3.2.1

---

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
- **系统管理合并** — `config` + `gateway` + `skill` + `knowledge` 合入 `spof info` 和 `spof gateway`
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
