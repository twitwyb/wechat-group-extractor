# -*- coding: utf-8 -*-
"""
打包脚本 - 使用PyInstaller将工具打包为EXE
使用方法: python build.py
"""

import os
import subprocess
import sys


def build():
    """打包为单文件EXE"""
    print("="*50)
    print("  微信群成员提取工具 - 打包EXE")
    print("="*50)

    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"[+] PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("[错误] 未安装PyInstaller，请运行: pip install pyinstaller")
        return

    # 获取rapidocr完整包路径（需要config.yaml、模型、子包）
    rapidocr_data = []
    try:
        import rapidocr_onnxruntime
        pkg_dir = os.path.dirname(rapidocr_onnxruntime.__file__)
        # 打包整个 rapidocr_onnxruntime 目录
        rapidocr_data.append(f"{pkg_dir};rapidocr_onnxruntime")
        print(f"[+] 找到OCR包: {pkg_dir}")
    except ImportError:
        print("[警告] 未安装rapidocr-onnxruntime，OCR功能将不可用")

    # PyInstaller参数
    args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # 单文件
        "--name", "微信群成员提取工具",   # EXE名称
        "--clean",                      # 清理缓存
        "--noconfirm",                  # 不确认覆盖
    ]

    # 添加hidden imports
    hidden_imports = [
        "openpyxl",
        "wxauto",
        "pyautogui",
        "PIL",
        "pyperclip",
        "rapidocr_onnxruntime",
        "rapidocr_onnxruntime.ch_ppocr_v2_cls",
        "rapidocr_onnxruntime.ch_ppocr_v3_det",
        "rapidocr_onnxruntime.ch_ppocr_v3_rec",
        "psutil",
        "uiautomation",
        "comtypes",
        "win32gui",
        "win32con",
    ]
    for mod in hidden_imports:
        args.extend(["--hidden-import", mod])

    # 添加数据文件
    for data in rapidocr_data:
        args.extend(["--add-data", data])

    # 入口文件
    args.append("main.py")

    print(f"\n[*] 开始打包...")
    print(f"[*] 命令: {' '.join(args[:6])}...")

    result = subprocess.run(args, capture_output=False)

    if result.returncode == 0:
        exe_path = os.path.join("dist", "微信群成员提取工具.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / 1024 / 1024
            print(f"\n[+] 打包成功！")
            print(f"[+] EXE路径: {os.path.abspath(exe_path)}")
            print(f"[+] 文件大小: {size_mb:.1f} MB")
        else:
            print("\n[+] 打包完成，请检查dist目录")
    else:
        print(f"\n[错误] 打包失败，返回码: {result.returncode}")


if __name__ == "__main__":
    build()
