claude-switch() {
    local config_file="$HOME/.claude_config"
    if [[ ! -f "$config_file" ]]; then
        cat > "$config_file" << 'EOF'
[
  {
    "name": "wenwen-ai",
    "WEBURL": "https://code.wenwen-ai.com",
    "ANTHROPIC_BASE_URL": "https://code.wenwen-ai.com",
    "ANTHROPIC_AUTH_TOKEN": "sk-hsg5hOghxxxxxxxHEk1rKHRxx"
  },
  {
    "name": "zone",
    "WEBURL": "https://zone.veloera.org",
    "ANTHROPIC_BASE_URL": "https://zone.veloera.org/pg",
    "ANTHROPIC_AUTH_TOKEN": "sk-xxxxxxxxxxxx"
  }
]
EOF
    fi

    if [[ $# -eq 0 ]]; then
        echo "可用配置："
        # 使用 jq 解析 JSON 并显示名称列表
        if command -v jq >/dev/null 2>&1; then
            jq -r '.[] | "\(.name)"' "$config_file"
        else
            echo "需要安装 jq 工具来解析配置"
        fi
        return 0
    fi

    # 使用 jq 查找匹配的配置项
    local config_entry=""
    if command -v jq >/dev/null 2>&1; then
        config_entry=$(jq -r --arg name "$1" '.[] | select(.name == $name)' "$config_file")
    fi

    if [[ -z "$config_entry" ]]; then
        echo "未知配置名：$1"; return 1
    fi

    # 导出环境变量
    export ANTHROPIC_AUTH_TOKEN=$(echo "$config_entry" | jq -r '.ANTHROPIC_AUTH_TOKEN')
    export ANTHROPIC_BASE_URL=$(echo "$config_entry" | jq -r '.ANTHROPIC_BASE_URL')
    local display_name=$(echo "$config_entry" | jq -r '.name')
    local web_url=$(echo "$config_entry" | jq -r '.WEBURL')
    echo "已切换到：$display_name"
    echo "网站地址：$web_url"
}

alias cs='claude-switch'
alias css='echo "Name: $name Token: ${ANTHROPIC_AUTH_TOKEN:0:15}... URL: $ANTHROPIC_BASE_URL"'