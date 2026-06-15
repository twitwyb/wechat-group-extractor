# 微信群成员微信号提取工具 v2.0

基于GitHub开源项目实现的微信群成员信息提取工具，支持三种提取方式。

## 功能特点

| 方式 | 库 | 获取信息 | 风险 | 权限要求 |
|------|-----|---------|------|---------|
| **WeChatFerry** | wcferry | wxid + 昵称 | 中（DLL注入） | 管理员 |
| **PyWxDump** | pywxdump | wxid + 昵称 + 备注 + 微信号 | 低（只读内存） | 管理员 |
| **wxauto** | wxauto | 昵称 + 备注 | 无（UI操作） | 普通 |

## 环境要求

- Windows 10/11
- Python 3.8+
- **经典版微信PC客户端 3.9.x**（已登录状态）

> ⚠️ **不支持新版微信（xwechat/WeChatAppEx）**。如果你安装的是基于 Electron 的新版微信，需要额外安装[经典版微信](https://weixin.qq.com/)才能使用本工具。

## 安装

```bash
pip install -r requirements.txt

# 可选: 安装WeChatFerry支持
pip install wcferry

# 可选: 安装PyWxDump支持
pip install pywxdump
```

## 使用方法

### 交互式模式
```bash
python main.py
```

### 命令行模式
```bash
# WeChatFerry模式（推荐）
python main.py -g "群名称" -m wcf

# PyWxDump数据库解密模式
python main.py -g "群名称" -m db

# wxauto UI自动化模式
python main.py -g "群名称" -m ui

# 组合模式（最完整）
python main.py -g "群名称" -m combined

# 导出CSV格式
python main.py -g "群名称" -m wcf -f csv
```

## 三种模式详解

### 模式1: WeChatFerry（推荐）

通过DLL注入直接调用微信内部API，获取最准确的数据。

```bash
# 需要以管理员权限运行
python main.py -g "群名称" -m wcf
```

**原理**：
1. 注入DLL到微信进程
2. 通过RPC调用微信内部函数
3. 获取群成员wxid和昵称

**优点**：数据最准确，包含真实wxid
**缺点**：需要管理员权限，可能触发微信安全检测

### 模式2: PyWxDump 数据库解密

从微信进程内存获取加密密钥，解密本地SQLite数据库。

```bash
python main.py -g "群名称" -m db
```

**原理**：
1. 扫描微信进程内存，找到32字节AES密钥
2. 使用密钥解密 MicroMsg.db 数据库
3. 查询 Contact 和 ChatRoom 表获取成员信息

**数据库表结构**：
```sql
-- 联系人表
Contact(UserName=wxid, NickName=昵称, Remark=备注, Alias=微信号)

-- 群聊表
ChatRoom(ChatRoomName=群ID, MemberList=成员wxid列表)
```

**优点**：信息最完整（wxid、昵称、备注、微信号）
**缺点**：需要微信正在运行

### 模式3: wxauto UI自动化

通过模拟操作微信界面获取数据。

```bash
python main.py -g "群名称" -m ui
```

**原理**：
1. 使用UI Automation API连接微信窗口
2. 搜索并进入目标群聊
3. 读取群成员列表显示的信息

**优点**：无需特殊权限，最安全
**缺点**：无法获取wxid，只能获取显示的昵称和备注

## 手动获取密钥

如果自动获取密钥失败，可以手动操作：

```bash
# 安装PyWxDump CLI
pip install pywxdump -U

# 获取密钥
wxdump bias -m

# 解密数据库
wxdump decrypt -k <密钥> -i "C:\Users\用户名\Documents\WeChat Files\wxid_xxx\Msg\MicroMsg.db" -o decrypted.db

# 然后使用解密后的数据库
python main.py -g "群名称" -m db
# 程序会提示输入已解密数据库的路径
```

## 输出示例

```
=== 导出摘要 ===
总成员数: 156
有wxid: 156 (100.0%)
有昵称: 142 (91.0%)
有微信号: 23 (14.7%)
================
```

## 项目结构

```
├── main.py              # 主程序
├── wcf_extractor.py     # WeChatFerry提取模块
├── db_extractor.py      # PyWxDump数据库解密模块
├── ui_extractor.py      # wxauto UI自动化模块
├── data_merger.py       # 数据合并模块
├── exporter.py          # 导出模块（Excel/CSV）
├── config.py            # 配置文件
├── requirements.txt     # 依赖清单
└── output/              # 输出目录
```

## 参考项目

- [PyWxDump](https://github.com/xaoyaoo/PyWxDump) - 微信数据库解密
- [WeChatFerry](https://github.com/lich0821/WeChatFerry) - 微信HOOK框架
- [wxauto](https://github.com/cluic/wxauto) - 微信UI自动化

## 常见问题

**Q: 提示"无法打开微信进程"？**
A: 需要以管理员权限运行CMD/PowerShell，再执行程序。

**Q: 密钥获取失败？**
A: 确保微信正在运行且已登录。也可以使用 `wxdump bias -m` 手动获取。

**Q: 找不到群？**
A: 程序会列出所有群聊供选择。确保群名称输入正确。

**Q: WeChatFerry连接失败？**
A: WeChatFerry需要特定微信版本。检查 [WeChatFerry文档](https://github.com/lich0821/WeChatFerry) 获取支持的版本列表。

**Q: 提示"无效的窗口句柄"？**
A: 你可能在使用新版微信（xwechat）。wxauto 只支持经典版微信（WeChat.exe），需要安装经典版。

## 免责声明

本工具仅供学习研究和个人数据备份使用。使用者应遵守相关法律法规，不得用于侵犯他人隐私或其他非法用途。
