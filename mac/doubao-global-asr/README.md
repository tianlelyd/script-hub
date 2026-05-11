# Doubao IME Global ASR Switch

开启豆包输入法隐藏的全局语音输入快捷键开关 `isGloableASRShortcutEnable`。

## 使用方法

```bash
cd /Users/liyd/Tools/myspace/script-hub/mac/doubao-global-asr
./enable-doubao-global-asr.sh
```

查看帮助：

```bash
./enable-doubao-global-asr.sh --help
```

## 适用场景

- 豆包输入法重启后，全局语音快捷键失效。
- macOS 重启、豆包升级或设置被重置后，需要重新打开隐藏开关。
- 已经在豆包输入法设置里配置好了语音输入快捷键，但该快捷键在非豆包输入法下不生效。

## 使用限制

- 仅适用于 macOS。
- 依赖系统自带 `/usr/bin/swift`。
- 依赖豆包输入法当前版本暴露的内部通知：`DoubaoImeSettings.enableGloableASRShortcutNotification`。这是非公开接口，豆包升级后可能失效。
- 只负责请求开启 `isGloableASRShortcutEnable`，不负责设置语音快捷键。
- 不负责切换输入法，也不负责语音输入结束后切回微信输入法。
- 不负责授予系统权限；豆包全局快捷键可能仍需要在 macOS「隐私与安全性」里给豆包输入法麦克风或辅助功能权限。
- 如果运行时豆包输入法进程没有启动，脚本会给出警告；此时可先打开或重启豆包输入法，再重新运行脚本。
