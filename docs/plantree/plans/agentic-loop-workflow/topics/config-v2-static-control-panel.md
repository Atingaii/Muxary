# Config V2 Static Control Panel

Date: 2026-07-08

## Status

Implementation topic with a served local editor. Config load, structured
V1/V2 visual editing, server-side TOML rendering, validation, guarded active
writes, Profile save/load, reload dry-run, and hot reload are landed under the
registered `config-designer-ui` plan.

Candidate-to-active unified diff review and explicit confirmation now gate
active writes. Static Codex/DeepSeek thinking and DeepSeek V4 model/API mapping
are writable. V3 remains preview-only and cannot activate.

`odesign` reviewed the `version = 2` static config panel direction in job
`job_f9100b2ffd30`; the artifact is stored at
`.ccb/ccbd/artifacts/text/completion-reply/job_f9100b2ffd30-art_2a614702dc8840cf.txt`.

This topic records the adopted demo direction: a V1/V2 static layout
preparation surface, not a runtime operations dashboard and not the v3 dynamic
workflow panel.

Prototype:

- [prototypes/v2-static-config-panel-demo/index.html](../prototypes/v2-static-config-panel-demo/index.html)

## Goal

Make formal static `.ccb/ccb.config` easier to inspect and edit without making
users hand-author compact layout grammar for common operations. V1 and V2 share
the same pane layout editor; V1 is the single-window/simple control surface,
while V2 adds named windows, sidebar settings, and richer static configuration
management.

The panel should answer five questions:

- which static windows exist;
- how each window is split into panes;
- which agent, provider, workspace mode, and optional RolePack belong to each
  pane;
- which overlay, Rich placement, or sidebar settings are configured;
- whether validate, reload dry-run, and runtime consumption agree with the
  saved config digest.

## Authority Boundary

- `.ccb/ccb.config` remains the desired-state source file.
- `[windows]` remains the authority for v2 static window topology, agent
  grouping, leaf provider, leaf workspace mode, and configured-agent set.
- `[agents.<name>]` remains an overlay for agents referenced by `[windows]`;
  it must not become topology authority.
- Rich is the only built-in supported non-agent surface in this design. It must
  be shown as a tool slot, not an `ask` target. Unsupported editor-tool fields
  are not part of this panel.
- `[ui.sidebar]` remains presentation-only and must not force provider/runtime
  topology mutation.
- The panel may hold an unsaved draft, generate TOML, run validate, request
  reload dry-run, and apply through CCB command contracts.
- The panel must not directly mutate `.ccb/runtime`, queues, provider sessions,
  tmux panes, or daemon graph records.

## Information Architecture

Final section order:

| Section | Purpose |
| :--- | :--- |
| Overview | Show config source, `version = 2`, digest/state chips, window count, agent count, validation summary, and reload impact summary. |
| Layout | Primary editor for static pane topology: binary split canvas, pane assignment, Rich availability, and compact layout preview. |
| Agent Details | Inspector for the selected pane/agent: provider, workspace mode, RolePack, model, and advanced overlay fields. |
| Rich Placement | Manage the built-in Rich files surface and clearly label it as not an ask target. |
| Sidebar | Edit `[ui.sidebar]` presentation settings and compatibility-read legacy `[ui.sidebar.view]`. |
| Review And Apply | Validate, save, reload dry-run, and apply through a digest-aware gated state machine. |
| Agent Communication Flow | Read-only explanation surface for recent `ask`, `chain`, `reply`, and `review` message movement. |

The surface is a static layout preparation workflow. It should not absorb
runtime logs, provider conversations, queue metrics, task dashboards, or v3
workflow role/capacity concepts. The communication-flow view is the exception
only as a compact read-only trace explainer; it must not become a mailbox,
queue, or lifecycle control surface.

### Mature Page Hierarchy

The full page should be organized as four quiet bands, not as a single
undifferentiated dashboard:

| Band | Visual priority | Contents |
| :--- | :--- | :--- |
| Configure | Primary | V1/V2/V3 editor, split canvas, selected pane inspector, compact preview. |
| Review | Secondary | Activation review and digest-aware validate/save/dry-run/reload gates. |
| Observe | Secondary | Agent communication flow observer with event list and sanitized trace drawer. |
| Maintain | Tertiary | Agent session storage scan and cleanup staging. |

