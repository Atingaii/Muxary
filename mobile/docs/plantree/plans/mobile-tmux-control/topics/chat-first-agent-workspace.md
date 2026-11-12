# Chat-First Agent Workspace

Date: 2026-06-22
Status: In Progress

## Purpose

Replan CCB Mobile from a status/terminal-oriented controller into a
ChatGPT/DeepSeek-style mobile client for one selected CCB agent at a time.
The app remains server-remote and CCB-authority-first; it should not become a
phone-local agent runtime or a generic terminal app.

## Product Shape

The default project screen should be a conversation workbench:

- top navigation: compact project context plus horizontal agent switcher;
- main content: one selected-agent timeline;
- bottom composer: persistent multiline input with send action;
- secondary controls: connection details, lifecycle, route diagnostics,
  readable history filters, and Open Terminal behind explicit buttons/menus.

The first viewport should answer:

- Which agent am I talking to?
- What did I ask?
- What did the agent answer or ask back?
- Is the agent busy, blocked, waiting for callback, or done?
- Can I type the next message now?

It should not spend the first viewport on runtime ids, gateway URLs, pairing
state, raw tmux state, or terminal chrome.

## Timeline Model

Timeline entries should be typed. The UI may render them as chat bubbles,
cards, or compact event rows depending on content:

- `user_message`: text submitted from the mobile composer;
- `agent_reply`: assistant/agent response, Markdown-rendered by default;
- `callback_request`: agent asks the user for input or continuation;
- `comms_item`: CCB Comms attention item or direct message;
- `status_event`: queued, started, completed, failed, blocked, cancelled;
- `tool_event`: concise tool/action progress when useful;
- `artifact_card`: validated text artifact or content reference;
- `terminal_history_block`: best-effort readable tmux history, clearly labeled;
- terminal-derived `user_message` / `agent_reply` items: compact foreground
  bubbles split from readable tmux history blocks, with command/input shown as
  strongly folded user-side history and log/code/diff/error output shown as
  folded agent-side evidence;
- `system_notice`: route, auth, stale view, permission, or retry notices.

For the default mobile interaction, pane-derived input/output is the primary
operational stream because the composer writes to the selected tmux pane.
Structured CCB content remains authoritative for ProjectView state, Comms,
artifacts, health, and explicit CCB records. When terminal-derived input and
output are shown in the foreground timeline, they must remain labeled by source
and keep the full readable-history panel available for context.

## Timeline Architecture And Scroll Policy

The selected-agent timeline must move from eager full-tree rendering to a
virtualized list before long-history work continues. The current implementation
still uses `SingleChildScrollView` plus `Column`, which mounts every bubble and
rich body. That is acceptable for local fixtures, but it is not acceptable for
hundreds or thousands of conversation, Comms, content, and terminal-history
items.

Target architecture:

- use `ListView.builder` or `CustomScrollView` plus `SliverList` for the
  selected-agent timeline;
- build only the visible items plus a small `cacheExtent` prefetch window;
- keep preview rendering cheap and always available;
- render rich Markdown/content bodies only for expanded items that are visible
  or near-visible;
- lift expanded/collapsed state out of `_ConversationBubbleState` into the
  selected-agent workspace or timeline controller, keyed by stable `item.id`;
- preserve draft and scroll state per project/agent when switching agents;
- keep terminal-derived foreground bubbles collapsed by default.

Scroll policy:

- detect whether the user is near the bottom before appending new remote,
  local, or refreshed conversation items;
- if the user is near the bottom, animate to the latest message after append;
- if the user is reading older history, do not force-scroll; append silently
  and show a compact "new messages" jump affordance near the composer;
- keep retries, post-send refreshes, and scheduled refreshes from disrupting
  the viewport when the user is not near the bottom;
- after expanding a collapsed or preview conversation bubble, bottom scrolling
  must remain stable and must not snap back to the top; audit key stability,
  scroll extent changes, refresh rebuilds, and any competing agent-list drawer
  gesture;
- preserve expanded state and scroll offset across rebuilds, refreshes, and
  route changes.

The first performance package should focus on this timeline architecture
before adding richer Markdown or terminal-history rendering features.

## Pane-Backed Composer

The composer is the primary compact pane control:

- multiline text input;
- send button;
- disabled states for offline, unpaired, missing `terminal_input` scope, stale
  project view, terminal session unavailable, or busy send;
- pending/sent/failed-or-echoed state visible in the timeline;
- retry failed send only when it is safe to avoid duplicate pane input;
- preserve drafts when switching away and back to the same project/agent;
- optional Markdown preview after the basic send path works;
- optional quick actions later: attach artifact, slash commands, stop/cancel,
  regenerate/continue, callback accept, and explicit ask/message send.

The composer writes to the selected agent's tmux pane through the gateway
terminal transport. It must not wrap default sends in the CCB ask/message route.

## Gateway/API Shape

The app needs a pane-backed chat boundary. Existing terminal routes are the
preferred send/read foundation:

