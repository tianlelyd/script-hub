# SleepDisabled 监控

只读排查 macOS 睡眠设置变化及 pmset 调用者，不修改电源设置。

- `watch.py`：每约 2 秒采样，记录 SleepDisabled 初始值、变化、防睡眠断言和相关系统日志。
- `audit.py`：记录所有 pmset 查询和写入调用，包括参数、进程身份及父进程信息；写入调用另存一份。

## 使用

需要 macOS 13+、Python 3.9+。审计需要管理员权限，并给启动它的终端应用授予“完全磁盘访问权限”。

在仓库根目录，分别打开两个终端运行：

```sh
python3 mac/sleep-watch/watch.py
sudo "$(command -v python3)" mac/sleep-watch/audit.py
```

默认运行 24 小时，分别按 Ctrl-C 停止。支持 `--duration 秒数`（1–86400）和 `--output-dir 路径`。同类监控不能重复使用同一目录；审计目录必须归 root 所有且不可被组或其他用户写入。

## 日志

普通监控写入脚本旁的 `logs/`；审计写入 `/var/log/sleep-watch/`。

| 文件 | 内容 |
| --- | --- |
| `events.jsonl` | 参数变化、断言、系统日志及运行状态 |
| `caller-audit.jsonl` | 所有 pmset 调用及审计运行状态 |
| `writer-audit.jsonl` | 单独保留的潜在写入调用 |
| `caller-audit-eslogger.stderr` | 审计工具错误，权限问题优先查看此文件 |

每份 JSONL 超过约 5 MB 后轮转为 `*.previous.jsonl`，仅保留当前和上一段，重要记录需及时另存。两种监控都有心跳；`sequence_gap` 表示审计检测到事件缺口。

调用记录中，`args` 是命令参数，`actor` 是直接调用进程，`target` 是 pmset 进程，`parent` 是已确认的父进程。`responsible_audit_token` 标识责任进程，需结合进程路径确认所属应用；审计启动前已存在的进程可能无法补全路径。

`time` 为本地收集时间，`es_time` 为原始执行时间。调用记录不代表写入成功，应结合参数变化判断；直接通过系统 API 修改、采样间隔内的快速变化或审计丢失的事件可能无法追踪。
