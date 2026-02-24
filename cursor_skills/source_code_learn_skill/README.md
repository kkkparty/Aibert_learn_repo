# 源码学习 Skill - Source Code Learning Skill

## 📖 简介

这是一个系统化的源码阅读和文档生成 Skill，帮助你高效地阅读、理解和讲解源码。

**适用场景**：
- 深入学习开源项目源码
- 编写技术文档和教程
- 准备技术分享和面试
- 团队知识传承

**核心特点**：
- ✅ 原理先行：先讲为什么，再看代码
- ✅ 图示优先：丰富的可视化图表
- ✅ 深入浅出：类比→概念→实现
- ✅ 自动化工具：提供实用脚本

---

## 🚀 快速开始

### 0. 安装环境依赖（首次使用）

**HTML 截图功能**：

使用 **Cursor Browser Extension** 进行截图，无需安装额外依赖。

**使用步骤**：
1. 在浏览器中安装 Cursor Browser Extension
2. 打开需要截图的 HTML 页面
3. 点击浏览器工具栏中的 Cursor 扩展图标
4. 选择截图功能（全页面、可见区域或自定义区域）
5. 截图会自动保存或复制到剪贴板

**优势**：
- ✅ 无需安装额外工具
- ✅ 支持全页面、可见区域、自定义区域截图
- ✅ 高质量渲染
- ✅ 简单易用

### 1. 安装 Skill

将此 Skill 链接到你的项目：

```bash
# 方法 1：符号链接（推荐）
ln -s /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/.cursorrules /path/to/your/project/.cursorrules

# 方法 2：复制文件
cp /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/.cursorrules /path/to/your/project/

# 方法 3：在项目根目录创建 .cursorrules 并包含此 Skill
echo 'include:/home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/.cursorrules' > /path/to/your/project/.cursorrules
```

### 2. 使用脚本工具

所有脚本工具都在 `scripts/` 目录下，支持独立运行。

**添加到 PATH**（可选）：

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export PATH="$PATH:/home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts"

# 使配置生效
source ~/.bashrc
```

### 3. 开始使用

在你的项目中，与 Cursor AI 对话时，它会自动遵循此 Skill 的规范。

**示例对话**：
```
你: @your_code.py 请帮我讲解这个函数的实现原理

AI: [会按照"原理先行"的方式，先讲解为什么需要、核心思想，然后展示源码]
```

---

## 🛠️ 脚本工具详解

### 1. 源码分析工具 `analyze_code.py`

**功能**：分析 Python 源码结构

```bash
# 分析单个文件
python scripts/analyze_code.py your_file.py

# 输出到文件
python scripts/analyze_code.py your_file.py -o analysis_report.md

# 示例输出：
# - 类/函数定义
# - 文档字符串
# - 导入依赖
# - 代码统计
```

**使用场景**：
- 快速了解源文件结构
- 提取函数签名和文档
- 生成源码概览文档

**实战示例**：
```bash
# 分析 PyTorch DDP 源码
cd /path/to/pytorch
python /path/to/scripts/analyze_code.py torch/nn/parallel/distributed.py -o DDP_structure.md
```

### 2. 目录生成工具 `generate_toc.py`

**功能**：自动生成 Markdown 文档目录

```bash
# 为单个文件生成目录（输出到终端）
python scripts/generate_toc.py your_doc.md

# 直接更新文件
python scripts/generate_toc.py your_doc.md -i

# 批量处理目录
python scripts/generate_toc.py docs/ -d -i

# 自定义最大层级
python scripts/generate_toc.py your_doc.md -l 4 -i
```

**使用场景**：
- 为长文档生成导航目录
- 自动更新目录（当标题变化时）
- 批量处理多个文档

**目录格式**：
```markdown
<!-- TOC START -->
## 目录

