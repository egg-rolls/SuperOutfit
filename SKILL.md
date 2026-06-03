---
name: superoutfit
description: "AI 智能穿搭顾问：衣物管理、穿搭推荐、衣橱分析。数据以 YAML 文件存储，用户可直接浏览和编辑。"
version: 2.0.0
author: Lirui
license: MIT
metadata:
  hermes:
    tags: [outfit, wardrobe, fashion, recommendation, clothing]
    related_skills: []
---

# SuperOutfit 智能穿搭顾问

AI 驱动的个人衣橱管理与穿搭推荐系统。所有数据以 YAML 文件 + 图片文件夹存储，用户可直接在资源管理器浏览编辑。

**兼容所有 AI Agent：** Hermes / Claude Code / OpenCode / Cursor / 任何能读文件和执行命令的 AI。

## When to Use

- 用户提到"穿搭"、"搭配"、"衣橱"、"今天穿什么"、"推荐穿"
- 用户想添加/查看/编辑衣物
- 用户想分析衣橱缺口或穿搭历史
- 用户上传衣物图片并希望识别属性
- 用户问色彩搭配、风格选择、场合着装

## 数据目录结构

```
data/                               # 与 skill 同级的 data/ 目录
├── profile.yaml                    # 用户画像（身材、风格偏好、预算）
├── wardrobe_index.yaml             # 衣物索引（自动生成）
├── history.yaml                    # 穿搭历史记录
├── preferences.yaml                # AI 学习到的偏好
├── items/                          # 衣物详情，每件一个 YAML
│   ├── item_001.yaml
│   └── ...
├── outfits/                        # 搭配方案
│   ├── outfit_001.yaml
│   └── ...
├── images/                         # 衣物图片（用户直接拖拽放入）
├── outfit_images/                  # 搭配效果图
└── archive/                        # 已淘汰衣物归档
```

**关键设计：** 用户可以直接在文件夹里操作——拖拽图片、编辑 YAML、删除文件。

## 工具脚本

所有脚本位于 `scripts/` 目录，纯 Python + PyYAML，无外部依赖（天气除外需网络）。

### wardrobe_ops.py — 衣物 CRUD

```bash
# 添加衣物
python scripts/wardrobe_ops.py add --type "上衣" --sub-type "短袖衬衫" --primary-color "米白色" --material "冰丝缎面" --style "简约,通勤" --season "春,夏" --temp-range "18~32"

# 列出所有衣物
python scripts/wardrobe_ops.py list

# JSON 输出（供 AI 解析）
python scripts/wardrobe_ops.py list --json

# 按类型/风格/季节筛选
python scripts/wardrobe_ops.py list --category "上衣"
python scripts/wardrobe_ops.py list --style "通勤"

# 查看单件详情
python scripts/wardrobe_ops.py show item_001

# 更新属性
python scripts/wardrobe_ops.py update item_001 --wear-count 5 --last-worn 2026-06-02

# 删除（移到归档，不丢失）
python scripts/wardrobe_ops.py delete item_001

# 从归档恢复
python scripts/wardrobe_ops.py restore item_001

# 统计概览
python scripts/wardrobe_ops.py stats

# 重建索引
python scripts/wardrobe_ops.py reindex

# 记录今天穿搭
python scripts/wardrobe_ops.py record --items item_001,item_003 --occasion "通勤"
```

### weather.py — 天气查询

```bash
# 查询天气（JSON 输出）
python scripts/weather.py --city "大连"

# 查询指定日期（未来 7 天）
python scripts/weather.py --city "北京" --date "2026-06-05"

# 列出支持的城市
python scripts/weather.py --list-cities
```

### scorer.py — 搭配评分

```bash
# 评分一套搭配
python scripts/scorer.py --items item_001,item_003,item_006 --occasion "通勤" --temp 22
```

输出 JSON，包含 6 个维度分数（颜色/风格/场合/天气/新鲜度/偏好）和综合评分。

