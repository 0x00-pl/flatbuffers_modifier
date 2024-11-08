import os
import platform
import tarfile
import urllib.request
import zipfile
from pathlib import Path


def get_project_install_path():
    """返回 Poetry 项目根目录下的 flatc 安装路径"""
    return Path(__file__).parent.parent / "build" / "flatc"


def download_and_extract_flatc(version="24.3.25"):
    install_path = get_project_install_path()
    if install_path.exists():
        print(f"flatc already installed at {install_path}")
        return

    system = platform.system()
    install_path.mkdir(parents=True, exist_ok=True)

    # 根据操作系统选择下载链接
    if system == "Windows":
        url = f"https://github.com/google/flatbuffers/releases/download/v{version}/Windows.flatc.binary.zip"
        archive_name = "flatc.zip"
    elif system == "Linux":
        url = f"https://github.com/google/flatbuffers/releases/download/v{version}/Linux.flatc.binary.clang++-15.zip"
        archive_name = "flatc.zip"
    else:
        raise OSError("Unsupported operating system")

    download_path = Path(archive_name)

    print(f"Downloading flatc {version} for {system}...")
    urllib.request.urlretrieve(url, download_path)
    if not download_path.exists():
        raise RuntimeError(f"Failed to download flatc from {url}")

    print("Extracting flatc...")
    if system == "Windows":
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(install_path)
    elif system == "Linux":
        with tarfile.open(download_path, 'r') as tar_ref:
            tar_ref.extractall(install_path)

    os.remove(download_path)
    print(f"flatc installed to {install_path}")

    # 添加 install_path 到 PATH 环境变量
    os.environ["PATH"] += os.pathsep + str(install_path)
    print(f"Added {install_path} to PATH for this session")


def main():
    download_and_extract_flatc()