Use subtle section labels and panel weight rather than large headers or
marketing-style cards. The editor is the only primary panel. `Review` and
`Observe` explain readiness and runtime movement. `Maintain` is low-frequency
local cleanup and should be visually quieter than the config editor.

The communication-flow panel should remain inline below activation review
rather than becoming a permanent right rail. A drawer is appropriate for trace
details, not for the whole observer. Session storage should remain at the
bottom as a maintenance panel; it may later be collapsed in dense mode, but it
should not interrupt the configure/review path.

## First View

First viewport:

```text
+--------------------------------------------------------------------+
| .ccb/ccb.config  version=2   Draft * Saved . Validated . Reloaded . |
| windows: 1   agents: 2   errors: 0   warnings: 0   reload: pending  |
+---------------+---------------------------------------+------------+
| Windows       | Layout Builder: main                  | Inspector  |
| blue main  3  | +---------------+-------------------+ | pane: odesign
| + Add window  | | archi         | odesign           | | provider codex
| Rename Delete | |               +-------------------+ | worktree yes
|               | |               | rich              | | role open-design
|               | +---------------+-------------------+ | validation ok
+---------------+---------------------------------------+------------+
| compact preview: main = "archi:codex(worktree); (odesign:codex, rich)" |
| [Validate] [Save Config] [Dry-run Reload] [Apply Reload]            |
+--------------------------------------------------------------------+
```

The first screen should stay operationally quiet. It should show topology,
validity, and next safe action, not live runtime activity.

## V1/V2 Shared Split Editing Model

Use one shared editing model for V1 and V2: a recursive binary layout tree.
Each split is exactly 50/50 and is either left/right or top/bottom. This keeps
the UI simple while still covering common layouts such as "left one pane, right
two stacked panes".

Use three synchronized representations:

- visual canvas for normal editing;
- structure breadcrumb for nested grouping;
- compact layout preview for generated grammar.

Editing should operate on a layout AST, not raw text.

V1 constraints:

- exactly one logical window;
- no window list management;
- no sidebar section;
- same binary split canvas and topology editing controls as V2;
- `Split LR`, `Split TB`, and `Undo` remain available; V1 differs from V2 by
  removing named-window and sidebar management, not by removing split editing;
- optional Rich appears as a tool pane in the same canvas when available;
- activation writes a supported single-window static config.

V2 constraints:

- one or more named windows;
- new V2 drafts start with exactly one `main` window;
- each window owns one binary layout tree;
- sidebar controls and Rich availability are visible;
- validation still uses the normal v2 config gates.

### Window List

V2 shows the window list as a slim rail beside the split canvas, not as a
toolbar dropdown. Each window row should use a distinct color accent so users
can see which named window owns the currently visible pane tree.

Each window row shows:

- window name;
- pane count;
- entry-window marker when relevant;
- validation state;
- reload impact after dry-run;
- tool-window collisions or duplicate name warnings.

Window actions live on this side rail:

- `Add window`;
- `Rename`;
- `Delete`.

Deleting the final remaining window is disabled. Adding a window creates an
empty single-pane layout tree; it does not mount runtime providers until the
config is saved, validated, and reloaded.

### Binary Split Canvas

Actions are pane oriented:

- select pane or group;
- split left/right, corresponding to `;`;
- split top/bottom, corresponding to `,`;
- clear pane content;
- reset selected subtree;
- undo the last layout edit.

There is no freeform drag layout, arbitrary N-by-M grid, merge, manual ratio,
irregular table shape, or visible template dropdown in this design. If users
need advanced compact grammar that cannot be represented as repeated 50/50
binary splits, they can use the full TOML view outside the first visual editor
slice.

The toolbar should stay intentionally small: `Split LR`, `Split TB`, and
`Undo`. Rich placement, agent conversion, and provider settings belong to the
selected pane inspector, not to extra toolbar modes.

Nested grouping should be shown as a breadcrumb for the selected leaf, for
example:

```text
ops / right column / lower group / odesign
```

The main path must not require understanding compact grammar operator
precedence or parentheses.

Example:

```text
+---------+---------+
| archi   | odesign |
|         +---------+
|         | rich    |
+---------+---------+
```

Generated preview:

```toml
[windows]
ops = "archi:codex; (odesign:codex, rich)"
```

### Compact Preview

Always show the generated compact layout string for the selected window.