色彩等级（基于人类审美分布）：SSS(≥85) / SS(≥75) / S(≥65) / A(≥50) / B(≥35) / C(≥20) / D(<20)

### color_math.py — 色彩协调度计算

```bash
# 通过衣物 ID 评分
python scripts/color_math.py --items item_001,item_003,item_006

# 直接传 HEX 色值
python scripts/color_math.py --colors "#F5F0E8,#C4A97D,#111111"

# 详细分析（含底色、逐对分析）
python scripts/color_math.py --items item_001,item_003 --detail
```

基于 6400 组真实色卡训练的高斯过程模型，MAE 2.66。

## 核心工作流

### 1. 添加衣物（图片识别模式）

当用户上传衣物图片时：

1. 将图片保存到 `data/images/item_NNN.jpg`
2. 用 AI 视觉能力分析图片，提取：颜色、材质、款式、类型、季节
3. 运行 `python scripts/wardrobe_ops.py add --type ... --primary-color ...`
4. 更新 HEX 色值：编辑 `data/items/item_NNN.yaml`，在 `colors.primary_hex` 填入 HEX 值
5. 运行 `python scripts/wardrobe_ops.py reindex`

### 2. 穿搭推荐

当用户问"今天穿什么"或请求推荐时：

1. 获取天气：`python scripts/weather.py --city 大连`
2. 加载用户画像：读取 `data/profile.yaml`
3. 加载衣橱：`python scripts/wardrobe_ops.py list --json`
4. 构建推荐 prompt：注入衣橱数据 + 天气 + 用户画像 + 场合
5. AI 推荐 3 套方案（不穷举组合，直接从衣橱中挑选）
6. 评分校验：`python scripts/scorer.py --items item_001,item_003,item_006 --temp 22`
7. 保存推荐到 `data/outfits/outfit_NNN.yaml`

**推荐 prompt 结构：**
```
你是穿搭顾问。以下是用户衣橱：
{wardrobe_json}

用户画像：
{profile_yaml}

今日天气：{weather_json}
场合：{occasion}

请推荐 3 套搭配，每套包含：衣物 ID、名称、颜色、搭配理由。
优先选择穿着次数少的衣物，避免搭配禁忌。
```

### 3. 衣橱分析

当用户问"我缺什么"或"该买什么"时：

1. `python scripts/wardrobe_ops.py stats`
2. 读取 `data/profile.yaml` 获取风格偏好
3. 结合 `references/buying.md` 中的购买策略给出建议

### 4. 记录穿搭

当用户说"今天穿了 XXX"时：

1. 识别涉及的衣物 ID
2. `python scripts/wardrobe_ops.py record --items item_001,item_003 --occasion "通勤"`

## 穿搭领域知识

领域知识存放在 `references/` 目录下，按需读取（不全部加载以节省 token）：

| 文件 | 内容 | 何时读取 |
|------|------|----------|
| `color.md` | 色彩搭配规则、万能色、肤色匹配 | 用户问颜色搭配 |
| `color_theory.md` | 色彩理论数学、底色理论、色环关系 | 深入理解色彩原理 |
| `color_pipeline.md` | 色彩模型数据管道：爬取→训练→预测 | 维护/扩展色彩评分系统 |
| `silhouette.md` | 版型与身材匹配、帽子与脸型 | 用户问什么版型适合 |
| `wardrobe.md` | 衣橱结构、日常穿搭流程、上下线穿搭 | 用户问怎么搭配 |
| `layering.md` | 叠穿三角区理论、3 个公式、配色规则 | 用户问叠穿/秋冬穿搭 |
| `occasion.md` | 5 大场合穿搭指南（面试/通勤/相亲/婚礼/商务） | 用户问某场合穿什么 |
| `style_archetypes.md` | 7 种风格体系、适合身材、搜索关键词 | 用户问什么风格适合 |
| `accessories.md` | 项链/戒指/手链/腰带/丝巾指南 | 用户问配饰搭配 |
| `shoes.md` | 鞋子类型、颜色配置、买鞋原则 | 用户问鞋子搭配 |
| `buying.md` | 购买决策、价格策略、淘宝搜索技巧 | 用户问该买什么 |
| `mistakes.md` | 常见穿搭雷区 | 用户问搭配对不对 |
| `care.md` | 衣物洗护、去污、存放 | 用户问怎么洗/保养 |
| `SOURCES.md` | 知识来源记录 | 回溯知识出处 |

