#!/usr/bin/env python3
"""
Tab 补全脚本生成器

为 bash 和 zsh 生成命令补全脚本。

用法：
  python completions.py --shell bash  # 生成 bash 补全脚本
  python completions.py --shell zsh   # 生成 zsh 补全脚本
  python completions.py --install     # 安装补全脚本
"""

import argparse
import sys
from pathlib import Path


# 命令和子命令定义
COMMANDS = {
    "wardrobe": {
        "aliases": ["w"],
        "subcommands": ["add", "list", "show", "update", "delete", "stats", "record", "reindex", "restore"],
        "options": ["--item-id", "--type", "--sub-type", "--primary-color", "--primary-hex",
                    "--secondary-color", "--secondary-hex", "--material", "--fit", "--style",
                    "--season", "--temp-range", "--occasion", "--pair-with", "--restrict",
                    "--image", "--wear-count", "--favorite", "--items", "--notes",
                    "--weather", "--temp", "--json", "--category", "--force"],
    },
    "weather": {
        "aliases": ["wt"],
        "subcommands": [],
        "options": ["--city", "--date", "--list-cities"],
    },
    "recommend": {
        "aliases": ["r"],
        "subcommands": ["recommend", "today"],
        "options": ["--items", "--occasion", "--city"],
    },
    "score": {
        "aliases": ["s"],
        "subcommands": [],
        "options": ["--items", "--occasion", "--temp"],
    },
    "color": {
        "aliases": ["c"],
        "subcommands": ["score", "show"],
        "options": ["--items", "--colors"],
    },
    "inverse": {
        "aliases": ["inv"],
        "subcommands": [],
        "options": ["--known", "--target", "--missing", "--method", "--top", "--samples", "--maxiter"],
    },
    "palette": {
        "aliases": ["p"],
        "subcommands": ["list", "train", "scrape"],
        "options": ["--top", "--source", "--min-score"],
    },
    "knowledge": {
        "aliases": ["k"],
        "subcommands": ["list", "show", "edit"],
        "options": ["--raw"],
    },
    "config": {
        "aliases": ["cf"],
        "subcommands": ["config", "stats"],
        "options": ["--json"],
    },
}


def generate_bash_completion():
    """生成 bash 补全脚本"""
    script = '''#!/bin/bash
# SuperOutfit bash 补全脚本
# 安装：source completions.bash

_superoutfit_completions() {
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # 主命令列表
    commands="wardrobe weather recommend score color inverse palette knowledge config"
    
    # 第一个参数：主命令
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi
    
    # 第二个参数：子命令
    case "${COMP_WORDS[1]}" in
        wardrobe|w)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=( $(compgen -W "add list show update delete stats record reindex restore" -- ${cur}) )
            else
                COMPREPLY=( $(compgen -W "--item-id --type --sub-type --primary-color --primary-hex --secondary-color --secondary-hex --material --fit --style --season --temp-range --occasion --pair-with --restrict --image --wear-count --favorite --items --notes --weather --temp --json --category --force" -- ${cur}) )
            fi
            ;;
        weather|wt)
            COMPREPLY=( $(compgen -W "--city --date --list-cities" -- ${cur}) )
            ;;
        recommend|r)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=( $(compgen -W "recommend today" -- ${cur}) )
            else
                COMPREPLY=( $(compgen -W "--items --occasion --city" -- ${cur}) )
            fi
            ;;
        score|s)
            COMPREPLY=( $(compgen -W "--items --occasion --temp" -- ${cur}) )
            ;;
        color|c)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=( $(compgen -W "score show" -- ${cur}) )
            else
                COMPREPLY=( $(compgen -W "--items --colors" -- ${cur}) )
            fi
            ;;
        inverse|inv)
            COMPREPLY=( $(compgen -W "--known --target --missing --method --top --samples --maxiter" -- ${cur}) )
            ;;
        palette|p)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=( $(compgen -W "list train scrape" -- ${cur}) )
            else
                COMPREPLY=( $(compgen -W "--top --source --min-score" -- ${cur}) )
            fi
            ;;
        knowledge|k)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=( $(compgen -W "list show edit" -- ${cur}) )
            else
                COMPREPLY=( $(compgen -W "--raw" -- ${cur}) )
            fi
            ;;
        config|cf)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=( $(compgen -W "config stats" -- ${cur}) )
            else
                COMPREPLY=( $(compgen -W "--json" -- ${cur}) )
            fi
            ;;
    esac
    
    return 0
}

complete -F _superoutfit_completions superoutfit
complete -F _superoutfit_completions python -m superoutfit
'''
    return script


