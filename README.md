# 🧥 SuperOutfit

**AI 智能穿搭顾问** — 基于 5462 组真实色卡 + 高斯过程数学模型的穿搭推荐系统。

数据是 YAML，图片在文件夹，打开资源管理器就能看。不锁死在数据库里，不依赖任何云服务。

> 支持 Hermes Agent · Claude Code · OpenCode · Cursor · 纯 Python

---

## ✨ 核心能力

### 🎨 色彩评分引擎

基于 **5462 组真实人类审美色卡**训练的高斯过程模型，不是拍脑袋的规则，是人类用点赞投票出来的审美共识。

```
评分等级（基于人类审美分布）：

  SSS ≥ 85   顶级     名画级配色，人类审美共识的前 8%
  SS  ≥ 75   优秀     专业搭配师水准
  S   ≥ 65   出色     有明确审美风格
  A   ≥ 50   良好     和谐不出错
  B   ≥ 35   一般     中规中矩
  C   ≥ 20   偏弱     需要调整
  D   < 20   差       明显不搭
```

**数据来源：** Color Hunt + 色采（名画/故宫/摄影配色）+ LOL Colors + Design Seeds + Colormind

**技术栈：** 42 维特征（HSL + OKLab）→ 点赞迁移 → 稀疏高斯过程（500 诱导点）

### 🧥 衣橱管理

每件衣物一个 YAML 文件 + 一张图片。你可以：
- 在资源管理器里直接浏览、编辑、拖拽图片
- 用 AI 语音/文字添加衣物（支持图片识别）
- 按类型/风格/季节/场合筛选
- 自动统计穿着频率

### ✨ 穿搭推荐

AI 基于天气 + 衣橱 + 用户画像推荐搭配，不是穷举组合，是真正的智能推荐。

### 📚 穿搭知识库

12 篇穿搭领域知识，从 5 个优质视频中提炼：
- 色彩搭配（万能色 / 4 种配色模型 / 底色理论）
- 版型身材（上衣 4 版型 / 裤子 4 版型 / 身材解决方案）
- 叠穿层次（三角区理论 / 3 个叠穿公式）
- 场合穿搭（面试 / 通勤 / 相亲 / 婚礼 / 商务）
- 风格体系（7 种风格 / 适合身材 / 搜索关键词）
- 配饰 / 鞋子 / 购买决策 / 常见雷区 / 衣物养护

---

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/superoutfit.git
cd superoutfit

# 2. 初始化数据目录
python setup.py

# 3. 爬取色卡 + 训练色彩模型（首次需要，约 1 分钟）
python scripts/scrape_palettes.py
python scripts/scrape_wxsecai.py
python scripts/like_based_scoring.py

# 4. 编辑个人画像
#    打开 data/profile.yaml，填写身材、风格偏好、预算

# 4. 添加衣物
python scripts/wardrobe_ops.py add \
  --type "上衣" --sub-type "短袖衬衫" \
  --primary-color "米白色" --primary-hex "#F5F0E8" \
  --material "冰丝缎面" --style "简约,通勤" \
  --season "春,夏" --temp-range "18~32"

# 5. 查看衣橱
python scripts/wardrobe_ops.py list

# 6. 生成可视化仪表盘
python build_ui.py
#    浏览器打开 ui/outfit.html
```

---

## 🛠️ 命令速查

```bash
# 衣橱管理
python scripts/wardrobe_ops.py add --type "上衣" --sub-type "T恤" --primary-color "黑色"
python scripts/wardrobe_ops.py list [--json] [--category "上衣"] [--style "通勤"]
python scripts/wardrobe_ops.py show item_001
python scripts/wardrobe_ops.py update item_001 --wear-count 5
python scripts/wardrobe_ops.py delete item_001          # 移到归档
python scripts/wardrobe_ops.py stats
python scripts/wardrobe_ops.py record --items item_001,item_003 --occasion "通勤"

# 天气查询
python scripts/weather.py --city "大连"

