---
name: superoutfit
description: "AI 智能穿搭顾问：衣物管理、穿搭推荐、衣橱分析。通过 MCP 工具调用，数据以 YAML 文件存储。"
version: 3.0.0
author: Lirui
license: MIT
metadata:
  hermes:
    tags: [outfit, wardrobe, fashion, recommendation, clothing]
    related_skills: []
---

# SuperOutfit 智能穿搭顾问

AI 驱动的个人衣橱管理与穿搭推荐系统。

**应用目录：** `D:\Application\SuperOutfit`（MCP Server + 数据 + 脚本）
**本目录：** 纯指令和知识文档（不含代码和数据）

## When to Use

- 用户提到"穿搭"、"搭配"、"衣橱"、"今天穿什么"
- 用户想添加/查看/编辑衣物
- 用户问色彩搭配、风格选择、场合着装
- 用户上传衣物图片并希望识别属性

## MCP 工具

SuperOutfit 通过 MCP Server 暴露以下工具（需先启动 server）：

| 工具 | 说明 |
|------|------|
| `wardrobe_list` | 列出衣橱（支持按类型/风格/季节筛选） |
| `wardrobe_add` | 添加衣物 |
| `wardrobe_show` | 查看单件详情 |
| `wardrobe_update` | 更新衣物属性 |
| `wardrobe_delete` | 删除衣物（移到归档） |
| `wardrobe_stats` | 衣橱统计概览 |
| `wardrobe_record` | 记录今天穿搭 |
| `weather_query` | 查询天气（Open-Meteo 免费 API） |
| `color_score` | 色彩协调度评分（GP 模型，SSS~D 等级） |
| `outfit_score` | 搭配综合评分（6 维度） |
| `profile_get` | 获取用户画像 |
| `ui_build` | 生成可视化 HTML 仪表盘 |

### 启动 MCP Server

```bash
# 直接启动（stdio 模式）
python D:\Application\SuperOutfit\server.py
```

### MCP 配置（.mcp.json）

```json
{
  "mcpServers": {
    "superoutfit": {
      "command": "python",
      "args": ["D:\\Application\\SuperOutfit\\server.py"]
    }
  }
}
```

### 非 MCP 模式（CLI 命令）

如果 MCP 不可用，可使用统一的 CLI 命令：

```bash
# 衣橱管理
superoutfit wardrobe list --json
superoutfit wardrobe add --type "上衣" --sub-type "T恤" --primary-color "黑色"
superoutfit wardrobe show item_001
superoutfit wardrobe stats

# 天气查询
superoutfit weather --city "大连"

# 搭配评分
superoutfit score --items item_001,item_003 --occasion 通勤 --temp 22

# 色彩协调度
superoutfit color --items item_001,item_003
superoutfit color --colors "#F5F0E8,#C4A97D,#111111"

# 色卡管理
superoutfit palette list --top 10
superoutfit palette train

# 知识库
superoutfit knowledge list
superoutfit knowledge show color.md

# 配置
superoutfit config
```

> 完整命令参考见 `D:\Application\SuperOutfit\CLI.md`

## 核心工作流

### 1. 添加衣物

当用户上传衣物图片时：

1. 保存图片到 `D:\Application\SuperOutfit\data\images\item_NNN.jpg`
2. 用 AI 视觉能力分析图片：颜色、材质、款式、类型、季节
3. 调用 `wardrobe_add` 工具添加衣物
4. 如果有图片，填写 `primary_hex` 色值

### 2. 穿搭推荐

当用户问"今天穿什么"时：

1. 调用 `weather_query` 获取天气
2. 调用 `profile_get` 获取用户画像
3. 调用 `wardrobe_list` 获取衣橱
4. AI 推荐 3 套搭配（不穷举，直接从衣橱挑选）
5. 调用 `outfit_score` 校验推荐结果
6. 调用 `wardrobe_record` 记录穿搭（用户确认后）

### 3. 色彩评分

色彩评分基于 5462 组真实色卡训练的高斯过程模型：

```
SSS ≥ 85   顶级     名画级配色（前 ~8%）
SS  ≥ 75   优秀     专业搭配师水准
S   ≥ 65   出色     有明确审美风格
A   ≥ 50   良好     和谐不出错
B   ≥ 35   一般     中规中矩
C   ≥ 20   偏弱     需要调整
D   < 20   差       明显不搭
```

## 穿搭领域知识

知识文档存放在 `references/` 目录，按需读取：

| 文件 | 内容 | 何时读取 |
|------|------|----------|
| `color.md` | 色彩搭配规则、万能色 | 颜色搭配问题 |
| `color_theory.md` | 色彩理论数学（底色/色环） | 深入色彩原理 |
| `color_pipeline.md` | 色彩模型技术文档 | 维护/扩展评分系统 |
| `silhouette.md` | 版型与身材匹配 | 什么版型适合 |
| `wardrobe.md` | 衣橱结构、日常穿搭流程 | 怎么搭配 |
| `layering.md` | 叠穿三角区理论、3 个公式 | 叠穿/秋冬穿搭 |
| `occasion.md` | 5 大场合穿搭指南 | 某场合穿什么 |
| `style_archetypes.md` | 7 种风格体系 | 什么风格适合 |
| `accessories.md` | 配饰指南 | 配饰搭配 |
| `shoes.md` | 鞋子指南 | 鞋子搭配 |
| `buying.md` | 购买决策、淘宝搜索 | 该买什么 |
| `mistakes.md` | 常见穿搭雷区 | 搭配对不对 |
| `care.md` | 衣物养护 | 怎么洗/保养 |

**读取策略：** 只加载与用户问题相关的文件，不全部加载。

## 安装

```bash
# 安装 skill 到 Hermes
python D:\Application\SuperOutfit\scripts\install_skill.py

# Pin 防止被 curator 归档
hermes curator pin superoutfit
```

## Common Pitfalls

1. **MCP Server 未启动。** 工具调用会失败，需先 `python server.py`。
2. **衣物 ID 必须唯一。** 添加前先 `wardrobe_list` 检查。
3. **图片文件名要对应。** `item_001.yaml` 的 image 应该是 `item_001.jpg`。
4. **HEX 色值影响评分。** 添加衣物时尽量填写 `primary_hex`。
5. **推荐不要穷举组合。** 直接让 AI 从衣橱中挑选。
6. **profile.yaml 是推荐质量基石。** 首次使用务必引导用户填写。