**读取策略：** 只加载与用户问题相关的文件，不全部加载。

## YAML Schema 速查

### 衣物 (items/item_NNN.yaml)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 唯一标识，如 `item_001` |
| type | string | 上衣/裤子/外套/鞋子/配饰 |
| sub_type | string | T恤/衬衫/牛仔裤/... |
| colors.primary | string | 主色名称 |
| colors.primary_hex | string | 主色 HEX 色值（色彩模型使用） |
| colors.secondary | string | 副色名称 |
| colors.secondary_hex | string | 副色 HEX 色值 |
| material | string | 材质 |
| fit | string | 紧身/修身/常规/宽松 |
| style | list | 风格标签 |
| season | list | 适合季节 |
| temperature_range | string | 适穿温度，如 `18~32` |
| occasion | list | 适合场合 |
| wear_count | int | 穿着次数 |
| last_worn | date | 最后穿着日期 |
| pair_with | list | 推荐搭配 |
| restrict | list | 搭配禁忌 |
| favorite | bool | 是否收藏 |
| image | string | 图片文件名 |

### 用户画像 (profile.yaml)

见 `templates/profile_template.yaml`

### 搭配方案 (outfits/outfit_NNN.yaml)

见 `templates/outfit_template.yaml`

## 可视化 UI

```bash
python build_ui.py
# 输出：ui/outfit.html（自包含，浏览器直接打开）
```

每次添加/修改衣物后重新运行。包含衣橱卡片、个人画像、搭配推荐、穿搭历史。

## 图片处理流程

当用户发送衣物图片时：

1. 保存图片到 `data/images/item_NNN.jpg`
2. 用 AI 视觉能力分析：类型、子类型、主色、副色、材质、适合季节、风格、适合场合
3. 创建对应的 `data/items/item_NNN.yaml`（含 HEX 色值）
4. 更新索引：`python scripts/wardrobe_ops.py reindex`
5. 告诉用户"已添加到衣橱，你可以在 images/ 文件夹里看到图片"

## Common Pitfalls

1. **衣物 ID 必须唯一。** 添加前先 `list` 检查现有 ID。
2. **图片文件名要和 YAML 的 image 字段对应。** `item_001.yaml` 的 image 应该是 `item_001.jpg`。
3. **wear_count 更新用增量。** 不要直接赋值，用 `--wear-count N` 或 `record` 命令。
4. **推荐时不要穷举组合。** 直接让 AI 从衣橱中挑选，不生成所有排列。
5. **temperature_range 必须是 "低~高" 格式。** 注意处理中文波浪号。
6. **profile.yaml 是推荐质量的基石。** 首次使用务必引导用户填写。
7. **HEX 色值影响色彩评分。** 添加衣物时尽量填写准确的 primary_hex。
8. **色彩模型文件在 data/ 下。** 如果 data/ 被删除，scorer.py 会降级到规则评分。

## Verification Checklist

- [ ] `data/profile.yaml` 存在且格式正确
- [ ] `data/items/` 下每个 YAML 都有 `id`、`type`、`colors.primary`
- [ ] `data/images/` 下的图片文件名与 YAML 的 `image` 字段对应
- [ ] `data/wardrobe_index.yaml` 与 `data/items/` 实际文件一致（用 `reindex` 修复）
- [ ] 推荐结果中的衣物 ID 都在衣橱中存在
