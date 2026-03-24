# 🖥️ 浏览器自动化控制工具

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Version-1.0.0-green.svg" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-orange.svg" alt="License">
</p>

> 强大的浏览器自动化工具，支持多实例管理、指纹定制、Cookie管理等高级功能。

## ✨ 功能特性

### 🔢 多浏览器实例管理
- 同时管理多个独立的浏览器实例
- 独立配置、互不干扰
- 支持克隆和复制浏览器实例
- 实例状态持久化保存

### 👆 指纹定制
- 随机生成真实的浏览器指纹
- 支持自定义 User-Agent、分辨率、时区、语言等
- WebGL 指纹伪装
- 硬件信息模拟 (CPU核心数、内存)
- 预设多种指纹配置 (Windows/Mac/Android/隐身模式)

### 🍪 Cookie 管理
- 导入/导出 Cookie (JSON、Netscape格式)
- Cookie 加密存储
- Cookie 合并与同步
- Cookie 验证与清洗
- 域名级 Cookie 管理

### 🔧 其他功能
- 代理服务器支持
- 无头模式运行
- 页面截图
- JavaScript 代码执行
- 命令行工具 (CLI)
- 完整的 Python SDK

## 📦 安装

### 环境要求

- Python 3.8+
- Playwright (自动安装)

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/a145137265/browser-automation-tool.git
cd browser-automation-tool

# 2. 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装 Playwright 浏览器
playwright install chromium
```

## 🚀 快速开始

### Python API 使用

```python
import asyncio
from browser_automation import BrowserManager, FingerprintGenerator

async def main():
    # 初始化管理器
    manager = BrowserManager()
    await manager.initialize()
    
    # 生成指纹
    fp_gen = FingerprintGenerator()
    fingerprint = fp_gen.generate(platform='windows')
    
    # 创建浏览器实例
    instance = manager.create_instance(
        name="my-browser",
        fingerprint=fingerprint.to_dict()
    )
    
    # 启动浏览器
    await manager.launch_instance(instance.instance_id, headless=False)
    
    # 访问网页
    await manager.navigate(instance.instance_id, "https://www.example.com")
    
    # 截图
    await manager.take_screenshot(instance.instance_id, "screenshot.png")
    
    # 获取Cookie
    cookies = await manager.export_cookies(instance.instance_id)
    print(f"获取到 {len(cookies)} 个Cookie")
    
    # 关闭
    await manager.close()

asyncio.run(main())
```

### 使用预设指纹

```python
from browser_automation.fingerprint import PresetFingerprints

# 防检测指纹
stealth_fp = PresetFingerprints.stealth()

# Windows Chrome
windows_fp = PresetFingerprints.windows_chrome()

# Mac Safari
mac_fp = PresetFingerprints.mac_safari()

# Android Chrome
android_fp = PresetFingerprints.android_chrome()
```

### Cookie 管理

```python
from browser_automation import CookieManager

cm = CookieManager()

# 从文件导入
cookies = cm.import_from_json('cookies.json')

# 过滤特定域名的Cookie
filtered = cm.filter_cookies(cookies, domains=['.example.com'])

# 导出为 Netscape 格式 (curl等工具使用)
cm.export_to_netscape(cookies, 'cookies.txt')

# 验证Cookie
result = cm.validate_cookies(cookies)
print(f"有效: {result['valid']}, 总数: {result['total']}")
```

### 命令行工具

```bash
# 安装后可以使用
browser-automation --help

# 生成指纹
browser-automation fingerprint --preset stealth -o fingerprint.json

# 创建浏览器实例
browser-automation create -n my-browser --platform windows

# 浏览网页
browser-automation browse -n test -u https://www.example.com

# 截图
browser-automation screenshot -i <instance_id> -o screenshot.png

# 执行JavaScript
browser-automation js -i <instance_id> -s "document.title"

# 列出所有实例
browser-automation list
```

## 📚 API 参考

### BrowserManager

| 方法 | 说明 |
|------|------|
| `initialize()` | 初始化管理器 |
| `create_instance()` | 创建浏览器实例 |
| `launch_instance()` | 启动浏览器 |
| `navigate()` | 导航到URL |
| `execute_script()` | 执行JavaScript |
| `take_screenshot()` | 截图 |
| `close_instance()` | 关闭实例 |
| `export_cookies()` | 导出Cookie |
| `import_cookies()` | 导入Cookie |
| `list_instances()` | 列出实例 |
| `close()` | 关闭所有实例 |

### FingerprintGenerator

| 方法 | 说明 |
|------|------|
| `generate()` | 生成随机指纹 |
| `generate_for_profile()` | 为配置生成一致指纹 |
| `export_fingerprint()` | 导出指纹配置 |
| `import_fingerprint()` | 导入指纹配置 |
| `detect_fingerprint()` | 检测页面指纹 |

### CookieManager

| 方法 | 说明 |
|------|------|
| `export_to_json()` | 导出为JSON |
| `import_from_json()` | 从JSON导入 |
| `merge_cookies()` | 合并Cookie |
| `filter_cookies()` | 过滤Cookie |
| `convert_to_netscape()` | 转换为Netscape格式 |
| `validate_cookies()` | 验证Cookie |
| `sync_cookies()` | 同步Cookie |

## 📁 项目结构

```
browser-automation-tool/
├── browser_automation/
│   ├── __init__.py          # 包入口
│   ├── browser_manager.py   # 浏览器管理器
│   ├── fingerprint.py       # 指纹生成器
│   ├── cookie_manager.py    # Cookie管理器
│   └── cli.py               # 命令行工具
├── requirements.txt          # 依赖
├── setup.py                  # 安装配置
├── README.md                 # 说明文档
└── LICENSE                   # MIT许可证
```

## 🔐 注意事项

1. **合规使用**: 请确保自动化操作符合网站的服务条款
2. **隐私安全**: 妥善保管Cookie和指纹数据
3. **反检测**: 指纹只是降低被检测的概率,无法完全避免
4. **更新**: 定期更新Playwright以获得最新的反检测改进

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License - 请查看 [LICENSE](LICENSE) 文件

---

<p align="center">如果对你有帮助,欢迎 ⭐ Star ⭐</p>