# 🧥 SuperOutfit

**AI 智能穿搭顾问** — 基于 YAML 文件的个人衣橱管理与穿搭推荐系统。

数据是 YAML，图片在文件夹，打开资源管理器就能看。不锁死在数据库里，不依赖任何云服务。

> 支持 Hermes Agent · Claude Code · OpenCode · Cursor · 纯 Python

---

## ✨ 特性

- **YAML 原生** — 每件衣物一个文件，可直接编辑，版本控制友好
- **图片可见** — 拖拽到 `data/images/` 即可，资源管理器里一目了然
- **AI 推荐** — 基于天气、场合、风格偏好自动搭配，不穷举组合
- **搭配评分** — 6 维度打分（颜色/风格/场合/天气/新鲜度/偏好）
- **可视化 UI** — 单文件 HTML，浏览器打开即用，衣橱卡片 + 推荐方案
- **多工具兼容** — Hermes / Claude Code / OpenCode / Cursor 都能用
- **零外部依赖** — 只需 Python + PyYAML，天气用免费 API

---

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/superoutfit.git
cd superoutfit

# 2. 初始化数据目录
python setup.py

# 3. 编辑个人画像
#    打开 data/profile.yaml，填写身材、风格偏好、预算

# 4. 添加衣物
python scripts/wardrobe_ops.py add \
  --type "上衣" --sub-type "短袖衬衫" \
  --primary-color "米白色" --material "冰丝缎面" \
  --style "简约,通勤" --season "春,夏" --temp-range "18~32"

# 5. 查看衣橱
python scripts/wardrobe_ops.py list

# 6. 生成可视化 UI
python build_ui.py
#    浏览器打开 ui/outfit.html
```

---

## 📂 目录结构

```
superoutfit/
├── SKILL.md                # AI Agent 指令文件
├── README.md               # 本文件
├── LICENSE                 # MIT License
├── setup.py                # 首次安装脚本
├── build_ui.py             # 生成可视化 HTML
├── export.py               # 导出分享包（不含个人数据）
│
├── scripts/                # 核心工具
│   ├── wardrobe_ops.py     # 衣物 CRUD（增删改查 + 统计）
│   ├── weather.py          # 天气查询（Open-Meteo 免费 API）
│   └── scorer.py           # 搭配评分（6 维度）
│
├── templates/              # 数据模板（参考用）
│   ├── item_template.yaml  # 衣物模板
│   ├── profile_template.yaml # 用户画像模板
│   └── outfit_template.yaml  # 搭配方案模板
│
└── data/                   # 用户数据（.gitignore 排除）
    ├── profile.yaml        # 个人画像
    ├── wardrobe_index.yaml # 衣物索引（自动生成）
    ├── history.yaml        # 穿搭历史
    ├── preferences.yaml    # AI 学习偏好
    ├── items/              # 衣物详情，每件一个 YAML
    ├── outfits/            # 搭配方案
    ├── images/             # 衣物图片（直接拖入）
    └── archive/            # 已淘汰衣物归档
```

---

## 🤖 AI 集成

### Hermes Agent

```bash
# 安装到 Hermes
cp -r . ~/.hermes/skills/productivity/superoutfit
hermes curator pin superoutfit

# 使用
# 对 Hermes 说："帮我推荐今天的穿搭"
```

Hermes 会自动读取 SKILL.md，调用脚本查询天气、分析衣橱、推荐搭配。

### Claude Code / OpenCode / Cursor

```bash
# 打开项目目录
cd superoutfit

# 对 AI 说：
# "阅读 SKILL.md，帮我查看衣橱并推荐今天的穿搭"
```

AI 会自动读取 `data/` 下的衣物和画像，调用脚本完成推荐。

### Python 直接调用

```python
from scripts.scorer import score_outfit

result = score_outfit(
    ["item_001", "item_003", "item_006"],
    occasion="通勤",
    temp=22
)
print(result["total_score"], result["grade"])
# 87.0 A
```

---

## 🛠️ 命令参考

### 衣橱管理

```bash
# 添加衣物
python scripts/wardrobe_ops.py add --type "上衣" --sub-type "T恤" --primary-color "黑色"

