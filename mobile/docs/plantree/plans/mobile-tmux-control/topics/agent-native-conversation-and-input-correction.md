# Agent-Native Conversation And Input Correction

Date: 2026-06-25
Role: Active implementation plan
Status: In Progress
Authority: Decisions 015 and 016
Read when: working on mobile chat send, conversation history, real local AVD
validation, or server-wide project chat acceptance.

## Purpose

Correct the current CCB Mobile chat path so phone input behaves like direct
input to the selected agent, and the phone timeline shows the agent's real
conversation history rather than only CCB ask/job records.

This is one cohesive product correction, not another micro-helper extraction.
It spans source gateway contract, app composer/timeline wiring, and real AVD
validation.

## Current Finding

The current default send path is:

```text
Flutter composer
  -> MobileCcbRepository.submitAgentMessage
  -> POST /v1/projects/{project}/agents/{agent}/messages
  -> MobileGatewayService._submit_agent_message
  -> MessageEnvelope(message_type='ask')
  -> provider ask/job wrapper
```

For Codex-backed agents, the provider turn prompt wrapper can inject
`CCB_REQ_ID`. That is correct for CCB ask jobs, but wrong for the mobile
composer. The mobile composer should not create a new ask job when the user is
trying to type into the selected agent.

The current read path also over-indexes on CCB job records:

```text
GET /v1/projects/{project}/agents/{agent}/conversation
  -> ProjectView content / Comms
  -> .ccb/agents/{agent}/jobs.jsonl history
```

That can show ask requests and completion snapshots, but it is not the full
provider-native transcript. The user expects the same conversation that exists
inside the selected agent session.

## Target Contract

### Product Definition: Pane-Equivalent Sync

The phone is a rendering and input surface for the selected desktop/server CCB
agent pane. For ordinary chat, the user should be able to compare the phone
timeline with the active tmux pane for the same project/agent and see the same
conversation turns in the same order, allowing only mobile presentation
differences such as wrapping, Markdown rendering, attachment chips, and
collapsed long blocks.

Implementation sources are subordinate to this product contract:

- provider-native session logs may provide the semantic user/assistant
  transcript;
- tmux scrollback and terminal history may provide live/in-progress pane output
  and fallback retained text;
- CCB jobs, Comms, content cards, completion snapshots, and reply-delivery
  records are supplemental metadata only;
- CCB ask/job history must not replace or interleave with the pane-equivalent
  conversation by default.

In the default selected-agent chat view, internal provenance such as
`mobile_gateway`, `completion_snapshot`, `provider_native/codex`, CCB request
ids, job ids, route names, and source labels must not be displayed as chat
content. They may be available in diagnostics or debug detail, but not in the
ordinary conversation timeline.

### Sync Model

The gateway must resolve the selected project/agent to a CCB-validated pane
target using the current `ProjectView`, namespace epoch, window, agent, tmux
socket/session, and pane identity evidence. Conversation loading then exposes a
pane-equivalent timeline:

- **Initial load** returns the newest visible conversation window for the
  selected pane/agent, not the newest CCB ask jobs.
- **Refresh** updates the visible timeline from the same pane/session source so
  desktop-side typing or provider output appears on the phone without changing
  projects or reopening the agent.
- **Older-page loading** walks backward through the same transcript/scrollback
  order and keeps a stable cursor.
- **Live/in-progress output** may be represented as a transient assistant
  block while the provider is streaming or the pane is still updating.
- **Fallback** to terminal scrollback is acceptable when provider-native
  transcript mapping is unavailable, but it must be visibly best-effort and
  must still target the selected pane.

The first implementation can poll the conversation endpoint while the agent
workspace is visible. A WebSocket/event stream is a follow-up optimization, not
required for correctness. Polling must be cheap enough for active use and must
avoid re-rendering unchanged pages.

### Send

Default mobile composer send must be semantically equivalent to typing in the
selected CCB agent pane:

- no `MessageEnvelope(message_type='ask')`;
- no generated `CCB_REQ_ID`;
- no mobile-specific prefix or "phone user" marker in the text sent to the
  agent;
- selected project, window, agent, namespace epoch, and pane target validated
  through CCB authority before input is sent;
- retry is conservative because replaying terminal input can execute twice.

The preferred current-alpha implementation is Decision 016: reuse the terminal
transport to paste text and send Enter. If a source-side helper is introduced,
it must still perform validated pane input and carry terminal-input semantics,
not ask/message semantics.

### Read

The selected-agent timeline should prefer provider-native conversation data
only when that data is mapped to the selected pane/session and therefore
matches the pane-equivalent contract:

- Codex first: read provider session metadata and rollout JSONL, filter system,
  developer, tool, and AGENTS/bootstrap context, then expose visible user and
  assistant messages with stable cursor/order.
- Other providers: add provider-specific readers or a clearly marked fallback
  path instead of pretending CCB job history is complete.
- CCB jobs, Comms, content cards, terminal history, artifacts, and status
  events are supplemental context.
- Comms should be rendered as inline activity/status or compact supplemental
  cards near the relevant conversation, not as a standalone "agent reply"
  substitute.
- If native logs and the current pane disagree, the product must fail toward
  the current pane view and surface diagnostics for the mismatch rather than
  showing stale job/completion history as if it were the live chat.

### Files

Files created by backend agents should be available to the phone through
authenticated opaque gateway file/artifact ids. The app should render them as
downloadable chips/links in the same conversation surface. Raw host paths and
unauthenticated public URLs are not acceptable.

## Implementation Packages

### Package A: Source Native Conversation Contract

Likely source tree: `/home/bfly/yunwei/ccb_source` or an explicit source
worktree.

Scope:

- add a pane-equivalent conversation resolver that starts from the
  CCB-validated selected pane target;
- add provider-native transcript reader abstraction and map records back to
  the active pane/session when possible;
- implement Codex session/rollout reader first, including current active
  thread selection rather than stale historical thread selection;
- add tmux scrollback/terminal-history fallback for the same selected pane;
- add cursor/pagination for older transcript pages;
- keep existing CCB ask/job history as explicit supplemental compatibility
  data, excluded from the default pane-equivalent timeline unless no pane or
  native source is available and the response marks it as compatibility data;
- expose the selected-agent conversation route with a source marker that lets
  the app distinguish native transcript, Comms, content, terminal history, and
  compatibility job items;
- add tests with a small fixture rollout containing user, assistant, tool, and
  system/developer records.

Acceptance:

- `/conversation` for a Codex agent returns the current selected-pane
  user/assistant transcript records that are not present in `jobs.jsonl`;
- the latest desktop pane turn appears in `/conversation` without requiring a
  CCB ask/job record;
- system/developer/bootstrap/tool records are filtered;
- pagination can load older transcript pages;
- CCB ask/job records do not replace native transcript or selected-pane
  scrollback as the primary source;
- a mismatch test proves stale jobs/completion snapshots do not appear above or
  instead of the current pane conversation.

### Package B: Native Pane Send Path

Scope:

- make ordinary mobile composer sends use validated terminal input/paste, or a
  source helper with exactly the same pane-input semantics;
- stop calling `/agents/{agent}/messages` for default chat sends;
- require `terminal_input` scope for default chat;
- preserve pending/sent/check-pane state and draft clearing only after the
  send path reaches the pane or fails deterministically;
- leave `/agents/{agent}/messages` as explicit compatibility/ask action only.

Acceptance:

- sending `hi` from the phone does not create a CCB ask job;
- no `CCB_REQ_ID` appears in the pane or in the provider transcript;
- desktop/tmux pane shows the same input text the phone sent;
- the app timeline shows the user message and the provider's real response;
- duplicate sends and retry do not silently replay terminal input.