The preview is primarily read-only. An advanced manual edit mode may be added
later, but it must parse back into the same AST and preserve the normal
validation gates.

## Agent Leaf Editing

Clicking a pane opens the pane inspector. The first control is `Pane type`.
Supported first-slice values are `Agent`, `Rich`, and later `Empty` if the
product chooses to support empty panes.

Rich is selected the same way as an agent: choose the pane, set `Pane type =
Rich`, and the pane becomes the built-in Rich files surface. There is no
separate toolbar-level Rich placement control. If the Rich package/workbench is
not installed or not healthy, the `Rich` pane type is disabled and the UI should
show the install/update action such as `ccb update rich` instead of emitting a
Rich leaf.

Default visible fields:

- agent name;
- provider;
- workspace mode;
- RolePack binding;
- agent name and workspace in one compact row;
- provider and RolePack in one compact row;
- model and thinking in one compact row;
- validation state.

Interaction rules:

- agent name input normalizes immediately and checks duplicates across all
  `[windows]`;
- provider is a required select;
- workspace uses a segmented control: `inplace`, `git-worktree`, and an
  advanced `copy` path when supported;
- RolePack binding is optional and writes to `[agents.<name>].role` unless the
  user is using a role-id shorthand leaf for the role's default agent name;
- multiple instances of one role should use distinct project-local agent names
  plus `[agents.<name>].role`;
- each saved agent must appear in `[windows]` exactly once;
- overlays must not introduce agents that are absent from `[windows]`.
- the inspector should be vertically compact and match the split canvas height
  at normal desktop widths; expanding optional sections may scroll inside the
  panel rather than stretching the whole page.

### API Override

API settings should sit below the core agent fields as a collapsed `API
override` section. The closed state is the normal inherited route and should
not ask the user to choose or understand a route mode. Opening the section
means "this pane needs its own API route" and then shows only non-inherited
settings:

- override type: existing provider profile, or custom key/base URL;
- profile selector when the override type is provider profile;
- API key input, rendered as a password/redacted field, when the override type
  is custom key/base URL;
- Base URL input when the override type is custom key/base URL.

Meaning of the underlying route concepts:

- inherit/default: no pane-local API config is written; the pane uses the
  project/provider default and the UI should keep this implicit;
- provider profile: the pane points at a named profile already managed by the
  provider settings;
- custom key/base URL: the pane has an explicit local route override.

The UI may let the user type a key for a new config, but it must never display
or log an existing stored secret. Generated diagnostics should prefer env-var
references, redaction, or provider profiles where possible.

## Overlay Strategy

The default agent inspector should not expose every overlay key. `model`,
`thinking`, and API route settings are common enough to stay in the main
inspector/API override areas. Put less common overlay fields behind a collapsed
`Advanced Overlay` section:

- `startup_args`;
- `env`, with values redacted by default;
- `workspace_group`;
- `workspace_path`;
- `provider_command_template`;
- `branch_template`;
- `labels`;
- `description`;
- `watch_paths`;
- `dispatch_disabled`.

The advanced section should be schema-driven. Unknown fields should be reported
by validate rather than silently accepted by the UI.

`thinking` is currently display-only model capability metadata. GPT-family
models can expose reasoning-effort choices, while unsupported models default to
inherit/no explicit value. V1/V2 must keep the control disabled because the
static config schema/compiler does not yet define a writable thinking field.

Style warnings should surface legacy or redundant overlay use:

- stale overlay for an agent no longer referenced by `[windows]`;
- overlay `provider` repeating the `[windows]` leaf provider;
- overlay `workspace_mode` repeating `inplace` or `git-worktree` already
  expressible in the leaf;
- overlay `workspace_group` without compatible workspace mode.

## Rich Placement

Rich should use the same pane assignment path as an agent instead of a separate
placement panel or a general tool-window table. The user can place Rich as a
leaf in the same binary split canvas by selecting the pane and choosing
`Pane type = Rich`.
There is no separate `Home only`, `Every window`, or percentage-placement mode
in the first visual editor slice; Rich is either placed in the current layout
tree or absent.

Rich availability is capability-gated:

- when the Rich workbench package is installed and healthy, `Rich` appears as a
  selectable pane type;
- when Rich is missing, `Rich` is visible but disabled with an install/update
  hint;
- generated config must not include a Rich leaf when the selected profile
  marks Rich unavailable.

