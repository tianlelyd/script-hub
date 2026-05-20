# MoMax BS6 蓝牙音箱切换脚本

这个脚本用于在 Mac 上一键连接、断开或切换 `MOMAX BS6` 蓝牙音箱。

## 依赖

需要安装 `blueutil`：

```bash
brew install blueutil
```

可选安装 `switchaudio-osx`，连接后自动把系统输出切到音箱：

```bash
brew install switchaudio-osx
```

## 使用

```bash
cd /Users/liyd/Tools/myspace/script-hub/mac/momax-bs6-switch
chmod +x momax-bs6.sh

./momax-bs6.sh connect
./momax-bs6.sh disconnect
./momax-bs6.sh toggle
./momax-bs6.sh status
```

当前系统里识别到的设备信息：

```text
Name: MOMAX BS6
Address: 55:44:8B:98:04:73
```

如果设备名识别不稳定，可以改用蓝牙地址：

```bash
blueutil --paired
MOMAX_DEVICE_ID="55:44:8B:98:04:73" ./momax-bs6.sh toggle
```

## 做成快捷入口

可以在 Raycast、Alfred、macOS Shortcuts 或 Automator 里运行：

```bash
/Users/liyd/Tools/myspace/script-hub/mac/momax-bs6-switch/momax-bs6.sh toggle
```

第一次运行如果提示没有蓝牙权限，打开：

```text
系统设置 > 隐私与安全性 > 蓝牙
```

然后给运行脚本的应用授权，例如 Terminal、iTerm、Raycast、快捷指令或 Codex。

## 限制

如果音箱当前已经被 iPhone 占用，Mac 不一定能直接抢占连接。这取决于音箱固件。此时需要先在 iPhone 上断开，或按音箱蓝牙键让它重新进入可连接状态，再运行脚本。
