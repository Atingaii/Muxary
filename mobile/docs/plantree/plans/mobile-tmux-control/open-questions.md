# Mobile Tmux Control Open Questions

Date: 2026-06-17

## Current Execution Gates

No unresolved question currently blocks the app-side gateway boundary package;
that package has landed. Android runtime validation is available through AVD
`ccb_mobile_api35`.

The first CCB source ready-check for `ccb mobile serve` is now recorded in
[topics/ccb-mobile-serve-ready-check.md](topics/ccb-mobile-serve-ready-check.md)
and [Decision 010](decisions/010-cli-managed-mobile-gateway-sidecar.md). The
G1 loopback current-project gateway skeleton is no longer blocked by the
runtime-ownership question. The next active execution gate is the agent-native
selected-agent chat correction from
[Decision 015](decisions/015-pane-backed-chat-input.md): the chat UI shape
from [Decision 014](decisions/014-chat-first-agent-workspace.md) remains
accepted, but default composer sends must use the selected agent's terminal
session rather than the mobile ask/message route. The concrete compact
composer send primitive is now resolved by
[Decision 016](decisions/016-pane-composer-send-primitive.md): keep app-side
paste plus Enter for this alpha and surface possible partial sends as
`Check pane`. Manual AVD/code inspection on 2026-06-25 confirmed the current
implementation is still non-compliant because ordinary sends route through
`/agents/{agent}/messages -> message_type='ask'` and conversation backfill
relies heavily on `jobs.jsonl`; see
[topics/agent-native-conversation-and-input-correction.md](topics/agent-native-conversation-and-input-correction.md).
The broader multi-project registry, production relay, platform
notification, content, and release questions below remain open for later
packages.

The first terminal demo transport is resolved by
[Decision 009](decisions/009-ssh-direct-pty-first-terminal-slice.md): use SSH
direct PTY for the first real terminal slice, while keeping `GatewayTransport`
as the product boundary for pairing, Cloudflare Tunnel, tokens, content,
notifications, lifecycle, and relay-compatible routing.

Batch 1 license/base posture is resolved by
[Decision 008](decisions/008-permissive-baseline-until-agpl-approval.md):
use a smaller permissive Flutter baseline until AGPL is explicitly accepted.

## Product Shape

1. Should the first native codebase fork ServerBox despite AGPL obligations, or
   should the project start from a smaller permissive Flutter app and port only
   the needed ServerBox/MuxPod ideas?
2. How much generic SSH/server-management UI should be removed from the base
   app before the first public CCB-focused release?
3. Where should the explicit agent-list pull-out button live on phone and iPad,
   and should all swipe-to-open behavior be removed or only the upward swipe
   that conflicts with timeline scrolling?

## Runtime Boundary

1. After loopback gateway behavior is proven, should the mobile gateway remain
   CLI-managed or become supervised by `ccbd`?
2. After pairing/device storage lands, should mobile clients become
   first-class runtime records under `.ccb/ccbd/`, or remain gateway-only
   state?
3. What minimal `ccb mobile ... --json` wrapper set is required for SSH-direct
   mode before the gateway exists?
4. For the advanced Cloudflare route, should setup remain fully external
   documentation, or should `ccb mobile serve` eventually shell out to
   `cloudflared` when present?

Resolved 2026-06-24: the first host-level registry should be a server-wide CCB
project discovery registry behind `ccb install mobile`, not an explicit
per-project register list or user-managed config as the primary product path.
See
[topics/server-wide-mobile-install-and-project-registry.md](topics/server-wide-mobile-install-and-project-registry.md).

## Tmux Transport

1. After the SSH-direct validation slice, what is the safest production
   interactive terminal transport for selected panes: gateway PTY attach, tmux
   control mode, or a managed grouped-session view?
2. How should mobile resize be handled without shrinking or reflowing the
   canonical desktop workspace?
3. Should raw input target a selected pane directly, or only an attached
   session client?
4. How much terminal scrollback should be stored or streamed through the mobile
   gateway?
5. Should the native app keep a capture-polling read-only mode for unreliable
   networks or permission-limited devices?

## Security

1. Are the proposed scopes `view`, `content`, `ask`, `focus`,
   `terminal-input`, `lifecycle`, `notify`, and `admin` enough, or are finer
   scopes needed for Comms, restart, and clear context?
2. Should raw terminal input be disabled by default for remote/tunnel access?
3. What audit events are required without logging private terminal keystrokes?
4. What should the default trusted-device profile include for
   LAN/tailnet/relay/Cloudflare use: terminal input only, or terminal input
   plus project lifecycle control?
