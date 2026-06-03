# SuperOutfit CLI 命令速查

## 安装

```bash
# 开发模式安装
cd D:\Application\SuperOutfit
uv pip install -e .

# 使用方式
superoutfit <command> <subcommand> [options]
# 或
python -m superoutfit <command> <subcommand> [options]
```

## 命令列表

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
# 查询天气
superoutfit weather --city "大连"
superoutfit weather --lat 38.91 --lon 121.60
```

### 搭配评分 (score / s)

```bash
# 评分搭配
superoutfit score --items item_001,item_003,item_006 --occasion 通勤 --temp 22
```

### 色彩协调度 (color / c)

```bash
# 按衣物 ID
superoutfit color --items item_001,item_003,item_006

# 按 HEX 色值
superoutfit color --colors "#F5F0E8,#C4A97D,#111111"
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
```

### 版本信息

```bash
superoutfit --version
superoutfit -v
```

## 示例工作流

### 1. 首次设置

```bash
# 安装
uv pip install -e .

# 查看配置
superoutfit config

# 编辑个人画像
notepad data\profile.yaml
```

### 2. 添加衣物

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

### 3. 评分搭配

```bash
# 查看搭配评分
superoutfit score --items item_001,item_004,item_006 --occasion 通勤

# 查看色彩协调度
superoutfit color --items item_001,item_004
```

### 4. 浏览色卡

```bash
# 查看高分色卡
superoutfit palette list --top 10 --min-score 80

# 从色卡获取灵感
superoutfit palette list --source colorhunt --top 5
```

### 5. 学习穿搭知识

```bash
# 查看有哪些知识文档
superoutfit knowledge list

# 学习色彩搭配
superoutfit knowledge show color.md

# 学习版型匹配
superoutfit knowledge show silhouette.md
```

## 命令别名

| 全称 | 别名 |
|------|------|
| wardrobe | w |
| weather | wt |
| recommend | r |
| score | s |
| color | c |
| palette | p |
| knowledge | k |
| config | cf |

```bash
# 使用别名
superoutfit w list
superoutfit s --items item_001,item_003
superoutfit k list
```

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

## 常见问题

### Q: 命令找不到？

```bash
# 方式 1：使用 python -m
python -m superoutfit --version

# 方式 2：检查安装
uv pip list | grep superoutfit
```

### Q: 如何更新 CLI？

```bash
cd D:\Application\SuperOutfit
git pull
uv pip install -e .
```

### Q: 如何卸载？

```bash
uv pip uninstall superoutfit
```

### Q: 数据在哪里？

```
data/
├── profile.yaml        # 用户画像
├── wardrobe_index.yaml # 衣物索引
├── history.yaml        # 穿搭历史
├── items/              # 衣物详情 YAML
├── images/             # 衣物图片
└── archive/            # 已淘汰衣物
```

所有数据都是 YAML 文件，可以直接在资源管理器中编辑。
