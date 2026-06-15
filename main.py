# -*- coding: utf-8 -*-
"""
微信群成员微信号提取工具 v2.0
主程序入口 - 命令行界面

支持三种提取方式:
1. wxauto - UI自动化（获取昵称/备注）
2. PyWxDump - 数据库解密（获取wxid）
3. WeChatFerry - DLL注入（获取wxid+昵称）

使用方法:
    python main.py
    python main.py -g "群名称"
    python main.py -g "群名称" -m wcf
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_DIR
from exporter import export_members


def print_banner():
    """打印程序横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║           微信群成员微信号提取工具 v2.0                          ║
║                                                                  ║
║  支持: wxauto(UI自动化) | PyWxDump(数据库解密) | WeChatFerry     ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_menu():
    """打印功能菜单"""
    menu = """
请选择提取方式:

  [1] WeChatFerry (推荐 - 最完整)
      - DLL注入方式，直接调用微信内部API
      - 可获取: wxid + 昵称
      - 需要管理员权限

  [2] PyWxDump 数据库解密
      - 从微信进程内存获取密钥，解密本地数据库
      - 可获取: wxid + 昵称 + 备注 + 微信号
      - 需要微信正在运行

  [3] wxauto UI自动化
      - 通过模拟操作微信界面获取数据
      - 可获取: 昵称 + 备注
      - 无需特殊权限

  [4] 组合模式 (PyWxDump + wxauto)
      - 数据库解密获取wxid，UI自动化补充昵称
      - 信息最完整

  [0] 退出

"""
    print(menu)


def get_group_name() -> str:
    """获取群名称"""
    while True:
        name = input("[?] 请输入群名称: ").strip()
        if name:
            return name
        print("[警告] 群名称不能为空")


def get_export_format() -> str:
    """获取导出格式"""
    while True:
        print("\n导出格式: [1] Excel  [2] CSV")
        choice = input("[?] 请选择 (1/2): ").strip()
        if choice == "1":
            return "excel"
        elif choice == "2":
            return "csv"
        print("[警告] 无效选择")


def mode_wcf(group_name: str, export_format: str):
    """WeChatFerry模式"""
    print("\n" + "="*50)
    print("  WeChatFerry 模式 - DLL注入提取")
    print("="*50)

    from wcf_extractor import extract_members_via_wcf

    members = extract_members_via_wcf(group_name)

    if not members:
        print("[错误] 未获取到成员信息")
        print("[提示] 请确保微信已登录且以管理员权限运行")
        return

    # 导出
    output_path = export_members(members, group_name, export_format)
    if output_path:
        print(f"\n[+] 提取完成！共 {len(members)} 个成员")
        print(f"[+] 文件: {output_path}")


