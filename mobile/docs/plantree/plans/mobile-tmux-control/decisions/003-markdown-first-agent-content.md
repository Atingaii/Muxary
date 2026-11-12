# Decision 003: Markdown-First Agent Content

Date: 2026-06-18
Status: Proposed

## Decision

Treat Markdown-rendered CCB message content as a first-class mobile surface,
separate from terminal pane snapshots.

## Rationale

CCB agents usually communicate in Markdown-shaped text: plans, findings,
patches, lists, code blocks, diffs, and callback replies. On phones, reading
that through a raw terminal is slower and less reliable than rendering the
message or artifact content directly.

CCB already tracks message bodies, previews, artifacts, Comms state, and reply
delivery status. Mobile should use that authority when available and fall back
to terminal snapshots only for live pane inspection.

## Consequences

- `project_view` can stay compact with previews and content ids.
- Full content should be loaded on demand through CCB-authorized message or
  artifact endpoints.
- The mobile UI needs a sanitized Markdown reader with code, table, copy,
  collapse, and raw-source controls.
- Pane capture may offer best-effort Markdown rendering, but it must remain
  labeled as terminal output.

## Validation Path

The decision is validated if the MVP can:

1. open a Comms/callback item as readable Markdown;
2. expand large artifact-backed content safely;
3. copy code blocks and raw source on mobile;
4. handle tables and long code blocks on narrow screens;
5. avoid remote image/script/local-file exposure by default.
