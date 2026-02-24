# MCP 配置生效指南

## 问题诊断

### webshot-mcp 连接失败

从日志看，webshot-mcp 尝试连接远程服务器 `mcp.api-inference.modelscope.net:443` 但超时。这说明：
- webshot-mcp 可能是一个远程服务，需要网络连接
- 如果网络不通或服务器不可用，webshot-mcp 无法工作

### Puppeteer MCP 配置生效

Puppeteer MCP 是本地工具，不需要网络连接，更适合本地 HTML 截图。

## 正确的 Puppeteer MCP 配置

### 1. 包名

**正确的包名**: `@modelcontextprotocol/server-puppeteer`

**错误的包名**: `puppeteer-mcp-screenshot`（这个包可能不存在）

### 2. MCP 配置文件位置

**Linux/Mac**: `~/.cursor/mcp.json`

**Windows**: `%APPDATA%\Cursor\mcp.json`

### 3. 配置内容

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ]
    }
  }
}
```

### 4. 如果已有其他 MCP 配置

如果 `~/.cursor/mcp.json` 已存在（比如已有 `arxiv-paper-mcp`），需要**合并配置**，不要覆盖：

```json
{
  "mcpServers": {
    "arxiv-paper-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "@langgpt/arxiv-paper-mcp@latest"
      ]
    },
    "puppeteer": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ]
    }
  }
}
```

## 配置生效步骤

### 方法 1: 使用安装脚本（推荐）

```bash
# 运行安装脚本（会自动合并配置）
bash scripts/install_puppeteer_mcp.sh
```

### 方法 2: 手动配置

1. **备份现有配置**（如果存在）:
   ```bash
   cp ~/.cursor/mcp.json ~/.cursor/mcp.json.backup
   ```

2. **编辑配置文件**:
   ```bash
   nano ~/.cursor/mcp.json
   # 或
   vim ~/.cursor/mcp.json
   ```

3. **添加 puppeteer 配置**（保留现有配置）:
   ```json
   {
     "mcpServers": {
       "existing-server": { ... },
       "puppeteer": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
       }
     }
   }
   ```

4. **验证 JSON 格式**:
   ```bash
   python3 -m json.tool ~/.cursor/mcp.json > /dev/null && echo "✓ JSON 格式正确" || echo "✗ JSON 格式错误"
   ```

5. **重启 Cursor IDE**（必须！）

## 验证配置是否生效

### 1. 检查配置文件

```bash
# 查看配置
cat ~/.cursor/mcp.json | python3 -m json.tool

# 检查 puppeteer 是否配置
grep -q "puppeteer" ~/.cursor/mcp.json && echo "✓ puppeteer 已配置" || echo "✗ puppeteer 未配置"
```

### 2. 在 Cursor 中测试

重启 Cursor 后，在对话中询问：
```
请列出可用的 MCP 工具
```

应该能看到 `puppeteer` 相关的工具，比如：
- `puppeteer.navigate` - 导航到 URL
- `puppeteer.screenshot` - 截图
- `puppeteer.evaluate` - 执行 JavaScript
- 等等

### 3. 测试截图功能

在 Cursor 对话中：
```
请使用 puppeteer.screenshot 工具截图：
- url: file:///home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/test_mcp_html/test_mermaid.html
- outputPath: /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/test_mcp_images/test_mermaid.png
```

## Puppeteer MCP 工具说明

### 主要工具

1. **puppeteer.navigate** - 导航到 URL
   ```json
   {
     "url": "file:///path/to/file.html"
   }
   ```

2. **puppeteer.screenshot** - 截图
   ```json
   {
     "url": "file:///path/to/file.html",
     "outputPath": "/path/to/output.png",
     "width": 1920,
     "height": 1080,
     "fullPage": false
   }
   ```

3. **puppeteer.evaluate** - 执行 JavaScript
   ```json
   {
     "code": "document.querySelector('.mermaid').innerHTML"
   }
   ```

### 使用示例

```python
# 在 Cursor 对话中
请使用 puppeteer.screenshot 工具截图本地 HTML 文件：
- url: file:///home/user/test.html
- outputPath: /home/user/output.png
- width: 1920
- height: 1080
- fullPage: false
```

## 故障排除

### 问题 1: 配置后工具仍不可用

**解决方案**:
1. 确认已重启 Cursor IDE（必须！）
2. 检查 JSON 格式是否正确
3. 检查包名是否正确：`@modelcontextprotocol/server-puppeteer`
4. 查看 Cursor 日志（Help > Show Logs）

### 问题 2: npx 命令失败

**解决方案**:
1. 检查 Node.js 和 npm 是否安装：
   ```bash
   node --version
   npm --version
   ```
2. 手动测试包：
   ```bash
   npx -y @modelcontextprotocol/server-puppeteer --help
   ```

### 问题 3: 截图失败

**解决方案**:
1. 确认 HTML 文件路径正确（使用绝对路径）
2. 确认输出目录有写入权限
3. 检查 Puppeteer 浏览器是否正确安装（首次运行会自动下载）

### 问题 4: 配置被覆盖

**解决方案**:
1. 使用安装脚本（会自动合并配置）
2. 手动编辑时，确保保留所有现有配置
3. 备份配置文件后再修改

## 与 webshot-mcp 对比

| 特性 | webshot-mcp | Puppeteer MCP |
|------|-------------|---------------|
| 连接方式 | 远程服务（需要网络） | 本地工具（无需网络） |
| 安装方式 | 配置远程服务器 | npx 本地运行 |
| 可靠性 | 依赖网络和服务器 | 本地运行，更可靠 |
| 功能 | 基础截图 | 功能丰富（导航、截图、执行 JS 等） |
| 推荐场景 | 网络稳定时 | 本地 HTML 截图（推荐） |

## 参考资源

- Puppeteer MCP: https://mcpbro.com/cn/mcp/puppeteer-mcp
- MCP 协议: https://modelcontextprotocol.io/
- Puppeteer 文档: https://pptr.dev/
