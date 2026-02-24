# 安装 HTML 截图功能依赖

## 快速安装

```bash
# 一键安装所有依赖
bash scripts/install_dependencies.sh

# 或手动安装（见下方）
```

## 依赖列表

### 必需依赖

1. **Python 3.6+**
2. **Playwright** (Python 包)
3. **Playwright Chromium 浏览器**
4. **wkhtmltopdf** (包含 wkhtmltoimage)

### 可选依赖

- **pandoc** (用于 PDF 导出)

## 详细安装步骤

### 1. Python 依赖

```bash
# 安装 Playwright Python 包
pip install playwright

# 或使用 pip3
pip3 install playwright
```

### 2. Playwright 浏览器

```bash
# 安装 Chromium 浏览器
python -m playwright install chromium

# 如果下载失败（网络问题），可以：
# 1. 设置代理
export HTTPS_PROXY=http://proxy:port
export HTTP_PROXY=http://proxy:port
python -m playwright install chromium

# 2. 或使用离线安装包
# 下载地址: https://playwright.dev/docs/browsers
```

**常见问题**：

- **下载失败**: 检查网络连接，或使用代理
- **权限问题**: 确保有写入 `~/.cache/ms-playwright` 的权限
- **磁盘空间**: 需要约 200MB 空间

### 3. wkhtmltopdf

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install wkhtmltopdf
```

#### CentOS/RHEL

```bash
sudo yum install wkhtmltopdf
# 或
sudo dnf install wkhtmltopdf
```

#### macOS

```bash
brew install wkhtmltopdf
```

#### 从源码编译

如果包管理器没有，可以从源码编译：

```bash
# 下载源码
wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6/wkhtmltox_0.12.6-1.focal_amd64.deb

# 安装
sudo dpkg -i wkhtmltox_0.12.6-1.focal_amd64.deb
sudo apt-get install -f  # 修复依赖
```

### 4. 验证安装

```bash
# 检查所有依赖
python scripts/check_dependencies.py

# 测试截图功能
python scripts/test_screenshot_tools.py
```

## 环境检查脚本

```bash
# 运行环境检查
python scripts/check_dependencies.py
```

输出示例：

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

## 故障排除

### 问题 1: Playwright 浏览器下载失败

**错误信息**:
```
Error: Failed to download Chrome for Testing
Error: Download failure, code=1
```

**解决方案**:

1. **检查网络连接**
   ```bash
   ping cdn.playwright.dev
   ```

2. **使用代理**
   ```bash
   export HTTPS_PROXY=http://proxy:port
   export HTTP_PROXY=http://proxy:port
   python -m playwright install chromium
   ```

3. **手动下载**
   - 访问 https://playwright.dev/docs/browsers
   - 下载对应版本的浏览器
   - 解压到 `~/.cache/ms-playwright/`

4. **使用国内镜像**（如果可用）
   ```bash
   export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
   python -m playwright install chromium
   ```

### 问题 2: wkhtmltoimage 命令未找到

**错误信息**:
```
wkhtmltoimage: command not found
```

**解决方案**:

1. **检查安装**
   ```bash
   which wkhtmltoimage
   ```

2. **重新安装**
   ```bash
   sudo apt-get install --reinstall wkhtmltopdf
   ```

3. **添加到 PATH**（如果需要）
   ```bash
   export PATH=$PATH:/usr/bin
   ```

### 问题 3: 权限问题

**错误信息**:
```
Permission denied: ~/.cache/ms-playwright
```

**解决方案**:

```bash
# 创建目录并设置权限
mkdir -p ~/.cache/ms-playwright
chmod 755 ~/.cache/ms-playwright
```

### 问题 4: 磁盘空间不足

**错误信息**:
```
No space left on device
```

**解决方案**:

```bash
# 检查磁盘空间
df -h

# 清理缓存
rm -rf ~/.cache/ms-playwright/*

# 重新安装
python -m playwright install chromium
```

## 不同系统的安装命令

### Ubuntu 20.04/22.04

```bash
# 更新包列表
sudo apt-get update

# 安装依赖
sudo apt-get install -y \
    python3-pip \
    wkhtmltopdf \
    xvfb \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2

# 安装 Python 包
pip3 install playwright

# 安装浏览器
python3 -m playwright install chromium
```

### CentOS 7/8

```bash
# 安装依赖
sudo yum install -y \
    python3-pip \
    wkhtmltopdf \
    xorg-x11-server-Xvfb \
    nss \
    atk \
    cups-libs \
    libdrm \
    libxkbcommon \
    libXcomposite \
    libXdamage \
    libXfixes \
    libXrandr \
    mesa-libgbm \
    alsa-lib

# 安装 Python 包
pip3 install playwright

# 安装浏览器
python3 -m playwright install chromium
```

### macOS

```bash
# 安装 Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install wkhtmltopdf

# 安装 Python 包
pip3 install playwright

# 安装浏览器
python3 -m playwright install chromium
```

## 验证安装

安装完成后，运行测试：

```bash
# 检查依赖
python scripts/check_dependencies.py

# 测试截图
python scripts/test_screenshot_tools.py
```

## 相关文档

- [HTML_TO_IMAGE_MCP_USAGE.md](HTML_TO_IMAGE_MCP_USAGE.md) - 使用指南
- [README.md](../README.md) - 主文档
