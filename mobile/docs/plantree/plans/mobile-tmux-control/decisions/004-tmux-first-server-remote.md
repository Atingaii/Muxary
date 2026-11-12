# Decision 004: Tmux-First Server Remote

Date: 2026-06-18
Status: Proposed

## Decision

Make the phone/iPad product a tmux-first remote client for server-side CCB
sessions. The main task is to control CCB tmux panes running on the server, not
to create an independent mobile agent application.

Use a native Flutter app as the preferred client surface. Keep tmux-mobile as a
server-side terminal/gateway reference, not the primary mobile client base.

## Rationale

CCB's everyday working surface is already tmux. A mobile/iPad client is most
valuable when it lets the user connect to the same server-side workspace and
operate existing CCB panes remotely.

The user wants a native Android and iOS/iPadOS client. A web terminal alone
does not provide the desired QR pairing, native reconnect, notification, and
phone/iPad interaction polish. ServerBox and MuxPod show that a Flutter native
tmux/SSH client can provide a better base while still connecting to server-side
CCB tmux sessions.

## Consequences

- Interactive terminal control is a primary workflow, not a deferred add-on.
- CCB ask/composer, Comms, and Markdown are enhancement layers around the tmux
  remote.
- The mobile client should stay thin; CCB and providers continue running on the
  server.
- Generic tmux operations must be filtered or wrapped so CCB-managed sessions
  remain consistent.
- The first implementation should adapt a native Flutter terminal/tmux client
  to CCB project sockets and `ccbd` metadata.
- tmux-mobile remains valuable for socket-aware terminal WebSocket and gateway
  tests, especially if a CCB gateway transport is used.

## Validation Path

The decision is validated if a prototype can:

1. connect a phone/iPad to an active server-side CCB tmux session;
2. switch CCB projects without exposing unrelated tmux sessions;
3. switch/focus CCB agents and windows through CCB authority;
4. type, paste, resize, and reconnect without stopping server-side CCB;
5. keep Comms/Markdown/status visible as secondary context;
6. prevent stale or destructive tmux actions by default.
