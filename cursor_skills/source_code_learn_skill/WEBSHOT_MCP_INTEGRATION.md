# webshot-mcp 集成完成

## 已完成的工作

### 1. 创建 webshot-mcp 专用脚本

- **`scripts/screenshot_with_webshot_mcp.py`** - 使用 webshot-mcp 的专用截图脚本
- **`scripts/install_webshot_mcp.sh`** - 一键安装和配置脚本
- **`scripts/WEBSHOT_MCP_SETUP.md`** - 详细配置指南

### 2. 更新现有脚本

- **`scripts/html_to_image_mcp.py`** - 已更新为使用 webshot-mcp
- **`README.md`** - 已更新依赖说明，优先推荐 webshot-mcp

## 快速开始

### 安装 webshot-mcp

```bash
# 一键安装和配置
bash scripts/install_webshot_mcp.sh

# 重启 Cursor IDE 后即可使用
```

### 使用 webshot-mcp 截图

**方法 1: 使用专用脚本**

```bash
# 单个文件
python scripts/screenshot_with_webshot_mcp.py test.html -o output.png

# 批量处理
python scripts/screenshot_with_webshot_mcp.py html_dir/ -o images/ -d
```

**方法 2: 在 Cursor 对话中直接使用**

在 Cursor 对话中，直接请求 AI 使用 webshot-mcp：

```
请使用 webshot-mcp MCP 工具，帮我截图以下 HTML 文件：

HTML 文件: file:///path/to/file.html
输出文件: /path/to/output.png
```

AI 会自动调用 webshot-mcp 工具完成截图。

## 配置说明

### MCP 配置文件

配置文件位置：`~/.cursor/mcp.json`

配置内容：
```json
{
  "mcpServers": {
    "webshot": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-webshot"
      ]
    }
  }
}
```

安装脚本会自动创建此配置。

## 优势对比

| 特性 | webshot-mcp | wkhtmltoimage | Playwright |
|-----|------------|---------------|------------|
| **MCP 集成** | ✅ 原生支持 | ❌ 不支持 | ❌ 不支持 |
| **AI 直接调用** | ✅ 是 | ❌ 否 | ❌ 否 |
| **配置复杂度** | ⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 复杂 |
| **截图质量** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **动态内容支持** | ✅ 是 | ⚠️ 有限 | ✅ 是 |

## 使用示例

### 示例 1: 单个文件截图

```bash
python scripts/screenshot_with_webshot_mcp.py \
    test_mcp_html/test_mermaid.html \
    -o test_mcp_images/test_mermaid_webshot.png
```

然后在 Cursor 对话中复制生成的指令并发送给 AI。

### 示例 2: 批量截图

```bash
python scripts/screenshot_with_webshot_mcp.py \
    html_output/ \
    -o images/ \
    -d -v
```

### 示例 3: 在 Cursor 对话中直接使用

```
请使用 webshot-mcp MCP 工具，帮我批量截图以下 HTML 文件：

HTML 文件: file:///home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/test_mcp_html/test_mermaid.html
输出文件: /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/test_mcp_images/test_mermaid_webshot.png

请开始截图。
```

## 故障排除

### 问题 1: webshot-mcp 未安装

**解决**：
```bash
bash scripts/install_webshot_mcp.sh
```

### 问题 2: MCP 配置未生效

**解决**：
1. 检查配置文件：`cat ~/.cursor/mcp.json`
2. 重启 Cursor IDE
3. 验证配置格式是否正确（JSON）

### 问题 3: Node.js 未安装

**解决**：
```bash
# Ubuntu/Debian
sudo apt-get install nodejs npm

# 验证
node --version
npm --version
```

## 相关文档

- [scripts/WEBSHOT_MCP_SETUP.md](scripts/WEBSHOT_MCP_SETUP.md) - 详细配置指南
- [scripts/screenshot_with_webshot_mcp.py](scripts/screenshot_with_webshot_mcp.py) - 使用脚本
- [README.md](README.md) - 主文档

---

**webshot-mcp 已集成完成，可以开始使用！** 🚀
