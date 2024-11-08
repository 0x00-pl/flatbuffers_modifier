import os
import sys
import subprocess
from pathlib import Path
from scripts.install_flatc import download_and_extract_flatc


def pytest_configure():
    """pytest 配置钩子，用于在测试运行前安装和配置 flatc，并生成 Python 文件"""
    # 1. 调用下载和解压 flatc 的函数
    download_and_extract_flatc()

    # 获取项目中的 flatc 安装路径
    project_root = Path(__file__).parent.parent
    flatc_path = project_root / "build" / "flatc"

    # 将 flatc 安装路径添加到 PATH
    os.environ["PATH"] += os.pathsep + str(flatc_path)

    # 3. 确定 .fbs 文件和输出目录
    fbs_file = project_root / "tests" / "data" / "monster.fbs"
    output_dir = project_root / "tests" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 4. 通过 flatc 生成 Python 文件
    subprocess.run([flatc_path / 'flatc', "--python", "-o", str(output_dir), str(fbs_file)], check=True)
    sys.path.insert(0, str(output_dir))  # 将 output_dir 添加到 sys.path
    print(f"Generated Python files from {fbs_file} to {output_dir}")
