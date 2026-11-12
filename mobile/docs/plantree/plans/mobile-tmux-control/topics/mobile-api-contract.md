# Mobile API Contract Sketch

Date: 2026-06-17
Status: Draft

## Purpose

Define the shape of a CCB-aware mobile gateway API before choosing a frontend
or fork base. This is not an implementation contract yet; it is the minimum
shape needed to test whether a mobile client can control multiple CCB projects
without becoming a generic tmux client.

Decision 005 changes the primary client target to a native Flutter app for
Android, iOS, and iPadOS. The API should therefore work behind two app
transports:

- `GatewayTransport`: HTTPS/WebSocket to `ccb mobile serve`;
- `SshTransport`: SSH PTY/exec commands for the first vertical slice and power
  users.

Decision 006 adds a route-provider boundary under `GatewayTransport`:

- `lan`;
- `tailnet`;
- `cloudflare_tunnel`;
- `relay`, post-MVP research.

Route providers change how the app reaches the gateway. They must not change
the project, agent, content, event, terminal-token, or terminal-frame contract.

## Layers

External mobile API:

- HTTP JSON for request/response operations;
- WebSocket or Server-Sent Events for project updates and terminal streams;
- paired-device tokens with explicit scopes.
- QR-imported host profiles for either gateway or SSH-direct transport.
- route metadata that identifies LAN/tailnet/Cloudflare/relay reachability
  without changing CCB action schemas.

Internal CCB API:

- gateway calls `CcbdClient` per registered project;
- existing `ccbd` ops should be reused first;
- missing tmux/pane operations should be added as `ccbd` endpoints, not as raw
  gateway tmux commands.
- SSH-direct mode may call `ccb mobile ... --json` wrappers, but those wrappers
  should enforce the same identity and stale-target rules as gateway endpoints.

## Native Transport Compatibility

The mobile app should not expose generic host tmux browsing as the main
workflow. Both transport modes should present the same CCB-shaped model:

- host;
- project;
- named agent/window;
- ProjectView status;
- scoped terminal target;
- Markdown/content item;
- completion/attention event.

`GatewayTransport` is the preferred product path because it can hide server
paths, issue short-lived terminal tokens, multiplex events, and later support a
relay. `SshTransport` is acceptable for the first native vertical slice and as
a durable fallback when the user already has SSH connectivity.

The app-facing repository abstraction should look roughly like:

```text
MobileCcbRepository
  listProjects()
  getProjectView(project_id)
  getAgentConversation(project_id, agent, cursor, limit)
  sendAgentMessage(project_id, agent, body, idempotency_key)
  focusAgent(project_id, agent)
  openTerminal(project_id, target, size)
  sendTerminalInput(terminal_id, input)
  getContent(project_id, content_id)
  subscribeEvents(cursor)
  requestLifecycle(project_id, action)
```

The concrete implementation may be gateway calls or SSH commands; UI code
should not know which one is active.

Normal user messages from the mobile composer should use
`sendAgentMessage`, not `sendTerminalInput`. Terminal input remains an
explicit raw-control permission and should not be required for chat.

## Pairing Route Envelope

QR pairing should wrap route metadata around the same CCB device-pairing
contract:

```json
{
  "scheme": "ccb-mobile",
  "transport": "gateway",
  "route_provider": "cloudflare_tunnel",
  "gateway_url": "https://ccb-mobile.example.com",
  "host_id": "host_...",
  "pairing_token": "short-lived",
  "expires_at": "2026-06-18T12:00:00Z",
  "server_fingerprint": "sha256:...",
  "capabilities": [
    "http_json",
    "websocket_terminal",
    "event_cursor"
  ]
}
```

For relay, the same envelope should change only the route fields, for example
`route_provider: relay` and relay bootstrap fields. The CCB pairing token,
device id, scopes, terminal token, and project ids remain CCB-owned.

## Identity Model

Every mobile action should carry stable CCB identity, not just tmux identity:

