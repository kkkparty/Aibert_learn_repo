# 环境依赖安装指南

## 快速安装

```bash
# 一键安装所有依赖
bash scripts/install_dependencies.sh

# 验证安装
python scripts/check_dependencies.py

# 测试工具
python scripts/test_screenshot_tools.py
```

## 依赖列表

### 必需依赖

| 依赖 | 用途 | 安装方法 |
|-----|------|---------|
| **Python 3.6+** | 运行脚本 | 系统自带或 `apt-get install python3` |
| **playwright** | 浏览器自动化 | `pip install playwright` |
| **Playwright Chromium** | 浏览器引擎 | `python -m playwright install chromium` |
| **wkhtmltopdf** | HTML 转图片 | `sudo apt-get install wkhtmltopdf` |

### 可选依赖

| 依赖 | 用途 | 安装方法 |
|-----|------|---------|
| **pandoc** | PDF 导出 | `sudo apt-get install pandoc` |
| **markdown** | Markdown 处理 | `pip install markdown` |

## 详细安装步骤

### 步骤 1: Python 依赖

```bash
# 安装 Playwright
pip install playwright
# 或
pip3 install playwright

# 验证
python -c "import playwright; print('Playwright 已安装')"
```

### 步骤 2: Playwright 浏览器

```bash
# 安装 Chromium 浏览器
python -m playwright install chromium

# 如果下载失败（网络问题）：
# 1. 设置代理
export HTTPS_PROXY=http://proxy:port
python -m playwright install chromium

# 2. 或使用离线安装包
# 下载地址: https://playwright.dev/docs/browsers
```

**常见问题**：
- 下载失败：检查网络，或使用代理
- 权限问题：确保有写入 `~/.cache/ms-playwright` 的权限
- 磁盘空间：需要约 200MB

### 步骤 3: wkhtmltopdf

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install wkhtmltopdf
```

#### CentOS/RHEL

```bash
sudo yum install wkhtmltopdf
```

#### macOS

```bash
brew install wkhtmltopdf
```

### 步骤 4: 验证安装

```bash
# 检查所有依赖
python scripts/check_dependencies.py

# 测试截图工具
python scripts/test_screenshot_tools.py
```

## 验证输出示例

### 成功示例

```
============================================================
  环境依赖检查
============================================================

[1/5] Python 版本
  Python 3.12.3
  ✓ 版本符合要求 (>= 3.6)

[2/5] Playwright Python 包
  ✓ 已安装

[3/5] Playwright Chromium 浏览器
  ✓ 已安装

[4/5] wkhtmltoimage
  ✓ wkhtmltoimage 0.12.6

[5/5] wkhtmltopdf (可选，用于 PDF 导出)
  ✓ wkhtmltopdf 0.12.6

============================================================
  ✓ 所有必需依赖已安装
============================================================
```

### 失败示例

```
============================================================
  ⚠️  部分依赖缺失
============================================================

安装缺失的依赖:
  运行: bash scripts/install_dependencies.sh
  或查看: scripts/INSTALL_DEPENDENCIES.md
```

## 故障排除

### 问题 1: Playwright 浏览器下载失败

**错误**:
```
Error: Failed to download Chrome for Testing
```

**解决方案**:

1. **检查网络**
   ```bash
   ping cdn.playwright.dev
   ```

2. **使用代理**
   ```bash
   export HTTPS_PROXY=http://proxy:port
   python -m playwright install chromium
   ```

3. **手动下载**
   - 访问 https://playwright.dev/docs/browsers
   - 下载对应版本
   - 解压到 `~/.cache/ms-playwright/`

### 问题 2: wkhtmltoimage 未找到

**错误**:
```
wkhtmltoimage: command not found
```

**解决方案**:

```bash
# 重新安装
sudo apt-get install --reinstall wkhtmltopdf

# 验证
which wkhtmltoimage
wkhtmltoimage --version
```

### 问题 3: 权限问题

**错误**:
```
Permission denied: ~/.cache/ms-playwright
```

**解决方案**:

```bash
mkdir -p ~/.cache/ms-playwright
chmod 755 ~/.cache/ms-playwright
```

## 不同系统安装命令

### Ubuntu 20.04/22.04

```bash
sudo apt-get update
sudo apt-get install -y python3-pip wkhtmltopdf
pip3 install playwright
python3 -m playwright install chromium
```

### CentOS 7/8

```bash
sudo yum install -y python3-pip wkhtmltopdf
pip3 install playwright
python3 -m playwright install chromium
```

### macOS

```bash
brew install wkhtmltopdf
pip3 install playwright
python3 -m playwright install chromium
```

## 相关文档

- [scripts/INSTALL_DEPENDENCIES.md](scripts/INSTALL_DEPENDENCIES.md) - 详细安装指南
- [scripts/check_dependencies.py](scripts/check_dependencies.py) - 环境检查脚本
- [scripts/test_screenshot_tools.py](scripts/test_screenshot_tools.py) - 工具测试脚本
- [requirements.txt](requirements.txt) - Python 包依赖
