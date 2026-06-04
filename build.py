#!/usr/bin/env python3
"""
SuperOutfit 打包脚本

将项目打包成独立可执行文件。

用法：
  python build.py              # 打包便携版
  python build.py --installer  # 打包安装版（需要 Inno Setup）
  python build.py --clean      # 清理打包文件
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


# 项目根目录
ROOT_DIR = Path(__file__).parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"


def clean():
    """清理打包文件"""
    print("清理打包文件...")
    
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
        print(f"  删除：{DIST_DIR}")
    
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"  删除：{BUILD_DIR}")
    
    # 删除 spec 文件
    for spec_file in ROOT_DIR.glob("*.spec"):
        spec_file.unlink()
        print(f"  删除：{spec_file}")
    
    print("清理完成")


def check_dependencies():
    """检查打包依赖"""
    print("检查打包依赖...")
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print(f"  ✓ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("  ✗ PyInstaller 未安装")
        print("    安装：uv pip install pyinstaller")
        return False
    
    return True


def build_portable():
    """打包便携版"""
    print("\n开始打包便携版...")
    
    # PyInstaller 参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--name", "SuperOutfit",
        "--noconfirm",
        "--clean",
        # 添加数据文件
        "--add-data", f"data{os.pathsep}data",
        "--add-data", f"references{os.pathsep}references",
        "--add-data", f"scripts{os.pathsep}scripts",
        # 主程序
        "superoutfit.py",
    ]
    
    # 如果有图标文件
    icon_path = ROOT_DIR / "assets" / "icon.ico"
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    # 执行打包
    print(f"执行：{' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT_DIR)
    
    if result.returncode != 0:
        print("打包失败！")
        return False
    
    # 复制额外文件
    dist_app_dir = DIST_DIR / "SuperOutfit"
    
    print("\n复制额外文件...")
    
    # 复制 README
    readme = ROOT_DIR / "README.md"
    if readme.exists():
        shutil.copy2(readme, dist_app_dir)
        print(f"  复制：README.md")
    
    # 复制 LICENSE
    license_file = ROOT_DIR / "LICENSE"
    if license_file.exists():
        shutil.copy2(license_file, dist_app_dir)
        print(f"  复制：LICENSE")
    
    # 创建空的 data 目录（如果不存在）
    data_dir = dist_app_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 创建 items 子目录
    items_dir = data_dir / "items"
    items_dir.mkdir(exist_ok=True)
    
    # 创建 images 子目录
    images_dir = data_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    print(f"\n打包完成！")
    print(f"输出目录：{dist_app_dir}")
    print(f"\n使用方法：")
    print(f"  1. 进入 {dist_app_dir}")
    print(f"  2. 运行 SuperOutfit.exe")
    print(f"  3. 首次运行请执行：SuperOutfit.exe init")
    
    return True


def build_installer():
    """打包安装版（使用 Inno Setup）"""
    print("\n开始打包安装版...")
    
    # 检查 Inno Setup
    inno_setup = Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe")
    if not inno_setup.exists():
        print("错误：未找到 Inno Setup")
        print("请先安装 Inno Setup：https://jrsoftware.org/isinfo.php")
        return False
    
    # 先打包便携版
    if not build_portable():
        return False
    
    # 创建 Inno Setup 脚本
    iss_content = f"""
[Setup]
AppId={{{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}}}
AppName=SuperOutfit
AppVersion=3.1.0
AppPublisher=SuperOutfit
AppPublisherURL=https://github.com/egg-rolls/SuperOutfit
DefaultDirName={{autopf}}\\SuperOutfit
DefaultGroupName=SuperOutfit
OutputDir={DIST_DIR}
OutputBaseFilename=SuperOutfit-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"
Name: "quicklaunchicon"; Description: "创建快速启动栏快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
Source: "{DIST_DIR}\\SuperOutfit\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\SuperOutfit"; Filename: "{{app}}\\SuperOutfit.exe"
Name: "{{group}}\\卸载 SuperOutfit"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\SuperOutfit"; Filename: "{{app}}\\SuperOutfit.exe"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\SuperOutfit"; Filename: "{{app}}\\SuperOutfit.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{{app}}\\SuperOutfit.exe"; Description: "运行 SuperOutfit"; Flags: nowait postinstall skipifsilent
"""
    
    # 写入 iss 文件
    iss_file = ROOT_DIR / "setup.iss"
    with open(iss_file, "w", encoding="utf-8") as f:
        f.write(iss_content)
    
    print(f"创建 Inno Setup 脚本：{iss_file}")
    
    # 执行 Inno Setup
    print("编译安装包...")
    result = subprocess.run([str(inno_setup), str(iss_file)], cwd=ROOT_DIR)
    
    if result.returncode != 0:
        print("编译失败！")
        return False
    
    print(f"\n打包完成！")
    print(f"安装包：{DIST_DIR / 'SuperOutfit-Setup.exe'}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="SuperOutfit 打包脚本")
    parser.add_argument("--installer", action="store_true", help="打包安装版（需要 Inno Setup）")
    parser.add_argument("--clean", action="store_true", help="清理打包文件")
    
    args = parser.parse_args()
    
    if args.clean:
        clean()
        return
    
    # 检查依赖
    if not check_dependencies():
        return
    
    if args.installer:
        build_installer()
    else:
        build_portable()


if __name__ == "__main__":
    main()