- `host_id`: gateway host identity;
- `project_id`: CCB project identity from `ccbd`/ProjectView;
- `project_root`: display and diagnostics only;
- `namespace_epoch`: stale-view guard for tmux namespace actions;
- `window`: configured CCB window name;
- `agent`: configured CCB agent slot name;
- `pane_id`: current evidence only;
- `runtime_generation` or equivalent runtime marker when available;
- `device_id`: paired mobile device identity;
- `scope`: permission scope used for the action.

`pane_id` must never be accepted alone for a destructive or input action.

## Existing Internal Endpoints To Reuse

The current `ccbd` client endpoint set already includes the first useful mobile
control primitives:

- `ping`
- `project_view`
- `project_focus_window`
- `project_focus_agent`
- `project_sidebar_click`
- `project_view_dismiss_comms`
- `project_restart_panes`
- `project_restart_agent`
- `project_clear_context`
- `project_reload_config`
- `submit`, `get`, `watch`, `queue`, `trace`, `inbox`, `ack`, `cancel`

Mobile should use these through a CCB-aware gateway wrapper. The browser should
not connect to arbitrary host tmux directly; the server gateway can open
CCB-scoped tmux streams after project and pane validation.

For SSH-direct mode, expose narrow wrappers instead of requiring the app to
reconstruct internal socket paths:

- `ccb mobile projects --json`
- `ccb mobile project-view --project <id> --json`
- `ccb mobile focus-agent --project <id> --agent <name> --json`
- `ccb mobile content-get --project <id> --content <id> --json`
- `ccb mobile terminal-attach --project <id> --target agent:<name>`
- `ccb mobile pane-snapshot --project <id> --target agent:<name> --json`
- `ccb mobile lifecycle --project <id> --action wake|stop --json`

The attach wrapper may internally execute `tmux -S <project_socket>
attach-session`, but the phone should not need to assemble that command from
unstable runtime files.

## New Internal Endpoints Likely Needed

### `project_view_subscribe`

Purpose: stream project-view deltas or snapshots.

Initial alternative: poll `project_view` at its short TTL until the event model
is stable.

Draft request:

```json
{
  "schema_version": 1,
  "cursor": "optional-last-event-id"
}
```

Draft event types:

- `project.snapshot`
- `project.health`
- `agent.state`
- `agent.activity`
- `comms.item`
- `comms.ack`
- `window.focus`
- `namespace.changed`
- `project.lifecycle`
- `agent.completion`

### `mobile_projects_list`

Purpose: list registered, recent, and favorite CCB projects for the mobile
home screen.

Draft response:

```json
{
  "projects": [
    {
      "project_id": "project-id",
      "display_name": "ccb_source",
      "root": "/path/to/project",
      "favorite": true,
      "pinned_order": 10,
      "last_opened_at": "2026-06-18T00:00:00Z",
      "lifecycle": "running",
      "health": "online",
      "active_agents": 3,
      "waiting_callbacks": 1,
      "unread_comms": 2
    }
  ]
}
```

### `mobile_project_favorite_set`

Purpose: pin, unpin, and reorder frequent projects.

Draft request:

```json
{
  "project_id": "project-id",
  "favorite": true,
  "pinned_order": 10
}
```

### `mobile_project_lifecycle`

Purpose: wake/open or close/stop a registered CCB project through CCB-owned
lifecycle behavior.

Draft request:

```json
{
  "project_id": "project-id",
  "action": "wake"
}
```

Allowed actions:

- `wake`: start or attach the project backend if allowed;
- `open`: attach/open remote view for an already running project;
- `close`: close the mobile view only;
- `stop`: stop the project backend using CCB shutdown semantics;
- `force_stop`: admin-only, explicit confirmation required.

`stop` and `force_stop` must not be raw tmux kill operations.

### `mobile_agent_conversation`

Purpose: return the selected agent's mobile chat timeline without requiring
the app to scrape tmux output.

Draft request:

```text
GET /v1/projects/{project_id}/agents/{agent}/conversation?cursor=&limit=50
```

Draft response:

