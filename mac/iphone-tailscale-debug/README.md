# iPhone Tailscale 远程调试

通过本机 OrbStack 代理，让 Xcode 连接已配对 iPhone 的 Tailscale 地址，无需路由器 SSH 或转发规则。

## 前提

- Mac 已安装 Python 3.8+、Xcode、Tailscale 和 OrbStack，`tailscale`、`docker`、`dns-sd` 可在终端调用；Docker 使用 OrbStack 上下文。
- Mac 和 iPhone 登录同一 tailnet；手机已与 Mac 配对，开启开发者模式并解锁。
- 本机已有 `ghcr.io/open-webui/open-webui:main` 镜像及其中的 Python 3.11。脚本仅使用其 Python，覆盖入口并禁用健康检查，不启动 Open WebUI、不挂载其数据、不下载镜像。
- 本目录存在 `iphone-profile.json`。当前机器已保留原配置；其他机器先复制 `iphone-profile.example.json`，再填入目标手机实际的 `_remotepairing._tcp` Bonjour 服务名、端口和 TXT 记录。模板中的占位值不能直接使用。

## 使用

在项目根目录执行：

```sh
python3 mac/iphone-tailscale-debug/iphone-tailscale-debug.py
```

按提示输入手机的 Tailscale IPv4 地址。看到“已发布调试服务”后，在 Xcode 选择原来的 iPhone 并 Run。按 Ctrl-C 撤销发布并关闭容器及代理连接；手机上已启动的 App 不会因此退出。

可直接传入 IP，或用 `--port` 覆盖控制端口：

```sh
python3 mac/iphone-tailscale-debug/iphone-tailscale-debug.py 100.x.x.x --port 59123
```

## 限制与清理

- 依赖 OrbStack 的本地 bridge 接口；代理监听虚拟机的 TCP 49000、49152–65535，仅接受 Mac 虚拟接口地址的连接。端口被占用时退出，不停止其他程序。
- 本地配置对应特定手机的已有配对发现信息。重新配对、系统更新、身份或端口变化后可能需更新配置；本工具不会自动重新发现手机。
- 正常退出清理容器和 Bonjour 发布；主进程异常退出时通过管道 EOF 清理，代理另有 40 秒心跳租约兜底。运行期间不要暂停 OrbStack。
- 配置和 `last-run.json` 属于本地文件，已加入 Git 忽略规则。日志中的“已发布”表示发现服务已启动，不代表 Xcode 已成功连接。

2026-09-29 的原始版本实机验证覆盖约 130 秒连续查询、启动已安装 App、正常停止后断开，以及强制结束主进程后的容器清理。未覆盖重新安装 App、断点和蜂窝网络；迁入本仓库不代表这些场景已重新验证。
