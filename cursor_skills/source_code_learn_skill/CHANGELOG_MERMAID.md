# Mermaid 可视化功能更新日志

## 📅 更新时间：2026-02-09

## 🎉 新增功能

### 1. Mermaid 可视化工具链

新增三个工具脚本，支持将 Mermaid 图表转换为高质量图片：

#### 📄 `mermaid_to_html.py`
- **功能**：从 Markdown 提取 Mermaid 代码块，生成独立 HTML 文件
- **特性**：
  - 自动提取所有 Mermaid 代码块
  - 生成可在浏览器中直接预览的 HTML
  - 支持批量处理
  - 自动关联标题
  - 详细输出模式
- **使用**：
  ```bash
  python scripts/mermaid_to_html.py doc.md -o html_output/
  python scripts/mermaid_to_html.py docs/ -d -o html_output/  # 批量
  ```

#### 📷 `mermaid_to_image.py`
- **功能**：将 HTML 文件转换为图片（PNG）
- **特性**：
  - 支持 Playwright 自动截图
  - 提供手动截图指南（无 Playwright 时）
  - 智能等待 Mermaid 渲染完成
  - 只截取内容区域（去除边距）
- **使用**：
  ```bash
  # 自动截图（需要安装 Playwright）
  pip install playwright && playwright install chromium
  python scripts/mermaid_to_image.py html_output/ -o images/

  # 手动截图指南
  python scripts/mermaid_to_image.py html_output/ --manual
  ```

#### 🔄 `replace_mermaid_with_images.py`
- **功能**：自动替换 Markdown 中的 Mermaid 为图片引用
- **特性**：
  - 智能匹配图片文件
  - 可选保留原始代码在折叠区域
  - 自动备份原文件
  - 支持预览模式（dry-run）
  - 生成相对路径引用
- **使用**：
  ```bash
  # 替换并保留原代码
  python scripts/replace_mermaid_with_images.py doc.md -i images/

  # 预览模式
  python scripts/replace_mermaid_with_images.py doc.md -i images/ --dry-run

  # 不保留原代码
  python scripts/replace_mermaid_with_images.py doc.md -i images/ --no-keep-code
  ```

### 2. 完整可视化指南

新增 `MERMAID_VISUALIZATION_GUIDE.md`：
- ✅ Mermaid vs ASCII 对比
- ✅ 6 种 Mermaid 图表类型示例
- ✅ 样式定制指南
- ✅ 最佳实践
- ✅ 完整工作流程
- ✅ 实战示例
- ✅ 故障排除

### 3. 测试文档

创建 `DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版.md`：
- ✅ ASCII vs Mermaid 对比
- ✅ 8 个 Mermaid 实战示例
- ✅ 完整工具链演示

### 4. 更新文档

#### 更新 `README.md`
- 新增第 6 节：Mermaid 可视化工具链
- 添加 3 个新工具的使用说明
- 添加使用场景和详细指南链接

#### 更新 `.cursorrules`
- 添加 ASCII vs Mermaid 流程图对比
- 添加 Mermaid 时序图示例
- 添加 Mermaid Gantt 图示例
- 新增"ASCII vs Mermaid 选择指南"章节
- 添加使用原则和工具链说明

---

## 🎨 支持的 Mermaid 图表类型

### 1. 流程图（Flowchart）
- 用途：算法逻辑、执行流程
- 语法：`flowchart TD/LR`
- 示例：DDP 梯度同步流程

### 2. 时序图（Sequence Diagram）
- 用途：时间维度交互、函数调用
- 语法：`sequenceDiagram`
- 示例：DDP 通信钩子流程

### 3. 状态图（State Diagram）
- 用途：状态转换、生命周期
- 语法：`stateDiagram-v2`
- 示例：Reducer 状态机

### 4. 类图（Class Diagram）
- 用途：类关系、继承结构
- 语法：`classDiagram`
- 示例：通信钩子类对比

### 5. 甘特图（Gantt Chart）
- 用途：时间线、性能对比
- 语法：`gantt`
- 示例：Static Graph 优化效果

### 6. Git 图（Git Graph）
- 用途：版本分支、数据流
- 语法：`gitgraph`
- 示例：梯度流向

---

## 📊 测试结果

### 测试文件
```
DDP原理与源码解读-第6章-通信钩子和优化机制-可视化增强版.md
```

### 提取结果
```
✓ 成功提取 8 个 Mermaid 代码块
✓ 生成 8 个 HTML 文件
✓ 文件命名自动关联标题
✓ 所有文件可在浏览器中正常预览
```

