# Markdown Rendering For Mobile

Date: 2026-06-18
Status: Draft

## Purpose

Make CCB mobile useful for reading agent work, not only watching terminals.
Agent replies, ask requests, callbacks, Comms, and text artifacts are often
Markdown-shaped. On a phone, those should render as readable content with
mobile controls instead of only appearing as cramped terminal text.

## Product Position

Markdown display should be a first-class mobile surface:

- terminal snapshots answer "what is on the pane?";
- Markdown content views answer "what did the agent say or produce?";
- ask/composer answers "what should I send next?";
- Comms answers "what requires attention?".

Do not rely on terminal capture as the only way to read a completed agent
response when CCB has message, reply, or artifact evidence.

## Content Sources

Initial sources:

- ask request bodies from `MessageEnvelope.body`;
- large ask bodies from `MessageEnvelope.body_artifact`;
- Comms body previews from `project_view`;
- full Comms/request/reply bodies through a future content endpoint;
- callback/reply-delivery bodies;
- text artifacts under CCB's validated artifact storage.

Later sources:

- provider-native session logs when ownership and privacy rules are explicit;
- generated reports or patch summaries;
- selected file previews from workspace-safe endpoints;
- terminal captures only as a best-effort convenience mode.

## Rendering Layers

### Preview Layer

Used in project list, agent rows, and Comms rows.

Rules:

- one to three lines;
- strip noisy reply guidance and artifact stubs where possible;
- preserve enough code-ish text to be recognizable;
- never execute links, HTML, or scripts;
- show an artifact indicator when full text is stored separately.

`project_view` can keep returning `body_preview` for this layer.

### Reading Layer

Used when opening a Comms item, reply, result, or artifact.

Required Markdown features:

- headings;
- paragraphs;
- ordered and unordered lists;
- task lists;
- blockquotes;
- fenced code blocks with language labels;
- inline code;
- links;
- tables;
- inline math;
- block math;
- horizontal rules;
- plain text fallback.

Mobile-specific controls:

- copy whole message;
- copy code block;
- wrap or horizontally scroll code;
- table fit/scroll/card modes;
- formula zoom/copy-source controls;
- collapse long sections;
- jump to headings;
- search in long content;
- raw source toggle.

### Lazy Rendering And Performance Caching

Rich Markdown rendering must be demand-driven. Long conversations should not
parse and mount every Markdown body just because the project page opened.

Rules:

- collapsed timeline bubbles render only a plain preview;
- rich Markdown, tables, math, diff, and code views render only when the item
  is expanded and visible or inside a small near-viewport prefetch window;
- moving off-screen may release the rich widget subtree while preserving
  expanded state and scroll position;
- prefetch should be small enough for phone memory, with a starting
  `cacheExtent` around one partial screen rather than the whole timeline;
- incoming messages should not force a full rich-render pass for off-screen
  items.

Cache strategy:

- key render caches by `item.id`, `namespace_epoch`, `format`, render mode, and
  a body hash so stale ProjectView or edited content cannot reuse old output;
- prefer caching parsed/render-ready models or sanitized preprocessing results
  over caching `Widget` instances that depend on `BuildContext`;
- keep the cache bounded with a small LRU, initially around 50 to 100 expanded
  rich items;
- invalidate entries when namespace epoch, content id, body hash, render hints,
  or safety policy changes;
- keep raw source available even when cached rich rendering fails.

The first implementation should prove the visible-window/lazy-build boundary
before optimizing parser internals. If the selected Markdown package does not
expose a stable parser AST, start with viewport gating plus bounded keep-alive
for expanded visible items, then add deeper parsing cache only when profiling
shows it is needed.

### Terminal Layer

Used for readable terminal history, pane snapshots, and interactive terminal
mode.

Rules:

- preserve terminal text/ANSI behavior;
- do not treat terminal output as authoritative Markdown;
- provide a vertically scrollable readable history for the selected agent from
  current tmux pane scrollback, not just a single current-screen snapshot;
- clean ANSI/control noise, progress-line churn, and repeated prompts where
  safe, while keeping raw terminal available for fidelity;
- group command output, logs, code blocks, diffs, stack traces, and
  Markdown-looking text into readable blocks;
- promote selected-agent terminal history into compact foreground chat bubbles
  when useful: commands/input as strongly folded user-side items, and output
  blocks as folded agent-side evidence;
- label terminal-derived blocks as best-effort and expose freshness, pane,
  namespace, and stale-evidence warnings;
- optionally offer "render as Markdown" for copied/snapshot text, clearly
  marked as best-effort and user-triggered.

Terminal-derived foreground bubbles have stricter defaults:

- command/input and tmux output stay plain text unless the user explicitly
  requests a best-effort rich view;
- best-effort rich view must be per-block, reversible, and labeled as terminal
  evidence, not an authoritative CCB reply;
- terminal-derived rich view should use the same lazy-render/cache boundary as
  normal Markdown, but with a separate render mode in the cache key;
- raw terminal fidelity remains available through the explicit Terminal route
  and the full readable-history panel.

