#!/bin/bash

# Bluetooth Audio Input Volume Fix for macOS
# Author: Claude & User
# Description: 自动调节蓝牙音频设备连接时的输入音量，并在可用时切换首选输出设备
# Version: 1.1

# 配置项
LOG_FILE="$HOME/Library/Logs/bluetooth_audio_fix.log"
LAST_STATE_FILE="/tmp/bluetooth_audio_last_state"
MAX_LOG_SIZE=1048576  # 1MB

# 可以在这里修改目标设备名称，留空则对所有蓝牙音频设备生效
TARGET_DEVICE="${BLUETOOTH_DEVICE_NAME:-}"

# 优选输出设备名称（可通过环境变量配置，留空则不切换）
PREFERRED_OUTPUT_DEVICE="${PREFERRED_OUTPUT_DEVICE:-}"
# 连接到设定操作之间的等待时间（秒）
POST_CONNECT_DELAY="${POST_CONNECT_DELAY:-2}"
# 输出设备匹配模式：exact 或 substring（默认 exact）
OUTPUT_MATCH_MODE="${OUTPUT_MATCH_MODE:-exact}"

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

# ===== 输出设备切换相关 =====
# 解析 SwitchAudioSource 路径（launchd 下 PATH 精简，需显式查找）
# 简单缓存避免重复查找
SAS_BIN_CACHE=""
find_switchaudio_bin() {
    if [ -n "$SAS_BIN_CACHE" ] && [ -x "$SAS_BIN_CACHE" ]; then
        echo "$SAS_BIN_CACHE"
        return 0
    fi
    if command -v SwitchAudioSource >/dev/null 2>&1; then
        SAS_BIN_CACHE=$(command -v SwitchAudioSource)
        echo "$SAS_BIN_CACHE"
        return 0
    fi
    # 常见 Homebrew 安装路径（Apple Silicon / Intel）
    for p in \
        "/opt/homebrew/bin/SwitchAudioSource" \
        "/usr/local/bin/SwitchAudioSource"; do
        if [ -x "$p" ]; then
            SAS_BIN_CACHE="$p"
            echo "$SAS_BIN_CACHE"
            return 0
        fi
    done
    return 1
}

# 检查 SwitchAudioSource 是否可用
check_switchaudio_available() {
    find_switchaudio_bin >/dev/null 2>&1
}

# 获取当前默认输出设备
get_current_output_device() {
    if check_switchaudio_available; then
        local sas
        sas=$(find_switchaudio_bin)
        "$sas" -c -t output 2>/dev/null
    else
        echo ""
    fi
}

# 检查目标输出设备是否存在
output_device_exists() {
    local device_name="$1"
    if check_switchaudio_available; then
        local sas
        sas=$(find_switchaudio_bin)
        "$sas" -a -t output 2>/dev/null | grep -Fxq "$device_name"
    else
        return 1
    fi
}

# 设置默认输出设备
set_output_device() {
    local device_name="$1"

    if [ -z "$device_name" ]; then
        log_message "输出设备名称为空，跳过设置"
        return 1
    fi

    if ! check_switchaudio_available; then
        log_message "未检测到 SwitchAudioSource，无法自动切换输出设备。可安装：brew install switchaudio-osx"
        return 1
    fi

    if ! output_device_exists "$device_name"; then
        local sas
        sas=$(find_switchaudio_bin)
        # 尝试按子串匹配唯一设备（仅在配置开启时）
        if [ "$OUTPUT_MATCH_MODE" = "substring" ]; then
            local candidates
            candidates=$("$sas" -a -t output 2>/dev/null | grep -F "$device_name" || true)
            local count
            count=$(echo "$candidates" | sed '/^\s*$/d' | wc -l | tr -d ' ')
            if [ "$count" = "1" ]; then
                local resolved
                resolved=$(echo "$candidates" | head -n1)
                log_message "按子串匹配解析到输出设备：$resolved（原始：$device_name）"
                device_name="$resolved"
            fi
        fi

        # 若仍找不到，则打印一次可用设备列表帮助排查
        if ! output_device_exists "$device_name"; then
            local all_devs
            all_devs=$("$sas" -a -t output 2>/dev/null | tr '\n' ',' | sed 's/,$//')
            log_message "未在可用输出设备中找到：$device_name，跳过切换。可用设备：${all_devs}"
            return 1
        fi
    fi

    local current_device
    current_device=$(get_current_output_device)
    if [ "$current_device" = "$device_name" ]; then
        log_message "当前默认输出已是目标：$device_name，跳过切换"
        return 0
    fi

    local sas
    sas=$(find_switchaudio_bin)
    log_message "SwitchAudioSource 路径：$sas"
    if "$sas" -s "$device_name" -t output >/dev/null 2>&1; then
        sleep 0.3
        local new_current
        new_current=$(get_current_output_device)
        if [ "$new_current" = "$device_name" ]; then
            log_message "已将默认输出设备切换为：$device_name"
        else
            log_message "切换输出设备后校验失败，当前为：${new_current:-未知}"
        fi
    else
        log_message "执行 SwitchAudioSource 切换输出设备失败：$device_name"
        return 1
    fi
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
        sleep "$POST_CONNECT_DELAY"
        
        # 设置输入音量
        local target_volume="${INPUT_VOLUME:-100}"
        local new_volume=$(set_input_volume "$target_volume")
        log_message "输入音量已设置为: $new_volume"

        # 切换输出设备：优先使用 PREFERRED_OUTPUT_DEVICE；若未配置，则尝试切到当前连接的蓝牙设备名
        local target_output_device
        if [ -n "$PREFERRED_OUTPUT_DEVICE" ]; then
            target_output_device="$PREFERRED_OUTPUT_DEVICE"
        else
            target_output_device="$current_device"
        fi

        if [ -n "$target_output_device" ]; then
            if check_switchaudio_available; then
                log_message "尝试切换默认输出到：$target_output_device"
                # 改为同步执行，便于日志按序可见
                set_output_device "$target_output_device"
            else
                log_message "未检测到 SwitchAudioSource，跳过输出切换（可选安装：brew install switchaudio-osx）"
            fi
        else
            log_message "未配置输出切换目标，且无法识别连接设备名称，跳过输出切换"
        fi
    fi
    
    # 保存当前状态
    save_state "$current_state"
}

# 执行主函数
main