### 生成的 HTML 文件
1. `DDP原理与源码解读-第6章-...-mermaid-01-时序对比图.html`
2. `DDP原理与源码解读-第6章-...-mermaid-02-架构对比图.html`
3. `DDP原理与源码解读-第6章-...-mermaid-03-性能提升对比.html`
4. `DDP原理与源码解读-第6章-...-mermaid-04-Mermaid-流程图.html`
5. `DDP原理与源码解读-第6章-...-mermaid-05-Mermaid-序列图.html`
6. `DDP原理与源码解读-第6章-...-mermaid-06-Mermaid-状态图.html`
7. `DDP原理与源码解读-第6章-...-mermaid-07-Mermaid-流程图.html`
8. `DDP原理与源码解读-第6章-...-mermaid-08-Mermaid-类图用于对比.html`

---

## 🚀 完整工作流程

### 方案 A：保留 Mermaid 代码（推荐）

```bash
# 步骤 1：在 Markdown 中编写 Mermaid
vim your_doc.md

# 步骤 2：生成 HTML
python scripts/mermaid_to_html.py your_doc.md -o html_output/

# 步骤 3：在浏览器中预览（可选）
open html_output/*.html

# 步骤 4：转换为图片（可选）
python scripts/mermaid_to_image.py html_output/ -o images/

# 完成！Mermaid 代码保留在 Markdown 中
# GitHub/GitLab 会自动渲染 Mermaid
```

### 方案 B：替换为图片（PDF 导出）

```bash
# 步骤 1-4：同方案 A

# 步骤 5：替换 Markdown
python scripts/replace_mermaid_with_images.py your_doc.md -i images/

# 完成！Markdown 中使用图片引用
# 适合导出 PDF 或不支持 Mermaid 的平台
```

---

## 💡 最佳实践

### 何时使用 Mermaid

✅ **推荐使用 Mermaid**：
- 复杂流程（>5 步）
- 状态机
- 时序图（多个参与者）
- 类图/架构图
- 性能对比（Gantt 图）
- 需要高质量输出

✅ **继续使用 ASCII**：
- 简单流程（<5 步）
- 快速草图
- 纯文本环境
- 兼容性优先

### 推荐工作流

1. **初稿阶段**：使用 ASCII（快速迭代）
2. **重要章节**：使用 Mermaid（高质量）
3. **最终发布**：
   - GitHub/GitLab：保留 Mermaid（自动渲染）
   - PDF 导出：转换为图片
   - 兼容性需求：转换为图片

---

## 📚 文档结构

```
source_code_learn_skill/
├── MERMAID_VISUALIZATION_GUIDE.md   # 完整使用指南
├── CHANGELOG_MERMAID.md             # 本文档
├── README.md                         # 已更新
├── .cursorrules                      # 已更新
│
├── scripts/
│   ├── mermaid_to_html.py           # 新增
│   ├── mermaid_to_image.py          # 新增
│   └── replace_mermaid_with_images.py  # 新增
│
└── examples/  # 测试示例
    └── DDP原理与源码解读-第6章-...-可视化增强版.md
```

---

## 🔧 依赖要求

### 必需
- Python 3.6+
- 标准库（无额外依赖）

### 可选（用于自动截图）
```bash
pip install playwright
playwright install chromium
```

### 备选方案
- 手动截图（浏览器开发工具）
- 在线工具（https://mermaid.live/）
- Mermaid CLI（npm 安装）

---

## 📖 参考资源

- [Mermaid 官方文档](https://mermaid.js.org/)
- [Mermaid Live Editor](https://mermaid.live/)
- [Playwright 文档](https://playwright.dev/)
- [MERMAID_VISUALIZATION_GUIDE.md](MERMAID_VISUALIZATION_GUIDE.md)

---

## 🎯 下一步计划

### 短期
- [ ] 添加更多 Mermaid 主题配置
- [ ] 支持 SVG 输出（更高质量）
- [ ] 添加 Mermaid 语法检查

### 长期
- [ ] 集成 GitHub Actions（自动转换）
- [ ] 支持自定义 CSS 样式
- [ ] 添加 Mermaid 代码片段库

---

## ✨ 总结

### 新增文件
- ✅ 3 个工具脚本（约 500 行代码）
- ✅ 1 个完整指南（约 600 行文档）
- ✅ 1 个测试文档（约 450 行）
- ✅ 1 个更新日志（本文档）

### 更新文件
- ✅ README.md（新增第 6 节）
- ✅ .cursorrules（新增 Mermaid 支持）

### 功能完整度
- ✅ 工具链完整（提取→生成→转换→替换）
- ✅ 文档完善（指南+示例+更新日志）
- ✅ 测试验证（8 个 Mermaid 图表成功提取）

---

**版本**：v1.0-mermaid
**状态**：✅ 已完成并测试
**位置**：`/home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/`

---

**Happy Visualizing! 🎨**
