# CCB Mobile Cloudflare Tunnel Alpha 设置

状态：alpha / 开发者预览

这份文档说明当前 CCB Mobile 的 Cloudflare Tunnel 远程访问路线。Mobile
gateway 仍然只监听 loopback；Cloudflare 只负责公开 HTTPS/WSS 路由；CCB
继续负责配对、设备 token、terminal token、ProjectView 脱敏和本地主机侧设备撤销。

## 前置条件

- CCB 项目可以正常用 `ccb` 启动。
- 服务器已安装 `cloudflared`。
- 有 Cloudflare 账号，并且域名已经使用 Cloudflare nameservers。
- 有一个可用 hostname，例如 `mobile.example.com`。
- Cloudflare Network 设置中启用了 WebSockets。

Quick Tunnels 适合开发 smoke test，但 Cloudflare 官方说明它们只用于测试和开发。
正常 alpha 路线应使用 named tunnel。

## 创建 Named Tunnel

在运行 CCB 的服务器上执行：

```bash
cloudflared tunnel login
cloudflared tunnel create ccb-mobile
cloudflared tunnel route dns ccb-mobile mobile.example.com
```

创建 `~/.cloudflared/config.yml`：

```yaml
tunnel: <tunnel-uuid>
credentials-file: /home/<user>/.cloudflared/<tunnel-uuid>.json

ingress:
  - hostname: mobile.example.com
    service: http://127.0.0.1:8787
  - service: http_status:404
```

检查 tunnel：

```bash
cloudflared tunnel info ccb-mobile
```

## 启动 CCB Mobile Gateway

在 CCB 项目目录中启动 gateway：

```bash
ccb mobile serve \
  --listen 127.0.0.1:8787 \
  --public-url https://mobile.example.com \
  --route-provider cloudflare_tunnel
```

这个命令会输出短期 pairing code 和 claim endpoint。它不会监听公网地址。
`--public-url` 只写入配对元数据。
这里必须只填写 HTTPS origin，例如 `https://mobile.example.com`；不要包含
path、query string、fragment 或用户名密码。`ccb mobile serve` 会在输出 pairing
metadata 前拒绝非 origin public URL。

在另一个终端启动 Cloudflare tunnel：

```bash
cloudflared tunnel run ccb-mobile
```

## 配对手机 App

在 mobile app 的 gateway pairing 页面输入输出的 gateway URL 和 pairing code。
pairing code 默认 10 分钟过期，并且只能 claim 一次。

配对设备默认获得这些 scope：

- `view`
- `focus`
- `terminal_input`

terminal-open token 默认 5 分钟过期。terminal input 和 paste frame 必须使用单调递增
sequence number；断线后 reconnect 必须携带最新 output resume cursor。

## 管理已配对设备

下面命令需要在服务器同一个 CCB 项目目录中执行。它们是本地管理命令，不会通过公网
tunnel 暴露。

列出已配对设备：

```bash
ccb mobile devices
```

撤销丢失或弃用的设备：

```bash
ccb mobile revoke <device_id>
```

撤销设备会把设备标记为 revoked，并级联撤销该设备仍未关闭的 terminal handles。
之后如果旧 terminal token 所属设备已被撤销，terminal token 认证会失败。

## 开发 Smoke 验证

如果你在 `ccb_mobile` 开发仓库中工作，先运行 named-tunnel preflight。它会检查本地
`cloudflared` binary、config、credentials file、public URL、route provider 和
loopback origin 是否匹配，但不会启动 CCB runtime：

如果 `cloudflared` config 有多条 ingress，preflight 会选择 `hostname` 匹配
`--gateway-public-url` 的那条，并在该 origin 没有指向 `--gateway-listen` 端口时
阻断验证。
Named tunnel 必须使用固定 loopback `--gateway-listen`，例如
`127.0.0.1:8787`；默认动态端口 `127.0.0.1:0` 只适合本地 LAN 或 quick-tunnel
smoke。
public URL 必须只是 gateway origin。如果包含 path、query string、fragment
或用户名密码，preflight 会阻断，并给出 origin-only 的
`--gateway-public-url` 建议值。

```bash
tools/mobile_gateway_terminal_smoke.py \
  --cloudflared-named-tunnel-preflight \
  --gateway-listen 127.0.0.1:8787 \
  --gateway-public-url https://mobile.example.com \
  --route-provider cloudflare_tunnel
```

如果 preflight 返回 `status: blocked`，读取 JSON 输出里的 `next_actions` 列表。
它会给出缺失 `cloudflared` binary、config、credentials、DNS route 或 ingress
mismatch 时最短的修复 checklist。
同一份 JSON 还会包含 `config_template`，这是一段无副作用的
`~/.cloudflared/config.yml` 草案，会使用本次传入的 hostname 和
`--gateway-listen` origin。复制前需要把 tunnel id 和 credentials path 替换成
`cloudflared tunnel create` 生成的真实值。
如果你的 tunnel 不叫 `ccb-mobile`，加上 `--cloudflared-tunnel-name <name>`；
preflight checklist 和自动 smoke 都会使用同一个 tunnel name。
JSON 还会包含 `named_tunnel_smoke_command`，这是一条可复制命令，会保留相关
`cloudflared` binary、config path、tunnel name、固定 listen 地址、public URL 和
route provider 参数。
如果你想自己启动 `cloudflared`，使用 `cloudflared_run_command`；如果 tunnel
已经在运行，使用 `existing_tunnel_smoke_command`。

preflight 通过后，开发 smoke 可以自动启动 named tunnel 的
`cloudflared tunnel run`、启动 disposable CCB gateway、等待公网 `/v1/health`、
执行 route diagnostics 和 terminal streaming，最后清理运行时：

```bash
tools/mobile_gateway_terminal_smoke.py \
  --cloudflared-named-tunnel \
  --gateway-listen 127.0.0.1:8787 \
  --gateway-public-url https://mobile.example.com \
  --route-provider cloudflare_tunnel
```

如果 tunnel 已经在另一个终端运行，则省略 `--cloudflared-named-tunnel`，用同一个
public URL 运行 smoke 命令。

只有当 route diagnostics ready、ProjectView 和 terminal-open 响应保持脱敏、
terminal input/paste/resize/close 与 resume reconnect 都通过，并且 cleanup 停止
disposable CCB runtime 时，smoke 才算通过。

## 安全注意事项

- 不要使用 `--listen 0.0.0.0:...`；gateway 会拒绝非 loopback listen 地址。
- 不要把 Cloudflare Access identity 当成 CCB device identity 的替代品。
  Cloudflare Access 后续可以作为可选 defense-in-depth，但 CCB pairing 和 device
  token 才是控制权威。
- 不要在公开 route payload 中暴露 tmux socket path、tmux session name 或原始 pane
  authority。
- 不要把 Quick Tunnels 当成正常 alpha 路线。

## Cloudflare 官方文档

- Quick Tunnels:
  <https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/>
- Locally-managed tunnels:
  <https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/local-management/create-local-tunnel/>
- Tunnel routing:
  <https://developers.cloudflare.com/tunnel/routing/>
- WebSockets:
  <https://developers.cloudflare.com/network/websockets/>
