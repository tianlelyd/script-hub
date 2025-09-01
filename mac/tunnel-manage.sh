#!/bin/bash

# 配置文件路径（系统级服务）
CONFIG_FILE="$HOME/.cloudflared/config.yml"
PLIST_FILE="/Library/LaunchDaemons/com.cloudflare.cloudflared.plist"
SERVICE_NAME="com.cloudflare.cloudflared"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

function show_usage() {
    echo "Cloudflare Tunnel 端口映射管理工具（系统级服务）"
    echo ""
    echo "用法: $0 {add|remove|list|restart|status|logs|install|uninstall|validate}"
    echo ""
    echo "命令:"
    echo "  add <hostname> <port>     - 添加新的端口映射"
    echo "  remove <hostname>         - 删除端口映射"
    echo "  list                      - 列出所有映射"
    echo "  restart                   - 重启服务（需要 sudo）"
    echo "  status                    - 查看服务状态"
    echo "  logs                      - 查看服务日志"
    echo "  install                   - 安装服务（需要 sudo）"
    echo "  uninstall                 - 卸载服务（需要 sudo）"
    echo "  validate                  - 验证配置文件"
    echo ""
    echo "示例:"
    echo "  $0 add api.example.com 8080"
    echo "  $0 restart"
    echo "  $0 list"
}

function add_mapping() {
    local hostname=$1
    local port=$2
    
    if [ -z "$hostname" ] || [ -z "$port" ]; then
        echo -e "${RED}错误: 需要提供 hostname 和 port${NC}"
        show_usage
        exit 1
    fi
    
    echo -e "${GREEN}添加映射: $hostname -> localhost:$port${NC}"
    
    # 备份配置文件
    local backup_file="$CONFIG_FILE.bak.$(date +%Y%m%d_%H%M%S)"
    cp "$CONFIG_FILE" "$backup_file"
    echo -e "${YELLOW}已备份配置文件到: $backup_file${NC}"
    
    # 获取 tunnel 名称
    tunnel_name=$(grep "^tunnel:" "$CONFIG_FILE" | awk '{print $2}')
    
    if [ -z "$tunnel_name" ]; then
        echo -e "${RED}错误: 无法从配置文件获取 tunnel 名称${NC}"
        exit 1
    fi
    
    # 添加 DNS 记录
    echo -e "${YELLOW}添加 DNS 记录...${NC}"
    if cloudflared tunnel route dns "$tunnel_name" "$hostname"; then
        echo -e "${GREEN}DNS 记录已成功添加${NC}"
    else
        echo -e "${RED}DNS 记录添加失败，请检查域名和权限${NC}"
        exit 1
    fi
    
    # 自动编辑配置文件
    echo -e "${YELLOW}更新配置文件...${NC}"
    
    # 创建新的 ingress 条目
    local new_entry="  - hostname: $hostname\n    service: http://localhost:$port"
    
    # 使用 awk 在 http_status:404 之前插入新条目
    awk -v entry="$new_entry" '
    /service: http_status:404/ && !inserted {
        print entry
        inserted = 1
    }
    { print }
    ' "$CONFIG_FILE" > "$CONFIG_FILE.tmp"
    
    # 替换原文件
    mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
    
    echo -e "${GREEN}配置文件已更新${NC}"
    
    # 验证配置
    echo -e "${YELLOW}验证配置...${NC}"
    if cloudflared tunnel ingress validate > /dev/null 2>&1; then
        echo -e "${GREEN}配置验证通过${NC}"
        
        # 自动重启服务
        echo -e "${YELLOW}重启服务...${NC}"
        sudo launchctl unload -w "$PLIST_FILE" 2>/dev/null
        sleep 2
        sudo launchctl load -w "$PLIST_FILE"
        
        sleep 3
        
        # 检查服务状态
        if sudo launchctl list | grep -q "$SERVICE_NAME"; then
            echo -e "${GREEN}服务已重启成功${NC}"
            echo ""
            echo -e "${GREEN}映射已成功添加并生效：${NC}"
            echo -e "  $hostname -> http://localhost:$port"
            echo ""
            echo -e "${GREEN}您可以通过 https://$hostname 访问服务${NC}"
        else
            echo -e "${RED}服务重启失败，恢复配置文件${NC}"
            cp "$backup_file" "$CONFIG_FILE"
            exit 1
        fi
    else
        echo -e "${RED}配置验证失败，恢复配置文件${NC}"
        cloudflared tunnel ingress validate
        cp "$backup_file" "$CONFIG_FILE"
        exit 1
    fi
}

function remove_mapping() {
    local hostname=$1
    
    if [ -z "$hostname" ]; then
        echo -e "${RED}错误: 需要提供 hostname${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}请手动编辑 $CONFIG_FILE 删除以下映射:${NC}"
    echo "$hostname"
    echo ""
    echo -e "${YELLOW}删除后运行: $0 restart${NC}"
}

function list_mappings() {
    echo -e "${GREEN}当前端口映射：${NC}"
    echo ""
    
    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${RED}配置文件不存在: $CONFIG_FILE${NC}"
        return 1
    fi
    
    # 提取并格式化映射信息
    awk '/^[ \t]*- hostname:/ {
        # 提取 hostname
        gsub(/^[ \t]*- hostname:[ \t]*/, "")
        hostname = $0
        # 读取下一行获取 service
        if (getline > 0 && /^[ \t]*service:/) {
            gsub(/^[ \t]*service:[ \t]*/, "")
            service = $0
            printf "  %-40s -> %s\n", hostname, service
        }
    }' "$CONFIG_FILE"
    
    # 显示 tunnel 名称
    tunnel_name=$(grep "^tunnel:" "$CONFIG_FILE" | awk '{print $2}')
    if [ -n "$tunnel_name" ]; then
        echo ""
        echo -e "Tunnel: ${GREEN}$tunnel_name${NC}"
    fi
    
    echo ""
}

