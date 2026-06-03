---
name: superoutfit
description: "AI 智能穿搭顾问：衣物管理、穿搭推荐、衣橱分析。数据以 YAML 文件存储，用户可直接浏览和编辑。"
version: 1.0.0
author: Lirui
license: MIT
metadata:
  hermes:
    tags: [outfit, wardrobe, fashion, recommendation, clothing]
    related_skills: []
---

# SuperOutfit 智能穿搭顾问

AI 驱动的个人衣橱管理与穿搭推荐系统。所有数据以 YAML 文件存储在 skill 的 `data/` 目录下，用户可直接在资源管理器中浏览、编辑文件和拖拽图片。

## When to Use

- 用户提到"穿搭"、"搭配"、"衣橱"、"今天穿什么"、"推荐穿"
- 用户想添加/查看/编辑衣物
- 用户想分析衣橱缺口或穿搭历史
- 用户上传衣物图片并希望识别属性

参考 `references/standalone-to-skill-pattern.md` 了解本 skill 的架构决策背景（独立应用转 skill 的模式）。

## 数据目录结构

数据存储在 skill 目录内部的 `data/` 子目录，与代码共存：

```
~/.hermes/skills/productivity/superoutfit/
├── SKILL.md
├── scripts/
├── templates/
└── data/                       # 用户数据（与 skill 绑定）
    ├── profile.yaml
    ├── wardrobe_index.yaml
    ├── history.yaml
    ├── preferences.yaml
    ├── items/                  # 衣物详情，每件一个 YAML
    ├── outfits/                # 搭配方案
    ├── images/                 # 衣物图片（用户直接拖拽放入）
    ├── outfit_images/          # 搭配效果图
    └── archive/                # 已淘汰衣物归档
```

环境变量 `SUPEROUTFIT_DATA` 可覆盖数据目录位置。脚本默认读取 skill 内的 `data/` 目录。

**⚠️ 必须 pin 此 skill：** `hermes curator pin superoutfit`
数据在 skill 内部时，如果 curator 归档了 skill，用户数据会一起消失。
Pin 之后 curator 永远不会碰它。

**关键设计：用户可以直接在文件夹里操作**
- 拖拽衣物图片到 `images/` 目录
- 用任意编辑器修改 YAML 文件
- 删除不需要的衣物文件
- 浏览 `outfits/` 看搭配方案
- 备份 = 复制整个 skill 目录

## 核心工作流

### 1. 添加衣物（图片识别模式）

当用户上传衣物图片时：

1. 将图片保存到 `data/images/item_NNN.jpg`
2. 用 `vision_analyze` 分析图片，提取：颜色、材质、款式、类型、季节
3. 用 `scripts/wardrobe_ops.py` 的 `add_item` 命令创建 YAML
4. 更新 `wardrobe_index.yaml`

```bash
python scripts/wardrobe_ops.py add \
  --type "上衣" --sub-type "衬衫" \
  --primary-color "白色" --secondary-color "浅蓝条纹" \
  --material "纯棉" --fit "修身" \
  --style "通勤,简约" --season "春,秋" \
  --image "item_015.jpg"
```

### 2. 穿搭推荐

当用户问"今天穿什么"或请求推荐时：

1. 获取天气：`python scripts/weather.py --city 北京`
2. 加载用户画像和衣橱：`python scripts/wardrobe_ops.py list --json`
3. 构建 prompt：注入衣橱数据 + 天气 + 用户画像 + 场合
4. LLM 直接推荐 3 套方案（不穷举组合）
5. 用 `scripts/scorer.py` 校验推荐结果的合理性
6. 保存推荐到 `outfits/outfit_NNN.yaml`

**推荐 prompt 结构：**
```
你是穿搭顾问。以下是用户衣橱：
{wardrobe_data}

用户画像：
{profile}

今日天气：{weather}

场合：{occasion}

请推荐 3 套搭配，每套包含：衣物 ID、名称、颜色、搭配理由。
优先选择穿着次数少的衣物，避免搭配禁忌。
```

### 3. 衣橱分析

当用户问"我缺什么"或"该买什么"时：

