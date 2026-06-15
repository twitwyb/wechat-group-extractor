# -*- coding: utf-8 -*-
"""
微信成员提取工具 - UI自动化模块
通过wxauto库实现微信PC客户端的UI自动化操作
"""

import time
import sys
from typing import List, Dict, Optional

try:
    from wxauto import WeChat
except ImportError:
    WeChat = None

from config import UI_DELAY_MEDIUM


class UIExtractor:
    """微信UI自动化提取器"""

    def __init__(self):
        self.wx: Optional[WeChat] = None

    def connect(self) -> bool:
        """连接到微信PC客户端"""
        if WeChat is None:
            print("[错误] 未安装wxauto库，请运行: pip install wxauto")
            return False
        try:
            print("[*] 正在连接微信PC客户端...")
            self.wx = WeChat()
            print("[+] 已成功连接到微信")
            return True
        except Exception as e:
            print(f"[错误] 连接微信失败: {e}")
            print("[提示] 请确保微信PC客户端已登录并在前台运行")
            return False

    def get_group_members(self, group_name: str) -> List[Dict[str, str]]:
        """
        获取指定群的成员列表
        返回: [{index, nickname, remark}]
        """
        if not self.wx:
            print("[错误] 未连接到微信")
            return []

        try:
            print(f"[*] 正在获取群 [{group_name}] 的成员列表...")
            group = self.wx.GetGroup(group_name)
            if not group:
                print(f"[错误] 未找到群: {group_name}")
                return []

            members = group.GetGroupMembers()
            if not members:
                print("[警告] 未获取到群成员信息")
                return []

            member_list = []
            for i, member in enumerate(members, 1):
                info = {"index": i, "nickname": str(member), "remark": ""}
                if hasattr(member, 'remark'):
                    info["remark"] = member.remark
                member_list.append(info)

            print(f"[+] 成功获取 {len(member_list)} 个群成员")
            return member_list

        except Exception as e:
            print(f"[错误] 获取群成员失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def disconnect(self):
        """断开与微信的连接"""
        self.wx = None
        print("[*] 已断开微信连接")


def extract_members_via_ui(group_name: str) -> List[Dict[str, str]]:
    """通过UI自动化提取群成员的主函数"""
    extractor = UIExtractor()
    if not extractor.connect():
        return []
    try:
        return extractor.get_group_members(group_name)
    finally:
        extractor.disconnect()


if __name__ == "__main__":
    test_group = sys.argv[1] if len(sys.argv) > 1 else input("请输入群名称: ")
    members = extract_members_via_ui(test_group)
    if members:
        print("\n=== 群成员列表 ===")
        for m in members:
            print(f"{m['index']}. {m['nickname']}")
    else:
        print("[!] 未获取到成员信息")