| Field | Meaning |
| :--- | :--- |
| `pane type` | `Rich` on the selected pane. |
| `profile` | Rich workbench profile, initially `rich`. |
| `command` | Generated from the supported Rich alias, not manually edited by default. |
| `ask target` | Always `false`; Rich is never an agent. |

Every Rich pane must visibly say `not ask target`.

Changing Rich placement is topology-impacting. Changing presentation text is
view-only. Unsupported editor-tool fields must not appear in the V1/V2 panel.

## Sidebar

Keep sidebar editing as a secondary section or collapsed `Sidebar settings`
panel.

Editable fields:

- `mode`;
- `position`;
- `width`;
- `bottom_height`;
- `agents_height`;
- `comms_height`;
- `tips_height`;
- `comms_limit`;
- `tips`.

The sidebar has three main vertical blocks:

- agents;
- comms;
- tips.

Expose their vertical space as percentage controls in the `Sidebar settings`
panel. Use compact slider + numeric percent inputs for each block, and warn
when the total is not close to 100%. This is presentation-only and should map
to the canonical sidebar height fields (`agents_height`, `comms_height`,
`tips_height`) when supported by the renderer. It must not affect agent
mounting, ask routing, or runtime ownership.

`tips` is edited as one multiline text field. The UI should preserve line
breaks exactly and should not model it as sortable/addable/deletable list
items. This keeps the control close to how users think about sidebar help text:
short paragraphs or shortcut notes that can be pasted and edited directly.

Sidebar changes are presentation-only. The drawer may expose a dedicated
`Hot reload sidebar` action after validation because this does not change
agent topology or ask routing.

Legacy `[ui.sidebar.view]` may be read with a compatibility note. Generated
output should prefer canonical `[ui.sidebar]` when the renderer supports it.

## Agent Session Storage

Add a lower maintenance bar for `.ccb` agent session/storage management. This
area is separate from config editing authority: it scans and stages cleanup
actions for project-owned `.ccb/agents` evidence, but it must not redefine the
mounted daemon graph, provider runtime ownership, lifecycle, lease, mailbox, or
active session authority.

The bar should show:

- total `.ccb` agent storage estimate;
- historical session storage estimate;
- mounted agent count;
- stale/unmounted agent count;
- per-agent status, provider, last activity, current-session protection state,
  historical storage, oldest session, and allowed cleanup action.

Allowed cleanup modes:

- delete session/evidence files older than a selected age threshold;
- delete all content for an unmounted/stale agent after explicit confirmation;
- delete only historical sessions for a mounted agent.

Hard protection rules:

- mounted agents are protected by current runtime graph authority, not by disk
  directory names;
- mounted agents cannot expose a `delete all agent content` action;
- mounted-agent cleanup must exclude the current provider state, active session
  file, mailbox, lifecycle, lease, runtime records, pid files, and current
  completion evidence;
- stale/unmounted agent deletion must still show a dry-run preview listing the
  directories and byte count before destructive execution;
- API keys and provider auth material are never read, displayed, or copied by
  this panel.

The first visual slice can be non-authoritative: buttons may show staged
actions such as `Scan storage`, `Delete old sessions`, `History only`, and
`Delete all`, but production implementation must route through a dedicated
cleanup command/service with validation and confirmation.

## Review And Apply Flow

Use the same digest-aware framing as the v3 panel, but mapped to v2 config:

1. `Draft only`: changes exist only in the panel.
2. `Saved to .ccb/ccb.config`: atomic write completed and backup created.
3. `Validated saved config`: server-side validation passed for the saved digest.
4. `Reload dry-run ready`: dry-run was computed against that saved digest.
5. `Runtime consumed config`: mounted runtime consumed the saved config digest.

Buttons must be disabled until the prior gate is satisfied:

- validate draft or saved config;
- save config;
- reload dry-run;
- apply reload.

Errors should group into:

- topology blockers: layout grammar, duplicate agent, missing provider, unknown
  provider;
- overlay warnings: stale overlay, redundant provider/workspace, unknown field;
- reload impact: add agent, remove agent, replace provider/model, layout
  change, tool command change, sidebar-only change;
- apply blockers: busy runtime, queue pending, digest mismatch, stale dry-run.

Every error or warning should include a path and, where possible, anchor the
affected window, pane, or overlay field.

## Agent Communication Flow

