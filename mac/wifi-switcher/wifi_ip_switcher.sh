#!/bin/bash

# ==========================================
# WiFi IP 手动切换工具
# ==========================================
# 用法：sudo ./wifi_ip_switcher.sh
# ==========================================

set -e

# 检测 Wi-Fi 服务名称
detect_service() {
    local wifi_device
    wifi_device=$(networksetup -listallhardwareports | awk '/Wi-Fi|AirPort/{getline; print $2}')
    networksetup -listallhardwareports | grep -B 1 "Device: $wifi_device" | grep "Hardware Port:" | sed 's/Hardware Port: //' | xargs
}

# 设置静态 IP
set_static() {
    local service=$1 ip=$2 mask=$3 router=$4
    shift 4
    local dns="$*"

    echo "正在配置..."
    echo "  IP: $ip / $mask"
    echo "  网关: $router"
    echo "  DNS: $dns"

    networksetup -setmanual "$service" "$ip" "$mask" "$router"
    networksetup -setdnsservers "$service" $dns

    echo "完成"
}

# 设置 DHCP
set_dhcp() {
    local service=$1
    echo "正在切换到 DHCP..."
    networksetup -setdhcp "$service"
    networksetup -setdnsservers "$service" "Empty"
    echo "完成"
}

# 主菜单
main() {
    if [ "$EUID" -ne 0 ]; then
        echo "请使用 sudo 运行此脚本"
        exit 1
    fi

    local service
    service=$(detect_service)

    if [ -z "$service" ]; then
        echo "未找到 Wi-Fi 服务"
        exit 1
    fi

    echo "==============================="
    echo "  WiFi IP 切换工具"
    echo "==============================="
    echo ""
    echo "  1) superGod_5G  (192.168.32.114)"
    echo "  2) mengmeng_5G  (192.168.31.114)"
    echo "  3) DHCP (自动获取)"
    echo ""
    echo "  0) 退出"
    echo ""
    read -p "请选择 [0-3]: " choice

    case $choice in
        1) set_static "$service" "192.168.32.114" "255.255.255.0" "192.168.32.1" "192.168.32.1" ;;
        2) set_static "$service" "192.168.31.114" "255.255.255.0" "192.168.31.2" "192.168.31.2" "192.168.31.1" ;;
        3) set_dhcp "$service" ;;
        0) echo "已退出" ;;
        *) echo "无效选择" ;;
    esac
}

main
