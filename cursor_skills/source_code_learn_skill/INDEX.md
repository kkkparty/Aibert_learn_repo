# Source Code Learning Skill - 完整索引

## 📁 目录结构

```
source_code_learn_skill/
├── README.md                   # 完整使用指南
├── QUICKSTART.md               # 5分钟快速开始
├── INDEX.md                    # 本文件：完整索引
├── .cursorrules                # Cursor AI 规则配置
├── setup.sh                    # 安装和设置脚本
│
├── scripts/                    # 实用脚本工具
│   ├── analyze_code.py         # 源码结构分析
│   ├── find_dependencies.py    # 函数依赖分析
│   ├── generate_toc.py         # 自动生成目录
│   ├── check_format.py         # 文档格式检查
│   └── validate_code_refs.py   # 代码引用验证
│
├── templates/                  # 文档模板
│   ├── concept_template.md     # 概念讲解模板
│   └── source_code_template.md # 源码讲解模板
│
└── examples/                   # 示例（可选）
    └── ...
```

---

## 🚀 快速导航

### 新手入门

1. **5分钟快速开始** → [QUICKSTART.md](QUICKSTART.md)
2. **完整使用指南** → [README.md](README.md)
3. **安装到项目** → 运行 `./setup.sh install <project_dir>`

### 核心文件

| 文件 | 用途 | 何时使用 |
|-----|------|---------|
| [.cursorrules](.cursorrules) | AI 规则配置 | 自动使用（链接到项目） |
| [setup.sh](setup.sh) | 安装脚本 | 第一次使用 |

### 脚本工具

| 脚本 | 功能 | 命令示例 |
|-----|------|---------|
| [analyze_code.py](scripts/analyze_code.py) | 分析源码结构 | `python scripts/analyze_code.py file.py` |
| [find_dependencies.py](scripts/find_dependencies.py) | 分析函数依赖 | `python scripts/find_dependencies.py file.py` |
| [generate_toc.py](scripts/generate_toc.py) | 生成文档目录 | `python scripts/generate_toc.py doc.md -i` |
| [check_format.py](scripts/check_format.py) | 检查文档格式 | `python scripts/check_format.py doc.md` |
| [validate_code_refs.py](scripts/validate_code_refs.py) | 验证代码引用 | `python scripts/validate_code_refs.py doc.md -c .` |

### 文档模板

| 模板 | 用途 | 何时使用 |
|-----|------|---------|
| [concept_template.md](templates/concept_template.md) | 概念讲解 | 讲解原理和概念 |
| [source_code_template.md](templates/source_code_template.md) | 源码讲解 | 深入分析源码 |

---

## 📖 使用流程

### 流程 1：在新项目中使用

```bash
# 1. 安装 Skill
./setup.sh install /path/to/project

# 2. 进入项目
cd /path/to/project

# 3. 在 Cursor 中开始学习
# AI 会自动遵循规范
```

### 流程 2：分析现有代码

```bash
# 1. 分析代码结构
python scripts/analyze_code.py target_file.py -o analysis.md

# 2. 分析函数依赖
python scripts/find_dependencies.py target_file.py -g call_graph.dot

# 3. 查看生成的文档
cat analysis.md
```

### 流程 3：编写学习文档

```bash
# 1. 使用模板
cp templates/concept_template.md 第1章.md

# 2. 在 Cursor 中编辑
# 与 AI 对话，AI 会按规范生成内容

# 3. 生成目录
python scripts/generate_toc.py 第1章.md -i

# 4. 质量检查
python scripts/check_format.py 第1章.md
python scripts/validate_code_refs.py 第1章.md -c /path/to/code
```

---

## 🎯 核心规范速查

### 讲解顺序

```
第0层：概念和原理（无代码）
  ↓
第1层：核心机制（概念代码）
  ↓
第2层：源码实现（真实代码+行号）
  ↓
第3层：实战应用（示例+面试题）
```

### 必须使用图示的场景

- ✅ 流程图：执行流程
- ✅ 时序图：时间维度交互
- ✅ 架构图：模块关系
- ✅ 数据流图：数据传递
- ✅ 对比图：方案对比
- ✅ 状态机图：状态转换

### 代码引用格式

```markdown
# 概念代码（无行号）
\`\`\`python
def concept():
    pass
\`\`\`

# 源码引用（有行号）
\`\`\`startLine:endLine:path/to/file.py
def real_code():
    pass
\`\`\`
```

### 面试题标准

- 每章 8-12 道
- 基础题：3-4 道
- 进阶题：3-4 道
- 深入题：3-4 道

