#!/usr/bin/env python3
"""
SuperOutfit 数据管理工具
支持用户数据的导入、导出和备份。
"""

import os
import sys
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BACKUP_DIR = PROJECT_ROOT / "backups"

def ensure_dirs():
    """确保目录存在"""
    BACKUP_DIR.mkdir(exist_ok=True)

def export_data(output_path=None):
    """
    导出用户数据为 zip 文件
    """
    ensure_dirs()
    
    if not DATA_DIR.exists():
        print("❌ 错误: 未找到 data/ 目录，无法导出。")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"superoutfit_data_{timestamp}.zip"
    
    if output_path:
        zip_path = Path(output_path)
    else:
        zip_path = PROJECT_ROOT / filename

    print(f"📦 正在打包数据...")
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(DATA_DIR):
                # 排除 __pycache__ 等
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(PROJECT_ROOT)
                    zf.write(file_path, arcname)
                    
        print(f"✅ 导出成功: {zip_path}")
        return True
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return False

def import_data(zip_path, merge=True, force=False):
    """
    导入用户数据
    merge: 是否合并（保留原有文件）
    force: 是否强制覆盖（不备份）
    """
    ensure_dirs()
    
    zip_file = Path(zip_path)
    if not zip_file.exists():
        print(f"❌ 错误: 文件不存在 {zip_path}")
        return False

    # 备份当前数据
    if DATA_DIR.exists() and not force:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"data_backup_{timestamp}"
        print(f"🛡️ 正在备份当前数据到: {backup_path}")
        try:
            shutil.copytree(DATA_DIR, backup_path)
        except Exception as e:
            print(f"⚠️ 备份失败: {e}，是否继续？(y/N)")
            if input().lower() != 'y':
                return False

    print(f"📥 正在解压数据...")
    
    try:
        # 解压到临时目录
        temp_dir = PROJECT_ROOT / ".temp_import"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        with zipfile.ZipFile(zip_file, 'r') as zf:
            zf.extractall(temp_dir)
            
        # 检查结构
        source_data = temp_dir / "data"
        if not source_data.exists():
            # 可能是直接压缩的 data 目录内容
            source_data = temp_dir
            
        # 移动文件
        if not DATA_DIR.exists():
            DATA_DIR.mkdir()
            
        imported = 0
        skipped = 0
        
        for root, dirs, files in os.walk(source_data):
            # 计算相对路径
            rel_root = Path(root).relative_to(source_data)
            target_root = DATA_DIR / rel_root
            target_root.mkdir(exist_ok=True)
            
            for file in files:
                src_file = Path(root) / file
                dst_file = target_root / file
                
                if dst_file.exists():
                    if merge:
                        # 简单合并逻辑：如果目标存在，比较修改时间或直接跳过
                        # 这里为了安全，默认跳过已存在的 ID
                        skipped += 1
                        continue
                    elif not force:
                        # 非强制模式下询问（此处简化为跳过，实际可增加交互）
                        skipped += 1
                        continue
                
                shutil.move(str(src_file), str(dst_file))
                imported += 1
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
        
        print(f"✅ 导入完成: 新增 {imported} 个文件，跳过 {skipped} 个冲突文件")
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

if __name__ == "__main__":
    # 简单的命令行测试
    if len(sys.argv) > 1:
        if sys.argv[1] == "export":
            export_data()
        elif sys.argv[1] == "import" and len(sys.argv) > 2:
            import_data(sys.argv[2])
