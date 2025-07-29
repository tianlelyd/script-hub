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

    # 检查是否安装了 jq
    if ! command -v jq >/dev/null 2>&1; then
        echo "需要安装 jq 工具来解析配置"
        return 1
    fi

    # 获取配置名称列表
    local config_names=($(jq -r '.[].name' "$config_file"))
    
    # 如果没有配置项
    if [[ ${#config_names[@]} -eq 0 ]]; then
        echo "配置文件中没有可用的配置"
        return 1
    fi

    local selected_name=""
    
    # 如果有参数直接使用，否则显示菜单选择
    if [[ $# -gt 0 ]]; then
        selected_name="$1"
    else
        # 显示交互式菜单
        echo "请选择配置："
        select config_name in "${config_names[@]}" "退出"; do
            case $config_name in
                "退出")
                    return 0
                    ;;
                "")
                    echo "无效选择，请重新选择"
                    ;;
                *)
                    selected_name="$config_name"
                    break
                    ;;
            esac
        done
    fi

    # 使用 jq 查找匹配的配置项
    local config_entry=""
    config_entry=$(jq -r --arg name "$selected_name" '.[] | select(.name == $name)' "$config_file")

    if [[ -z "$config_entry" ]]; then
        echo "未知配置名：$selected_name"
        return 1
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