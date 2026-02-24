#!/bin/bash
#
# Source Code Learning Skill - Setup Script
# 用途：快速设置和使用源码学习 Skill
#

SKILL_DIR="/home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill"
SCRIPTS_DIR="$SKILL_DIR/scripts"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
Source Code Learning Skill - Setup Script

用法:
    $0 <command> [options]

命令:
    install <project_dir>   - 在项目中安装 Skill
    add-path               - 将脚本目录添加到 PATH
    alias                  - 创建便捷别名
    test                   - 测试所有脚本
    help                   - 显示此帮助信息

示例:
    # 在项目中安装
    $0 install /path/to/your/project

    # 添加到 PATH
    $0 add-path

    # 创建别名
    $0 alias

    # 测试脚本
    $0 test

EOF
}

# 在项目中安装 Skill
install_skill() {
    local project_dir="$1"

    if [ -z "$project_dir" ]; then
        print_error "请指定项目目录"
        echo "用法: $0 install <project_dir>"
        exit 1
    fi

    if [ ! -d "$project_dir" ]; then
        print_error "目录不存在: $project_dir"
        exit 1
    fi

    local cursorrules="$project_dir/.cursorrules"

    # 检查是否已存在
    if [ -f "$cursorrules" ]; then
        print_warn ".cursorrules 已存在"
        read -p "是否覆盖? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "取消安装"
            exit 0
        fi
    fi

    # 创建符号链接
    ln -sf "$SKILL_DIR/.cursorrules" "$cursorrules"
    print_info "✓ 已在 $project_dir 中安装 Skill"
    print_info "  .cursorrules -> $SKILL_DIR/.cursorrules"

    # 提示下一步
    echo ""
    print_info "下一步:"
    echo "  1. cd $project_dir"
    echo "  2. 在 Cursor 中打开项目"
    echo "  3. 与 AI 对话时，它会自动遵循 Skill 规范"
}

# 添加到 PATH
add_to_path() {
    local shell_rc=""

    # 检测 shell 类型
    if [ -n "$BASH_VERSION" ]; then
        shell_rc="$HOME/.bashrc"
    elif [ -n "$ZSH_VERSION" ]; then
        shell_rc="$HOME/.zshrc"
    else
        print_warn "未检测到 bash 或 zsh，请手动配置"
        echo "添加以下行到你的 shell 配置文件:"
        echo "export PATH=\"\$PATH:$SCRIPTS_DIR\""
        exit 0
    fi

    # 检查是否已添加
    if grep -q "$SCRIPTS_DIR" "$shell_rc" 2>/dev/null; then
        print_info "PATH 中已包含脚本目录"
        return
    fi

    # 添加到 PATH
    echo "" >> "$shell_rc"
    echo "# Source Code Learning Skill" >> "$shell_rc"
    echo "export PATH=\"\$PATH:$SCRIPTS_DIR\"" >> "$shell_rc"

    print_info "✓ 已添加到 $shell_rc"
    print_warn "请运行以下命令使配置生效:"
    echo "  source $shell_rc"
}

# 创建别名
create_aliases() {
    local shell_rc=""

    # 检测 shell 类型
    if [ -n "$BASH_VERSION" ]; then
        shell_rc="$HOME/.bashrc"
    elif [ -n "$ZSH_VERSION" ]; then
        shell_rc="$HOME/.zshrc"
    else
        print_warn "未检测到 bash 或 zsh，请手动配置"
        exit 0
    fi

    # 检查是否已添加
    if grep -q "skill-analyze" "$shell_rc" 2>/dev/null; then
        print_info "别名已存在"
        return
    fi

    # 添加别名
    cat >> "$shell_rc" << EOF

# Source Code Learning Skill Aliases
alias skill-analyze='python $SCRIPTS_DIR/analyze_code.py'
alias skill-deps='python $SCRIPTS_DIR/find_dependencies.py'
alias skill-toc='python $SCRIPTS_DIR/generate_toc.py'
alias skill-check='python $SCRIPTS_DIR/check_format.py'
alias skill-validate='python $SCRIPTS_DIR/validate_code_refs.py'
EOF

    print_info "✓ 已添加别名到 $shell_rc"
    print_warn "请运行以下命令使配置生效:"
    echo "  source $shell_rc"
    echo ""
    print_info "可用别名:"
    echo "  skill-analyze   - 分析源码结构"
    echo "  skill-deps      - 分析函数依赖"
    echo "  skill-toc       - 生成目录"
    echo "  skill-check     - 检查格式"
    echo "  skill-validate  - 验证代码引用"
}

# 测试所有脚本
test_scripts() {
    print_info "测试脚本..."

    local all_passed=true

    # 测试每个脚本
    for script in "$SCRIPTS_DIR"/*.py; do
        local script_name=$(basename "$script")

        # 检查是否可执行
        if ! python "$script" --help > /dev/null 2>&1; then
            print_error "$script_name - FAILED"
            all_passed=false
        else
            print_info "$script_name - PASSED"
        fi
    done

    echo ""
    if [ "$all_passed" = true ]; then
        print_info "✓ 所有脚本测试通过"
    else
        print_error "部分脚本测试失败"
        exit 1
    fi
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    case "$1" in
        install)
            install_skill "$2"
            ;;
        add-path)
            add_to_path
            ;;
        alias)
            create_aliases
            ;;
        test)
            test_scripts
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
