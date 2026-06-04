# -*- mode: python ; coding: utf-8 -*-
# SuperOutfit PyInstaller spec 文件

import sys
from pathlib import Path

block_cipher = None

# 项目根目录
root_dir = Path(SPECPATH)

# 数据文件
datas = [
    (str(root_dir / 'data'), 'data'),
    (str(root_dir / 'references'), 'references'),
    (str(root_dir / 'scripts'), 'scripts'),
]

# 隐藏导入
hiddenimports = [
    'yaml',
    'json',
    'argparse',
    'pathlib',
    'colorsys',
    'math',
    'random',
    'datetime',
    'collections',
    'urllib',
    'http',
    'socket',
    'ssl',
    'pickle',
    'numpy',
    'scipy',
    'sklearn',
]

# 排除模块（减小体积）
excludes = [
    'tkinter',
    'matplotlib',
    'pandas',
    'PIL',
    'cv2',
    'torch',
    'tensorflow',
]

a = Analysis(
    ['superoutfit.py'],
    pathex=[str(root_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SuperOutfit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root_dir / 'assets' / 'icon.ico') if (root_dir / 'assets' / 'icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SuperOutfit',
)
