# 环境依赖安装总结

## ✅ 已完成的安装

### 1. wkhtmltopdf/wkhtmltoimage ✅

- **状态**: 已安装
- **版本**: 0.12.6
- **位置**: `/usr/bin/wkhtmltoimage`, `/usr/bin/wkhtmltopdf`
- **测试**: ✓ 工作正常（已成功生成测试截图）

### 2. Playwright Python 包 ✅

- **状态**: 已安装
- **版本**: 1.58.0
- **测试**: ✓ Python 包可用

## ⚠️ 待完成的安装

### Playwright Chromium 浏览器 ⚠️

- **状态**: 未安装（网络下载失败）
- **原因**: 网络连接问题（ECONNRESET）
- **安装方法**:

```bash
# 方法 1: 直接安装（如果网络正常）
python -m playwright install chromium

# 方法 2: 使用代理（如果网络受限）
export HTTPS_PROXY=http://proxy:port
export HTTP_PROXY=http://proxy:port
python -m playwright install chromium

# 方法 3: 手动下载（如果网络完全不可用）
# 1. 访问 https://playwright.dev/docs/browsers
# 2. 下载对应版本的浏览器
# 3. 解压到 ~/.cache/ms-playwright/
```

## 📊 当前功能状态

### 可用的截图方案

| 方案 | 状态 | 说明 |
|-----|------|------|
| **wkhtmltoimage** | ✅ 可用 | 已成功测试，可正常截图 |
| **Playwright** | ⚠️ 部分可用 | Python 包已安装，浏览器待安装 |
| **MCP 浏览器** | ✅ 可用 | 需要在 Cursor 对话中使用 |

### 测试结果

```bash
# 使用 wkhtmltoimage 成功生成截图
✓ test_mcp_images/test_mermaid.png (1.1 MB)

# 验证结果
✓ PNG 文件数量: 1 / 1
✅ 所有图片已生成！
```

## 🚀 完成 Playwright 浏览器安装

### 快速安装

```bash
# 运行安装脚本（会自动处理）
bash scripts/install_dependencies.sh

# 或手动安装
python -m playwright install chromium
```

### 验证安装

```bash
# 检查依赖
python scripts/check_dependencies.py

# 测试工具
python scripts/test_screenshot_tools.py
```

## 📚 相关文档

### 安装文档

1. **[ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md)** - 环境安装指南
2. **[scripts/INSTALL_DEPENDENCIES.md](scripts/INSTALL_DEPENDENCIES.md)** - 详细安装说明
3. **[requirements.txt](requirements.txt)** - Python 包依赖

### 工具脚本

1. **[scripts/install_dependencies.sh](scripts/install_dependencies.sh)** - 一键安装脚本
2. **[scripts/check_dependencies.py](scripts/check_dependencies.py)** - 环境检查脚本
3. **[scripts/test_screenshot_tools.py](scripts/test_screenshot_tools.py)** - 工具测试脚本

### 使用文档

1. **[scripts/HTML_TO_IMAGE_MCP_USAGE.md](scripts/HTML_TO_IMAGE_MCP_USAGE.md)** - MCP 使用指南
2. **[QUICK_START_MCP.md](QUICK_START_MCP.md)** - 快速开始
3. **[README.md](README.md)** - 主文档（已更新依赖说明）

## ✅ 当前可用功能

即使 Playwright 浏览器未安装，以下功能已可用：

1. **wkhtmltoimage 截图** ✅
   ```bash
   python scripts/screenshot_html_mermaid.py test.html -o output.png
   ```

2. **MCP 浏览器截图** ✅
   ```bash
   python scripts/html_to_image_mcp.py html/ -o images/ -v
   # 然后在 Cursor 对话中使用 MCP 工具
   ```

3. **自动截图脚本** ✅
   ```bash
   python scripts/auto_screenshot_mcp.py html/ -o images/
   ```

## 📝 下一步

1. **完成 Playwright 浏览器安装**（可选，用于完全自动化）
   ```bash
   python -m playwright install chromium
   ```

2. **验证所有工具**
   ```bash
   python scripts/test_screenshot_tools.py
   ```

3. **开始使用**
   ```bash
   # 生成 HTML
   python scripts/mermaid_to_html.py doc.md -o html/

   # 截图（使用 wkhtmltoimage）
   python scripts/screenshot_html_mermaid.py html/*.html -o images/

   # 或使用 MCP 工具
   python scripts/html_to_image_mcp.py html/ -o images/ -v
   ```

---

**总结**: 核心功能已可用（wkhtmltoimage），Playwright 浏览器安装因网络问题待完成，但不影响基本使用。
