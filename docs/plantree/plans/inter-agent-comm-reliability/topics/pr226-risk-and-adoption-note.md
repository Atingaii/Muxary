# PR226 Risk And Adoption Note

Date: 2026-06-14

Role: risk analysis and adoption gate
Status: planning record only
Domain: inter-agent communication transport
Read when: considering PR226-style transport hardening or diagnosing ask/callback message delivery races

## Context

PR226 proposed a broad inter-agent communication reliability slice:

- keep Codex bridge FIFO read end open for the process lifetime
- use non-blocking FIFO sends with bounded retry
- spool oversized request payloads and send a pointer through the FIFO
- write ACK files when the bridge reads a request
- add cancel flag files visible to agents
- add structured communication-path logging

For normal low-frequency ask usage on Linux, macOS, and WSL, the current system
does not appear to have a frequent user-visible stability problem. The value of
this change is mainly in closing low-probability races and improving diagnosis
under stress, chained callbacks, bridge restart windows, and large prompts.

Native Windows behavior is not evaluated in this note.

## Expected Stability Gains

- Persistent FIFO reader reduces the brief no-reader window created by
  open/read/close polling loops.
- Non-blocking writes prevent indefinite sender hangs when the bridge is dead,
  restarting, or not listening.
- ACK files distinguish "sender wrote a line" from "bridge read the line",
  which narrows delivery diagnosis.
- Spool-backed large payloads avoid relying on FIFO atomic writes for prompts
  larger than the safe pipe buffer.
- Communication logs make previously swallowed FIFO, pane-send, and binding
  refresh failures observable.

## Remaining Risks

- ACK currently means "bridge read the request"; it does not prove that the
  provider pane accepted or processed the prompt.
- ACK and spool filenames depend on request markers. If markers remain
  second-resolution plus PID, high-frequency sends from the same process can
  collide.
- Spool pointer resolution should be constrained to the runtime spool
  directory before promotion.
- Cancel flag file creation is not enough by itself; tests must prove the
  execution prompt actually includes the cancel flag path.
- Changing `ask_async` return type from plain bool to a bool-compatible enum is
  likely safe inside the repo, but still deserves compatibility review for
  external/plugin callers.
- The PR226 unit tests cover the new primitives, but not every cross-layer
  semantic boundary above.

## Adoption Gate

Do not promote this work from planning to implementation until the following
are explicit:

- ACK semantics are named precisely in UI/log output, or a second provider-send
  confirmation exists.
- Marker generation is collision-resistant for repeated sends in the same
  process.
- Spool references are restricted to the expected runtime spool directory.
- Cancel prompt injection has a regression test.
- Stress tests cover rapid sends, large prompts, callback-heavy traffic, and
  bridge restart windows on Linux or WSL.

## Current Decision

Record only. No source changes, release candidate changes, or main-branch
promotion are authorized by this note.
