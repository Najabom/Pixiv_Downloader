"""
清理脚本 —— 删除 downloads 和 data 目录
用于测试后清除上一次下载残留的文件
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).parent

for folder in ["downloads", "data"]:
    target = ROOT / folder
    if target.exists():
        shutil.rmtree(target)
        print(f"  [OK] 已删除: {folder}/")

print("\n清理完成。")
input("\n按 Enter 退出...")
