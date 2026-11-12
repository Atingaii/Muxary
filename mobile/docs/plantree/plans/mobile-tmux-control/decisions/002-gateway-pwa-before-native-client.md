# Decision 002: Thin Gateway Client Before Native-Only Client

Date: 2026-06-17
Status: Superseded by [Decision 005](005-native-flutter-tmux-first-client.md)

## Decision

Prototype the CCB mobile control surface as a server-side gateway plus mobile
web/PWA or thin shell before investing in a native-only client.

This direction is superseded. The user clarified that native Android and iOS
clients are first-class, and the latest source review found stronger native
Flutter bases than a web-first fork. The gateway/PWA reasoning remains useful
for server pairing, relay, and terminal proxy design, but it is no longer the
primary app delivery path.

## Rationale

The riskiest work is the CCB authority boundary, project discovery, ProjectView
mapping, tmux session/pane input validation, pairing, and terminal transport.
Those risks are mostly server/protocol risks, not native UI risks.

A gateway/PWA path keeps CCB and providers on the server, reuses web-terminal
components, tests on desktop and phone browsers, and leaves room for a later
Capacitor or native shell.

## Consequences

- `ccb mobile serve` or a sidecar gateway becomes the first prototype target.
- tmux-mobile becomes the closest implementation base for the tmux remote
  surface.
- ChatMux remains a useful reference for gateway auth and packaging patterns.
- MuxPod remains the strongest mobile UX reference, especially for terminal
  gestures and special keys.
- Native push, voice, secure enclave storage, and OS-specific integrations are
  deferred until the CCB protocol is stable.

## Validation Path

The decision is validated if a browser/PWA prototype can:

1. pair from a phone by QR;
2. list registered CCB projects;
3. open one project's server-side tmux session;
4. type, paste, resize, and reconnect through the terminal;
5. focus an agent/window through `ccbd`;
6. show ProjectView/Comms/Markdown side context;
7. reconnect without losing project identity or stopping server-side CCB.
