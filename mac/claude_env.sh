claude-switch() {
    local config_file="$HOME/.claude_config"
    if [[ ! -f "$config_file" ]]; then
        cat > "$config_file" << 'EOF'
ww|问问Code|sk-xxxxxxWWWWWWxxxxxx|https://code.wenwen-ai.com
any|AnyRouter|sk-xxxxxxANYxxxxxx|https://anyrouter.top
kimi|月之暗面|sk-xxxxxxKIMIxxxxxx|https://api.moonshot.cn/anthropic
EOF
    fi

    if [[ $# -eq 0 ]]; then
        echo "可用配置："
        cut -d'|' -f1,2 "$config_file" | sed 's/|/ - /'
        return 0
    fi

    local line=$(grep "^$1|" "$config_file")
    if [[ -z "$line" ]]; then
        echo "未知别名：$1"; return 1
    fi

    IFS='|' read -r alias name token url <<< "$line"
    export ANTHROPIC_AUTH_TOKEN="$token"
    export ANTHROPIC_BASE_URL="$url"
    echo "已切换到：$name"
}

alias cs='claude-switch'
alias css='echo "Alias: $name Token: ${ANTHROPIC_AUTH_TOKEN:0:15}... URL: $ANTHROPIC_BASE_URL"'
