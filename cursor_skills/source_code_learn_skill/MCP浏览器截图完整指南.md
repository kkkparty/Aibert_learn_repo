# 使用 Cursor MCP 浏览器自动截图 Mermaid 图表

## 📋 任务清单

### 当前状态

✅ **已完成**：
- Mermaid 代码已编写
- HTML 文件已生成（8 个）
- 输出目录已创建

⏳ **待执行**：
- 使用 Cursor MCP 浏览器批量截图

---

## 🎯 执行方案：在 Cursor 中新建对话

### 步骤 1：复制以下完整请求

```markdown
请使用 cursor-ide-browser 或 cursor-browser-extension MCP 工具，
帮我批量截图 8 个 Mermaid HTML 文件。

## 任务详情

**源目录**：`/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_html_test/`
**输出目录**：`/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_images/`

## 操作步骤（每个文件）：

1. 打开 HTML 文件（file:// 协议）
2. 等待页面完全加载
3. 等待 `.mermaid svg` 元素出现（确保 Mermaid 渲染完成）
4. 等待 1-2 秒让动画完成
5. 使用浏览器开发者工具：
   - 按 F12 打开开发者工具
   - 按 Ctrl+Shift+P 打开命令面板
   - 输入 "Capture node screenshot"
   - 点击页面中的 `.container` 元素
6. 保存截图为对应的 PNG 文件

## 需要截图的 8 个文件：

### 文件 1: 时序对比图
- **HTML**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_html_test/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-01-时序对比图.html`
- **PNG**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_images/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-01-时序对比图.png`

### 文件 2: 架构对比图
- **HTML**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_html_test/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-02-架构对比图.html`
- **PNG**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_images/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-02-架构对比图.png`

### 文件 3: 性能提升对比
- **HTML**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_html_test/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-03-性能提升对比.html`
- **PNG**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_images/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-03-性能提升对比.png`

### 文件 4: 通信钩子流程图
- **HTML**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_html_test/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-04-Mermaid-流程图.html`
- **PNG**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_images/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-04-Mermaid-流程图.png`

### 文件 5: 序列图
- **HTML**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_html_test/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-05-Mermaid-序列图.html`
- **PNG**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_images/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-05-Mermaid-序列图.png`

### 文件 6: 状态图
- **HTML**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_html_test/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-06-Mermaid-状态图.html`
- **PNG**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_images/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-06-Mermaid-状态图.png`

### 文件 7: 混合精度流程图
- **HTML**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_html_test/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-07-Mermaid-流程图.html`
- **PNG**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_images/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-07-Mermaid-流程图.png`

### 文件 8: 性能对比矩阵
- **HTML**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_html_test/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-08-Mermaid-类图用于对比.html`
- **PNG**: `/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_images/DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版-mermaid-08-Mermaid-类图用于对比.png`

## 截图要求

- 等待 Mermaid 完全渲染（svg 元素出现）
- 截取 `.container` 元素（包含标题和图表）
- 图片格式：PNG
- 视口大小：1200x800 或更大
- 背景：白色

## 预期结果

完成后应该有 8 个 PNG 文件在：
`/home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_images/`

请逐个处理并告知进度。完成后告知结果！
```

### 步骤 2：在 Cursor 中新建对话并粘贴

1. 点击 Cursor 左侧的"新建对话"按钮
2. 粘贴上面的完整请求
3. 发送

### 步骤 3：AI 会自动执行

AI 将使用 MCP 浏览器工具：
- 打开每个 HTML 文件
- 等待 Mermaid 渲染
- 截图保存

---

## 📝 验证脚本

截图完成后，运行此脚本验证：

```bash
#!/bin/bash
cd /home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_images

echo "=== 验证截图结果 ==="
echo ""

# 检查文件数量
count=$(ls -1 *.png 2>/dev/null | wc -l)
echo "✓ PNG 文件数量: $count / 8"

if [ $count -eq 8 ]; then
    echo "✅ 所有图片已生成！"
else
    echo "⚠️  还缺少 $((8 - count)) 个图片"
fi

echo ""
echo "=== 文件列表 ==="
ls -lh *.png 2>/dev/null

echo ""
echo "=== 下一步 ==="
echo "运行替换脚本："
echo "cd /home/aibert.liu/libra/code/ai_infra/torch/pytorch"
echo "python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/replace_mermaid_with_images.py \\"
echo "    'DDP原理与源码解读-第6章-通信钩子和优化机制-最终版.md' \\"
echo "    -i mermaid_images/ --dry-run"
```

---

## 🔄 完整流程总结

```
1. ✅ 编写 Mermaid 代码（已完成）
   ↓
2. ✅ 生成 HTML 文件（已完成，8 个文件）
   ↓
3. ⏳ MCP 浏览器截图（进行中）
   - 新建 Cursor 对话
   - 发送截图请求
   - AI 自动执行
   ↓
4. ⏳ 替换 Markdown（待执行）
   - 运行 replace_mermaid_with_images.py
   ↓
5. ✅ 最终文档（包含图片）
```

---

## 💡 提示

### 如果 MCP 不可用

备选方案：手动截图（每个文件 1-2 分钟，共 10-15 分钟）

```bash
# 1. 在文件管理器中打开
cd /home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_html_test

# 2. 双击打开任意 HTML 文件（会在浏览器中打开）

# 3. 按 F12 → Ctrl+Shift+P → 输入 "Capture node screenshot"

# 4. 点击页面中的图表区域（.container 元素）

# 5. 保存到 mermaid_images/ 目录

# 6. 重复 8 次
```

---

## ✅ 已就绪的文件

### HTML 文件（8 个）
```
✓ mermaid-01-时序对比图.html
✓ mermaid-02-架构对比图.html
✓ mermaid-03-性能提升对比.html
✓ mermaid-04-Mermaid-流程图.html
✓ mermaid-05-Mermaid-序列图.html
✓ mermaid-06-Mermaid-状态图.html
✓ mermaid-07-Mermaid-流程图.html
✓ mermaid-08-Mermaid-类图用于对比.html
```

### 输出目录
```
✓ /home/aibert.liu/libra/code/ai_infra/torch/pytorch/mermaid_images/
```

---

**现在请在 Cursor 中新建对话，粘贴上面的请求，让 AI 使用 MCP 工具完成截图！** 🚀
