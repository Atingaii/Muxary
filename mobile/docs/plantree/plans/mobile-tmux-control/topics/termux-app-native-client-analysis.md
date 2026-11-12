# Termux App Native Client Analysis

Date: 2026-06-18
Status: Superseded for primary base by Decision 005; retained as Android-only
terminal architecture research.

## Source Checkout

Repository: <https://github.com/termux/termux-app>

Local research checkout:

- path: `/tmp/ccb-mobile-research/termux-app`
- commit: `401bbe54b8f4e68302b1ff70678015a24628fb1d`
- commit date: 2026-06-05
- commit subject: ``Fixed: Do not add `BigTextStyle` to notification if big text is null``

Documents/source read:

- `README.md`
- `LICENSE.md`
- `settings.gradle`
- `build.gradle`
- `app/build.gradle`
- `app/src/main/AndroidManifest.xml`
- `app/src/main/java/com/termux/app/TermuxActivity.java`
- `app/src/main/java/com/termux/app/TermuxService.java`
- `app/src/main/java/com/termux/app/RunCommandService.java`
- `terminal-emulator/src/main/java/com/termux/terminal/TerminalSession.java`
- `terminal-emulator/src/main/java/com/termux/terminal/TerminalEmulator.java`
- `terminal-view/src/main/java/com/termux/view/TerminalView.java`
- `terminal-view/src/main/java/com/termux/view/TerminalViewClient.java`

## What Termux Actually Provides

Termux is a mature Android terminal application and Linux environment. Its
repository includes:

- `app`: Android app, activity, foreground service, installer, local session
  management, notifications, command intent service;
- `terminal-emulator`: terminal buffer, ANSI/vt emulation, local
  `TerminalSession`, key handling;
- `terminal-view`: Android custom `View` for terminal rendering, gestures,
  scale, text selection, soft keyboard integration;
- `termux-shared`: shared Android, shell, settings, notification, markdown,
  plugin, and utility code.

This is valuable terminal infrastructure, but it is not a remote CCB control
protocol.

## Fit For CCB

Termux is attractive if the goal is a native Android client:

- better keyboard, IME, gesture, and terminal interaction than a browser;
- foreground service and notification patterns for stable reconnect;
- native QR scanner and deep-link pairing are natural additions;
- Android notifications can be integrated cleanly;
- offline paired-host/project cache is straightforward;
- the app can feel closer to Paseo-style mobile control than a plain terminal
  website.

It is not a direct replacement for the server gateway:

- CCB still runs on the server;
- project tmux sockets are on the server;
- `ccbd` JSON RPC is on the server;
- terminal streaming still needs a gateway or remote protocol;
- phone should not become the authority for tmux/session lifecycle.

## Key Constraint: Local PTY Assumption

The current `TerminalSession` is a local-process abstraction:

- it calls `JNI.createSubprocess(...)`;
- it owns a local PTY file descriptor;
- `updateSize()` calls `JNI.setPtyWindowSize(...)`;
- input writes to a local queue that writes to the local PTY;
- output is read from the local PTY into `TerminalEmulator`.

For CCB, terminal bytes come from the server over WebSocket or another remote
stream. A Termux-derived CCB app therefore needs a new abstraction:

```text
TerminalTransport
  connect(pairing/profile/project/terminal token)
  onBytes(bytes)
  write(bytes)
  resize(cols, rows, pixels)
  close(reason)
  reconnect(cursor/session token)
```

Then Android terminal code needs either:

- `RemoteTerminalSession` parallel to `TerminalSession`; or
- a refactor where `TerminalView` depends on a smaller session interface rather
  than concrete `TerminalSession`.

This is feasible, but it is a real Android engineering project, not a small
configuration patch.

## Product Shape If Using Termux

The right shape is not "Termux SSH into the server and run tmux". That would
feel simple but bypass CCB authority.

Recommended shape:

```text
Android app based on Termux terminal UX
  |
  | QR pairing, HTTPS/WebSocket, device token, resume cursor
  v
CCB mobile gateway on server
  |
  | terminal stream to project tmux socket/session
  | ccbd RPC for ProjectView, focus, lifecycle, content, notifications
  v
server-side CCB projects
```

In the current plan this Android-only shape is a reference, not the primary
implementation route. The cross-platform client should be Flutter-based, with
Termux kept as evidence for Android terminal/session ergonomics.

## QR Pairing Design

Server command:

```bash
ccb mobile serve --host 0.0.0.0 --pair
```

Server prints a QR code containing a pairing offer:

```json
{
  "scheme": "ccb-mobile",
  "gateway": "https://host-or-tailnet-name:port",
  "pairing_token": "short-lived-token",
  "expires_at": "2026-06-18T12:00:00Z",
  "host_fingerprint": "sha256:...",
  "server_name": "workstation",
  "suggested_scopes": [
    "view",
    "content",
    "focus",
    "terminal_input",
    "notify"
  ]
}
```

Phone flow:

1. first screen is "scan server QR";
2. app verifies host fingerprint and expiry;
3. app generates a device key pair;
4. app calls `POST /v1/pair/complete`;
5. server stores device id, public key, scopes, and display name;
6. app stores host profile and refresh/resume token;
7. app opens project list.

This is the user-facing "server configured, phone scans, then connects" model.

## Stability And Recovery Model

Native app should use a reconnect-first model:

