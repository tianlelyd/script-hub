# Bluetooth Audio Fix for macOS

## 问题描述

macOS 在连接蓝牙音箱/耳机后，输入音量（Input Volume）经常会自动变得非常小，即使手动调节后，下次连接时仍会重置为很小的值。这个工具可以自动解决这个问题。

## 功能特点

- 🎯 **智能检测**：自动检测蓝牙音频设备连接事件
- 🔊 **自动调节**：连接时立即将输入音量调整到指定值
- 🎛️ **灵活配置**：支持指定特定设备或所有蓝牙音频设备
- 📝 **日志记录**：记录所有操作，方便排查问题
- 🚀 **低资源占用**：事件驱动，仅在蓝牙状态变化时运行

## 系统要求

- macOS 10.12 或更高版本
- Bash shell（系统自带）

## 快速安装

### 方法一：自动安装（推荐）

1. 克隆或下载此项目
2. 进入项目目录并运行安装脚本：

```bash
cd bluetooth-audio-fix
chmod +x install.sh
./install.sh
```

3. 按照提示进行配置：
   - 选择是否指定特定蓝牙设备
   - 设置目标输入音量（0-100）

### 方法二：手动安装

如果你想手动安装或自定义配置，请参考以下步骤：

1. 复制监控脚本到合适位置：
```bash
mkdir -p ~/.bluetooth-audio-fix
cp bluetooth_audio_monitor.sh ~/.bluetooth-audio-fix/
chmod +x ~/.bluetooth-audio-fix/bluetooth_audio_monitor.sh
```

2. 创建 LaunchAgent plist 文件：
```bash
cp com.user.bluetooth.audio.fix.plist ~/Library/LaunchAgents/
```

3. 加载服务：
```bash
launchctl load ~/Library/LaunchAgents/com.user.bluetooth.audio.fix.plist
```

## 使用方法

安装完成后，服务会自动在后台运行。当你连接蓝牙音频设备时，输入音量会自动调整到设定值。

### 常用命令

查看服务状态：
```bash
launchctl list | grep bluetooth.audio
```

查看日志：
```bash
tail -f ~/Library/Logs/bluetooth_audio_fix.log
```

临时停止服务：
```bash
launchctl unload ~/Library/LaunchAgents/com.user.bluetooth.audio.fix.plist
```

重新启动服务：
```bash
launchctl load ~/Library/LaunchAgents/com.user.bluetooth.audio.fix.plist
```

## 配置说明

### 环境变量

你可以通过修改 plist 文件中的环境变量来调整行为：

- `BLUETOOTH_DEVICE_NAME`：指定设备名称（留空则对所有蓝牙音频设备生效）
- `INPUT_VOLUME`：目标输入音量（0-100，默认100）

### 修改配置

1. 编辑 plist 文件：
```bash
nano ~/Library/LaunchAgents/com.user.bluetooth.audio.fix.plist
```

2. 修改 `EnvironmentVariables` 部分：
```xml
<key>EnvironmentVariables</key>
<dict>
    <key>BLUETOOTH_DEVICE_NAME</key>
    <string>你的设备名称</string>
    <key>INPUT_VOLUME</key>
    <string>100</string>
</dict>
```

3. 重新加载服务：
```bash
launchctl unload ~/Library/LaunchAgents/com.user.bluetooth.audio.fix.plist
launchctl load ~/Library/LaunchAgents/com.user.bluetooth.audio.fix.plist
```

## 卸载

运行卸载脚本：
```bash
~/.bluetooth-audio-fix/uninstall.sh
```

或手动卸载：
```bash
# 停止服务
launchctl unload ~/Library/LaunchAgents/com.user.bluetooth.audio.fix.plist

# 删除文件
rm -f ~/Library/LaunchAgents/com.user.bluetooth.audio.fix.plist
rm -rf ~/.bluetooth-audio-fix
rm -f /tmp/bluetooth_audio_last_state

# 删除日志（可选）
rm -f ~/Library/Logs/bluetooth_audio_fix*.log
```

## 故障排除

### 服务没有自动运行

1. 检查服务状态：
```bash
launchctl list | grep bluetooth.audio
```

2. 查看错误日志：
```bash
cat ~/Library/Logs/bluetooth_audio_fix_error.log
```

### 音量没有自动调整

1. 确认蓝牙设备名称是否正确：
```bash
system_profiler SPAudioDataType | grep -E "^\s+[^:]+:$"
```

2. 检查运行日志：
```bash
tail -20 ~/Library/Logs/bluetooth_audio_fix.log
```

### 权限问题

如果遇到权限问题，确保脚本有执行权限：
```bash
chmod +x ~/.bluetooth-audio-fix/bluetooth_audio_monitor.sh
```

## 工作原理

1. **事件监听**：通过 LaunchAgent 的 `WatchPaths` 功能监听系统蓝牙配置文件的变化
2. **状态检测**：检测蓝牙音频设备的连接状态
3. **智能触发**：仅在设备从"断开"变为"连接"时执行调节
4. **音量调节**：使用 AppleScript 设置系统输入音量

## 兼容性

- ✅ macOS Monterey (12.x)
- ✅ macOS Ventura (13.x)  
- ✅ macOS Sonoma (14.x)
- ✅ macOS Sequoia (15.x)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 作者

Created with Claude & User

---

**注意**：此工具通过系统 API 调节音量，不会修改系统文件或蓝牙驱动。