1. 加载衣橱索引
2. 统计各类别数量、穿着频率
3. 识别缺口：缺少的类型、场合覆盖不足的衣物
4. 结合用户偏好给出购买建议

### 4. 记录穿搭

当用户说"今天穿了 XXX"时：

1. 识别涉及的衣物 ID
2. 更新对应衣物的 `wear_count` 和 `last_worn`
3. 追加记录到 `history.yaml`

## 穿搭领域知识

穿搭专业知识存放在 `references/` 目录下，按需读取：

| 文件 | 内容 | 何时读取 |
|------|------|----------|
| `color.md` | 色彩搭配规则、万能色、肤色匹配 | 用户问颜色搭配 |
| `silhouette.md` | 版型与身材匹配、帽子与脸型 | 用户问什么版型适合 |
| `wardrobe.md` | 衣橱结构、日常穿搭流程、上下线穿搭 | 用户问怎么搭配 |
| `buying.md` | 购买决策、价格策略、单次穿着成本 | 用户问该买什么 |
| `accessories.md` | 项链/戒指/手链/腰带/丝巾指南 | 用户问配饰搭配 |
| `shoes.md` | 鞋子类型、颜色配置、买鞋原则 | 用户问鞋子搭配 |
| `mistakes.md` | 常见穿搭雷区 | 用户问搭配对不对 |
| `care.md` | 衣物洗护、去污、存放 | 用户问怎么洗/保养 |
| `style_archetypes.md` | 7种风格体系、适合身材、搜索关键词 | 用户问什么风格适合 |
| `layering.md` | 叠穿三角区理论、3个公式、配色规则、南方无外套叠穿 | 用户问怎么叠穿/秋冬穿搭 |

**读取策略：** 只加载与用户问题相关的文件，不全部加载。

## 可视化 UI

```bash
# 生成自包含 HTML（数据 + 图片 base64 嵌入，单文件可分享）
python build_ui.py

# 输出：ui/outfit.html，浏览器直接打开
# 功能：衣橱网格、筛选、详情弹窗、个人画像、自动搭配推荐、穿搭历史
```

每次添加/修改衣物后运行 `python build_ui.py` 重新生成。

## 安装与分享

```bash
# 首次安装（初始化空数据目录）
python setup.py

# 导出分享包（不含个人数据，zip 约 22KB）
python export.py
# 输出：superoutfit_YYYYMMDD.zip
# 接收者解压后 python setup.py 即可使用
```

非 Hermes 用户（Claude Code / OpenCode / Cursor）：解压后用对应工具打开目录，对 AI 说"阅读 SKILL.md"。

## 命令参考（wardrobe_ops.py）

```bash
# 添加衣物
python scripts/wardrobe_ops.py add --type "上衣" --sub-type "T恤" --primary-color "黑色"

# 列出所有衣物（表格）
python scripts/wardrobe_ops.py list

# 列出（JSON，供 AI 解析）
python scripts/wardrobe_ops.py list --json

# 按类别筛选
python scripts/wardrobe_ops.py list --category "上衣"

# 查看单件详情
python scripts/wardrobe_ops.py show item_001

# 更新衣物属性
python scripts/wardrobe_ops.py update item_001 --wear-count 24 --last-worn 2026-06-02

# 删除衣物（移到 archive）
python scripts/wardrobe_ops.py delete item_001

# 统计概览
python scripts/wardrobe_ops.py stats

# 重建索引
python scripts/wardrobe_ops.py reindex
```

## 命令参考（scorer.py）

```bash
# 评分一套搭配
python scripts/scorer.py --items item_001,item_020,item_040 --occasion "办公"

# 评分并附带天气
python scripts/scorer.py --items item_001,item_020,item_040 --occasion "办公" --temp 22
```

## 命令参考（weather.py）

```bash
# 查询天气（返回 JSON）
python scripts/weather.py --city "北京"

# 查询指定日期
python scripts/weather.py --city "上海" --date "2026-06-03"
```

## YAML Schema 速查