```text
POST /v1/projects/{project_id}/terminals
GET  /v1/terminals/{terminal_id}              # WebSocket terminal frames
GET  /v1/projects/{project_id}/terminal-history?agent={agent}&limit=
GET  /v1/projects/{project_id}/agents/{agent}/conversation?cursor=&limit=
GET  /v1/projects/{project_id}/agents/{agent}/events?cursor=
GET  /v1/projects/{project_id}/content/{content_id}
```

Default composer send:

```json
{
  "type": "paste",
  "seq": 12,
  "text": "User text"
}
```

The app sends Enter after paste through an input frame, or through an equivalent
terminal-input operation that preserves multiline paste behavior and does not
shell-quote user text.

Implementation should reuse CCB authority where possible:

- open and validate terminal targets through ProjectView namespace/window/agent
  evidence before sending;
- read timeline source material from terminal output frames and
  `/terminal-history`;
- merge supplemental conversation state from ProjectView, Comms, inbox/watch/
  get, reply delivery, and validated artifacts when available;
- use `project_view` for agent state and attention summaries;
- fetch full Markdown bodies on demand through content routes;
- use polling first if a streaming event route is not ready.

Required scopes:

- `view` for project/conversation summaries;
- `terminal_input` for default composer sends;
- `content` for full Markdown/artifact reads;
- `ask` or `message_submit` only for explicit compatibility sends, not the
  default chat composer.

## Flutter Landing Packages

1. Chat shell with fake repository data:
   agent switcher, message timeline, bottom composer, keyboard-safe layout,
   pending/sent/failed states, and widget tests.
2. Pane-chat state boundary:
   add conversation item, pane cursor, pending-send, echo-dedup, and
   terminal-history DTOs around the existing repository/terminal transport
   seams before source work expands.
3. Pane-backed chat transport:
   connect the selected-agent composer to a reusable terminal session, send
   paste/input frames, track renewal/reconnect, and keep raw Open Terminal as
   the full-control route.
4. Paired-gateway app wiring:
   claim `terminal_input`/`content` scopes, send through the terminal gateway,
   load terminal history/live output into the timeline, and render supplemental
   replies/Comms as Markdown cards.
5. Emulator smoke:
   start disposable CCB runtime, pair through loopback, type into the composer,
   send to the selected pane, observe pane echo/output in the timeline or
   readable history, and verify Open Terminal remains an explicit fallback.

## Performance Landing Packages

1. Timeline virtualization and scroll-safe append: landed in app `a5fa0aa`.
   replace `SingleChildScrollView`/`Column` with a builder/sliver list, lift
   expanded item ids into parent state, detect near-bottom before auto-scroll,
   add a "new messages" jump affordance, and cover 500+ item fixture scrolling
   plus "new reply while reading history" widget tests. Current coverage uses a
   160-item fixture and virtualized tmux-history scrolling; emulator validation
   should now confirm the same behavior with real phone/tablet surfaces.
2. Lazy rich rendering: next app package.
   keep collapsed bubbles as plain previews, render Markdown/content only when
   the item is expanded and visible or within the list prefetch window, and add
   regression fixtures for long Markdown, tables, code, and nested lists.
3. Terminal-derived manual rich view:
   keep tmux input/output plain by default, then add an explicit best-effort
   "render as Markdown" toggle for selected terminal-derived output blocks
   after the lazy renderer and cache boundaries exist.

## Non-Goals For This Phase

- Production public relay server.
- Physical phone validation.
- iOS release packaging.
- Full project-lifetime terminal journal.
- Full arbitrary remote file browsing. Known CCB attachments/artifacts may
  still expose focused Download/Open actions from the conversation.
- Requiring Cloudflare, a public IP, or user-owned DNS.
- Replacing CCB source authority with mobile-only state.

## Acceptance Criteria

- Phone-sized emulator shows one selected-agent chat timeline and a bottom
  composer backed by the selected tmux pane, without requiring the raw terminal
  route to be open.
- User can type, send, see pending/sent/failed state, and continue using the
  screen with the soft keyboard open.
- Markdown replies, callback text, and Comms items render readably in the
  timeline with copy support.
- Agent switching preserves per-agent scroll/draft state.
- Connection/runtime details do not occupy the first viewport.
- Open Terminal remains available but is only the full raw-control surface; the
  compact chat composer still sends to the same selected pane.
- Local AVD loopback smoke validates the full path without public routing.

## Risks And Open Edges

- Pane echo and local optimistic sends need robust deduplication.
- The app needs clear warnings when the selected pane is in an editor, shell,
  pager, or other non-provider-prompt state.
- Conversation ordering needs a stable cursor that can merge pane output,
  retained history, Comms, artifacts, and status events.
- Long-running replies may require streaming or polling with clear pending
  states.
- Long histories require timeline virtualization before richer message
  rendering, otherwise Flutter will keep building off-screen bubbles and
  eventually degrade scrolling or memory.
- Text selection across off-screen virtualized items may be interrupted; every
  long block should keep explicit copy actions as a fallback.
- Duplicate sends need pane-aware retry rules; automatic retry must not replay
  terminal input without explicit user intent.
- The app now requires `terminal_input` permission for default chat, because
  chat is the compact pane input surface.
- Markdown/artifact routes must avoid arbitrary host file reads.
