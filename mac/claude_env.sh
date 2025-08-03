claude_env.sh
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

    # Check if jq is installed
    if ! command -v jq >/dev/null 2>&1; then
        echo "jq tool is required to parse the configuration"
        return 1
    fi

    # Get configuration name list
    local config_names=($(jq -r '.[].name' "$config_file"))
    
    # If there are no configuration items
    if [[ ${#config_names[@]} -eq 0 ]]; then
        echo "No available configurations in the config file"
        return 1
    fi

    local selected_name=""
    
    # If argument is provided, use it directly, otherwise show menu selection
    if [[ $# -gt 0 ]]; then
        selected_name="$1"
    else
        # Show interactive menu
        echo "Please select configuration:"
        select config_name in "${config_names[@]}" "Exit"; do
            case $config_name in
                "Exit")
                    return 0
                    ;;
                "")
                    echo "Invalid selection, please try again"
                    ;;
                *)
                    selected_name="$config_name"
                    break
                    ;;
            esac
        done
    fi

    # Use jq to find the matching configuration entry
    local config_entry=""
    config_entry=$(jq -r --arg name "$selected_name" '.[] | select(.name == $name)' "$config_file")

    if [[ -z "$config_entry" ]]; then
        echo "Unknown configuration name: $selected_name"
        return 1
    fi

    # Export environment variables
    export ANTHROPIC_AUTH_TOKEN=$(echo "$config_entry" | jq -r '.ANTHROPIC_AUTH_TOKEN')
    export ANTHROPIC_BASE_URL=$(echo "$config_entry" | jq -r '.ANTHROPIC_BASE_URL')
    local display_url=$(echo "$config_entry" | jq -r '.ANTHROPIC_BASE_URL')
    local display_token=$(echo "$config_entry" | jq -r '.ANTHROPIC_AUTH_TOKEN')
    # 只显示前8位和后4位，中间用*号代替
    local token_prefix=${display_token:0:8}
    local token_suffix=${display_token: -4}
    local token_length=${#display_token}
    local mask_length=$((token_length-12))
    if [[ $mask_length -gt 0 ]]; then
        local token_mask=$(printf '%*s' "$mask_length" | tr ' ' '*')
        local masked_token="${token_prefix}${token_mask}${token_suffix}"
    else
        local masked_token="$display_token"
    fi
    echo "ANTHROPIC_BASE_URL: $display_url"
    echo "ANTHROPIC_AUTH_TOKEN: $masked_token"
}

alias cs='claude-switch'
alias css='echo "Name: $name Token: ${ANTHROPIC_AUTH_TOKEN:0:15}... URL: $ANTHROPIC_BASE_URL"'