---

## 🛠️ 常用命令

### 一键设置

```bash
# 添加脚本到 PATH
./setup.sh add-path

# 创建便捷别名
./setup.sh alias

# 测试所有脚本
./setup.sh test
```

### 日常使用

```bash
# 如果设置了别名
skill-analyze file.py
skill-deps file.py
skill-toc doc.md -i
skill-check doc.md
skill-validate doc.md -c .

# 或使用完整路径
python /path/to/scripts/analyze_code.py file.py
```

---

## 📚 学习资源

### 文档

- [README.md](README.md) - 完整文档（必读）
- [QUICKSTART.md](QUICKSTART.md) - 快速开始（推荐）
- [.cursorrules](.cursorrules) - 规则配置（参考）

### 实战示例

**DDP 源码解读**（本 Skill 的实战应用）：
- 位置：`/home/aibert.liu/libra/code/ai_infra/torch/pytorch/`
- 内容：12 个完整章节，126+ 道面试题
- 特点：完全遵循本 Skill 的所有规范

**学习路径**：
1. 阅读 QUICKSTART.md（5 分钟）
2. 在测试项目中试用（15 分钟）
3. 参考 DDP 示例（深入学习）
4. 应用到自己的项目

---

## 🔧 高级技巧

### 自定义规则

```bash
# 项目 .cursorrules
cat > /path/to/project/.cursorrules <<'EOF'
# 包含通用 Skill
include:/home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/.cursorrules

# 项目特定规则
## 背景
本项目是 XXX

## 特殊约定
- XXX
EOF
```

### CI/CD 集成

```yaml
# .github/workflows/doc-check.yml
name: Doc Check
on: [push]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check docs
        run: |
          python scripts/check_format.py docs/ -d
          python scripts/validate_code_refs.py docs/ -d -c .
```

### 团队协作

```bash
# 1. 统一规范
git submodule add <skill-repo> .skills/source_code_learn

# 2. 创建团队配置
cat > .cursorrules <<'EOF'
include:.skills/source_code_learn/.cursorrules

## 团队约定
...
EOF

# 3. 代码审查检查清单
# - [ ] 文档有图示
# - [ ] 代码有行号
# - [ ] 有面试题
# - [ ] 格式检查通过
```

---

## 💡 常见问题

### Q1: 如何更新 Skill？

```bash
cd /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill
git pull  # 如果是 git 仓库

# 或
# 重新下载/复制最新版本
```

### Q2: 可以用于非 Python 项目吗？

可以！除了 `analyze_code.py` 只支持 Python，其他工具都是语言无关的。

### Q3: 如何贡献改进？

1. 修改文件
2. 测试：`./setup.sh test`
3. 更新文档
4. 提交反馈

### Q4: 脚本报错怎么办？

```bash
# 检查 Python 版本（需要 3.6+）
python --version

# 测试脚本
./setup.sh test

# 查看详细错误
python scripts/xxx.py --help
```

---

## 📞 获取帮助

### 查看帮助信息

```bash
# 安装脚本帮助
./setup.sh help

# 各个工具的帮助
python scripts/analyze_code.py --help
python scripts/find_dependencies.py --help
python scripts/generate_toc.py --help
python scripts/check_format.py --help
python scripts/validate_code_refs.py --help
```

### 文件位置

```
Skill 根目录:
/home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill

脚本目录:
/home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/scripts

模板目录:
/home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/templates
```

---

## 🎓 最佳实践

1. **学习新项目**：先用 `analyze_code.py` 了解结构
2. **编写文档**：使用模板，确保结构一致
3. **质量保证**：使用 `check_format.py` 和 `validate_code_refs.py`
4. **团队协作**：统一使用此 Skill，定期检查
5. **持续改进**：收集反馈，更新规范

---

## 📊 功能矩阵

| 功能 | 脚本 | 自动化 | 说明 |
|-----|------|--------|-----|
| 源码分析 | analyze_code.py | ✅ | 提取结构 |
| 依赖分析 | find_dependencies.py | ✅ | 调用关系 |
| 目录生成 | generate_toc.py | ✅ | 自动更新 |
| 格式检查 | check_format.py | ✅ | CI/CD 集成 |
| 引用验证 | validate_code_refs.py | ✅ | 代码变更检测 |
| 文档模板 | templates/*.md | ✅ | 统一规范 |
| AI 规则 | .cursorrules | ✅ | 自动遵循 |

---

**版本**: 1.0
**更新时间**: 2026-02-09
**位置**: `/home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill`

---

**Happy Learning! 🚀**
