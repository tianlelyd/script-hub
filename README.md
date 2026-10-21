# script-hub
Some commonly used scripts

## maskData

脱敏数据「Json OR Yame」

```shell
node .\maskData.js -t json -f .\mrsoft.common.config.json -o .\mrsoft.common.config--.json
```

## generateStructure

生成项目文件夹结构树

```shell
node ..\script-hub\generateStructure.js ./
```

## macOS 工具

- [Doubao IME Global ASR Switch](./mac/doubao-global-asr/README.md): 开启豆包输入法隐藏的全局语音输入快捷键开关。
- [SleepDisabled 参数监控与调用者审计](./mac/sleep-watch/README.md): 记录睡眠开关变化，追踪 pmset 的调用进程与参数。