Add a secondary `Agent Communication Flow` panel after `Activation Review` and
before `Agent session storage`. This placement keeps the config editor primary,
puts runtime explanation near reload/apply context, and avoids turning the
right inspector into an operations dashboard.

Purpose:

- explain recent agent-to-agent movement such as `ask`, `chain`, `reply`, and
  `review`;
- help users understand why a job is running, waiting, blocked, stale, or
  complete;
- provide trace and artifact entry points for diagnostics;
- remain strictly read-only and non-authoritative.

Non-authority rule:

- do not write mailbox, queue, lifecycle, completion tracker, daemon graph, or
  provider state;
- do not retry, cancel, unblock, or mutate jobs from this panel;
- any future action must route through an explicit diagnostics or command
  surface with its own permission and validation model.

### Placement And Layout

Recommended default:

```text
--------------------------------------------------------------+
| Activation review                                            |
+--------------------------------------------------------------+
| Agent communication flow          observer only              |
| [Pause] [Window 15m] [Agent all]                 [Details]   |
| +---------------------------+  +---------------------------+ |
| | node graph with pulses    |  | Latest events             | |
| | ccb_self -> odesign       |  | ask delivered             | |
| | odesign -> worker1        |  | chain waiting             | |
| | worker1 -> reviewer3      |  | review running            | |
| | reviewer3 -> odesign      |  | reply stale/blocked       | |
| +---------------------------+  +---------------------------+ |
+--------------------------------------------------------------+
| Agent session storage                                         |
+--------------------------------------------------------------+
```

Keep the panel collapsed or compact in future dense modes, but do not place it
inside the layout editor. The main split canvas and selected pane inspector
must stay focused on desired-state config.

### Visual Model

Use quiet node-and-edge animation:

- agent nodes are circles, not cards; the circle contains only the agent name,
  a very short role/state hint, and one compact status badge;
- the communication map uses a 1:1 square frame so circular placement remains
  visually stable across V1/V2 modes;
- for V1/V2, currently opened or mounted agents should be arranged on a circle
  around a small active-trace center, so the user reads the flow as movement
  among live project participants rather than as another layout editor;
- when many agents are open, circle nodes should scale down before the map
  grows into a dense graph; keep detail in the event list and drawer instead of
  expanding each node;
- directed edges represent message movement, for example `A -> B`, `B -> C`,
  `C -> B`, `B -> A`;
- animated dashed strokes plus arrowheads show active movement direction, not
  throughput metrics;
- labels on edges show event type and trace id prefix, not full payload;
- a right-side event list provides the scannable truth; the animation is only
  an explanatory aid.

Flow color semantics:

- request/inbound ask flow: blue;
- reply/backflow: green;
- chain/child-work flow: amber;
- stale, failed, blocked, or unsafe flow: red and slower or stopped.

State colors should stay consistent with existing badges:

| State | Visual treatment |
| :--- | :--- |
| `queued` | muted/info badge, no pulse or slow pulse |
| `delivered` | green badge, completed edge pulse stops after arrival in real implementation |
| `running` | blue/info badge and active edge pulse |
| `chain waiting` | amber badge and slower pulse |
| `reply completed` | green reply edge |
| `incomplete` | amber outline, event remains in list |
| `failed` | red badge and stopped edge |
| `stale` | red muted badge, dashed stopped edge |
| `blocked` | red badge with blocker reason in details drawer |

Avoid large animated backgrounds, particle effects, large gradients, or
always-on high-contrast motion. Respect reduced-motion preferences by disabling
edge animation.

### Controls

First-slice controls:

- `Pause animation` / `Resume animation`;
- time window selector: `15 min`, `1 hour`, `24 hours`;
- agent filter: `all agents` or one selected agent;
- `Trace details` drawer.

Do not add live replay scrubbing, graph layout editing, timeline zoom, or
multi-dimensional filters in the config panel MVP.

### Interaction

Clicking a node, edge, or event opens the existing side drawer with a sanitized
trace summary:

- trace/job id with copy action;
- route: source agent, target agent, parent/child relationship;
- event type and state;
- timestamps and duration when available;
- artifact path/link when allowed;
- short sanitized payload summary;
- blocker or stale reason if present.

The drawer should not show full private prompts by default. Long message bodies
should be summarized and linked to artifacts rather than embedded.

### Data Contract

Future implementation should assemble the view from existing evidence streams,
not from a new authority:

- mailbox trace entries for source, target, event type, timestamps, and trace
  id;
