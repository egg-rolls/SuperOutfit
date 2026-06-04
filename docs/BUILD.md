# SuperOutfit 打包说明

## 快速打包（便携版）

```bash
# 1. 安装 PyInstaller
uv pip install pyinstaller

# 2. 打包
pyinstaller --onedir --name SuperOutfit superoutfit.py

# 3. 生成的文件在 dist/SuperOutfit/ 目录
```

## 完整打包（安装版）

### 前置条件

1. 安装 PyInstaller：
   ```bash
   uv pip install pyinstaller
   ```

2. 安装 Inno Setup（可选，用于制作安装包）：
   - 下载：https://jrsoftware.org/isinfo.php
   - 安装后运行 Inno Setup Compiler

### 打包步骤

#### 方法 1：使用打包脚本（推荐）

```bash
# 运行打包脚本
python build.py
```

#### 方法 2：手动打包

```bash
# 1. 清理旧文件
rm -rf build/ dist/

# 2. 使用 PyInstaller 打包
pyinstaller --onedir ^
    --name SuperOutfit ^
    --icon=assets/icon.ico ^
    --add-data "data;data" ^
    --add-data "references;references" ^
    --add-data "scripts;scripts" ^
    --noconfirm ^
    superoutfit.py

# 3. 复制额外文件
cp README.md dist/SuperOutfit/
cp LICENSE dist/SuperOutfit/
cp -r data/ dist/SuperOutfit/data/
cp -r references/ dist/SuperOutfit/references/

# 4. 制作安装包（可选）
# 用 Inno Setup 打开 setup.iss 并编译
```

## 输出文件

打包完成后，会生成以下文件：

```
dist/
├── SuperOutfit/                    # 便携版
│   ├── SuperOutfit.exe            # 主程序
│   ├── _internal/                  # 依赖文件
│   ├── data/                      # 数据目录
│   ├── references/                # 知识库
│   └── README.md
│
└── SuperOutfit-Setup.exe          # 安装包（如果使用 Inno Setup）
```

## 使用方式

### 便携版

1. 解压 `dist/SuperOutfit/` 到任意目录
2. 运行 `SuperOutfit.exe`

### 安装版

1. 运行 `SuperOutfit-Setup.exe`
2. 按照向导完成安装
3. 从开始菜单或桌面快捷方式启动

## 注意事项

1. **数据目录**：打包后的程序会在 exe 同级目录查找 `data/` 和 `references/`
2. **首次运行**：建议先运行 `SuperOutfit.exe init` 完成初始化
3. **更新**：便携版直接替换文件即可；安装版需要重新安装

## 常见问题

### Q: 打包后运行报错 "ModuleNotFoundError"

A: 检查 PyInstaller 是否正确打包了所有依赖，可以添加 `--hidden-import` 参数。

### Q: 打包后运行报错 "FileNotFoundError"

A: 检查 `--add-data` 参数是否正确包含了数据文件。

### Q: 打包后的 exe 文件太大

A: 可以使用 `--exclude-module` 排除不需要的模块，或使用 UPX 压缩。

### Q: 打包后启动很慢

A: 这是 PyInstaller --onedir 模式的正常现象，首次启动需要解压文件。可以考虑使用 --onefile 模式（但会更慢）。