def mode_pywxdump(group_name: str, export_format: str):
    """PyWxDump数据库解密模式"""
    print("\n" + "="*50)
    print("  PyWxDump 模式 - 数据库解密")
    print("="*50)

    from db_extractor import DBExtractor

    extractor = DBExtractor()

    # 尝试自动解密
    print("\n[*] 尝试自动获取密钥并解密数据库...")
    if not extractor.auto_decrypt():
        print("\n[提示] 自动解密失败，请手动操作:")
        print("  1. 使用 wxdump bias -m 获取密钥")
        print("  2. 使用 wxdump decrypt -k <密钥> -i MicroMsg.db -o decrypted.db 解密")
        db_path = input("\n[?] 输入已解密的数据库路径: ").strip()
        if not db_path or not os.path.exists(db_path):
            print("[错误] 文件不存在")
            return
        if not extractor.connect_existing_db(db_path):
            return

    try:
        # 查找群
        print(f"\n[*] 正在查找群: {group_name}")
        wxids, chatroom_id = extractor.get_group_members_by_name(group_name)

        if not wxids:
            print(f"[错误] 未找到群: {group_name}")
            # 列出所有群供选择
            chatrooms = extractor.get_chatrooms()
            if chatrooms:
                print("\n=== 可用群聊 ===")
                for i, room in enumerate(chatrooms[:30], 1):
                    print(f"{i}. {room['nickname']} ({room['member_count']}人) - {room['chatroom_name']}")
                choice = input("\n[?] 选择群聊序号 (直接回车取消): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(chatrooms):
                    selected = chatrooms[int(choice) - 1]
                    wxids = selected["member_list"]
                    chatroom_id = selected["chatroom_name"]
                    group_name = selected["nickname"]

        if not wxids:
            print("[错误] 未获取到群成员")
            return

        # 获取联系人详细信息
        contacts = extractor.get_contacts()
        wxid_to_contact = {c["wxid"]: c for c in contacts}

        # 构建成员列表
        members = []
        for i, wxid in enumerate(wxids, 1):
            contact = wxid_to_contact.get(wxid, {})
            members.append({
                "index": i,
                "wxid": wxid,
                "nickname": contact.get("nickname", ""),
                "remark": contact.get("remark", ""),
                "alias": contact.get("alias", ""),
            })

        # 导出
        output_path = export_members(members, group_name, export_format)
        if output_path:
            print(f"\n[+] 提取完成！共 {len(members)} 个成员")
            print(f"[+] 文件: {output_path}")

    finally:
        extractor.close()


def mode_wxauto(group_name: str, export_format: str):
    """wxauto UI自动化模式"""
    print("\n" + "="*50)
    print("  wxauto 模式 - UI自动化")
    print("="*50)

    from ui_extractor import extract_members_via_ui

    members = extract_members_via_ui(group_name)

    if not members:
        print("[错误] 未获取到成员信息")
        print("[提示] 请确保微信已登录且窗口在前台")
        return

    # 转换格式
    formatted = []
    for m in members:
        formatted.append({
            "index": m.get("index", len(formatted) + 1),
            "wxid": "",  # UI模式无法获取wxid
            "nickname": m.get("nickname", ""),
            "remark": m.get("remark", ""),
            "alias": "",
        })

    # 导出
    output_path = export_members(formatted, group_name, export_format)
    if output_path:
        print(f"\n[+] 提取完成！共 {len(formatted)} 个成员")
        print(f"[+] 文件: {output_path}")
        print("[注意] UI模式无法获取wxid")


def mode_combined(group_name: str, export_format: str):
    """组合模式 - PyWxDump + wxauto"""
    print("\n" + "="*50)
    print("  组合模式 - 数据库解密 + UI自动化")
    print("="*50)

    from db_extractor import DBExtractor
    from ui_extractor import extract_members_via_ui
    from data_merger import merge_member_data

    # Step 1: 数据库解密获取wxid
    print("\n[步骤 1/2] 数据库解密获取wxid...")
    extractor = DBExtractor()
    contacts = []
    wxids = []

    if extractor.extract_key_and_decrypt():
        try:
            contacts = extractor.get_contacts()
            wxids, _ = extractor.get_group_members_by_name(group_name)
        finally:
            extractor.close()

    # Step 2: UI自动化获取昵称
    print("\n[步骤 2/2] UI自动化获取昵称...")
    ui_members = extract_members_via_ui(group_name)

    # 合并数据
    if wxids or ui_members:
        merged = merge_member_data(ui_members or [], contacts, wxids)

        # 导出
        output_path = export_members(merged, group_name, export_format)
        if output_path:
            print(f"\n[+] 提取完成！共 {len(merged)} 个成员")
            print(f"[+] 文件: {output_path}")
    else:
        print("[错误] 两种方式均未获取到数据")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="微信群成员微信号提取工具 v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-g", "--group", help="群名称")
    parser.add_argument("-f", "--format", choices=["excel", "csv"], default="excel", help="导出格式")
    parser.add_argument("-m", "--mode", choices=["wcf", "db", "ui", "combined"], default="wcf",
                        help="提取模式: wcf(WeChatFerry), db(PyWxDump), ui(wxauto), combined(组合)")

    args = parser.parse_args()

    print_banner()

    # 命令行模式
    if args.group:
        print(f"[*] 命令行模式: 提取群 [{args.group}]")
        print(f"[*] 模式: {args.mode}, 格式: {args.format}")

        if args.mode == "wcf":
            mode_wcf(args.group, args.format)
        elif args.mode == "db":
            mode_pywxdump(args.group, args.format)
        elif args.mode == "ui":
            mode_wxauto(args.group, args.format)
        elif args.mode == "combined":
            mode_combined(args.group, args.format)
        return

    # 交互式模式
    while True:
        print_menu()
        choice = input("[?] 请选择 (0-4): ").strip()

        if choice == "0":
            print("\n[*] 再见！")
            break

        group_name = get_group_name()
        export_format = get_export_format()

        if choice == "1":
            mode_wcf(group_name, export_format)
        elif choice == "2":
            mode_pywxdump(group_name, export_format)
        elif choice == "3":
            mode_wxauto(group_name, export_format)
        elif choice == "4":
            mode_combined(group_name, export_format)
        else:
            print("[警告] 无效选择")
            continue

        if input("\n[?] 继续使用? (y/n): ").strip().lower() != 'y':
            print("\n[*] 再见！")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[*] 用户中断")
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()