- job state for queued/running/waiting/completed/failed/blocked;
- reply artifacts and completion tracker for reply availability and digest;
- daemon graph for mounted/stale agent identity and current lifecycle status;
- review artifacts for review state and summary.

Suggested read-only event shape:

```json
{
  "trace_id": "job_8b204be32628",
  "parent_trace_id": "job_parent",
  "event_type": "ask|chain|reply|review",
  "source_agent": "ccb_self",
  "target_agent": "odesign",
  "state": "queued|delivered|running|chain_waiting|reply_completed|incomplete|failed|stale|blocked",
  "created_at": "2026-07-09T14:52:11+08:00",
  "updated_at": "2026-07-09T14:53:02+08:00",
  "artifact_ref": ".ccb/ccbd/artifacts/text/completion-reply/job_...",
  "summary": "Sanitized one-line explanation",
  "blocker": null
}
```

Security rules:

- never show API keys, provider auth files, tokens, environment secrets, or
  raw provider sessions;
- do not expose full private prompts or large message bodies in the graph;
- redact path or payload segments that contain secrets;
- prefer summaries, state labels, trace ids, and artifact links.

## Responsive Layout

Desktop:

- left window navigation;
- center layout canvas;
- right inspector and action rail.

Medium width:

- window navigation becomes top tabs or a select;
- inspector becomes a drawer.

Narrow/mobile:

- single-column flow;
- window selector at the top;
- visual builder opens full-screen for complex nested layouts;
- action rail becomes sticky bottom controls;
- mobile supports inspect, validate, and light edits, not primary heavy
  authoring.

## MVP Demo

A minimal non-authoritative demo should include:

- mock v2 config data;
- sticky header with active config digest, profile selector, version dropdown,
  and explicit confirm switch;
- shared V1/V2 binary split canvas;
- V2 slim window rail, starting with one `main` window and lightweight
  `Add`, `Rename`, `Delete` actions;
- `Split LR`, `Split TB`, and `Undo` only;
- selected pane inspector with compact rows: agent/workspace,
  provider/RolePack, and model/thinking;
- `API override` collapsed by default, with no visible inherited-route option;
- Rich selected through `Pane type = Rich`, capability-gated and labeled
  `not ask target`;
- compact layout preview;
- sidebar settings drawer with Agents/Comms/Tips percentage sliders and one
  multiline tips textarea;
- validation/error details drawer;
- read-only Agent Communication Flow panel with node pulses, event list,
  pause control, filters, and sanitized trace drawer;
- bottom action bar for validate, save profile/config, reload dry-run, and hot
  reload;
- compact activation review that shows the gated flow without dominating the
  editor.
- lower agent session storage bar for scanning `.ccb/agents`, deleting
  age-thresholded historical sessions, and staging stale-agent cleanup while
  protecting mounted agents.

Suggested future prototype path:

```text
docs/plantree/plans/agentic-loop-workflow/prototypes/v2-static-config-panel-demo/index.html
```

Suggested component names:

- `ConfigPanelApp`;
- `StateHeader`;
- `WindowList`;
- `LayoutCanvas`;
- `SplitToolbar`;
- `PaneInspector`;
- `CompactPreview`;
- `ValidationPanel`;
- `AgentCommunicationFlow`;
- `SidebarPanel`;
- `ReviewApplyRail`.

## Prototype Maturation Pass

The current standalone prototype at
`prototypes/v2-static-config-panel-demo/index.html` should read as a quiet
engineering control panel rather than a temporary demo:

- subdued background, low shadow, stable 8px radius, and no decorative hero
  treatment;
- main workspace uses a fixed left canvas and right inspector rhythm on
  desktop;
- the V2 window rail is visually lighter than the topology canvas and starts
  with only `main`;
- V1 reuses the same canvas and inspector, keeps split editing available, and
  removes only named-window/sidebar affordances;
- pane metadata uses small chips so provider, workspace, RolePack, and
  `not ask target` are scannable without becoming dashboard metrics;
- activation review and communication flow use secondary panel weight so they
  explain state without competing with the editor;
- the communication-flow panel sits below activation review as an observer,
  not inside the primary config editor;
- agent session storage is a tertiary maintenance band at the bottom, not a
  primary workflow surface;
- activation review is compact and secondary to the editor, while the sticky
  bottom action bar remains the main execution control.

