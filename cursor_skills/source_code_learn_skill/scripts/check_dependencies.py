#!/usr/bin/env python3
"""
检查 HTML 截图功能所需的环境依赖
"""

import sys
import subprocess
import shutil
from pathlib import Path


def check_python_package(package_name):
    """检查 Python 包是否安装"""
    try:
        __import__(package_name)
        return True, "已安装"
    except ImportError:
        return False, "未安装"


def check_system_command(cmd):
    """检查系统命令是否可用"""
    path = shutil.which(cmd)
    if path:
        try:
            result = subprocess.run([cmd, '--version'],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)
            version = result.stdout.strip().split('\n')[0] if result.stdout else "未知版本"
            return True, version
        except:
            return True, "可用（无法获取版本）"
    return False, "未安装"


def check_playwright_browser():
    """检查 Playwright 浏览器是否安装"""
    home = Path.home()
    browser_paths = [
        home / ".cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell",
        home / ".cache/ms-playwright/chromium-*/chrome-linux/chrome",
    ]

    import glob
    for pattern in browser_paths:
        matches = glob.glob(str(pattern))
        if matches:
            return True, f"已安装 ({matches[0]})"

    return False, "未安装"


def main():
    print("=" * 60)
    print("  环境依赖检查")
    print("=" * 60)
    print()

    all_ok = True

    # 1. 检查 Python 版本
    print("[1/5] Python 版本")
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 6:
        print("  ✓ 版本符合要求 (>= 3.6)")
    else:
        print("  ✗ 版本不符合要求 (需要 >= 3.6)")
        all_ok = False
    print()

    # 2. 检查 Playwright Python 包
    print("[2/5] Playwright Python 包")
    ok, msg = check_python_package('playwright')
    if ok:
        print(f"  ✓ {msg}")
    else:
        print(f"  ✗ {msg}")
        print("  安装: pip install playwright")
        all_ok = False
    print()

    # 3. 检查 Playwright 浏览器
    print("[3/5] Playwright Chromium 浏览器")
    ok, msg = check_playwright_browser()
    if ok:
        print(f"  ✓ {msg}")
    else:
        print(f"  ✗ {msg}")
        print("  安装: python -m playwright install chromium")
        all_ok = False
    print()

    # 4. 检查 wkhtmltoimage
    print("[4/5] wkhtmltoimage")
    ok, msg = check_system_command('wkhtmltoimage')
    if ok:
        print(f"  ✓ {msg}")
    else:
        print(f"  ✗ {msg}")
        print("  安装: sudo apt-get install wkhtmltopdf")
        all_ok = False
    print()

    # 5. 检查 wkhtmltopdf (可选)
    print("[5/5] wkhtmltopdf (可选，用于 PDF 导出)")
    ok, msg = check_system_command('wkhtmltopdf')
    if ok:
        print(f"  ✓ {msg}")
    else:
        print(f"  ⚠️  {msg} (可选)")
    print()

    # 总结
    print("=" * 60)
    if all_ok:
        print("  ✓ 所有必需依赖已安装")
        print("=" * 60)
        return 0
    else:
        print("  ⚠️  部分依赖缺失")
        print("=" * 60)
        print()
        print("安装缺失的依赖:")
        print("  运行: bash scripts/install_dependencies.sh")
        print("  或查看: scripts/INSTALL_DEPENDENCIES.md")
        return 1


if __name__ == '__main__':
    sys.exit(main())
