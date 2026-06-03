# 独立应用转 Hermes Skill 的架构模式

## 背景

SuperOutfit 最初设计为独立应用（FastAPI 后端 + Vue 前端 + egg-harness AI 运行时）。
分析后发现核心能力（语言理解 + 图片理解）Hermes 原生支持，不需要自建基础设施。
因此将整个架构压缩为一个 Hermes Skill。

## 核心决策：数据放在 Skill 内部 + Pin

### 问题
Skill 目录存放代码和指令，但 SuperOutfit 需要持久化用户数据（衣物 YAML、图片）。
数据放在独立目录（如 `D:\Application\SuperOutfit`）会让用户管理两个地方。

### 解决方案
把数据放在 skill 的 `data/` 子目录，然后 pin 住 skill 防止 curator 归档。

```
~/.hermes/skills/productivity/superoutfit/
├── SKILL.md              # 指令
├── scripts/              # 工具脚本
├── templates/            # 模板
└── data/                 # 用户数据（与 skill 绑定）
```

### 关键命令
```bash
hermes curator pin superoutfit
```

### 为什么不放在独立目录
- 一个目录 = 一份心智负担
- 备份 = 复制整个文件夹
- 用户可以在资源管理器里直接操作数据和代码

### 风险
- 如果忘记 pin，curator 归档 skill 时数据一起消失
- Skill 更新时要小心不覆盖 `data/` 目录

## 脚本路径自动解析

脚本使用相对于自身位置的路径解析，不硬编码绝对路径：

```python
DATA_DIR = Path(os.environ.get("SUPEROUTFIT_DATA", Path(__file__).resolve().parent.parent / "data"))
```

这样 skill 移动到任何位置都能工作。`SUPEROUTFIT_DATA` 环境变量可覆盖。

## 原始架构 vs Skill 架构

| 原始设计 | Skill 替代 | 说明 |
|----------|-----------|------|
| FastAPI 后端 | 不需要 | Hermes 本身就是后端 |
| Vue 前端 | 不需要 | CLI 对话足够 |
| EggHarnessAdapter | 不需要 | Hermes 就是 harness |
| DirectLLMAdapter | 不需要 | Hermes 已有 provider 降级 |
| WebSocket 流式 | 不需要 | Hermes 已有流式支持 |
| 工厂模式 | 不需要 | 一个 skill 搞定 |
| YAML Schema | 保留 | 数据结构设计直接用 |
| 评分算法 | skill 脚本 | scorer.py 做 LLM 推荐的校验 |

## 适用场景

这个模式适合：
- 领域特定的个人工具（衣橱、笔记、习惯追踪等）
- 数据结构化且用户需要直接浏览/编辑
- 核心能力是 LLM 推理，不需要复杂后端

不适合：
- 需要多用户协作
- 需要实时 Web UI（但可以用 build_ui.py 生成静态 HTML）
- 数据量极大（>10000 条记录考虑 SQLite）

## 可视化层：静态 HTML 生成

独立应用方案是 Vue 前端 + FastAPI 后端。Skill 方案用 `build_ui.py` 替代：

1. 读取 `data/` 下所有 YAML + 图片
2. 图片转 base64 嵌入
3. 数据转 JSON 注入 HTML
4. 输出单个自包含 HTML 文件（~1.8 MB for 9 items with images）
5. 浏览器直接打开，无需服务器

**关键实现细节：** Python 生成含 JavaScript 的 HTML 时，不能用 f-string（JS 的 `{}` 与 f-string 花括号转义冲突）。用 `TEMPLATE.replace("__PLACEHOLDER__", json_data)` 模式。

## 分享机制

```
export.py → 打包 SKILL.md + scripts + templates（不含 data/）→ zip (~22KB)
setup.py → 接收者运行后初始化空 data/ 目录
README.md → 通用文档，非 Hermes 用户也能用
```

接收者只需：解压 → `python setup.py` → 填写 profile.yaml → 开始使用。
