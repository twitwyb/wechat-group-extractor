# 微信群成员微信号提取工具 v3.0

支持微信3.9.x和4.x版本的群成员信息提取工具，提供五种提取方式。

## 功能特点

| 方式 | 获取信息 | 微信3.9.x | 微信4.x | 风险 |
|------|---------|-----------|---------|------|
| **WeChatFerry** | wxid + 昵称 | ✅ | ❌ | 中（DLL注入） |
| **PyWxDump** | wxid + 昵称 + 备注 + 微信号 | ✅ | ❓ | 低（只读内存） |
| **wxauto** | 昵称 + 备注 | ✅ | ❌ | 无（UI操作） |
| **组合模式** | wxid + 昵称 + 备注 | ✅ | ❌ | 低 |
| **微信4.x OCR** ⭐ | 昵称 | ✅ | ✅ | 无（截图识别） |

## 环境要求

- Windows 10/11
- Python 3.8+
- 微信PC客户端（已登录状态）
  - 3.9.x 经典版：支持所有模式
  - 4.x 新版：仅支持截图OCR模式

## 安装

```bash
pip install -r requirements.txt

# 可选: 安装WeChatFerry支持
pip install wcferry

# 可选: 安装PyWxDump支持
pip install pywxdump
```

## 使用方法

### 自动检测模式（推荐）
```bash
python main.py -g "群名称"
# 自动检测微信版本，选择最佳提取方式
```

### 指定模式
```bash
# 微信4.x 截图OCR
python main.py -g "群名称" -m wx4

# WeChatFerry（微信3.9.x）
python main.py -g "群名称" -m wcf

# PyWxDump数据库解密
python main.py -g "群名称" -m db

# wxauto UI自动化（微信3.9.x）
python main.py -g "群名称" -m ui

# 组合模式（最完整）
python main.py -g "群名称" -m combined

# 导出CSV格式
python main.py -g "群名称" -m wx4 -f csv
```

### 交互式模式
```bash
python main.py
```

## 微信4.x截图OCR模式

针对微信4.x（Electron/Qt架构）的通用提取方案。

**原理**：
1. 自动找到微信窗口
2. 搜索群名进入群聊
3. 打开群成员列表
4. 滚动截图 + OCR识别成员昵称

**优点**：不依赖UI Automation，适用于任何微信版本
**缺点**：只能获取显示的昵称，无法获取wxid

## 打包为EXE

```bash
python build.py
```

生成的EXE在 `dist/` 目录下，双击即可运行，无需Python环境。

## 项目结构

```
├── main.py              # 主程序（v3.0，支持5种模式+自动检测）
├── wechat_detector.py   # 微信版本检测模块
├── wx4_extractor.py     # 微信4.x截图OCR提取模块
├── wcf_extractor.py     # WeChatFerry提取模块
├── db_extractor.py      # PyWxDump数据库解密模块
├── ui_extractor.py      # wxauto UI自动化模块
├── data_merger.py       # 数据合并模块
├── exporter.py          # 导出模块（Excel/CSV）
├── config.py            # 配置文件
├── build.py             # PyInstaller打包脚本
├── requirements.txt     # 依赖清单
└── output/              # 输出目录
```

## 参考项目

- [PyWxDump](https://github.com/xaoyaoo/PyWxDump) - 微信数据库解密
- [WeChatFerry](https://github.com/lich0821/WeChatFerry) - 微信HOOK框架
- [wxauto](https://github.com/cluic/wxauto) - 微信UI自动化
- [RapidOCR](https://github.com/RapidAI/RapidOCR) - 轻量OCR引擎

## 常见问题

**Q: 微信4.x怎么用？**
A: 直接运行 `python main.py -g "群名称" -m wx4`，程序会自动截图识别。

**Q: OCR识别不准？**
A: 确保微信窗口完全可见，不要被其他窗口遮挡。OCR对清晰的中文昵称识别率较高。

**Q: 提示"无法打开微信进程"？**
A: 需要以管理员权限运行CMD/PowerShell，再执行程序。

**Q: WeChatFerry连接失败？**
A: WeChatFerry仅支持微信3.9.x。检查 [WeChatFerry文档](https://github.com/lich0821/WeChatFerry) 获取支持的版本列表。

**Q: 打包的EXE太大？**
A: OCR模型约占30MB，这是正常大小。如不需要微信4.x支持，可移除rapidocr依赖后重新打包。

## 免责声明

本工具仅供学习研究和个人数据备份使用。使用者应遵守相关法律法规，不得用于侵犯他人隐私或其他非法用途。
