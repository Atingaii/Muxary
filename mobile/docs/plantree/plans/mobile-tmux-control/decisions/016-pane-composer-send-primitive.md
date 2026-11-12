# Decision 016: Pane Composer Send Primitive

Date: 2026-06-22

## Status

Accepted.

Refines [Decision 015](015-pane-backed-chat-input.md). This decision freezes
the current compact composer send primitive so the A3 chat extraction can
continue without re-opening the source/gateway contract on every UI package.

## Context

Decision 015 moved the selected-agent composer from the mobile ask/message
route to direct selected-pane terminal input. After that change, the active
open question was whether the composer should keep using app-side paste plus
Enter, switch to bracketed paste plus Enter, or add a source/gateway helper
that performs both operations atomically against the selected pane.

The current app and gateway contract already support route-agnostic terminal
frames over the gateway WebSocket: paste text and write input bytes. The local
Android Emulator smoke proves this path can type into the selected CCB pane and
still open the raw terminal fallback. The app now also distinguishes partial
pane sends: if input may have reached the pane but Enter or transport follow-up
fails, the timeline shows `Check pane` and does not offer blind Retry.

Adding a source/gateway atomic helper now would be a gateway contract change,
not an app architecture extraction. It would require new source-side authority,
idempotency semantics, failure staging, and tests to avoid hiding terminal
state ambiguity behind a false "sent" signal.

## Decision

For the current mobile alpha and A3 app refactor:

- keep the default composer send primitive as app-side terminal `paste(text)`
  followed by Enter bytes against the selected CCB-validated pane;
- keep partial-send detection in `PaneChatController` and the chat UI's
  `Check pane` state as the conservative retry boundary;
- do not add a source/gateway atomic paste-plus-Enter helper in this A3 app
  extraction package;
- do not enable bracketed paste as the default compact-composer behavior until
  the gateway can prove the foreground program/pane mode supports it safely;
- treat a future CCB-owned multiline paste helper as a separate gateway/source
  contract package, not as a prerequisite for extracting timeline, bubble,
  content-reader, or readable-history widgets.

## Consequences

- A3 app extraction can proceed with the current `TerminalSession` abstraction.
- The compact composer remains honest about terminal ambiguity: the app cannot
  promise atomic execution when it only controls a remote terminal stream.
- The source/gateway roadmap still may add a stronger multiline helper later,
  but it must carry its own route contract, authorization, idempotency, failure
  staging, and emulator/source tests.
- The phone UI should keep making partial sends visible instead of retrying
  silently.

## Validation

The current contract is validated by:

1. widget and direct controller coverage for paste plus Enter sends;
2. staged send-failure tests that classify open, paste, and Enter failures;
3. selected-agent timeline coverage proving possible partial input renders as
   `Check pane` without Retry;
4. full app `flutter test`;
5. Android Emulator loopback smoke against a disposable CCB runtime proving the
   default paired-gateway path still works.