### Package C: App Timeline And UX Rebase

Scope:

- prefer pane-equivalent conversation pages in the selected-agent timeline;
- poll/refresh the visible agent conversation while the workspace is active,
  with de-duplication so unchanged snapshots do not reflow the list;
- keep terminal history as labeled best-effort evidence, not the main reply
  substitute;
- render Comms/status inline without popping a misleading standalone
  conversation bubble;
- hide internal metadata labels such as `completion_snapshot`,
  `provider_native/codex`, `mobile_gateway`, and job/request ids from the
  normal chat surface;
- keep file upload/download and backend artifact chips in the same chat
  timeline;
- preserve per-agent draft, scroll, and attachment state.

Acceptance:

- switching agents loads each agent's own native transcript;
- upward scrolling fetches older native transcript pages without jank;
- desktop-side pane input/output appears on the phone after the next refresh
  without reopening the project or agent;
- send/receive state remains visible while the real agent is thinking;
- file and image attachments remain downloadable after transcript refresh.

### Package D: Real Local AVD Validation

Scope:

- start server-wide local gateway through `ccb install mobile` or the current
  equivalent test entry;
- list all mounted/reachable local CCB projects on the phone first page;
- open `/home/bfly/yunwei/test_ccb2` or another explicit real test project,
  not the mobile repo demo unless it is intentionally selected;
- send to at least two agents;
- load older transcript pages upward;
- upload image/document attachments and download backend-generated files;
- collect p50/p95 timings for send, first visible echo, first reply, older
  transcript load, render, upload, and download.

Acceptance:

- no fake repository active during the P0 run;
- no `CCB_REQ_ID` in pane, transcript, or visible phone conversation for
  ordinary mobile sends;
- the desktop CCB pane and the phone timeline agree on the user input and
  assistant reply;
- a desktop-only typed prompt appears in the phone timeline, proving sync is
  bidirectional around the shared pane transcript rather than phone-only state;
- stale `.ccb/agents/<agent>/jobs.jsonl` ask records do not appear as the
  newest chat when the active pane has newer turns;
- evidence includes screenshot, UI dump, logcat, gateway logs, source commit,
  app commit, project id, agent names, and latency summary.

## Performance Targets

Initial targets for the local AVD acceptance run:

- project list refresh: p50 under 500 ms, p95 under 1500 ms on loopback;
- selected-agent initial pane-equivalent conversation load: p50 under 1000 ms,
  p95 under 2500 ms for the newest page;
- active conversation refresh after desktop-side pane update: p50 under
  1000 ms, p95 under 2500 ms;
- phone send accepted into pane: p50 under 500 ms, p95 under 1500 ms;
- first visible provider reply after it appears in the pane: p50 under
  1000 ms, p95 under 2500 ms;
- older-page load of 50 conversation items: p50 under 1000 ms, p95 under
  3000 ms;
- visible timeline render for 200 items with attachments: no dropped-frame
  burst that makes scrolling unusable during manual AVD review.

These are alpha budgets for loopback/local testing. Tailnet/relay/public route
budgets should be tracked separately after the local contract is correct.

## Non-Goals

- Do not make the phone run CCB agents locally.
- Do not use Tailnet/relay/Cloudflare as a prerequisite for local correction.
- Do not expose provider cache directories, host file paths, tmux sockets, or
  runtime roots through public mobile APIs.
- Do not broaden this package into a UI redesign beyond the Comms/status
  correction needed for conversation clarity.

## Review Gates

- Source and app reviewers must verify that the default composer no longer
  calls the mobile ask/message route.
- Tests must fail if `message_type='ask'` or `CCB_REQ_ID` appears on the
  ordinary mobile send path.
- Native transcript tests must include at least one user/assistant pair that
  does not exist in `jobs.jsonl`.
- AVD evidence must use a real local CCB project and must record the selected
  project root to prevent accidentally validating the wrong repo.
