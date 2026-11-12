# Product Requirements

Date: 2026-06-18
Status: Draft

## Product Mission

The phone/iPad client is a remote controller for CCB already running on a
server. It should make server-side CCB projects usable away from the desktop
through a CCB-aware agent workspace first, while keeping raw tmux pane control
available when explicitly requested. The app should expose the CCB-specific
structure that plain tmux clients do not know: projects, named agents, agent
status, Comms, lifecycle, and Markdown/math content.

## Requirement Pillars

### Project Layer

The user can work across multiple CCB projects.

Required behavior:

- show registered CCB projects, not arbitrary tmux sessions;
- keep a frequent/favorite project list;
- pin, unpin, and reorder common projects;
- show project health and lifecycle state;
- wake/open a stopped project when allowed;
- close only the mobile view without stopping the project;
- stop a running project through CCB lifecycle semantics when explicitly
  requested;
- remember last opened project and last selected agent/window per device.

State labels:

- stopped;
- starting;
- running;
- degraded;
- stopping;
- failed;
- offline;
- unknown.

### Multi-Agent Layer

One CCB project has multiple named agents. Switching between them must be fast.

Required behavior:

- list named agents with provider, window, and current state;
- one-tap select an agent as the current workspace;
- provide explicit focus and open-terminal actions for the selected agent;
- show which agent/window is currently selected and which pane is currently
  active when that evidence is available;
- show queue depth, callback waiting, Comms attention, and health;
- show completion state for recent tasks;
- avoid exposing raw pane ids as the main user-facing identity.

Agent state labels:

- idle;
- active;
- running;
- waiting;
- callback;
- completed;
- failed;
- blocked;
- unhealthy;
- missing;
- unknown.

### Agent Workspace Layer

The default project surface is a single selected-agent workspace.

Required behavior:

- show a top agent switcher inside the project view;
- render exactly one selected agent workspace in the main body;
- keep project path, gateway URL, pairing, runtime id, and diagnostics behind a
  connection details affordance instead of in the main viewport;
- show structured Comms, replies, artifacts, current task, and attention state
  for the selected agent;
- let agent taps switch the selected agent instead of opening raw terminal by
  default;
- provide explicit ask, focus, refresh, and open-terminal actions.

### Terminal Remote Layer

The terminal is a required raw-control fallback, not the default reading
surface.

Required behavior:

- open a server-side CCB tmux project session from phone/iPad;
- type, paste, resize, reconnect, and close the mobile view;
- provide mobile/iPad special keys and paste controls;
- switch projects, windows, and agents without memorizing tmux pane ids;
- lock input when namespace or pane evidence is stale;
- avoid destructive tmux operations by default.

### Completion And Attention Layer

The user needs to know when remote work needs attention.

Required behavior:

- notify on task completed;
- notify on failed/incomplete/cancelled;
- notify on callback waiting;
- notify on Comms mention;
- notify on agent unhealthy or pane missing;
- notify on project backend offline/start/stop result;
- show a compact notification center inside the app;
- deep-link notifications to project plus agent/window/Comms identity.

Notifications should not depend on pane ids alone.

### Markdown And Formula Layer

Agent output is often Markdown. It should be readable on phone/iPad.

Required behavior:

- render Comms, ask/callback bodies, replies, and artifacts as Markdown;
- support headings, lists, task lists, code blocks, diffs, tables, links, and
  long text;
- support inline and block math formulas;
- provide copy buttons for code and raw source;
- provide table scroll/card behavior for narrow screens;
- provide formula zoom or expand behavior;
- keep raw source fallback;
- block unsafe HTML, scripts, remote images, and arbitrary local-file reads by
  default.

## MVP Cut

Minimum useful MVP:

1. favorite project list;
2. wake/open running project agent workspace;
3. close mobile view and stop project with confirmation;
4. named-agent switcher with state badges and single selected-agent workspace;
5. explicit terminal input/paste/reconnect mode;
6. completion/callback notifications in-app;
7. Markdown reader with code, table, and formula support;
8. safe CCB-scoped tmux access only.

## Non-Goals

- running providers on the phone;
- making the phone an independent CCB runtime;
- browsing arbitrary tmux sessions by default;
- generic SSH server management;
- unrestricted tmux session/window/pane mutation;
- treating pane id as the durable user-facing identity.

## Acceptance Criteria

- A user can pin three CCB projects and switch between them from iPad.
- A stopped project can be woken and opened into the CCB project workspace.
- A running project can be stopped only through an explicit CCB lifecycle
  confirmation.
- A project with multiple named agents shows a top agent switcher and only one
  selected agent workspace in the main body.
- Agent taps switch the selected agent; focus and terminal entry are explicit
  actions.
- A completed or blocked task produces a visible reminder.
- A Markdown reply with code, table, and formulas is readable on phone and iPad.
- Raw terminal remains available as an explicit control/debug fallback.
