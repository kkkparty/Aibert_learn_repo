# 快速开始指南

## 5 分钟上手源码学习 Skill

### 步骤 1：链接 Skill 到你的项目

```bash
# 进入你的项目目录
cd /path/to/your/project

# 创建 .cursorrules 链接
ln -s /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/.cursorrules .cursorrules

# 或者使用 include 方式（推荐）
echo 'include:/home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/.cursorrules' > .cursorrules
```

### 步骤 2：分析源码结构

```bash
# 分析你要学习的源文件
python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/analyze_code.py your_file.py

# 输出到文件
python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/analyze_code.py your_file.py -o analysis.md
```

### 步骤 3：使用模板创建学习笔记

```bash
# 复制概念讲解模板
cp /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/templates/concept_template.md 第1章-概念.md

# 或复制源码讲解模板
cp /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/templates/source_code_template.md 第2章-源码.md
```

### 步骤 4：在 Cursor 中与 AI 对话

打开 Cursor，与 AI 对话时，它会自动遵循 Skill 的规范：

```
你: @your_file.py 请帮我讲解这个类的实现原理，先讲为什么需要，再讲怎么做

AI: [会按照"原理先行"的方式回答]
1. 为什么需要这个类
2. 核心原理（附带图示）
3. 源码实现（带行号）
4. 使用示例
```

### 步骤 5：自动化处理文档

```bash
# 生成目录
python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/generate_toc.py 第1章-概念.md -i

# 检查格式
python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/check_format.py 第1章-概念.md

# 验证代码引用
python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/validate_code_refs.py 第1章-概念.md -c .
```

---

## 完整示例：学习一个新项目

### 场景：学习 Flask 的路由机制

```bash
# 1. 创建学习目录
mkdir -p ~/learning/flask-routing
cd ~/learning/flask-routing

# 2. 链接 Skill
ln -s /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/.cursorrules .cursorrules

# 3. 分析 Flask 路由源码
python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/analyze_code.py \
    /path/to/flask/flask/app.py \
    -o flask_routing_structure.md

# 4. 创建学习笔记
cp /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/templates/concept_template.md \
    第1章-路由机制原理.md

# 5. 在 Cursor 中编辑
cursor 第1章-路由机制原理.md

# 6. 与 AI 对话
# 你: @flask/app.py 请讲解 Flask 的路由注册机制，先讲为什么需要路由
# AI: [按规范回答]

# 7. 生成目录
python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/generate_toc.py \
    第1章-路由机制原理.md -i

# 8. 质量检查
python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/check_format.py \
    第1章-路由机制原理.md
```

---

## 常用命令速查

### 分析源码

```bash
# 基础分析
analyze_code.py file.py

# 输出到文件
analyze_code.py file.py -o report.md
```

### 依赖分析

```bash
# 分析调用关系
find_dependencies.py file.py

# 分析特定函数
find_dependencies.py file.py -f function_name

# 生成调用图
find_dependencies.py file.py -g call_graph.dot
```

### 文档处理

```bash
# 生成目录
generate_toc.py doc.md -i

# 批量生成
generate_toc.py docs/ -d -i

# 格式检查
check_format.py doc.md

# 验证引用
validate_code_refs.py doc.md -c /path/to/code
```

---

## Tip: 添加到 PATH

为了更方便使用，可以将脚本目录添加到 PATH：

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export PATH="$PATH:/home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts"' >> ~/.bashrc

# 重新加载
source ~/.bashrc

# 现在可以直接使用命令
analyze_code.py file.py
generate_toc.py doc.md -i
```

或者创建别名：

```bash
# 添加到 ~/.bashrc
alias skill-analyze='python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/analyze_code.py'
alias skill-toc='python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/generate_toc.py'
alias skill-check='python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/check_format.py'
alias skill-validate='python /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts/validate_code_refs.py'

# 使用
skill-analyze file.py
skill-toc doc.md -i
skill-check doc.md
```

---

## 下一步

- 📖 查看 [README.md](README.md) 了解完整功能
- 📝 查看 [templates/](templates/) 目录了解所有模板
- 🛠️ 查看 [scripts/](scripts/) 目录了解所有工具
- 🎓 查看 DDP 源码解读示例（实战应用）

---

**Happy Learning! 🚀**
