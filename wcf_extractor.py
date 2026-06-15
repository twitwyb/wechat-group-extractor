# -*- coding: utf-8 -*-
"""
微信成员提取工具 - WeChatFerry模块
基于WeChatFerry的DLL注入方式获取群成员信息

参考项目: https://github.com/lich0821/WeChatFerry
注意: 此方式需要注入DLL到微信进程，有一定风险
"""

import sys
from typing import Dict, List, Optional

try:
    from wcferry import Wcf
except ImportError:
    Wcf = None


class WCFExtractor:
    """WeChatFerry提取器 - 通过DLL注入获取微信数据"""

    def __init__(self):
        self.wcf: Optional[Wcf] = None

    def connect(self) -> bool:
        """连接到微信（需要微信已登录）"""
        if Wcf is None:
            print("[错误] 未安装wcferry库，请运行: pip install wcferry")
            return False
        try:
            print("[*] 正在通过WeChatFerry连接微信...")
            self.wcf = Wcf()
            print("[+] WeChatFerry连接成功")
            return True
        except Exception as e:
            print(f"[错误] WeChatFerry连接失败: {e}")
            print("[提示] 请确保微信已登录且以管理员权限运行")
            return False

    def get_contacts(self) -> List[Dict[str, str]]:
        """获取所有联系人"""
        if not self.wcf:
            return []
        try:
            contacts = self.wcf.get_contacts()
            print(f"[+] 获取到 {len(contacts)} 个联系人")
            return contacts
        except Exception as e:
            print(f"[错误] 获取联系人失败: {e}")
            return []

    def get_groups(self) -> List[Dict[str, str]]:
        """获取所有群聊"""
        if not self.wcf:
            return []
        try:
            contacts = self.wcf.get_contacts()
            groups = [c for c in contacts if "@chatroom" in c.get("wxid", "")]
            print(f"[+] 获取到 {len(groups)} 个群聊")
            return groups
        except Exception as e:
            print(f"[错误] 获取群聊失败: {e}")
            return []

    def get_chatroom_members(self, chatroom_id: str) -> Dict[str, str]:
        """获取指定群的成员列表，返回 {wxid: nickname}"""
        if not self.wcf:
            return {}
        try:
            members = self.wcf.get_chatroom_members(chatroom_id)
            print(f"[+] 群 {chatroom_id} 有 {len(members)} 个成员")
            return members
        except Exception as e:
            print(f"[错误] 获取群成员失败: {e}")
            return {}

    def find_group_by_name(self, group_name: str) -> Optional[str]:
        """通过群名称查找群ID"""
        groups = self.get_groups()
        for group in groups:
            if group_name.lower() in group.get("name", "").lower():
                return group.get("wxid")
        return None

    def extract_group_members(self, group_name: str) -> List[Dict[str, str]]:
        """提取指定群的成员信息"""
        if not self.wcf:
            return []

        chatroom_id = self.find_group_by_name(group_name)
        if not chatroom_id:
            print(f"[错误] 未找到群: {group_name}")
            return []

        members_dict = self.get_chatroom_members(chatroom_id)
        if not members_dict:
            return []

        return [
            {"index": i, "wxid": wxid, "nickname": nick, "remark": "", "alias": ""}
            for i, (wxid, nick) in enumerate(members_dict.items(), 1)
        ]

    def disconnect(self):
        """断开连接"""
        if self.wcf:
            try:
                self.wcf.disable_recv_msg()
            except Exception:
                pass
            self.wcf = None
            print("[*] 已断开WeChatFerry连接")


def extract_members_via_wcf(group_name: str) -> List[Dict[str, str]]:
    """通过WeChatFerry提取群成员的主函数"""
    extractor = WCFExtractor()
    if not extractor.connect():
        return []
    try:
        self_wxid = extractor.get_self_wxid() if hasattr(extractor, 'get_self_wxid') else None
        if self_wxid:
            print(f"[+] 当前用户: {self_wxid}")
        return extractor.extract_group_members(group_name)
    finally:
        extractor.disconnect()


if __name__ == "__main__":
    test_group = sys.argv[1] if len(sys.argv) > 1 else input("请输入群名称: ")
    print("\n=== WeChatFerry 提取测试 ===\n")
    members = extract_members_via_wcf(test_group)
    if members:
        print(f"\n=== 群成员列表（共 {len(members)} 人）===")
        for m in members:
            print(f"{m['index']}. {m['nickname']} ({m['wxid']})")
    else:
        print("[!] 未获取到成员信息")
