# -*- coding: utf-8 -*-
"""
微信成员提取工具 - 配置文件
"""

import os
import sys

# 输出目录 — EXE模式输出到exe同目录，源码模式输出到脚本目录
if getattr(sys, 'frozen', False):
    # PyInstaller打包后，__file__指向临时目录，用exe所在目录
    OUTPUT_DIR = os.path.join(os.path.dirname(sys.executable), "output")
else:
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# UI自动化延迟配置（秒）
UI_DELAY_SHORT = 0.5      # 短延迟，用于UI响应等待
UI_DELAY_MEDIUM = 1.0     # 中等延迟，用于页面切换
UI_DELAY_LONG = 2.0       # 长延迟，用于加载等待

# 滚动配置
SCROLL_TIMES = 5          # 每次滚动的滚轮格数
SCROLL_WAIT = 0.8         # 滚动后等待时间（秒）
MAX_SCROLL_COUNT = 200    # 最大滚动次数，防止无限循环

# 微信4.x截图OCR配置
OCR_SCROLL_COUNT = 50         # 最大滚动截图次数
OCR_SCROLL_WAIT = 0.3         # 滚动后等待时间（秒）
OCR_MIN_NAME_LEN = 2          # 昵称最小长度（过滤噪声）

# 数据库相关
WECHAT_DB_NAME = "MicroMsg.db"  # 微信联系人数据库名称

# 导出配置
EXCEL_FILENAME_PREFIX = "微信群成员_"  # Excel文件名前缀
CSV_FILENAME_PREFIX = "微信群成员_"    # CSV文件名前缀

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)