function restart_service() {
    echo -e "${YELLOW}重启 Cloudflare Tunnel 服务...${NC}"
    
    # 先验证配置
    validate_config
    
    # 重启服务
    echo "需要 sudo 权限来重启系统服务"
    sudo launchctl unload -w "$PLIST_FILE" 2>/dev/null
    sleep 2
    sudo launchctl load -w "$PLIST_FILE"
    
    sleep 3
    
    # 检查服务状态
    if sudo launchctl list | grep -q "$SERVICE_NAME"; then
        echo -e "${GREEN}服务已重启成功${NC}"
        # 获取 tunnel 信息
        tunnel_name=$(grep "^tunnel:" "$CONFIG_FILE" | awk '{print $2}')
        if [ -n "$tunnel_name" ]; then
            sleep 2
            echo ""
            cloudflared tunnel info "$tunnel_name" 2>/dev/null || true
        fi
    else
        echo -e "${RED}服务重启失败${NC}"
        echo "请查看日志: $0 logs"
        exit 1
    fi
}

function check_status() {
    echo -e "${GREEN}Cloudflare Tunnel 服务状态：${NC}"
    echo ""
    
    # 检查 LaunchDaemon 状态
    if sudo launchctl list | grep -q "$SERVICE_NAME"; then
        echo -e "LaunchDaemon: ${GREEN}运行中${NC}"
        sudo launchctl list | grep "$SERVICE_NAME"
    else
        echo -e "LaunchDaemon: ${RED}未运行${NC}"
    fi
    
    echo ""
    
    # 检查进程
    if pgrep -x cloudflared > /dev/null; then
        echo -e "Cloudflared 进程: ${GREEN}运行中${NC}"
        ps aux | grep cloudflared | grep -v grep | head -1
    else
        echo -e "Cloudflared 进程: ${RED}未运行${NC}"
    fi
    
    echo ""
    
    # 获取 tunnel 信息
    tunnel_name=$(grep "^tunnel:" "$CONFIG_FILE" | awk '{print $2}')
    if [ -n "$tunnel_name" ]; then
        echo -e "Tunnel 名称: ${GREEN}$tunnel_name${NC}"
        echo ""
        cloudflared tunnel info "$tunnel_name" 2>/dev/null || echo -e "${YELLOW}无法获取 tunnel 信息${NC}"
    fi
}

function show_logs() {
    echo -e "${GREEN}查看最近的日志：${NC}"
    echo ""
    
    # 系统级日志
    if [ -f "/Library/Logs/com.cloudflare.cloudflared.out.log" ]; then
        echo "标准输出日志："
        sudo tail -n 20 "/Library/Logs/com.cloudflare.cloudflared.out.log"
    fi
    
    echo ""
    
    if [ -f "/Library/Logs/com.cloudflare.cloudflared.err.log" ]; then
        echo "错误日志："
        sudo tail -n 20 "/Library/Logs/com.cloudflare.cloudflared.err.log"
    fi
    
    echo ""
    echo -e "${YELLOW}持续查看日志请运行:${NC}"
    echo "  sudo tail -f /Library/Logs/com.cloudflare.cloudflared.err.log"
}

# 添加新函数
function validate_config() {
    echo -e "${YELLOW}验证配置文件...${NC}"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${RED}配置文件不存在: $CONFIG_FILE${NC}"
        exit 1
    fi
    
    if cloudflared tunnel ingress validate > /dev/null 2>&1; then
        echo -e "${GREEN}配置验证通过${NC}"
        return 0
    else
        echo -e "${RED}配置验证失败：${NC}"
        cloudflared tunnel ingress validate
        exit 1
    fi
}

function install_service() {
    echo -e "${GREEN}安装 Cloudflare Tunnel 服务...${NC}"
    
    # 验证配置
    validate_config
    
    echo "安装系统级服务（需要 sudo 权限）"
    sudo cloudflared --config "$CONFIG_FILE" service install
    
    # 确保 plist 文件包含正确的参数
    if [ -f "$PLIST_FILE" ]; then
        echo -e "${GREEN}服务已安装到: $PLIST_FILE${NC}"
        echo "启动服务..."
        sudo launchctl load -w "$PLIST_FILE"
    else
        echo -e "${RED}服务安装失败${NC}"
        exit 1
    fi
    
    sleep 3
    check_status
}

function uninstall_service() {
    echo -e "${YELLOW}卸载 Cloudflare Tunnel 服务...${NC}"
    
    echo "卸载系统级服务（需要 sudo 权限）"
    sudo launchctl unload -w "$PLIST_FILE" 2>/dev/null
    sudo cloudflared service uninstall
    
    echo -e "${GREEN}服务已卸载${NC}"
}

# 主程序
case "$1" in
    add)
        add_mapping "$2" "$3"
        ;;
    remove)
        remove_mapping "$2"
        ;;
    list)
        list_mappings
        ;;
    restart)
        restart_service
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
        ;;
    validate)
        validate_config
        ;;
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    *)
        show_usage
        exit 1
        ;;
esac