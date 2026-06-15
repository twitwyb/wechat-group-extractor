# -*- coding: utf-8 -*-
"""
微信版本检测模块
自动检测当前运行的微信版本，返回版本号和推荐的提取方式
"""

import ctypes
from typing import Optional, Tuple


class WeChatInfo:
    """微信窗口信息"""
    def __init__(self, hwnd: int, version: str, window_class: str):
        self.hwnd = hwnd
        self.version = version
        self.window_class = window_class


def _enum_windows_by_class(class_name: str) -> list:
    """按窗口类名枚举窗口"""
    EnumWindows = ctypes.windll.user32.EnumWindows
    GetClassNameW = ctypes.windll.user32.GetClassNameW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible

    results = []

    def callback(hwnd, _):
        if not IsWindowVisible(hwnd):
            return True
        cls = ctypes.create_unicode_buffer(256)
        GetClassNameW(hwnd, cls, 256)
        if class_name in cls.value:
            results.append(hwnd)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int)
    )
    EnumWindows(WNDENUMPROC(callback), 0)
    return results


def detect_wechat() -> Optional[WeChatInfo]:
    """
    检测当前运行的微信版本
    返回: WeChatInfo 或 None
    """
    # 微信 3.9.x 经典版
    hwnds = _enum_windows_by_class("WeChatMainWndForPC")
    if hwnds:
        return WeChatInfo(hwnds[0], "3.x", "WeChatMainWndForPC")

    # 微信 4.x 新版 (Qt + Chromium)
    hwnds = _enum_windows_by_class("Qt51514QWindowIcon")
    if hwnds:
        return WeChatInfo(hwnds[0], "4.x", "Qt51514QWindowIcon")

    return None


def get_recommended_mode(info: Optional[WeChatInfo]) -> str:
    """根据微信版本推荐提取模式"""
    if info is None:
        return "none"
    if info.version == "3.x":
        return "wxauto"
    return "wx4"


if __name__ == "__main__":
    info = detect_wechat()
    if info:
        mode = get_recommended_mode(info)
        print(f"检测到微信 {info.version}")
        print(f"  窗口句柄: {info.hwnd}")
        print(f"  窗口类名: {info.window_class}")
        print(f"  推荐模式: {mode}")
    else:
        print("未检测到微信运行")
