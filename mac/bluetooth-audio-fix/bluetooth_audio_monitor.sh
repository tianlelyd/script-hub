#!/bin/bash

# Bluetooth Audio Input Volume Fix for macOS
# Author: Claude & User
# Description: 自动调节蓝牙音频设备连接时的输入音量
# Version: 1.0

# 配置项
LOG_FILE="$HOME/Library/Logs/bluetooth_audio_fix.log"
LAST_STATE_FILE="/tmp/bluetooth_audio_last_state"
MAX_LOG_SIZE=1048576  # 1MB

# 可以在这里修改目标设备名称，留空则对所有蓝牙音频设备生效
TARGET_DEVICE="${BLUETOOTH_DEVICE_NAME:-}"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 日志轮转
rotate_log() {
    if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || echo 0) -gt $MAX_LOG_SIZE ]; then
        mv "$LOG_FILE" "$LOG_FILE.old"
    fi
}

# 记录日志
log_message() {
    rotate_log
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$LOG_FILE"
}

# 检查蓝牙音频设备是否连接
check_bluetooth_device() {
    if [ -n "$TARGET_DEVICE" ]; then
        # 检查特定设备
        system_profiler SPAudioDataType 2>/dev/null | grep -q "$TARGET_DEVICE"
    else
        # 检查任何蓝牙音频设备
        system_profiler SPAudioDataType 2>/dev/null | grep -q "Transport: Bluetooth"
    fi
    return $?
}

# 获取当前连接的蓝牙音频设备名称
get_bluetooth_device_name() {
    system_profiler SPAudioDataType 2>/dev/null | \
    awk '/Transport: Bluetooth/{for(i=NR-10;i<NR;i++)if(a[i]~/^[[:space:]]+[^:]+:$/){gsub(/^[[:space:]]+|:$/,"",a[i]);print a[i];exit}}{a[NR]=$0}'
}

# 设置输入音量
set_input_volume() {
    local volume="${1:-100}"
    osascript -e "set volume input volume $volume" 2>/dev/null
    local current_volume=$(osascript -e 'input volume of (get volume settings)' 2>/dev/null)
    echo "$current_volume"
}

# 获取当前状态
get_current_state() {
    if check_bluetooth_device; then
        local device_name=$(get_bluetooth_device_name)
        echo "connected:$device_name"
    else
        echo "disconnected"
    fi
}

# 读取上次状态
get_last_state() {
    if [ -f "$LAST_STATE_FILE" ]; then
        cat "$LAST_STATE_FILE"
    else
        echo "unknown"
    fi
}

# 保存当前状态
save_state() {
    echo "$1" > "$LAST_STATE_FILE"
}

# 主函数
main() {
    current_state=$(get_current_state)
    last_state=$(get_last_state)
    
    # 解析当前状态
    current_connection="${current_state%%:*}"
    current_device="${current_state#*:}"
    
    # 解析上次状态
    last_connection="${last_state%%:*}"
    
    # 只在状态从断开变为连接时执行
    if [ "$current_connection" = "connected" ] && [ "$last_connection" != "connected" ]; then
        if [ -n "$current_device" ]; then
            log_message "检测到蓝牙音频设备已连接: $current_device"
        else
            log_message "检测到蓝牙音频设备已连接"
        fi
        
        # 等待系统完全建立连接
        sleep 2
        
        # 设置输入音量
        local target_volume="${INPUT_VOLUME:-100}"
        local new_volume=$(set_input_volume "$target_volume")
        log_message "输入音量已设置为: $new_volume"
    fi
    
    # 保存当前状态
    save_state "$current_state"
}

# 执行主函数
main