### Prototype Validation Evidence

2026-07-09 real-browser validation used the standalone prototype directly from
the project checkout. Evidence screenshots:

- desktop static view:
  `/tmp/ccb-config-panel-final-desktop.png`;
- mobile static view:
  `/tmp/ccb-config-panel-final-mobile.png`;
- interactive V3/Chinese state:
  `/tmp/ccb-config-panel-final-workflow-cdp.png`;
- interactive mobile state:
  `/tmp/ccb-config-panel-final-mobile-cdp.png`.

Validation commands:

- `perl -0ne 'print $1 if /<script>([\s\S]*)<\/script>/m' .../index.html |
  node --check -`;
- `google-chrome --headless=new --disable-gpu --no-sandbox --window-size=1500,1750
  --screenshot=/tmp/ccb-config-panel-final-desktop.png file://.../index.html`;
- `google-chrome --headless=new --disable-gpu --no-sandbox --window-size=390,1200
  --screenshot=/tmp/ccb-config-panel-final-mobile.png file://.../index.html`;
- a Chrome DevTools Protocol script against headless Chrome.

The CDP script passed 16 assertions covering:

- Static V2 default view and one-window `main` rail;
- shared V1/V2 split toolbar availability;
- Rich pane selection and `not ask target` labeling;
- absence of unsupported editor-tool labels in the prototype DOM;
- communication-flow pause/resume and trace drawer;
- sidebar percentage controls and multiline tips textarea;
- language switch to Chinese;
- V1 switch confirmation plus V1 TOML without `[windows]`;
- V3 switch confirmation and activation-blocked state;
- validate/dry-run gate state updates;
- mobile viewport without material horizontal overflow.

2026-07-10 provider/model integration evidence added:

- the served page loads token-guarded `/api/capabilities` rather than relying
  only on frontend constants;
- current project-managed Codex cache entries render in the browser, including
  GPT-5.6 Sol/Terra/Luna and their advertised reasoning metadata;
- current Claude, Gemini, and DeepSeek V4 suggestions are exposed;
- DeepSeek V4 Pro/Flash compile through Deep Code model/API environment
  overrides;
- V1/V2 thinking is writable for Codex and DeepSeek and remains disabled for
  providers without a tested compiler;
- the external 13-case matrix lives at
  `/home/bfly/yunwei/test_ccb2/config_ui_provider_model_matrix_20260710`.

The same 2026-07-10 browser pass added full English/Chinese UI coverage and
embedded the mobile Android 48px launcher asset as the page icon. CDP
tests sent real mouse and keyboard input through language, drawer, provider,
animation, validation, dry-run, and version-confirmation controls, then checked
desktop and 390px mobile screenshots for overflow.

The observer was subsequently constrained to a 500px maximum square and
`58dvh`, with smaller fixed agent nodes and a matching event-list height. The
1366x768 browser gate requires the complete observer panel to remain visible
between the sticky header and bottom action bar.

## Non-Goals

- Do not build a v3 workflow role/capacity matrix in this v2 panel.
- Do not build a runtime operations dashboard.
- Do not show provider secrets, auth files, or provider session excerpts.
- Do not treat tool windows as ask targets.
- Do not auto-save and auto-reload.
- Do not require raw compact grammar as the main editing path.
- Do not add a free-form workflow graph editor.
- Do not implement independent browser-side validation authority.

## Implementation Dependencies

The UI needs shared service/JSON contracts before a real implementation:

- parse/render layout AST;
- validate draft and saved config;
- effective config summary;
- provider/model capability summary for `model` and `thinking` controls
  (initial read-only capability endpoint landed 2026-07-10);
- reload dry-run result;
- apply result;
- stable error/warning paths;
- reload impact categories.

## Open Questions

- Should the panel write rich `[windows]` TOML only, or also preserve compact
  header plus overlay input when the existing file uses that older style?
- Should advanced manual compact-layout editing be available in the MVP, or
  deferred until AST round-trip tests are strong?
- Which overlay fields are formal v2 schema versus future/demo-only fields?
- Should `thinking` become a formal `[agents.<name>]` v2 overlay field, or
  should the panel route Codex/GPT reasoning effort through provider-profile
  config until agent-level schema support exists?
- What exact reload dry-run taxonomy should the panel use for
  `layout_change`, `replace_agent`, `tool_command_change`, and
  `sidebar_presentation_change`?