5. In SSH-direct mode, should the app store SSH credentials, use imported
   private keys, rely on system keychain identities, or prefer short-lived
   gateway tokens only?
6. For the advanced Cloudflare route, should Cloudflare Access be documented
   as optional defense-in-depth, or integrated into the app pairing flow?

## CCB APIs

### Pane-Backed Chat

1. What is the stable cursor/order model for merging pane live output, retained
   terminal history, optimistic local sends, Comms, status events, and artifacts
   into one selected-agent timeline?
2. Should the MVP timeline stream terminal output frames continuously while
   using `/terminal-history` for refresh/backfill, or poll history first and
   add live streaming after the parser stabilizes?
3. How should the app detect and warn when the selected pane is not at a
   provider prompt, such as shell, editor, pager, or alternate-screen state?
4. Where should pane-chat draft/pending/echo-dedup state live: app-only memory,
   app secure storage, gateway-local state, or a future CCB terminal journal?
5. How should duplicate sends be prevented when the phone retries after network
   loss, given that replaying terminal input may execute the same command
   twice?
6. Which supplemental content sources should enrich the pane-backed timeline:
   Comms, reply delivery, message bureau records, artifacts, provider session
   logs, or readable terminal history only?

### Other API Questions

1. Should `project_view` become a streaming subscription endpoint or remain a
   short-TTL polling endpoint for the MVP?
2. Should project favorite/lifecycle state live in `ccbd`, the mobile gateway,
   or a per-user mobile registry?
3. Should project wake/stop call existing CCB CLI flows, new `ccbd` lifecycle
   endpoints, or a gateway-managed wrapper?
4. Should `project_pane_snapshot` return text first only, or include ANSI mode
   in the MVP?
5. After the gateway PTY stream proves stable, should terminal input/paste/
   resize stay in the mobile gateway with `ccbd` target validation, move into
   `ccbd` proper, or move to tmux control mode?
6. Should the first content endpoint return raw Markdown only, or also include
   render hints for math, attachments, and local file-link degradation?
7. Which authoritative CCB/tmux completion signal should drive cross-project
   pane completion phone reminders, and what stable completion event id or
   state-transition marker should the gateway expose as `dedupe_key`? Decision
   019 accepts the app-facing P0 contract but leaves this source marker spike
   open.

## Relay Follow-Up

1. Should the default relay forward HTTP/WebSocket as-is, or expose a single
   framed bidirectional session that maps to the same request/response schemas?
2. Which maintained Python/Dart library and reviewed Noise-compatible handshake
   should implement the accepted message-level E2EE contract without custom
   cryptography?
3. Should production start in Alibaba Cloud Hong Kong for fast no-ICP staging,
   or in a China mainland region using an already-filed domain?

Resolved 2026-07-15: the hosted public relay uses one-time applicant-specific
invitations, host public-key binding, short-lived session capabilities, quotas,
and no forwarded CCB payload storage. Encryption above relay TLS is required.
This is separate from the reusable host-to-phone pairing handoff in Decision
021. See [Decision 023](decisions/023-one-time-public-relay-admission.md),
[the deployment plan](topics/public-relay-invitation-and-aliyun-deployment.md),
and [the public Emulator gate](topics/public-relay-android-emulator-acceptance.md).

## App Install And Upgrade

Resolved 2026-06-30: the first user-facing fix is both a same-channel
cover-install release path and an in-app browser handoff to the configured
APK/release URL. Android release builds must use stable release signing
material from local secrets or environment variables and must not fall back to
debug signing. Debug/profile APKs remain local test artifacts, not the user
upgrade channel. See
[Decision 018](decisions/018-stable-android-release-channel.md).

## Markdown Display

1. Should full Markdown content be exposed by a new `project_content_get`
   endpoint, or should mobile fetch it through existing job/message endpoints?
2. Should Markdown rendering happen fully client-side, or should the gateway
   also provide sanitized HTML/render hints for constrained clients?
3. Which CCB content sources are authoritative for Markdown: ask body,
   reply-delivery body, text artifacts, provider session logs, or terminal
   captures?
4. How should local file links and image references be handled on a remote
   phone without exposing arbitrary host paths?
5. Which math renderer should the native mobile client use first, and how should
   formula rendering be disabled or degraded when sanitizer constraints require
   it?
6. Should external URL/file opening use a per-action confirmation, a per-host
   "remember" choice, or a global setting, and how should that behave for
   untrusted Markdown rendered from provider output?
7. For a remote file long-press, should Open always download first and invoke
   the OS chooser from app storage, or should some MIME types get an in-app
   preview before the external app handoff?