- [第一章](#第一章)
  - [1.1 节](#11-节)
  - [1.2 节](#12-节)
- [第二章](#第二章)
<!-- TOC END -->
```

### 3. 格式检查工具 `check_format.py`

**功能**：检查文档是否符合规范

```bash
# 检查单个文件
python scripts/check_format.py your_doc.md

# 批量检查
python scripts/check_format.py docs/ -d

# 检查报告示例：
# ✓ 统计信息
# ⚠️ 警告：面试题数量不足
# ❌ 问题：代码块过大
```

**检查项**：
- ✅ 代码引用格式（是否有行号）
- ✅ 图示数量
- ✅ 面试题数量（建议 ≥ 8道）
- ✅ 章节结构（是否有目标、总结）
- ✅ 特殊字符（emoji）
- ✅ 代码块大小（建议 ≤ 100行）

**使用场景**：
- 文档质量检查
- 确保符合写作规范
- CI/CD 集成

### 4. 代码引用验证工具 `validate_code_refs.py`

**功能**：验证文档中的代码引用是否有效

```bash
# 验证单个文档
python scripts/validate_code_refs.py your_doc.md -c /path/to/code

# 批量验证
python scripts/validate_code_refs.py docs/ -d -c /path/to/code

# 检查内容：
# - 文件路径是否存在
# - 行号是否越界
# - 引用的代码是否匹配（检测代码变更）
```

**使用场景**：
- 代码更新后验证文档
- 确保文档引用准确
- 防止失效的代码引用

**代码引用格式**：
````markdown
```startLine:endLine:path/to/file.py
# 实际代码内容
```
````

### 5. 依赖分析工具 `find_dependencies.py`

**功能**：分析函数调用关系

```bash
# 分析单个文件的依赖
python scripts/find_dependencies.py your_file.py

# 生成调用图
python scripts/find_dependencies.py your_file.py --graph call_graph.dot

# 查找特定函数的调用链
python scripts/find_dependencies.py your_file.py --function my_function
```

**使用场景**：
- 理解代码执行流程
- 找出函数依赖关系
- 生成调用图文档

### 6. Mermaid 可视化工具链 🎨 **新增**

**功能**：增强文档可视化效果，使用 Mermaid 图表替代 ASCII 艺术图

#### 6.1 Mermaid to HTML (`mermaid_to_html.py`)

```bash
# 从 Markdown 提取 Mermaid 并生成 HTML
python scripts/mermaid_to_html.py your_doc.md -o html_output/

# 批量处理
python scripts/mermaid_to_html.py docs/ -d -o html_output/
```

#### 6.2 HTML to Image - 使用 Cursor Browser Extension

**使用 Cursor Browser Extension 截图**：

```bash
# 1. 生成 HTML 文件（已由 mermaid_to_html.py 完成）
python scripts/mermaid_to_html.py your_doc.md -o html_output/

# 2. 在浏览器中打开 HTML 文件
# 使用本地服务器或直接打开文件
python -m http.server 8000
# 然后在浏览器中访问 http://localhost:8000/html_output/your_file.html

# 3. 使用 Cursor Browser Extension 截图
# - 点击浏览器工具栏中的 Cursor 扩展图标
# - 选择截图功能（全页面、可见区域或自定义区域）
# - 保存截图到 images/ 目录
```

**批量截图流程**：
1. 使用脚本生成所有 HTML 文件
2. 在浏览器中逐个打开 HTML 文件
3. 使用 Cursor Browser Extension 进行截图
4. 将截图保存到统一的 `images/` 目录

**优势**：
- ✅ 无需安装额外工具（Playwright、wkhtmltoimage 等）
- ✅ 高质量渲染，与浏览器显示一致
- ✅ 支持全页面、可见区域、自定义区域
- ✅ 简单直观的操作界面

#### 6.3 自动替换 (`replace_mermaid_with_images.py`)

```bash
# 替换 Markdown 中的 Mermaid 为图片
python scripts/replace_mermaid_with_images.py your_doc.md -i images/

# 预览模式
python scripts/replace_mermaid_with_images.py your_doc.md -i images/ --dry-run
```

#### 6.4 全自动流水线 (`mermaid_full_pipeline.py`) ⚡ **推荐**

**功能**：一键完成 Mermaid → HTML → 图片 → 替换 → PDF 全流程

```bash
# 完整流水线（推荐）
python scripts/mermaid_full_pipeline.py your_document.md -o output/

# 只生成 PDF（不处理 Mermaid）
python scripts/mermaid_full_pipeline.py your_document.md --pdf-only

# 详细输出
python scripts/mermaid_full_pipeline.py your_document.md -o output/ -v
```

**特点**：
- ✅ **半自动流程**：脚本生成 HTML，使用 Cursor Browser Extension 截图
- ✅ **高质量渲染**：与浏览器显示完全一致
- ✅ **支持 PDF 导出**：自动生成 PDF 文档
- ✅ **保留原始代码**：Mermaid 源码保留在折叠区域

**输出结构**：
```
output/
├── html/          # HTML 中间文件
├── images/        # PNG 图片文件
├── document.md    # 更新后的 Markdown（含图片引用）
└── document.pdf   # 最终 PDF 文档
```

**依赖**：
- `python markdown`（已安装）
- `pandoc`（可选，用于 PDF 生成）
- **Cursor Browser Extension**（浏览器扩展，用于截图）

**安装依赖**：
```bash
# 安装 pandoc（可选，仅用于 PDF 生成）
# Ubuntu/Debian
sudo apt-get install pandoc

# macOS
brew install pandoc
```

**使用场景**：
- 复杂流程图、状态机
- 时序图、类图
- 高质量文档输出
- PDF 导出需求
- **批量处理多个文档**

**详细指南**：查看 [MERMAID_VISUALIZATION_GUIDE.md](MERMAID_VISUALIZATION_GUIDE.md)

---

## 📝 文档模板

所有模板文件在 `templates/` 目录下：

### 1. 概念讲解模板 `concept_template.md`

用于讲解核心概念（原理层）。

**结构**：
- 为什么需要？
- 核心原理
- 概念性代码
- 类比

### 2. 源码讲解模板 `source_code_template.md`

用于讲解源码实现（实现层）。

**结构**：
- 代码位置
- 引导（重点关注什么）
- 源码展示（带行号）
- 逐行解析
- 执行流程图
- 关键点总结

### 3. 章节模板 `chapter_template.md`

完整章节的模板。

**结构**：
- 本章目标
- 原理回顾
- 源码解读
- 实战示例
- 面试题
- 本章总结

### 4. 图示模板 `diagrams.md`

常用图示的模板和示例。

**包含**：
- 流程图
- 时序图
- 架构图
- 数据流图
- 对比图
- 状态机图

---

## 🎨 使用示例

### 示例 1：学习 PyTorch DDP

```bash
# 1. 创建项目目录
mkdir -p ~/projects/pytorch-ddp-learning
cd ~/projects/pytorch-ddp-learning

# 2. 链接 Skill
ln -s /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/.cursorrules .cursorrules

# 3. 分析 DDP 源码
python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/analyze_code.py \
    /path/to/pytorch/torch/nn/parallel/distributed.py \
    -o DDP_analysis.md

# 4. 在 Cursor 中与 AI 对话
# "请帮我讲解 DDP 的初始化流程，遵循原理先行的方式"
```

### 示例 2：编写技术文档

```bash
# 1. 使用模板创建文档
cp /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/templates/chapter_template.md \
    第1章-概述.md

# 2. 编写内容（在 Cursor 中，AI 会遵循规范）

# 3. 生成目录
python scripts/generate_toc.py 第1章-概述.md -i

# 4. 检查格式
python scripts/check_format.py 第1章-概述.md

# 5. 验证代码引用
python scripts/validate_code_refs.py 第1章-概述.md -c /path/to/source
```

### 示例 3：批量处理文档

```bash
# 为所有章节生成目录
python scripts/generate_toc.py docs/ -d -i -p "第*章*.md"

# 检查所有文档格式
python scripts/check_format.py docs/ -d

# 验证所有代码引用
python scripts/validate_code_refs.py docs/ -d -c /path/to/source
```

---

## 📐 核心原则

### 1. 讲解顺序：原理先行

**禁止**：直接展示大段源码
**正确**：先讲为什么→怎么做→再看代码

```
第 0 层：基础概念（无代码）
   ↓
第 1 层：核心原理（概念代码）
   ↓
第 2 层：源码实现（真实代码+行号）
   ↓
第 3 层：实战应用（示例+面试题）
```

### 2. 图示优先

**必须使用图示的场景**：
- 流程图：执行流程
- 时序图：时间维度的交互
- 架构图：模块关系
- 数据流图：数据传递
- 对比图：优化前后对比
- 状态机图：状态转换

### 3. 深入浅出

**三层讲解法**：
- 类比层：生活中的例子
- 概念层：伪代码/概念代码
- 实现层：真实源码

---

## 🎯 质量标准

### 文档完整性检查清单

- [ ] 每个核心概念都有"为什么需要"
- [ ] 每个原理都有图示说明
- [ ] 每段源码都有行号标注
- [ ] 每个章节都有面试题（8-12道）
- [ ] 有生活类比
- [ ] 有概念性代码
- [ ] 有真实源码
- [ ] 有执行示例
- [ ] **代码与示例关联完整**（新增）
- [ ] 章节层次分明
- [ ] 重点内容前置
- [ ] 代码位置明确
- [ ] 总结归纳到位

### 代码与示例关联规范 ⭐ **新增**

**要求**：所有代码片段必须配有详细的执行示例，展示代码如何工作。

**规范格式**：

```markdown
**代码执行过程示例（场景描述）**：

```python
# 场景：具体的使用场景
# 调用：函数名(参数1=值1, 参数2=值2, ...)

# 步骤 1（第 X 行）：步骤描述
变量 = 值
# 注释说明

# 步骤 2（第 Y 行）：步骤描述
变量 = 值
# 注释说明

# 最终结果：结果描述
```

**关键代码逻辑对应**：

1. **功能模块1**（第 X-Y 行）：
   - 逻辑说明1
   - 逻辑说明2

2. **功能模块2**（第 Z-W 行）：
   - 逻辑说明1
   - 逻辑说明2
```

**示例要求**：

1. **场景明确**：每个示例都要说明具体的使用场景
2. **步骤详细**：展示代码执行的每一步，包括：
   - 函数调用和参数
   - 中间变量值
   - 条件判断结果
   - 循环执行过程
3. **行号对应**：示例中的步骤要对应源码的具体行号
4. **结果验证**：展示最终结果，验证代码的正确性
5. **多场景覆盖**：对于复杂的代码，提供多个场景的示例

**完整示例**（参考 `DDP原理与源码解读-附录B-NCCL底层实现与优化.md`）：

```markdown
**代码执行过程示例（4 个 GPU，数据大小 1 MB）**：

```python
# 假设参数：
nranks = 4
ringIx = 0  # GPU0 在 Ring 中的索引
channelCount = 1 * 1024 * 1024  # 1 MB
chunkCount = channelCount / nranks = 256 KB

# 初始数据分布：
GPU0: [A0, B0, C0, D0]  # 每个块 256 KB
GPU1: [A1, B1, C1, D1]
GPU2: [A2, B2, C2, D2]
GPU3: [A3, B3, C3, D3]

# ========== ReduceScatter 阶段 ==========

# Step 0 (第 490-495 行)：推送数据到下一个 GPU
# chunk = modRanks(0 + 4 - 1) = modRanks(3) = 3
# chunkOffset = 3 * 256 KB = 768 KB
# GPU0 发送 D0 到 GPU1
prims.directSend(offset=768KB, nelem=256KB)  # 发送 D0

# ... 更多步骤 ...

# 最终结果：所有 GPU 都有完整结果 [A, B, C, D]
```

**关键代码逻辑对应**：

1. **Chunk 计算**（第 491-494 行）：
   - `chunk = modRanks(ringIx + nranks - 1)`：计算当前 rank 负责的第一个 chunk
   - 在 4 GPU 示例中，GPU0 (ringIx=0) 负责 chunk 3 (D)

2. **ReduceScatter 循环**（第 498-504 行）：
   - `j` 从 2 到 `nranks-1`：执行 `nranks-2` 次中间步骤
   - 每次：接收、Reduce、发送（流水线操作）
```

**检查清单**：

- [ ] 每个重要的代码片段都有执行示例
- [ ] 示例包含具体的场景和参数值
- [ ] 示例展示代码执行的每一步
- [ ] 示例中的步骤对应源码行号
- [ ] 示例展示最终结果和验证
- [ ] 复杂代码有多个场景的示例

### 面试题标准

**数量**：每章 8-12 道
**分类**：
- 基础题：3-4 道（概念理解、基本流程）
- 进阶题：3-4 道（原理深入、性能优化）
- 深入题：3-4 道（实现细节、边界情况）

---

## 🔧 高级用法

### 1. 自定义规则

在项目的 `.cursorrules` 中追加自定义规则：

```bash
# 创建项目 .cursorrules
cat > .cursorrules <<'EOF'
# 包含通用 Skill
include:/home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/.cursorrules

# 项目特定规则
## 项目背景
本项目是 XXX，主要技术栈：YYY

## 特殊约定
- 代码风格：遵循 PEP 8
- 命名规范：使用下划线分隔
EOF
```

### 2. CI/CD 集成

```yaml
# .github/workflows/doc-check.yml
name: Documentation Check

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Check format
        run: |
          python scripts/check_format.py docs/ -d

      - name: Validate code references
        run: |
          python scripts/validate_code_refs.py docs/ -d -c .
```

### 3. 团队协作

**统一规范**：
1. 所有成员使用相同的 Skill
2. 代码审查时检查文档质量
3. 定期运行格式检查

**文档模板库**：
```bash
# 创建团队模板库
mkdir -p team_templates/
cp templates/*.md team_templates/

# 团队成员使用
cp team_templates/chapter_template.md 第X章-XXX.md
```

---

## 📚 参考资源

### 学习资料

- [Cursor 文档](https://cursor.sh/docs)
- [Markdown 语法](https://www.markdownguide.org/)
- [Python AST 文档](https://docs.python.org/3/library/ast.html)

### 示例项目

- DDP 源码解读（本 Skill 的实战应用）
  - 位置：`/home/aibert.liu/libra/code/ai_infra/torch/pytorch/`
  - 包含：12 个完整章节，126+ 道面试题

---

## 🤝 贡献指南

### 报告问题

如果发现 Bug 或有改进建议：
1. 记录问题现象
2. 提供复现步骤
3. 提出改进方案（可选）

### 添加新功能

欢迎添加新的脚本工具或模板：
1. 在 `scripts/` 或 `templates/` 中添加
2. 更新本 README
3. 提供使用示例

---

## 📄 许可证

本 Skill 为内部学习工具，供个人和团队使用。

---

## 🎓 最佳实践

### 1. 学习新项目的流程

```bash
# 步骤 1：代码结构分析
python scripts/analyze_code.py main_file.py -o structure.md

# 步骤 2：创建学习笔记（使用模板）
cp templates/chapter_template.md 第1章-概述.md

# 步骤 3：在 Cursor 中学习
# 与 AI 对话，AI 会自动遵循 Skill 规范

# 步骤 4：生成目录
python scripts/generate_toc.py 第1章-概述.md -i

# 步骤 5：质量检查
python scripts/check_format.py 第1章-概述.md
python scripts/validate_code_refs.py 第1章-概述.md -c /path/to/source
```

### 2. 文档编写流程

```
1. 确定主题 → 使用模板
2. 先写原理 → 类比+图示
3. 再看源码 → 带行号引用
4. 添加示例 → 可运行代码
5. 编写面试题 → 分级别
6. 生成目录 → 自动化
7. 质量检查 → 自动化
```

### 3. 团队协作流程

```
1. 统一使用此 Skill
2. 定义项目特定规则（追加到 .cursorrules）
3. Code Review 检查文档质量
4. CI/CD 自动化检查
5. 定期同步最新版本
```

---

## 💡 常见问题

### Q1：如何在多个项目中使用此 Skill？

**A**：使用符号链接或 include 语句：
```bash
# 方法 1：符号链接
ln -s /path/to/skill/.cursorrules /path/to/project/.cursorrules

# 方法 2：include（推荐）
echo 'include:/path/to/skill/.cursorrules' > /path/to/project/.cursorrules
```

### Q2：如何自定义图示样式？

**A**：参考 `templates/diagrams.md`，复制并修改符号：
```
自定义符号：
╔═╗ ╚═╝  粗边框
┏━┓ ┗━┛  双线框
▲ ▼ ◀ ▶  三角形箭头
```

### Q3：脚本工具需要安装依赖吗？

**A**：只需要 Python 3.6+，无需额外依赖。所有脚本都使用标准库。

### Q4：如何处理 C++/Java 等非 Python 代码？

**A**：
1. `analyze_code.py` 只支持 Python
2. 其他工具（格式检查、目录生成等）语言无关
3. 可以用概念性 Python 代码说明其他语言的逻辑

### Q5：可以用于其他类型的文档吗（非源码学习）？

**A**：可以！此 Skill 的原则适用于：
- API 文档
- 架构设计文档
- 技术分享 PPT
- 博客文章
- 教程编写

---

## 📮 联系方式

如有问题或建议，欢迎联系：
- 路径：`/home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/`
- 更新日期：2026-02-09

---

**Happy Learning! 🚀**