### 衣物 (items/item_NNN.yaml)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 唯一标识，如 `item_001` |
| type | string | 上衣/裤子/外套/鞋子/配饰 |
| sub_type | string | T恤/衬衫/牛仔裤/... |
| colors.primary | string | 主色 |
| colors.secondary | string | 副色/花纹 |
| material | string | 材质 |
| fit | string | 紧身/修身/常规/宽松 |
| style | list | 通勤/简约/轻熟/运动/... |
| season | list | 春/夏/秋/冬 |
| temperature_range | string | 适穿温度，如 `15~25` |
| occasion | list | 办公/日常/约会/运动/... |
| wear_count | int | 穿着次数 |
| last_worn | date | 最后穿着日期 |
| pair_with | list | 推荐搭配的衣物类型 |
| restrict | list | 搭配禁忌 |
| favorite | bool | 是否收藏 |
| image | string | 图片文件名，如 `item_001.jpg` |

### 用户画像 (profile.yaml)

见 `templates/profile_template.yaml`

### 搭配方案 (outfits/outfit_NNN.yaml)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 唯一标识 |
| items | list | 衣物 ID 列表 |
| occasion | string | 适用场合 |
| score | float | 评分 (0-100) |
| reason | string | 搭配理由 |
| weather | dict | 创建时的天气 |
| created_at | datetime | 创建时间 |

## 图片处理流程

当用户发送衣物图片时：

1. 保存图片到 `data/images/item_NNN.jpg`
2. 调用 `vision_analyze(image_path, "分析这件衣物：类型、子类型、主色、副色、材质、适合季节、风格、适合场合")`
3. 解析返回的结构化信息
4. 创建对应的 `items/item_NNN.yaml`
5. 更新 `wardrobe_index.yaml`
6. 告诉用户"已添加到衣橱，你可以在 images/ 文件夹里看到图片"

## Common Pitfalls

1. **必须 pin 住 Skill。** 数据在 Skill 内部，curator 会归档闲置 skill 导致数据丢失。首次安装后立即执行 `hermes curator pin superoutfit`。
2. **衣物 ID 必须唯一。** 添加前先 `list` 检查现有 ID，避免覆盖。
2. **图片文件名要和 YAML 的 image 字段对应。** `item_001.yaml` 的 image 应该是 `item_001.jpg`。
3. **wear_count 是手动或自动累加的，不要覆盖。** 更新时用增量，不要直接赋值。
4. **推荐时不要穷举所有组合。** 47 件衣物的全组合是天文数字，直接让 LLM 从衣橱中挑选。
5. **temperature_range 必须是 "低~高" 格式。** 解析时用 `split('~')`，注意处理中文波浪号。
6. **profile.yaml 是整个系统的基石。** 如果没有画像，推荐质量会大幅下降。首次使用时务必引导用户填写。
7. **不要把图片存在 YAML 里。** YAML 只存文件名引用，图片文件放在 `images/` 目录。
8. **用户可能手动编辑 YAML。** 读取时要容错，用 `yaml.safe_load` 并处理缺失字段。
9. **终端工具传中文参数有编码问题。** bash (MSYS) 处理 CJK 字符会 garble。用 `execute_code` 调用脚本，或让脚本接受 JSON stdin 传参，避免 bash 中转中文。
10. **Python 生成含 JS 的 HTML 时避免 f-string。** JavaScript 大量使用 `{}`，与 Python f-string 的花括号转义冲突。用 `TEMPLATE.replace("__PLACEHOLDER__", data)` 模式代替 f-string 注入数据。见 `build_ui.py` 的实现。
11. **导出分享时排除 data/。** `export.py` 只打包 SKILL.md + scripts + templates，data/ 只保留空目录结构。接收者运行 `setup.py` 初始化空数据。

## Verification Checklist

- [ ] `data/profile.yaml` 存在且格式正确
- [ ] `items/` 目录下每个 YAML 都有 `id`、`type`、`colors.primary`
- [ ] `images/` 目录下的图片文件名与 YAML 的 `image` 字段对应
- [ ] `wardrobe_index.yaml` 与 `items/` 目录实际文件一致（可用 `reindex` 修复）
- [ ] 推荐结果中的衣物 ID 都在衣橱中存在
