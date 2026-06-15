# -*- coding: utf-8 -*-
"""
微信成员提取工具 - 数据合并模块
将UI自动化获取的昵称与数据库解密获取的wxid进行关联
"""

from typing import List, Dict, Optional


def merge_member_data(
    ui_members: List[Dict[str, str]],
    db_contacts: List[Dict[str, str]],
    db_group_wxids: List[str] = None
) -> List[Dict[str, str]]:
    """
    合并UI自动化和数据库解密的数据
    参数:
        ui_members: UI自动化获取的成员列表 [{index, nickname, remark}]
        db_contacts: 数据库中的联系人列表 [{wxid, nickname, remark, alias}]
        db_group_wxids: 数据库中的群成员wxid列表（可选）
    返回: 合并后的完整成员信息列表
    """
    # 创建索引
    wxid_to_contact = {}
    name_to_contacts = {}  # 昵称/备注 -> 联系人列表

    for contact in db_contacts:
        wxid_to_contact[contact["wxid"]] = contact
        for key in ("nickname", "remark"):
            val = contact[key]
            if val:
                name_to_contacts.setdefault(val, []).append(contact)

    merged = []
    matched_wxids = set()

    # 优先用数据库的群成员wxid列表
    if db_group_wxids:
        for i, wxid in enumerate(db_group_wxids, 1):
            contact = wxid_to_contact.get(wxid, {})
            merged.append({
                "index": i,
                "wxid": wxid,
                "nickname": contact.get("nickname", ""),
                "remark": contact.get("remark", ""),
                "alias": contact.get("alias", ""),
            })
            matched_wxids.add(wxid)
        print(f"[+] 从数据库获取到 {len(merged)} 个群成员的wxid")

    # 通过昵称匹配UI自动化获取的成员
    for ui_member in ui_members:
        ui_nick = ui_member.get("nickname", "")
        ui_remark = ui_member.get("remark", "")

        # 检查是否已匹配
        already = any(
            (m["nickname"] == ui_nick or m["remark"] == ui_nick or
             m["nickname"] == ui_remark or m["remark"] == ui_remark)
            for m in merged
        )
        if already:
            continue

        # 尝试匹配
        matched_contact = None
        for name in (ui_nick, ui_remark):
            if name in name_to_contacts:
                candidates = name_to_contacts[name]
                if len(candidates) == 1:
                    matched_contact = candidates[0]
                    break
                # 多个候选，尝试通过另一个字段进一步匹配
                other = ui_remark if name == ui_nick else ui_nick
                for c in candidates:
                    if c["nickname"] == other or c["remark"] == other:
                        matched_contact = c
                        break
                if not matched_contact:
                    matched_contact = candidates[0]
                break

        if matched_contact and matched_contact["wxid"] not in matched_wxids:
            merged.append({
                "index": len(merged) + 1,
                "wxid": matched_contact["wxid"],
                "nickname": matched_contact.get("nickname", ui_nick),
                "remark": matched_contact.get("remark", ui_remark),
                "alias": matched_contact.get("alias", ""),
            })
            matched_wxids.add(matched_contact["wxid"])
        else:
            merged.append({
                "index": len(merged) + 1,
                "wxid": "",
                "nickname": ui_nick,
                "remark": ui_remark,
                "alias": "",
            })

    # 重新编号
    for i, member in enumerate(merged, 1):
        member["index"] = i

    matched_count = sum(1 for m in merged if m["wxid"])
    print(f"[+] 合并后共 {len(merged)} 个成员")
    print(f"[+] 成功匹配wxid: {matched_count} 个, 未匹配: {len(merged) - matched_count} 个")

    return merged
