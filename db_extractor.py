# -*- coding: utf-8 -*-
"""
微信成员提取工具 - 数据库解密模块
基于PyWxDump实现微信数据库解密和wxid提取

使用方式:
1. 自动模式: 程序调用PyWxDump CLI获取密钥并解密
2. 手动模式: 用户手动使用PyWxDump CLI解密后，程序读取解密后的数据库

参考项目:
- PyWxDump: https://github.com/xaoyaoo/PyWxDump
"""

import os
import sys
import sqlite3
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple


class WeChatDBReader:
    """
    微信数据库读取器
    从解密后的数据库中提取联系人和群成员信息
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> bool:
        """连接到数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            print(f"[+] 已连接到数据库: {self.db_path}")
            return True
        except Exception as e:
            print(f"[错误] 连接数据库失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_all_contacts(self) -> List[Dict[str, str]]:
        """
        获取所有联系人信息
        返回: 联系人列表 [{wxid, nickname, remark, alias}]
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            # 查询Contact表
            query = """
            SELECT UserName, NickName, Remark, Alias, Type
            FROM Contact
            WHERE UserName IS NOT NULL
            AND UserName != ''
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            contacts = []
            for row in rows:
                username = row["UserName"] or ""
                # 过滤掉系统账号
                if username.startswith("gh_") or username.startswith("weixin"):
                    continue
                contact = {
                    "wxid": username,
                    "nickname": row["NickName"] or "",
                    "remark": row["Remark"] or "",
                    "alias": row["Alias"] or "",
                    "type": row["Type"] or 0,
                }
                contacts.append(contact)

            print(f"[+] 获取到 {len(contacts)} 个联系人")
            return contacts

        except Exception as e:
            print(f"[错误] 查询联系人失败: {e}")
            return []

    @staticmethod
    def _parse_member_list(member_list_str: str) -> List[str]:
        """解析MemberList字段（逗号或分号分隔）"""
        if not member_list_str:
            return []
        for sep in (",", ";"):
            if sep in member_list_str:
                return [m.strip() for m in member_list_str.split(sep) if m.strip()]
        return [member_list_str]

    def get_all_chatrooms(self) -> List[Dict]:
        """
        获取所有群聊信息
        返回: 群聊列表 [{chatroom_name, nickname, member_count, member_list}]
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            # 尝试查询ChatRoom表
            query = """
            SELECT ChatRoomName, NickName, MemberCount, MemberList
            FROM ChatRoom
            WHERE ChatRoomName IS NOT NULL
            AND ChatRoomName != ''
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            chatrooms = []
            for row in rows:
                members = self._parse_member_list(row["MemberList"] or "")

                chatroom = {
                    "chatroom_name": row["ChatRoomName"] or "",
                    "nickname": row["NickName"] or "",
                    "member_count": row["MemberCount"] or len(members),
                    "member_list": members,
                }
                chatrooms.append(chatroom)

            print(f"[+] 获取到 {len(chatrooms)} 个群聊")
            return chatrooms

        except Exception as e:
            print(f"[错误] 查询群聊失败: {e}")
            # 尝试列出所有表
            self._list_tables()
            return []

    def _list_tables(self):
        """列出数据库中的所有表（调试用）"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print("[调试] 数据库中的表:")
            for t in tables:
                print(f"  - {t[0]}")
        except Exception:
            pass

    def get_chatroom_members(self, chatroom_id: str) -> List[str]:
        """
        获取指定群的成员wxid列表
        参数:
            chatroom_id: 群ID (如 12345678@chatroom)
        返回: wxid列表
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            query = """
            SELECT MemberList
            FROM ChatRoom
            WHERE ChatRoomName = ?
            """
            cursor.execute(query, (chatroom_id,))
            row = cursor.fetchone()

            if row and row["MemberList"]:
                wxids = self._parse_member_list(row["MemberList"])
                print(f"[+] 群 {chatroom_id} 有 {len(wxids)} 个成员")
                return wxids

            return []

        except Exception as e:
            print(f"[错误] 查询群成员失败: {e}")
            return []

    def get_contact_by_wxid(self, wxid: str) -> Optional[Dict[str, str]]:
        """
        通过wxid查询联系人信息
        参数:
            wxid: 微信ID
        返回: 联系人信息或None
        """
        if not self.conn:
            return None

        try:
            cursor = self.conn.cursor()

            query = """
            SELECT UserName, NickName, Remark, Alias
            FROM Contact
            WHERE UserName = ?
            """
            cursor.execute(query, (wxid,))
            row = cursor.fetchone()

            if row:
                return {
                    "wxid": row["UserName"] or "",
                    "nickname": row["NickName"] or "",
                    "remark": row["Remark"] or "",
                    "alias": row["Alias"] or "",
                }

            return None

        except Exception as e:
            print(f"[错误] 查询联系人失败: {e}")
            return None

    def get_chatroom_by_name(self, group_name: str) -> Optional[Dict]:
        """
        通过群名称查找群聊
        参数:
            group_name: 群名称关键字
        返回: 群聊信息或None
        """
        if not self.conn:
            return None

        try:
            cursor = self.conn.cursor()

            query = """
            SELECT ChatRoomName, NickName, MemberCount, MemberList
            FROM ChatRoom
            WHERE NickName LIKE ?
            """
            cursor.execute(query, (f"%{group_name}%",))
            rows = cursor.fetchall()

            if rows:
                row = rows[0]
                members = self._parse_member_list(row["MemberList"] or "")

                return {
                    "chatroom_name": row["ChatRoomName"] or "",
                    "nickname": row["NickName"] or "",
                    "member_count": row["MemberCount"] or len(members),
                    "member_list": members,
                }

            return None

        except Exception as e:
            print(f"[错误] 查询群聊失败: {e}")
            return None


class DBExtractor:
    """微信数据库提取器"""

    def __init__(self):
        self.db_reader: Optional[WeChatDBReader] = None

    def find_wechat_data_dir(self) -> Optional[str]:
        """
        查找微信数据目录
        返回: 数据目录路径或None
        """
        possible_paths = [
            os.path.expanduser("~/Documents/WeChat Files"),
            "D:/WeChat Files",
            "E:/WeChat Files",
        ]

        for base_path in possible_paths:
            if os.path.exists(base_path):
                for user_dir in os.listdir(base_path):
                    msg_dir = os.path.join(base_path, user_dir, "Msg")
                    if os.path.exists(msg_dir):
                        db_file = os.path.join(msg_dir, "MicroMsg.db")
                        if os.path.exists(db_file):
                            print(f"[+] 找到微信数据目录: {os.path.join(base_path, user_dir)}")
                            return msg_dir

        return None

    def try_pywxdump_cli(self) -> Optional[str]:
        """
        尝试使用PyWxDump CLI解密数据库
        返回: 解密后的数据库路径或None
        """
        print("[*] 尝试使用PyWxDump CLI解密数据库...")

        # 检查wxdump命令是否可用
        try:
            result = subprocess.run(["wxdump", "--help"], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print("[警告] wxdump命令不可用")
                return None
        except FileNotFoundError:
            print("[警告] 未安装PyWxDump CLI，请运行: pip install pywxdump")
            return None
        except Exception:
            return None

        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="wechat_decrypt_")
        output_path = os.path.join(temp_dir, "decrypted_MicroMsg.db")

        try:
            # 获取密钥
            print("[*] 正在获取加密密钥...")
            result = subprocess.run(
                ["wxdump", "bias", "-m"],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                print(f"[错误] 获取密钥失败: {result.stderr}")
                return None

            # 从输出中提取密钥
            key = None
            for line in result.stdout.split("\n"):
                if "key" in line.lower() or len(line.strip()) == 64:
                    # 尝试提取64位十六进制字符串
                    import re
                    match = re.search(r'[0-9a-fA-F]{64}', line)
                    if match:
                        key = match.group()
                        break

            if not key:
                print("[错误] 无法从输出中提取密钥")
                return None

            print(f"[+] 获取到密钥: {key[:8]}...{key[-8:]}")

            # 解密数据库
            data_dir = self.find_wechat_data_dir()
            if not data_dir:
                print("[错误] 未找到微信数据目录")
                return None

            db_path = os.path.join(data_dir, "MicroMsg.db")
            print(f"[*] 正在解密: {db_path}")

            result = subprocess.run(
                ["wxdump", "decrypt", "-k", key, "-i", db_path, "-o", output_path],
                capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0 and os.path.exists(output_path):
                print(f"[+] 解密成功: {output_path}")
                return output_path
            else:
                print(f"[错误] 解密失败: {result.stderr}")
                return None

        except Exception as e:
            print(f"[错误] PyWxDump CLI执行失败: {e}")
            return None

    def connect_existing_db(self, db_path: str) -> bool:
        """
        连接已解密的数据库
        参数:
            db_path: 解密后的数据库路径
        返回: 是否成功
        """
        if not os.path.exists(db_path):
            print(f"[错误] 文件不存在: {db_path}")
            return False

        self.db_reader = WeChatDBReader(db_path)
        return self.db_reader.connect()

    def auto_decrypt(self) -> bool:
        """
        自动解密数据库
        返回: 是否成功
        """
        # 尝试PyWxDump CLI
        decrypted_path = self.try_pywxdump_cli()
        if decrypted_path:
            return self.connect_existing_db(decrypted_path)

        return False

    def get_contacts(self) -> List[Dict[str, str]]:
        """获取所有联系人"""
        if not self.db_reader:
            return []
        return self.db_reader.get_all_contacts()

    def get_chatrooms(self) -> List[Dict]:
        """获取所有群聊"""
        if not self.db_reader:
            return []
        return self.db_reader.get_all_chatrooms()

    def get_group_members_by_name(self, group_name: str) -> Tuple[List[str], str]:
        """
        通过群名称获取成员wxid列表
        参数:
            group_name: 群名称关键字
        返回: (wxid列表, 群ID)
        """
        if not self.db_reader:
            return [], ""

        chatroom = self.db_reader.get_chatroom_by_name(group_name)
        if chatroom:
            return chatroom["member_list"], chatroom["chatroom_name"]

        return [], ""

    def close(self):
        """关闭数据库连接"""
        if self.db_reader:
            self.db_reader.close()


def extract_members_via_db(group_name: str = None, db_path: str = None) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    通过数据库解密提取群成员的主函数
    参数:
        group_name: 群名称（可选）
        db_path: 已解密的数据库路径（可选）
    返回: (联系人列表, 群成员wxid列表)
    """
    extractor = DBExtractor()

    # 连接数据库
    connected = False
    if db_path and os.path.exists(db_path):
        # 使用已解密的数据库
        connected = extractor.connect_existing_db(db_path)
    else:
        # 自动解密
        connected = extractor.auto_decrypt()

    if not connected:
        print("[错误] 无法连接到数据库")
        print("[提示] 请手动解密数据库:")
        print("  1. 安装PyWxDump: pip install pywxdump")
        print("  2. 获取密钥: wxdump bias -m")
        print("  3. 解密数据库: wxdump decrypt -k <密钥> -i MicroMsg.db -o decrypted.db")
        print("  4. 运行本程序时指定解密后的数据库路径")
        return [], []

    try:
        # 获取所有联系人
        contacts = extractor.get_contacts()

        # 如果指定了群名，获取群成员wxid
        group_wxids = []
        if group_name:
            wxids, chatroom_id = extractor.get_group_members_by_name(group_name)
            if wxids:
                group_wxids = wxids
                print(f"[+] 群 [{group_name}] (ID: {chatroom_id}) 有 {len(wxids)} 个成员")
            else:
                print(f"[警告] 未找到群: {group_name}")

        return contacts, group_wxids

    finally:
        extractor.close()


if __name__ == "__main__":
    print("=== 微信数据库解密测试 ===\n")

    # 可以指定已解密的数据库路径
    test_db = input("[?] 输入已解密的数据库路径（直接回车自动解密）: ").strip()
    if not test_db:
        test_db = None

    contacts, group_wxids = extract_members_via_db(db_path=test_db)

    if contacts:
        print(f"\n=== 联系人列表（共 {len(contacts)} 个）===")
        for i, c in enumerate(contacts[:20], 1):
            alias_info = f" 微信号:{c['alias']}" if c['alias'] else ""
            remark_info = f" 备注:{c['remark']}" if c['remark'] else ""
            print(f"{i}. {c['nickname']}{remark_info}{alias_info} | wxid: {c['wxid']}")

        if len(contacts) > 20:
            print(f"... 还有 {len(contacts) - 20} 个联系人")

    if group_wxids:
        print(f"\n=== 群成员wxid列表（共 {len(group_wxids)} 个）===")
        for i, wxid in enumerate(group_wxids[:20], 1):
            print(f"{i}. {wxid}")