```json
{
  "schema_version": 1,
  "project_id": "project-id",
  "agent": "mobile",
  "cursor": "next-cursor",
  "items": [
    {
      "id": "msg_123",
      "kind": "user_message",
      "state": "sent",
      "format": "markdown",
      "body": "Please summarize the status.",
      "created_at": "2026-06-21T00:00:00Z"
    },
    {
      "id": "reply_456",
      "kind": "agent_reply",
      "format": "markdown",
      "content_id": "content_456",
      "body_preview": "Current status...",
      "created_at": "2026-06-21T00:00:10Z"
    }
  ]
}
```

Initial item kinds:

- `user_message`
- `agent_reply`
- `callback_request`
- `comms_item`
- `status_event`
- `tool_event`
- `artifact_card`
- `terminal_history_block`
- `system_notice`

The default pane-backed implementation should synthesize a conservative
timeline from live terminal output, readable terminal-history evidence,
ProjectView, Comms, message bureau state, reply delivery state, and artifacts.
Terminal-derived entries must be labeled by source and deduplicated against
optimistic local sends; structured CCB records still enrich state, attention,
artifacts, and Comms.

### `mobile_pane_chat_send`

Purpose: send text from the selected-agent composer to the selected agent's
CCB-validated tmux pane. This is the default chat send path after
[Decision 015](../decisions/015-pane-backed-chat-input.md).

Preferred foundation:

```text
POST /v1/projects/{project_id}/terminals
GET  /v1/terminals/{terminal_id}              # WebSocket terminal frames
```

Draft terminal frames:

```json
{
  "type": "paste",
  "seq": 12,
  "text": "User text"
}
```

```json
{
  "type": "input",
  "seq": 13,
  "bytes_b64": "DQ=="
}
```

Rules:

- require `terminal_input`;
- reject stale namespace/project evidence when needed;
- reuse terminal handle renewal/reconnect behavior;
- do not automatically replay terminal input on retry;
- deduplicate optimistic local user bubbles against pane echo;
- record audit metadata without storing private message text in gateway audit
  logs;
- keep raw Open Terminal as the full-control surface over the same pane.

### `mobile_agent_message_submit`

Purpose: compatibility or future explicit action for sending text through CCB
ask/message authority. This is no longer the default selected-agent composer
path.

Draft request:

```text
POST /v1/projects/{project_id}/agents/{agent}/messages
```

Rules:

- require a paired device scope such as `ask` or `message_submit`;
- reject stale namespace/project evidence when needed;
- use idempotency keys so network retries do not duplicate CCB message
  submissions;
- do not silently replace the pane-backed default composer path.

### `mobile_agent_events`

Purpose: update the timeline after send. Polling can be the MVP; SSE or
WebSocket can be added after the item/cursor model stabilizes.

Draft request:

```text
GET /v1/projects/{project_id}/agents/{agent}/events?cursor=
```

Useful event classes:

- `message.queued`
- `message.started`
- `message.failed`
- `reply.available`
- `callback.waiting`
- `comms.updated`
- `agent.state`
- `content.available`
- `terminal_history.updated`

### `project_pane_snapshot`

Purpose: read pane output through CCB authority.

Draft request:

```json
{
  "schema_version": 1,
  "namespace_epoch": 12,
  "target": {
    "kind": "agent",
    "agent": "coder"
  },
  "lines": 120,
  "format": "text"
}
```

Allowed target kinds:

- `agent`
- `window_active_pane`
- `pane_evidence`, only when paired with window/agent identity and epoch

Draft response:

```json
{
  "snapshot": {
    "project_id": "project-id",
    "namespace_epoch": 12,
    "window": "main",
    "agent": "coder",
    "pane_id": "%7",
    "alive": true,
    "captured_at": "2026-06-17T00:00:00Z",
    "format": "text",
    "content": "..."
  }
}
```

Text mode can use current pane capture helpers. ANSI mode can be added once the
mobile renderer path is chosen.

### `project_content_get`

Purpose: fetch full CCB message, reply, or text-artifact content for mobile
Markdown display.

`project_view` can keep lightweight previews. Full Markdown bodies should be
loaded on demand to avoid bloating the high-frequency project view response.

Draft request:

```json
{
  "schema_version": 1,
  "kind": "comms_job",
  "id": "job-id",
  "format": "markdown"
}
```

Allowed content kinds:

- `ask_request`
- `reply`
- `comms_job`
- `text_artifact`
- `provider_message`, after provider-log ownership is defined

Draft response:

```json
{
  "content": {
    "id": "job-id",
    "source": "ccbd",
    "format": "markdown",
    "text": "...",
    "artifact": null,
    "render_hints": {
      "trust": "project-local",
      "allow_html": false,
      "max_preview_chars": 1200
    }
  }
}
```

This endpoint should resolve `body_artifact` references through CCB storage
validation instead of returning arbitrary file paths to the phone.

Content and artifact action metadata should let the app separate Download from
Open. For validated remote files, the response or linked artifact record should
include a stable content/file id, display filename, MIME type, size when known,
and whether the item can be downloaded through the authenticated gateway. The
phone should never open a server path directly; Open means "download or reuse
the cached local copy, then invoke the OS app chooser." HTTP/HTTPS links can be
opened externally after user confirmation; local file links require gateway
resolution into validated CCB content first.

### `project_terminal_open`

Purpose: issue a short-lived terminal token for a selected CCB target.

Draft request:

```json
{
  "namespace_epoch": 12,
  "mode": "interactive",
  "target": {
    "kind": "agent",
    "agent": "coder"
  },
  "terminal": {
    "cols": 80,
    "rows": 24
  }
}
```

Draft response:

```json
{
  "terminal": {
    "terminal_id": "term_...",
    "token": "single-use-token",
    "expires_in_ms": 30000,
    "mode": "interactive",
    "transport": "websocket"
  }
}
```

The token binds to project id, namespace epoch, target slot/window, current
pane evidence, device id, and permission scope.

### `project_terminal_input`

Purpose: send raw terminal input only after explicit permission.

Draft request:

```json
{
  "terminal_id": "term_...",
  "kind": "text",
  "data": "ls",
  "submit": false
}
```

Input kinds:

- `text`
- `key`
- `paste`
- `resize`
- `close`

Multiline paste should use CCB's tmux buffer strategy rather than key-by-key
input.

### `project_mobile_event_ack`

Purpose: acknowledge mobile-visible events such as Comms items or attention
notifications without confusing them with terminal input.

This can wrap existing `ack` and Comms endpoints where possible.

### `mobile_notifications_subscribe`

Purpose: stream completion and attention events for paired mobile clients.

Event classes:

- task completed;
- task failed/incomplete/cancelled;
- callback waiting;
- Comms mention;
- agent unhealthy or missing;
- project started/stopped/offline;
- terminal disconnected.

P0 task-completed events should be enough for the app to render a local OS
notification without exposing private task content:

```json
{
  "id": "notif_...",
  "kind": "task_completed",
  "project_id": "proj_...",
  "project_short_name": "test_ccb2",
  "agent": "agy1",
  "completed_at": "2026-06-30T08:00:00Z",
  "dedupe_key": "proj_...:agy1:completion_..."
}
```

The preferred app-facing transport is a dedicated server-wide gateway
subscription, such as SSE behind `mobile_notifications_subscribe`, with
`GET /v1/notifications` reserved for reconnect/catch-up if needed.
ProjectView deltas can remain a foreground/current-project fallback, but they
are not the P0 cross-project notification source. This is accepted by
[Decision 019](../decisions/019-app-lifetime-task-completion-notifications.md).

The mobile app should derive the notification text from only
`project_short_name`, `agent`, and `kind`: `<project short name> / <agent>
task completed`. Route payload may include `project_id`, `agent`,
`dedupe_key`, and `completed_at` so taps can deep-link without exposing task
content. The payload must not include terminal output, prompt text, reply text,
file paths, error details, or provider transcript detail. P0 should not require
a custom sound field; the app should use its default system notification
channel.

Dedupe guidance:

- persist a bounded recent `seenDedupeKeys` set, such as an LRU of the last 100
  keys, so reconnect/catch-up replay does not repost old notifications;
