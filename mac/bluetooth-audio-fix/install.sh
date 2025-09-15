#!/bin/bash

# Bluetooth Audio Fix 安装脚本
# 自动配置 macOS 蓝牙音频输入音量修复

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${2}${1}${NC}"
}

print_error() {
    print_message "❌ $1" "$RED"
    exit 1
}

print_success() {
    print_message "✅ $1" "$GREEN"
}

print_info() {
    print_message "ℹ️  $1" "$YELLOW"
}

# 检查是否在 macOS 上运行
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "此脚本仅支持 macOS 系统"
    fi
}

# 可选依赖检测：SwitchAudioSource（用于切换默认输出设备）
check_switchaudiosource() {
    if command -v SwitchAudioSource >/dev/null 2>&1; then
        print_success "已检测到 SwitchAudioSource（输出切换可用）"
        return 0
    fi
    print_info "未检测到 SwitchAudioSource（可选）。如需自动切换输出设备，可安装：brew install switchaudio-osx"
    if command -v brew >/dev/null 2>&1; then
        read -p "是否通过 Homebrew 安装 switchaudio-osx？(Y/n，默认Y): " install_sas
        install_sas=${install_sas:-Y}
        if [[ "$install_sas" == "Y" || "$install_sas" == "y" ]]; then
            if brew install switchaudio-osx; then
                print_success "已安装 switchaudio-osx"
            else
                print_info "安装失败，稍后可手动执行：brew install switchaudio-osx"
            fi
        else
            print_info "已跳过安装，可后续手动安装：brew install switchaudio-osx"
        fi
    fi
}

# 主安装函数
install() {
    print_info "开始安装 Bluetooth Audio Fix..."
    # 检查可选依赖
    check_switchaudiosource
    
    # 获取脚本所在目录
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    # 定义安装路径
    INSTALL_DIR="$HOME/.bluetooth-audio-fix"
    PLIST_NAME="com.user.bluetooth.audio.fix"
    PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
    
    # 检查是否已安装
    if launchctl list | grep -q "$PLIST_NAME"; then
        print_info "检测到已安装的服务，正在卸载旧版本..."
        launchctl unload "$PLIST_PATH" 2>/dev/null || true
    fi
    
    # 创建安装目录
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$HOME/Library/LaunchAgents"
    
    # 复制监控脚本
    cp "$SCRIPT_DIR/bluetooth_audio_monitor.sh" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/bluetooth_audio_monitor.sh"
    print_success "监控脚本已安装"
    
    # 询问用户配置
    echo ""
    read -p "是否要指定特定的蓝牙设备？(y/n，默认为所有蓝牙音频设备): " specify_device
    
    DEVICE_NAME=""
    if [[ "$specify_device" == "y" ]] || [[ "$specify_device" == "Y" ]]; then
        echo ""
        print_info "当前系统中的音频设备："
        system_profiler SPAudioDataType | grep -E "^\s+[^:]+:$" | grep -v "Audio:" | sed 's/://g' | sed 's/^[[:space:]]*/  /'
        echo ""
        read -p "请输入设备名称（如 'HK Aura Studio 2'）: " DEVICE_NAME
    fi
    
    echo ""
    read -p "设置目标输入音量 (0-100，默认100): " target_volume
    target_volume=${target_volume:-100}

    echo ""
    read -p "设置首选输出设备名称（留空=不切换）: " preferred_output
    preferred_output=${preferred_output:-}
    
    # 创建 plist 文件
    cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>${INSTALL_DIR}/bluetooth_audio_monitor.sh</string>
    </array>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>BLUETOOTH_DEVICE_NAME</key>
        <string>${DEVICE_NAME}</string>
        <key>INPUT_VOLUME</key>
        <string>${target_volume}</string>
        <key>PREFERRED_OUTPUT_DEVICE</key>
        <string>${preferred_output}</string>
    </dict>
    
    <!-- 监听蓝牙相关的系统文件变化 -->
    <key>WatchPaths</key>
    <array>
        <string>/Library/Preferences/com.apple.Bluetooth.plist</string>
        <string>/Library/Preferences/Audio</string>
    </array>
    
    <!-- 限制执行频率，避免频繁触发 -->
    <key>ThrottleInterval</key>
    <integer>5</integer>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>${HOME}/Library/Logs/bluetooth_audio_fix_output.log</string>
    
    <key>StandardErrorPath</key>
    <string>${HOME}/Library/Logs/bluetooth_audio_fix_error.log</string>
</dict>
</plist>
EOF
    
    print_success "LaunchAgent 配置文件已创建"
    
    # 加载服务
    launchctl load "$PLIST_PATH"
    print_success "服务已启动"
    
    # 验证安装
    if launchctl list | grep -q "$PLIST_NAME"; then
        print_success "安装成功！"
        echo ""
        print_info "配置信息："
        if [ -n "$DEVICE_NAME" ]; then
            echo "  • 目标设备: $DEVICE_NAME"
        else
            echo "  • 目标设备: 所有蓝牙音频设备"
        fi
        echo "  • 目标音量: $target_volume"
        echo "  • 日志文件: $HOME/Library/Logs/bluetooth_audio_fix.log"
        echo ""
        print_info "使用以下命令管理服务："
        echo "  • 查看状态: launchctl list | grep bluetooth.audio"
        echo "  • 停止服务: launchctl unload $PLIST_PATH"
        echo "  • 启动服务: launchctl load $PLIST_PATH"
        echo "  • 查看日志: tail -f $HOME/Library/Logs/bluetooth_audio_fix.log"
        echo "  • 卸载服务: $INSTALL_DIR/uninstall.sh"
    else
        print_error "安装失败，请检查错误信息"
    fi
}

# 创建卸载脚本
create_uninstall_script() {
    INSTALL_DIR="$HOME/.bluetooth-audio-fix"
    cat > "$INSTALL_DIR/uninstall.sh" << 'EOF'
#!/bin/bash

# 卸载脚本
PLIST_NAME="com.user.bluetooth.audio.fix"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
INSTALL_DIR="$HOME/.bluetooth-audio-fix"

echo "正在卸载 Bluetooth Audio Fix..."

# 停止并卸载服务
if launchctl list | grep -q "$PLIST_NAME"; then
    launchctl unload "$PLIST_PATH" 2>/dev/null
    echo "✅ 服务已停止"
fi

# 删除文件
rm -f "$PLIST_PATH"
rm -rf "$INSTALL_DIR"
rm -f /tmp/bluetooth_audio_last_state

echo "✅ 卸载完成"
echo "日志文件保留在: $HOME/Library/Logs/bluetooth_audio_fix*.log"
echo "如需删除日志，请运行: rm -f $HOME/Library/Logs/bluetooth_audio_fix*.log"
EOF
    
    chmod +x "$INSTALL_DIR/uninstall.sh"
}

# 主执行流程
main() {
    check_macos
    install
    create_uninstall_script
}

main "$@"
