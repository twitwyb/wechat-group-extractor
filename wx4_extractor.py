# -*- coding: utf-8 -*-
"""
微信4.x 成员提取模块
通过截图+OCR方式提取微信4.x群成员信息
适用于微信4.1.x (Electron/Qt架构，UI Automation无法获取内容)
"""

import os
import sys
import time
import ctypes
from typing import List, Dict, Optional, Set

try:
    import pyautogui
    from PIL import Image
except ImportError:
    pyautogui = None

try:
    from rapidocr_onnxruntime import RapidOCR
except ImportError:
    RapidOCR = None


class WX4Extractor:
    """微信4.x截图OCR提取器"""

    def __init__(self):
        self.ocr: Optional[RapidOCR] = None
        self._wechat_hwnd: Optional[int] = None

    def _init_ocr(self) -> bool:
        """初始化OCR引擎"""
        if RapidOCR is None:
            print("[错误] 未安装rapidocr-onnxruntime，请运行: pip install rapidocr-onnxruntime")
            return False
        if self.ocr is None:
            print("[*] 正在初始化OCR引擎（首次加载较慢）...")
            self.ocr = RapidOCR()
            print("[+] OCR引擎就绪")
        return True

    def _find_wechat_window(self) -> Optional[int]:
        """找到微信4.x窗口句柄"""
        EnumWindows = ctypes.windll.user32.EnumWindows
        GetClassNameW = ctypes.windll.user32.GetClassNameW
        IsWindowVisible = ctypes.windll.user32.IsWindowVisible

        results = []

        def callback(hwnd, _):
            if not IsWindowVisible(hwnd):
                return True
            cls = ctypes.create_unicode_buffer(256)
            GetClassNameW(hwnd, cls, 256)
            if "Qt51514QWindowIcon" in cls.value:
                results.append(hwnd)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int)
        )
        EnumWindows(WNDENUMPROC(callback), 0)

        return results[0] if results else None

    def _activate_window(self, hwnd: int) -> bool:
        """激活微信窗口"""
        try:
            user32 = ctypes.windll.user32
            # SW_RESTORE = 9, SW_SHOW = 5
            user32.ShowWindow(hwnd, 9)
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"[错误] 激活窗口失败: {e}")
            return False

    def _get_window_rect(self, hwnd: int) -> tuple:
        """获取窗口位置和大小"""
        import ctypes.wintypes as wintypes

        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)

    def _screenshot_region(self, region: tuple = None) -> "Image.Image":
        """截取屏幕指定区域"""
        return pyautogui.screenshot(region=region)

    def _ocr_image(self, image: "Image.Image") -> list:
        """对图片进行OCR识别，返回文字列表"""
        import numpy as np
        img_array = np.array(image)
        result, _ = self.ocr(img_array)
        if result is None:
            return []
        # result = [[box, text, confidence], ...]
        return [item[1] for item in result]

    def _search_group(self, group_name: str) -> bool:
        """在微信中搜索并进入群聊"""
        print(f"[*] 搜索群聊: {group_name}")

        # Ctrl+F 打开搜索
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.5)

        # 输入群名
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)

        # 使用剪贴板输入中文
        import pyperclip
        pyperclip.copy(group_name)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1.0)

        # 按回车选择第一个结果
        pyautogui.press('enter')
        time.sleep(1.0)

        return True

    def _open_member_list(self) -> bool:
        """打开群成员列表"""
        print("[*] 打开群成员列表...")

        # 点击群聊标题区域（窗口顶部中间偏右）
        hwnd = self._wechat_hwnd
        x, y, w, h = self._get_window_rect(hwnd)

        # 群名通常在窗口顶部中间位置
        title_x = x + w // 2
        title_y = y + 30
        pyautogui.click(title_x, title_y)
        time.sleep(0.5)

        # 尝试点击"群成员"或成员数按钮
        # 这需要根据实际UI位置调整
        pyautogui.click(title_x + 100, title_y)
        time.sleep(1.0)

        return True

    def _scroll_and_capture(self, max_scrolls: int = 50) -> List[str]:
        """
        滚动截图+OCR识别成员昵称
        返回: 去重后的昵称列表
        """
        all_names: Set[str] = set()
        prev_names: Set[str] = set()

        hwnd = self._wechat_hwnd
        x, y, w, h = self._get_window_rect(hwnd)

        # 成员列表通常在窗口右侧
        # 截取右侧1/3区域作为成员列表
        list_x = x + w * 2 // 3
        list_y = y + 80
        list_w = w // 3
        list_h = h - 160

        print(f"[*] 开始滚动截图识别（最多{max_scrolls}次）...")

        for i in range(max_scrolls):
            # 截图
            screenshot = self._screenshot_region((list_x, list_y, list_w, list_h))

            # OCR识别
            names = self._ocr_image(screenshot)

            # 过滤有效昵称（去掉太短的、纯数字的）
            valid_names = set()
            for name in names:
                name = name.strip()
                if len(name) >= 2 and not name.isdigit():
                    valid_names.add(name)

            # 检查是否有新内容
            new_names = valid_names - all_names
            if new_names:
                all_names.update(valid_names)
                print(f"  第{i+1}轮: 新增 {len(new_names)} 个, 累计 {len(all_names)} 个")
            elif valid_names and valid_names <= all_names:
                # 连续两轮没有新内容，可能到底了
                if valid_names == prev_names:
                    print(f"  第{i+1}轮: 无新内容，停止滚动")
                    break
            prev_names = valid_names

            # 向下滚动
            pyautogui.scroll(-3, list_x + list_w // 2, list_y + list_h // 2)
            time.sleep(0.3)

        return sorted(all_names)

    def extract_members(self, group_name: str) -> List[Dict[str, str]]:
        """
        提取群成员主函数
        参数:
            group_name: 群名称
        返回: 成员列表 [{index, nickname, remark, wxid, alias}]
        """
        if pyautogui is None:
            print("[错误] 未安装pyautogui，请运行: pip install pyautogui")
            return []

        if not self._init_ocr():
            return []

        # 找到微信窗口
        self._wechat_hwnd = self._find_wechat_window()
        if not self._wechat_hwnd:
            print("[错误] 未检测到微信4.x窗口")
            return []

        print(f"[+] 找到微信4.x窗口 (hwnd={self._wechat_hwnd})")

        # 激活窗口
        if not self._activate_window(self._wechat_hwnd):
            return []

        # 搜索群聊
        if not self._search_group(group_name):
            return []

        # 打开成员列表
        if not self._open_member_list():
            return []

        # 滚动截图+OCR
        names = self._scroll_and_capture()

        if not names:
            print("[警告] 未识别到任何成员昵称")
            return []

        # 构建成员列表
        members = []
        for i, name in enumerate(names, 1):
            members.append({
                "index": i,
                "wxid": "",  # 截图模式无法获取wxid
                "nickname": name,
                "remark": "",
                "alias": "",
            })

        print(f"[+] 提取完成，共 {len(members)} 个成员")
        return members


def extract_members_via_wx4(group_name: str) -> List[Dict[str, str]]:
    """通过截图OCR提取微信4.x群成员的主函数"""
    extractor = WX4Extractor()
    return extractor.extract_members(group_name)


if __name__ == "__main__":
    test_group = sys.argv[1] if len(sys.argv) > 1 else input("请输入群名称: ")
    members = extract_members_via_wx4(test_group)
    if members:
        print(f"\n=== 群成员列表（共 {len(members)} 人）===")
        for m in members:
            print(f"{m['index']}. {m['nickname']}")
    else:
        print("[!] 未获取到成员信息")
