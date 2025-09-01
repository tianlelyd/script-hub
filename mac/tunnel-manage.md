# Cloudflare Tunnel 管理文档

## 1. 系统级服务管理

### ⚠️ macOS 系统级服务注意事项

在 macOS 中以 root 运行 Cloudflare Tunnel 服务时，需要特别注意：

1. **cloudflared service install 的局限性**：
   - `sudo cloudflared service install` 命令生成的 plist 文件**不包含配置文件路径**
   - 必须手动编辑 plist 文件添加配置参数

2. **正确的安装流程**：
```bash
# 1. 安装服务（会生成基础 plist 文件）
sudo cloudflared service install

# 2. 手动编辑 plist 文件
sudo nano /Library/LaunchDaemons/com.cloudflare.cloudflared.plist

# 3. 在 ProgramArguments 数组中添加配置参数：
<key>ProgramArguments</key>
<array>
    <string>/opt/homebrew/bin/cloudflared</string>
    <string>--config</string>
    <string>/Users/liyd/.cloudflared/config.yml</string>
    <string>tunnel</string>
    <string>run</string>
</array>

# 4. 重新加载服务使配置生效
sudo launchctl unload -w /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
sudo launchctl load -w /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
```

### 加载并启动服务
```bash
sudo launchctl load -w /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
```

### 停止服务
```bash
sudo launchctl unload /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
```

### 重启服务
```bash
sudo launchctl unload -w /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
sudo launchctl load -w /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
```

### 查看服务状态
```bash
sudo launchctl list | grep cloudflare
```

## 2. 配置文件位置

- 配置文件：`~/.cloudflared/config.yml`
- 服务配置：`/Library/LaunchDaemons/com.cloudflare.cloudflared.plist`
- 日志文件：
  - `/Library/Logs/com.cloudflare.cloudflared.out.log`
  - `/Library/Logs/com.cloudflare.cloudflared.err.log`

## 3. 使用管理脚本

### 脚本功能概览
```bash
./mac/tunnel-manage.sh {add|remove|list|restart|status|logs|install|uninstall|validate}
```

### 添加新端口映射（全自动）
```bash
# 自动完成：添加 DNS 记录、更新配置、验证、重启服务
./mac/tunnel-manage.sh add api.myandai.com 8080
```

### 查看所有映射
```bash
./mac/tunnel-manage.sh list
```
输出示例：
```
当前端口映射：
  lyd-mac-workroom.myandai.com             -> http://localhost:3000
  ai.myandai.com                            -> http://localhost:10000
  ssh.myandai.com                           -> http://localhost:4020

Tunnel: lyd-mac-workroom
```

### 查看服务状态
```bash
./mac/tunnel-manage.sh status
```

### 查看日志
```bash
./mac/tunnel-manage.sh logs
```

### 重启服务
```bash
./mac/tunnel-manage.sh restart
```

### 验证配置
```bash
./mac/tunnel-manage.sh validate
```

## 4. 配置文件示例

编辑 `~/.cloudflared/config.yml`：

```yaml
tunnel: lyd-mac-workroom
credentials-file: /Users/liyd/.cloudflared/3e2daba3-5f6a-41a5-b284-f5217ceff5d5.json

ingress:
  # 现有映射
  - hostname: lyd-mac-workroom.myandai.com
    service: http://localhost:3000
    
  # 添加新的端口映射
  - hostname: app2.myandai.com
    service: http://localhost:8080
    
  - hostname: api.myandai.com
    service: http://localhost:4000
    
  # 默认规则（必须在最后）
  - service: http_status:404

protocol: http2
```

## 5. 手动添加端口映射流程

如果需要手动操作，按以下步骤：

### 步骤 1: 添加 DNS 记录
```bash
cloudflared tunnel route dns lyd-mac-workroom app.myandai.com
```

### 步骤 2: 编辑配置文件
在 `ingress` 部分的 `service: http_status:404` 之前添加：
```yaml
  - hostname: app.myandai.com
    service: http://localhost:8080
```

### 步骤 3: 验证配置
```bash
cloudflared tunnel ingress validate
```

### 步骤 4: 重启服务
```bash
sudo launchctl unload -w /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
sudo launchctl load -w /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
```


## 6. 常见问题

### 查看日志
```bash
# 系统级服务日志
sudo tail -f /Library/Logs/com.cloudflare.cloudflared.err.log
sudo tail -f /Library/Logs/com.cloudflare.cloudflared.out.log

# 或使用管理脚本
./mac/tunnel-manage.sh logs
```

### 验证配置
```bash
cloudflared tunnel ingress validate
```

### 测试连接
```bash
# 测试 tunnel 连接
cloudflared tunnel info lyd-mac-workroom

# 测试特定域名
curl -I https://lyd-mac-workroom.myandai.com
```

## 7. 安全建议

1. **使用 HTTPS**: 对于生产环境，建议配置 HTTPS
2. **访问控制**: 可以在 Cloudflare Zero Trust 中配置访问策略
3. **日志监控**: 定期检查日志文件
4. **备份配置**: 在修改前备份配置文件

## 8. 快速开始

```bash
# 1. 安装 cloudflared
brew install cloudflare/cloudflare/cloudflared

# 2. 登录 Cloudflare
cloudflared login

# 3. 创建 tunnel（如果还没有）
cloudflared tunnel create lyd-mac-workroom

# 4. 创建配置文件
cat > ~/.cloudflared/config.yml << EOF
tunnel: lyd-mac-workroom
credentials-file: ~/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: app.yourdomain.com
    service: http://localhost:3000
  - service: http_status:404

protocol: http2
EOF

# 5. 安装系统级服务
sudo cloudflared --config ~/.cloudflared/config.yml service install

# 6. 启动服务
sudo launchctl load -w /Library/LaunchDaemons/com.cloudflare.cloudflared.plist

# 7. 使用管理脚本添加新映射
./mac/tunnel-manage.sh add api.yourdomain.com 8080
```

## 9. 管理脚本特性

### 全自动化流程
`tunnel-manage.sh add` 命令会自动完成：
1. ✅ 添加 DNS 记录到 Cloudflare
2. ✅ 更新本地配置文件
3. ✅ 验证配置正确性
4. ✅ 重启服务使配置生效
5. ✅ 错误时自动回滚

### 安全特性
- 配置修改前自动备份
- 验证失败自动恢复
- 服务状态实时检查

## 10. 故障排查

### 服务无法启动
```bash
# 检查配置文件语法
cloudflared tunnel ingress validate

# 查看详细错误
sudo tail -50 /Library/Logs/com.cloudflare.cloudflared.err.log
```

### DNS 记录问题
```bash
# 列出所有 DNS 记录
cloudflared tunnel route list

# 检查 tunnel 信息
cloudflared tunnel info lyd-mac-workroom
```

### 端口映射不工作
1. 确认本地服务正在运行：`curl http://localhost:port`
2. 检查配置文件格式
3. 查看错误日志
4. 验证 DNS 解析：`nslookup hostname.domain.com`