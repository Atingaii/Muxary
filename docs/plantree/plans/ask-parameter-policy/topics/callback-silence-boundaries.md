# Chain And Silence Boundaries

Date: 2026-06-07

## Chain Boundary

`--chain` is not a parent-task flag. It is a child-dependency flag used by
the current active agent when the current task cannot finish until the child
result is available.

Top-level delegation uses plain `ask`:

```text
A -> B
```

Nested dependency delegation uses `--chain` only from the active parent task:

```text
A is running an active task from user
A --chain -> B

B is running an active task from A
B --chain -> C
```

CCB automatically delivers the continuation only after a chain edge exists. The
B-to-C chain continues B. A receives a continuation only after B later finishes
its own chain continuation.

## Chain Continuation Finalization Boundary

When an agent receives a CCB chain continuation, that continuation is not a
new delegation request to the original caller. The agent should finish the
current task directly with the final result. CCB owns delivery of that
continuation result upstream.

Do not use `ask`, `--chain`, or `--silence` to send the final continuation
result to the original caller. The runtime safety plan for this boundary lives
in
[callback-continuation-safety](../../callback-continuation-safety/README.md).

## Silence Boundary

`--silence` is silent-on-success delivery. It does not mean the task is
unimportant, and it does not make the target job finish immediately.

Good silent tasks include:

- release or deploy execution steps
- smoke checks, lint checks, cleanup, and sync
- notifications or status broadcasts
- background work where success is routine

Failures, blockers, risks, and required next actions should still surface.

## Boundary Rule

An upstream silent edge does not decide downstream routing:

```text
A --silence -> B
```

B still runs an active job. If B needs C's result to finish, B uses chain. If
B is only dispatching independent work to C, B uses silence.

## Discouraged Combination

Avoid combining `--chain` and `--silence` in normal skill guidance. The
intents conflict: callback says the current task needs the result, while silence
says successful completion should not interrupt the caller. This is a guidance
rule, not a claim that the CLI rejects the combination.