- derive the Android integer notification id from an explicit stable 32-bit
  hash of `dedupe_key`; do not depend on a runtime-random or process-local
  string hash unless the implementation proves it is stable enough;
- duplicate events with the same `dedupe_key` should replace the same system
  notification or be dropped, never create a notification burst.
- source should generate `dedupe_key`, preferably from
  `project_id + namespace_epoch + agent + completion_sequence_or_activity_transition_id`;
  the app must not guess dedupe from notification text or time windows.

## External Gateway Endpoints

Suggested HTTP shape:

- `POST /v1/pair/start`
- `POST /v1/pair/complete`
- `GET /v1/host`
- `GET /v1/health`
- `GET /v1/capabilities`
- `GET /v1/projects`
- `POST /v1/projects/{project_id}/favorite`
- `POST /v1/projects/{project_id}/lifecycle`
- `GET /v1/projects/{project_id}/view`
- `GET /v1/projects/{project_id}/events`
- `POST /v1/projects/{project_id}/focus/window`
- `POST /v1/projects/{project_id}/focus/agent`
- `POST /v1/projects/{project_id}/ask`
- `GET /v1/projects/{project_id}/content/{content_id}`
- `POST /v1/projects/{project_id}/panes/snapshot`
- `POST /v1/projects/{project_id}/terminals`
- `GET /v1/projects/{project_id}/terminals/{terminal_id}/stream`
- `POST /v1/projects/{project_id}/terminals/{terminal_id}/input`
- `POST /v1/projects/{project_id}/terminals/{terminal_id}/close`
- `GET /v1/notifications`

The gateway can keep this web-friendly while the internal `ccbd` protocol stays
line-delimited JSON RPC.

Cloudflare Tunnel mode should expose the same endpoints. Future relay mode
should either forward this endpoint set or map it to an equivalent framed
session without changing request/response schemas.

## Permission Scopes

Minimum scopes:

- `view`: project list, ProjectView, pane snapshots, event stream;
- `content`: full message/artifact content reads for Markdown display;
- `ask`: submit ask/composer messages and callback responses;
- `focus`: focus window/agent through `ccbd`;
- `terminal-input`: raw terminal input and paste;
- `lifecycle`: wake/open/close registered projects;
- `notify`: subscribe to completion/attention events;
- `admin`: restart panes/agents, clear context, reload config, stop project.

Default paired devices should start from a host-approved pairing profile. A
tmux-remote profile should include `view`, `content`, `focus`,
`terminal-input`, and `notify`; `ask` and `lifecycle` can be enabled when the
user wants full CCB control from the device. `admin` should remain separate and
require explicit host-side approval.

For the P0 task-completion notification package, `notify` is part of the
ordinary paired-device profile by default. Existing profiles that do not carry
`notify` should fail closed for OS notifications and guide the user to re-pair
or otherwise degrade without treating `view`, `content`, or `terminal-input` as
implicit notification scopes.

## Error Shape

Mobile should receive stable error codes, even if internal `ccbd` errors are
plain messages initially:

- `project_unavailable`
- `permission_denied`
- `stale_namespace_epoch`
- `target_missing`
- `pane_not_alive`
- `terminal_token_expired`
- `terminal_mode_denied`
- `tmux_transport_failed`
- `ccbd_unreachable`
- `project_not_registered`
- `lifecycle_denied`
- `notification_cursor_expired`
- `route_unavailable`
- `route_identity_changed`

Error responses should include whether the client should refresh ProjectView.

## Audit Events

Audit the operation, not private terminal content:

- device paired/revoked;
- project opened;
- project wake/stop requested;
- focus changed;
- ask/composer submitted;
- terminal opened/closed;
- paste submitted with byte/line counts, not content;
- admin action requested/executed/failed.

## MVP Boundary

The first MVP must include interactive terminal streaming because remote CCB
tmux control is the product center. A useful MVP has:

1. project registry;
2. paired mobile auth;
3. favorite/frequent project list;
4. wake/open and close/stop project lifecycle actions;
5. project terminal stream;
6. fast agent/window switching;
7. ProjectView side status;
8. completion/attention notifications;
9. Markdown/math content view.