def generate_zsh_completion():
    """生成 zsh 补全脚本"""
    script = '''#compdef superoutfit

# SuperOutfit zsh 补全脚本
# 安装：fpath=(/path/to/completions $fpath) && compinit

_superoutfit() {
    local -a commands
    commands=(
        'wardrobe:衣橱管理'
        'weather:天气查询'
        'recommend:穿搭推荐'
        'score:搭配评分'
        'color:色彩协调度'
        'inverse:反向推导颜色'
        'palette:色卡管理'
        'knowledge:知识库管理'
        'config:配置查看'
    )
    
    _arguments -C \
        '1:command:->commands' \
        '*::arg:->args'
    
    case $state in
        commands)
            _describe 'command' commands
            ;;
        args)
            case $words[1] in
                wardrobe|w)
                    _arguments '1:subcommand:(add list show update delete stats record reindex restore)'
                    ;;
                weather|wt)
                    _arguments '*:option:(--city --date --list-cities)'
                    ;;
                recommend|r)
                    _arguments '1:subcommand:(recommend today)'
                    ;;
                score|s)
                    _arguments '*:option:(--items --occasion --temp)'
                    ;;
                color|c)
                    _arguments '1:subcommand:(score show)'
                    ;;
                inverse|inv)
                    _arguments '*:option:(--known --target --missing --method --top --samples --maxiter)'
                    ;;
                palette|p)
                    _arguments '1:subcommand:(list train scrape)'
                    ;;
                knowledge|k)
                    _arguments '1:subcommand:(list show edit)'
                    ;;
                config|cf)
                    _arguments '1:subcommand:(config stats)'
                    ;;
            esac
            ;;
    esac
}

_superoutfit "$@"
'''
    return script


def install_completion(shell):
    """安装补全脚本"""
    import os
    
    if shell == "bash":
        script = generate_bash_completion()
        # 检查 .bashrc
        bashrc = Path.home() / ".bashrc"
        if bashrc.exists():
            content = bashrc.read_text()
            if "superoutfit" in content:
                print("✓ bash 补全已安装")
                return
        
        # 添加到 .bashrc
        with open(bashrc, "a") as f:
            f.write(f"\n# SuperOutfit 补全\n")
            f.write(f"source {Path(__file__).parent / 'completions.bash'}\n")
        
        print("✓ bash 补全已安装，请运行：source ~/.bashrc")
    
    elif shell == "zsh":
        script = generate_zsh_completion()
        # 检查 fpath
        zshrc = Path.home() / ".zshrc"
        if zshrc.exists():
            content = zshrc.read_text()
            if "superoutfit" in content:
                print("✓ zsh 补全已安装")
                return
        
        # 添加到 .zshrc
        with open(zshrc, "a") as f:
            f.write(f"\n# SuperOutfit 补全\n")
            f.write(f"fpath=({Path(__file__).parent} $fpath)\n")
            f.write(f"compinit\n")
        
        print("✓ zsh 补全已安装，请运行：source ~/.zshrc")


def main():
    parser = argparse.ArgumentParser(description="Tab 补全脚本生成器")
    parser.add_argument("--shell", choices=["bash", "zsh"], help="Shell 类型")
    parser.add_argument("--install", action="store_true", help="安装补全脚本")
    
    args = parser.parse_args()
    
    if args.install:
        if not args.shell:
            # 自动检测 shell
            import os
            shell = os.environ.get("SHELL", "")
            if "zsh" in shell:
                args.shell = "zsh"
            else:
                args.shell = "bash"
        
        install_completion(args.shell)
        return
    
    if not args.shell:
        args.shell = "bash"
    
    if args.shell == "bash":
        print(generate_bash_completion())
    else:
        print(generate_zsh_completion())


if __name__ == "__main__":
    main()