- foreground service while a terminal is active;
- persistent notification for active remote session;
- WebSocket heartbeat with server cursor;
- exponential backoff reconnect;
- resume event stream by cursor;
- terminal reconnect with short-lived reissued terminal token;
- ProjectView snapshot refresh after reconnect;
- local cache of host/project list and last selected project;
- explicit "connection stale" input lock before accepting terminal input;
- terminal close never stops the CCB project.

Server support:

- terminal ids are scoped to device, project, namespace epoch, and session;
- terminal input is rejected if namespace epoch or target identity is stale;
- event stream is idempotent and can replay from cursor;
- notification acknowledgements are idempotent.

## Simple Mobile UI

The app should not expose a raw Termux shell home screen. It should expose CCB:

First run:

- scan QR;
- approve host;
- choose trusted profile.

Home:

- frequent projects;
- project health;
- active agents;
- waiting callbacks;
- unread Comms;
- last activity.

Project screen:

- terminal as primary tab;
- agent switcher bottom sheet;
- Comms/messages drawer;
- notifications drawer;
- Markdown/math reader drawer.

Terminal controls:

- extra keys row;
- paste/compose button;
- font size;
- reconnect indicator;
- input lock status;
- no raw split/kill/new-session buttons.

This matches the user's "more foolproof" goal better than exposing generic
Termux session management.

## Markdown And Formula Display

Termux already uses Markwon in parts of the app/shared code, which is useful
for Markdown. CCB still needs a content endpoint so the native app can render
message/reply/artifact text by id.

Native drawer should add:

- GFM table/task-list behavior;
- code copy;
- raw source toggle;
- formula rendering through a chosen Android math renderer or WebView-backed
  KaTeX/MathJax surface;
- link policy that blocks arbitrary server-local file paths.

Terminal capture should remain fallback only. Markdown should come from CCB
message/artifact authority.

## Licensing And Distribution

Termux app is GPLv3-only at the app level. The repository notes exceptions for
terminal emulator/view code and termux-shared licensing details, but a direct
fork of the whole app should be treated as GPLv3-only until a legal/license
audit says otherwise.

Implications:

- compatible with open-source/free distribution if CCB accepts GPLv3 for this
  Android app;
- different from the MIT tmux-mobile path;
- may complicate reuse in a permissively licensed CCB mobile component;
- using only terminal-view/terminal-emulator code still needs a file-level
  license audit.

## iPad And Cross-Platform Implication

Termux only helps Android. It does not solve iPad, iOS, or one shared native
codebase.

If iPad remains a primary target, CCB still needs one of:

- Flutter/React Native client using a terminal renderer;
- separate iOS native client;
- server-hosted PWA with xterm.js as a fallback or diagnostics surface.

Therefore Termux should not replace the native Flutter plan. It can remain a
source of Android terminal UX patterns after the shared app architecture is
stable.

## Comparison With Current Native Flutter Path

Termux-based native route:

- stronger Android terminal UX;
- stronger foreground-service/reconnect/notification primitives;
- QR scan and native pairing feel natural;
- much larger Android codebase;
- needs new remote session abstraction;
- Android-only;
- GPLv3 app license boundary.

Native Flutter route:

- one Android/iOS/iPadOS codebase;
- can reuse ServerBox-style SSH/session management if AGPL is acceptable;
- can reuse MuxPod-style tmux UX concepts;
- still needs CCB-specific project/agent/content/lifecycle model;
- terminal rendering may need hardening for IME, paste, resize, and math
  content drawers.

## Recommendation

Use Termux only as a research reference:

1. Keep the primary app route on native Flutter.
2. Borrow Android ideas around foreground service, notification lifecycle,
   terminal keyboard handling, and local session state only where useful.
3. Do not fork Termux as the main CCB mobile app unless the project becomes
   Android-first and accepts GPLv3 app licensing.
4. Keep server-side CCB authority in `ccbd`/gateway/CLI wrappers rather than
   inside an Android terminal shell.

If a later Android-specialized client is needed, it should still talk to the
same CCB transport contract instead of SSHing directly to arbitrary tmux.

## Android-Native Work Packages

### A1: Native Pairing Shell

- add camera/QR scan;
- parse `ccb-mobile://pair` or JSON QR offers;
- complete pairing with gateway;
- store host profile and device key;
- show project list from gateway.

### A2: Remote Terminal Session

- introduce `TerminalTransport`;
- implement WebSocket transport;
- implement `RemoteTerminalSession`;
- feed remote bytes into `TerminalEmulator`;
- write keyboard/paste bytes back to gateway;
- map resize to terminal resize frames.

### A3: CCB Project UI

- replace Termux session drawer with CCB projects and agents;
- add ProjectView status;
- add focus agent/window actions;
- lock input on stale epoch.

### A4: Recovery And Notifications

- foreground connection service;
- notification for active terminal;
- reconnect with resume cursor;
- Android notifications for completion/callback/Comms.

### A5: Markdown Reader

- content drawer backed by CCB content endpoint;
- Markdown/code/table support;
- formula rendering;
- safe link policy.

## Decision Point

Choose Termux route early only if:

- Android is the first-class target over iPad;
- GPLv3 app distribution is acceptable;
- native terminal UX is more important than fastest cross-platform MVP;
- there is Android engineering capacity for terminal/session refactoring.

Otherwise, keep Termux as a reference and implement the shared native Flutter
client first.