MVP history scope:

- capture the current pane plus retained tmux scrollback on demand when the
  selected agent opens or refreshes;
- preserve vertical scroll position while new output arrives;
- support pull-to-refresh and periodic incremental refresh when the selected
  agent is alive;
- show history-limit boundaries when older pane output is no longer available.

Long-term complete history requires a recorder/journal that stores terminal
output as it happens. Do not claim "all history" from tmux capture alone.

## API Implications

`project_view` should remain compact. It can include previews and content ids,
but full Markdown bodies should be fetched on demand.

Likely addition:

- `project_content_get`: returns a full message, reply, or validated artifact
  as text plus render hints.

Suggested content payload fields:

- `id`;
- `kind`;
- `format`: `markdown`, `plain`, `ansi`, or `unknown`;
- `text`;
- `artifact` metadata if backed by a text artifact;
- `source`: `ccbd`, `artifact`, `provider-log`, or `pane-capture`;
- `history_scope`: `structured`, `tmux_scrollback`, `terminal_journal`, or
  `current_screen` when the source is terminal-derived;
- `render_hints`;
- `created_at` and `updated_at` where available.

Render hints:

- `allow_html: false` by default;
- `trust: project-local`;
- `max_preview_chars`;
- `may_contain_host_paths`;
- `may_contain_secrets`;
- `preferred_code_wrap`.
- `math_enabled`;
- `math_renderer`: `katex`, `mathjax`, or `none`.

## Security And Privacy

Markdown rendering must be sanitized.

Default policy:

- raw HTML disabled;
- JavaScript URLs blocked;
- remote images disabled unless explicitly allowed;
- math rendering must not allow unsafe HTML/script injection;
- local file paths displayed as text unless routed through an approved CCB file
  endpoint;
- workspace links require a separate permission model;
- no arbitrary host path read from Markdown links;
- no automatic external navigation without user action.

This matters because agent output may contain untrusted or accidentally
sensitive content.

## Phone-Specific Display Details

The mobile reader should optimize for narrow screens:

- tables need horizontal scroll and card/list fallback;
- code blocks need copy and wrap controls;
- formulas need readable display on phone and iPad, including pinch/zoom or
  tap-to-expand for large block equations;
- long lines should not break layout;
- headings should create a compact outline;
- repeated logs should be collapsible;
- diff blocks should use a readable compact diff view;
- task lists should preserve checked state visually;
- footnotes and references can be placed behind expandable detail.

For CCB workflows, code blocks and diffs are especially important.

## Composer Support

The ask/composer should also be Markdown-aware:

- multiline editor;
- preview toggle;
- code fence helper;
- paste cleanup;
- artifact request hint when message is large;
- callback context shown above the editor;
- send-as-plain-text behavior preserved.

The default composer now writes plain text/Markdown-looking text to the
selected tmux pane through the pane-backed chat path from
[Decision 015](../decisions/015-pane-backed-chat-input.md). Markdown rendering
remains a client display feature unless a future API explicitly adds structured
rich content.

## Relation To Existing CCB Markdown Work

CCB already has rich/workbench-side Markdown preview behavior. Mobile Markdown
should be separate from that terminal integration:

- rich/workbench rendering improves terminal-side reading and preview surfaces;
- mobile rendering improves remote reading and Comms handling;
- both should use CCB content authority rather than raw pane identity.

## MVP Recommendation

Phase 1 should include:

1. Markdown-rendered Comms/detail view;
2. Markdown-rendered ask/callback request bodies where available;
3. artifact expansion through validated CCB artifact refs;
4. code-block copy;
5. formula rendering for common inline and block math syntax;
6. table horizontal scroll;
7. raw source toggle;
8. no raw HTML or remote image loading by default.

This gives a large usability gain before interactive terminal mode exists.

## Risks

- Rendering from terminal captures can misidentify prompts, ANSI, and partial
  output as Markdown.
- Eager rich rendering of long chat history can make the phone UI janky or
  memory-heavy; timeline virtualization and lazy rich rendering are required
  before scaling to large histories.
- Virtualized lists can interrupt long cross-screen text selection when
  off-screen cells are recycled; copy buttons and raw-source actions are the
  fallback.
- Returning full message bodies in `project_view` can make the high-frequency
  view heavy and leak more content than needed.
- Local links in agent output can become an unintended file-browsing API.
- Sanitized HTML from the server can drift from client renderer behavior.
- Mobile Markdown rendering can hide important raw formatting if there is no
  source toggle.

## Acceptance Criteria

- A phone can open a Comms item and read the full Markdown body without using a
  raw terminal.
- Long code blocks and tables remain usable on a narrow screen.
- Inline and block formulas render readably and have raw-source fallback.
- Large artifact-backed requests can be expanded through CCB validation.
- Raw source remains available for copy/debugging.
- Unsafe HTML, script links, remote images, and arbitrary local file reads are
  blocked by default.
- Pane snapshots remain clearly labeled as terminal output, not authoritative
  Markdown replies.
