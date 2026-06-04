# SuperOutfit 安装说明

## 一键安装（推荐）

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/egg-rolls/SuperOutfit/master/scripts/install-simple.ps1 | iex
```

### macOS / Linux (Bash)

```bash
curl -fsSL https://raw.githubusercontent.com/egg-rolls/SuperOutfit/master/scripts/install.sh | bash
```

## 手动安装

### 前置条件

- Python 3.11+
- Git
- uv（可选，推荐）

### 安装步骤

#### 1. 克隆仓库

```bash
git clone https://github.com/egg-rolls/SuperOutfit.git
cd SuperOutfit
```

#### 2. 创建虚拟环境

```bash
# 使用 uv（推荐）
uv venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# 或使用 venv
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

#### 3. 安装依赖

```bash
# 使用 uv（推荐）
uv pip install -e .

# 或使用 pip
pip install -e .
```

#### 4. 初始化数据

```bash
superoutfit init --quick
```

#### 5. 验证安装

```bash
superoutfit --version
superoutfit --help
```

## 使用方式

### 命令行模式

```bash
# 查看帮助
superoutfit --help

# 衣橱管理
superoutfit wardrobe list
superoutfit wardrobe add --type 上衣 --primary-hex '#F5F0E8'

# 天气查询
superoutfit weather

# 今日推荐
superoutfit recommend today

# 搭配评分
superoutfit score --items item_001,item_003

# 色彩分析
superoutfit color show '#F5F0E8'
superoutfit color --colors '#F5F0E8,#111111'

# 反向推导
superoutfit inverse --known '#F5F0E8,#111111' --target 75 --missing 2

# 衣橱统计
superoutfit config stats

# 交互模式
superoutfit tui

# 启动 Gateway
superoutfit gateway
```

### Gateway 模式

```bash
# 启动所有服务（API + 前端 + MCP）
superoutfit gateway

# 指定端口
superoutfit gateway --port 8000

# 不启动前端
superoutfit gateway --no-frontend

# 开发模式（前端热重载）
superoutfit gateway --dev
```

## 配置文件

配置文件位于 `data/profile.yaml`：

```yaml
name: 用户
city: 大连
height: 175
weight: 70
styles:
  - 休闲
  - 简约
preferred_colors:
  - 黑白灰
budget:
  top: 200
  bottom: 300
  outer: 500
```

## 数据目录

```
data/
├── items/              # 衣物数据
│   ├── item_001.yaml
│   ├── item_002.yaml
│   └── ...
├── images/             # 衣物图片
├── profile.yaml        # 用户配置
├── scored_palettes.json # 色卡数据
└── color_model_gp.pkl  # 色彩模型
```

## 卸载

### 删除程序

```bash
# 删除安装目录
rm -rf ~/.superoutfit  # macOS/Linux
rm -rf %LOCALAPPDATA%\SuperOutfit  # Windows
```

### 删除数据

```bash
# 删除数据目录
rm -rf data/
```

## 常见问题

### Q: 安装后命令找不到

A: 检查虚拟环境是否激活，或检查 PATH 是否包含安装目录。

### Q: 依赖安装失败

A: 尝试使用 uv 替代 pip：
```bash
uv pip install -e .
```

### Q: 权限错误

A: 使用管理员权限运行安装脚本，或使用 `--user` 选项：
```bash
pip install --user -e .
```

### Q: Python 版本不兼容

A: SuperOutfit 需要 Python 3.11+，请升级 Python：
```bash
# 使用 uv 安装 Python
uv python install 3.11
```

## 开发模式

### 安装开发依赖

```bash
uv pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black .
isort .
```

### 类型检查

```bash
mypy .
```