# 搭配评分
python scripts/scorer.py --items item_001,item_003,item_006 --occasion "通勤" --temp 22

# 色彩协调度
python scripts/color_math.py --items item_001,item_003,item_006
python scripts/color_math.py --colors "#F5F0E8,#C4A97D,#111111"

# 可视化 UI
python build_ui.py                                       # 生成 ui/outfit.html
```

---

## 🎨 色彩评分技术

### 为什么比"规则"更准

```
传统方案：专家写的规则 → 同色系 95 分，撞色 55 分
  问题：规则有主观偏见，无法覆盖"意外好看"的组合

SuperOutfit：5462 组人类点赞色卡 → 学习人类审美共识
  优势：被 4 万人的点赞验证过，包含规则无法覆盖的配色
```

### 数据管道

```
6400 原始色卡
  → 剔除离群（全黑/全白/霓虹色 938 组）
  → 5462 干净色卡
  → 1456 组有人类点赞 → 百分位分数
  → Sparse GP 迁移模型 → 预测 4006 组无赞色卡
  → 5462 组全部有分数
  → Sparse GP 最终模型（500 诱导点，MAE 6.95，训练 ~10 秒）
```

### 42 维特征

```
27 维 HSL 色彩空间：
  加权平均 HSL / 简单平均 HSL / 色相统计 / 饱和度统计
  明度统计 / 色相距离统计 / 有彩色比例 / 面积熵 / 颜色数量

15 维 OKLab 感知色彩空间：
  加权平均 Lab / 简单平均 Lab / L 统计
  Chroma 统计 / Hue 距离
  （等数值距离 = 等感知差异，比 HSL 更适合色彩计算）
```

---

## 📦 分享给别人

```bash
# 导出 zip（不含个人数据）
python export.py

# 或直接发 Git 仓库链接
# .gitignore 已排除所有个人数据
```

接收者：`git clone` → `python setup.py` → 开始使用。

---

## 🤖 AI 集成

### Hermes Agent

```bash
cp -r . ~/.hermes/skills/productivity/superoutfit
hermes curator pin superoutfit
# 对 Hermes 说："帮我推荐今天的穿搭"
```

### Claude Code / OpenCode / Cursor

```bash
cd superoutfit
# 对 AI 说："阅读 SKILL.md，帮我查看衣橱并推荐今天的穿搭"
```

### Python 直接调用

```python
from scripts.scorer import score_outfit

result = score_outfit(["item_001", "item_003", "item_006"], occasion="通勤", temp=22)
print(result["total_score"], result["grade"])
# 63.7 B
```

---

## 📂 目录结构

```
superoutfit/
├── AGENTS.md / SKILL.md / README.md
├── setup.py / build_ui.py / export.py
├── scripts/
│   ├── wardrobe_ops.py         # 衣物 CRUD
│   ├── weather.py              # 天气查询
│   ├── scorer.py               # 搭配评分（6 维度）
│   ├── color_math.py           # 色彩协调度（GP 模型）
│   ├── like_based_scoring.py   # 点赞迁移 + 模型训练
│   ├── scrape_palettes.py      # 色卡爬虫
│   └── scrape_wxsecai.py       # 色采爬虫
├── templates/                  # 数据模板
├── references/                 # 12 篇穿搭知识
└── data/                       # 用户数据（.gitignore 排除）
    ├── items/ / outfits/ / images/
    ├── raw_palettes.json       # 5462 组色卡
    ├── scored_palettes.json    # 色卡 + 分数
    ├── color_model_gp.pkl      # GP 模型
    └── profile.yaml / history.yaml
```

---

## 📄 License

[MIT](LICENSE)

## 🙏 致谢

- [Color Hunt](https://colorhunt.co) — 热门配色方案
- [色采](https://www.wxsecai.com) — 名画/故宫/摄影配色
- [Open-Meteo](https://open-meteo.com) — 免费天气 API
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — AI Agent 框架