# 列出所有衣物
python scripts/wardrobe_ops.py list

# JSON 输出（供 AI 解析）
python scripts/wardrobe_ops.py list --json

# 按类型/风格/季节筛选
python scripts/wardrobe_ops.py list --category "上衣"
python scripts/wardrobe_ops.py list --style "通勤"
python scripts/wardrobe_ops.py list --season "夏"

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

### 天气查询

```bash
# 查询天气（返回 JSON）
python scripts/weather.py --city "大连"

# 查询指定日期（未来 7 天）
python scripts/weather.py --city "北京" --date "2026-06-05"

# 列出支持的城市
python scripts/weather.py --list-cities
```

### 搭配评分

```bash
# 评分一套搭配
python scripts/scorer.py --items item_001,item_003,item_006 --occasion "通勤"

# 附带天气评分
python scripts/scorer.py --items item_001,item_003 --occasion "日常" --temp 25
```

### 可视化 UI

```bash
# 生成 HTML（读取数据 + 图片，打包成单文件）
python build_ui.py

# 打开浏览器查看
start ui/outfit.html        # Windows
open ui/outfit.html         # macOS
xdg-open ui/outfit.html     # Linux
```

---

## 📋 数据格式

每件衣物是一个独立的 YAML 文件：

```yaml
id: item_001
type: 上衣
sub_type: 短袖衬衫
colors:
  primary: 米白色
  secondary: 无
material: 冰丝缎面
fit: 宽松落肩
style: [简约, 通勤, 轻商务]
season: [春, 夏, 初秋]
temperature_range: "18~32"
occasion: [日常通勤, 外出逛街, 轻商务会面]
wear_count: 0
pair_with: [休闲西裤, 直筒牛仔裤]
restrict: [厚重高领内搭]
image: item_001.jpg         # 图片放在 data/images/
```

完整字段说明见 `templates/item_template.yaml`。

---

## 🎨 可视化 UI

运行 `python build_ui.py` 生成自包含的 HTML 文件：

- **衣橱视图** — 卡片网格，支持按类型/风格筛选，点击查看详情
- **个人画像** — 身材、风格偏好、颜色偏好、预算
- **搭配推荐** — 自动生成 3 套方案，带评分和搭配理由
- **穿搭历史** — 记录每天穿了什么

单文件，含图片 base64，可直接分享给别人查看。

---

## 📦 分享给别人

```bash
# 方式 1：导出 zip（不含个人数据）
python export.py
# 生成 superoutfit_YYYYMMDD.zip

# 方式 2：直接发 Git 仓库链接
# .gitignore 已排除所有个人数据，可以放心 push
```

接收者运行 `python setup.py` 即可初始化空数据目录。

---

## 🧩 架构设计

```
用户请求 → AI Agent 读取 SKILL.md
         → 调用 weather.py 获取天气
         → 调用 wardrobe_ops.py 读取衣橱
         → AI 基于画像 + 天气 + 衣橱推荐搭配
         → 调用 scorer.py 校验评分
         → 输出推荐方案
```

评分算法权重：

| 维度 | 权重 | 说明 |
|------|------|------|
| 颜色协调 | 25% | 安全色系 + 冲突检测 |
| 风格一致 | 20% | 风格兼容矩阵 |
| 场合匹配 | 20% | 衣物 occasion 标签匹配 |
| 天气适配 | 15% | 温度范围匹配 |
| 穿着新鲜度 | 10% | 鼓励穿少穿的衣物 |
| 用户偏好 | 10% | 颜色 + 风格偏好匹配 |

---

## 📄 License

[MIT](LICENSE)

---

## 🙏 致谢

- [Open-Meteo](https://open-meteo.com/) — 免费天气 API
- [PyYAML](https://pyyaml.org/) — YAML 解析
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — AI Agent 框架
