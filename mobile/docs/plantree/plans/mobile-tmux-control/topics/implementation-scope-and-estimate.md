# Implementation Scope And Estimate

Date: 2026-06-18
Status: Draft

## Assumptions

This estimate assumes the chosen path is a native Flutter mobile app:

- Android and iOS/iPadOS are first-class targets;
- CCB and provider CLIs keep running on the server;
- the default project view is agent-first, with raw terminal/tmux control as
  an explicit fallback;
- ServerBox is the preferred fork candidate if AGPL is acceptable;
- MuxPod is the main tmux UX/command reference;
- CCB core remains authority for project lifecycle, ProjectView, focus,
  content, and namespace epoch;
- first usable local slice may use LAN/tailnet/manual URL;
- first ordinary not-on-LAN release should use CCB Relay;
- Cloudflare Tunnel remains an advanced/self-hosted route provider.

The estimate is for one experienced engineer unless stated otherwise.

## Change Surface Summary

Primary mobile app surfaces:

- Flutter repository/fork setup and license cleanup;
- CCB data model and local storage;
- QR pairing and host profile;
- route provider and diagnostics for LAN, CCB Relay, and advanced Cloudflare;
- terminal screen and transport adapters;
- socket-aware tmux command layer;
- project/agent/window UI with top agent switcher and single selected-agent
  workspace;
- Markdown/math reader;
- local notifications and deep links;
- Android/iOS packaging and device testing.

Primary CCB surfaces:

- optional `ccb mobile serve` gateway;
- optional `ccb mobile ... --json` wrappers for SSH direct transport;
- existing `project_view`, `project_focus_agent`, and `project_focus_window`
  reuse;
- content endpoint for full Markdown/artifact bodies;
- notification/event cursor later;
- lifecycle wrapper polish if existing CLI behavior is not stable enough.
- route-provider metadata for LAN/tailnet/Cloudflare/relay-compatible
  profiles.

## Base Options

### ServerBox Fork

Pros:

- mature Flutter iOS/Android app;
- existing SSH terminal and tmux attach/list/switch support;
- foreground service, Android notification, and iOS Live Activity patterns;
- broad platform packaging already exists.

Cons:

- AGPL license must be accepted for the app component;
- generic server management UI must be removed or hidden;
- tmux command layer is not socket-aware yet;
- app model is SSH host/server first, not CCB project/agent first.

Estimate to CCB-shaped baseline: 6-10 engineer-days.

### MuxPod Fork Or Port

Pros:

- best tmux-specific mobile UX;
- Apache-2.0;
- pane tree, special keys, deep links, reconnect, and paste-buffer patterns are
  highly relevant.

Cons:

- Android-first public target;
- less mature cross-platform product base;
- terminal is mostly capture-poll command mode, not full attach;
- no CCB/gateway/pairing model.

Estimate to CCB-shaped baseline: 8-14 engineer-days.

### Smaller New Flutter App

Pros:

- clean CCB-first model;
- cleaner license posture;
- avoids broad server-management cleanup.

Cons:

- more terminal, SSH, storage, notification, and platform code must be built or
  ported;
- slower to reach native polish.

Estimate to terminal-capable baseline: 12-20 engineer-days.

## Recommended Base

Use ServerBox as the main fork candidate if AGPL is acceptable. Keep the app
fully open source. Port/reimplement MuxPod's tmux-specific pieces where
ServerBox is too generic.

If a permissive-license mobile app is required, use a smaller Flutter app and
reuse MuxPod concepts without directly taking AGPL ServerBox/Paseo code.

## Mobile App Work

### Native Baseline And Cleanup

Work:

- create dedicated mobile repo;
- keep Android/iOS builds green;
- preserve upstream attribution;
- remove generic server dashboard from CCB profile;
- add fake CCB transport and fixture data.

Estimate: 4-8 engineer-days with ServerBox; 8-14 with new app.

### Socket-Aware Tmux Terminal

Work:

- add `tmux -S <socket>` to attach/list/capture/paste commands;
- bind terminal to project tmux socket and session;
- support SSH direct and/or gateway terminal transport;
- add tests for quoting and target binding;
- validate app background/resume and close behavior.

Estimate: 4-8 engineer-days.

### QR Pairing And Host Profile

Work:

- define pairing payload;
- implement QR scan and paste-link fallback;
- store host/device profile securely;
- add reconnect and revocation path;
- implement `ccb mobile serve` pairing if gateway mode is chosen first.

Estimate: 5-10 engineer-days for LAN/tailnet/manual gateway URL.

### Cloudflare Tunnel Remote Access

Work:

- route-provider envelope in QR and host profile;
- gateway health/capabilities endpoints;
- Cloudflare URL setup docs and diagnostics;
- WebSocket terminal stream through the tunnel;
- CCB token revocation independent of Cloudflare configuration;
- reconnect and route identity checks.

Estimate: 4-8 engineer-days after gateway pairing exists.

Relay is not included in this estimate.

### Project/Agent UI

Work:

- home/favorites/recent projects;
- project detail with agents, windows, Comms, health, and completion state;
- focus agent/window through CCB;
- stale namespace handling;
- phone bottom sheet and iPad side panel layouts.

Estimate: 8-14 engineer-days.

### Markdown And Math

Work:

- content id route or CCB endpoint;
- native Markdown renderer;
- formula renderer;
- code copy/table scroll/raw source toggle;
- safe link/image policy.

Estimate: 4-8 engineer-days if CCB content endpoint exists; 8-13 if the
endpoint and artifact validation must be built too.

### Notifications

Work:

- derive deltas from ProjectView/Comms;
- local notification and deep link routing;
- acknowledgement storage;
- background behavior tests.

Estimate: 5-9 engineer-days for local notifications; cloud push is separate.

### Lifecycle Controls

Work:

- wake/open/close/stop via CCB lifecycle;
- scope checks and confirmations;
- avoid raw tmux kill semantics.

Estimate: 4-8 engineer-days after project registry and pairing exist.

## CCB Source Impact

### Minimal Core Change Path

For the first terminal vertical slice, CCB core can remain mostly unchanged:

- manually provide project tmux socket/session facts;
- use existing `project_view`;
- use existing focus endpoints;
- test against an isolated CCB project.

Estimate: 1-3 engineer-days for wrappers/docs/manual harness.

### Likely CCB Additions For Alpha

Files likely touched:

- `lib/ccbd/socket_client_runtime/endpoints.py`;
- content lookup service under `lib/ccbd/`;
- CLI command registration/launcher code under `lib/cli/`;
- tests for socket endpoints, project view payloads, lifecycle, and content.

New or expanded behavior:

- `ccb mobile serve`;
- `ccb mobile ... --json` wrappers;
- content endpoint for full message/reply/artifact bodies;
- gateway/device registry and scopes;
- optional notification/event cursor.

Estimate: 10-18 engineer-days for Alpha/MVP-grade CCB-side additions.

## Construction Time By Milestone

### Native Terminal Vertical Slice

Goal:

- one known running CCB project;
- manual project socket/session facts;
- native app opens the CCB tmux session;
- basic terminal input/paste/reconnect;
- fixture project/agent side panel.

Time: 8-14 engineer-days.

With two engineers: 1-1.5 calendar weeks if one owns mobile terminal and the
other owns CCB/test harness.

### Usable Alpha

Goal:

- QR pairing or simple host profile;
- project list/favorites;
- live ProjectView;
- fast agent/window focus;
- guarded terminal input;
- Markdown/math drawer;
- basic completion/attention notifications.

Time: 30-45 engineer-days, roughly 6-9 calendar weeks for one engineer.

With two engineers: 3.5-5.5 calendar weeks if work splits cleanly across
mobile UI/terminal and CCB gateway/content.

### MVP

Goal:

- wake/open/close/stop for registered projects;
- reliable stale-epoch handling;
- content endpoint backed by CCB validation;
- notification acknowledgement and deep links;
- device revocation and scopes;
- phone and iPad layout coverage;
- documented Cloudflare Tunnel setup for not-on-LAN access.

Time: 55-83 engineer-days, roughly 11-17 calendar weeks for one engineer.

With two engineers: 6-9 calendar weeks.

### Production-Hardened Open Source Release

Goal:

- stable Android/iOS builds;
- security review of pairing and tunnel exposure;
- regression tests against real tmux and CCB test projects;
- installer/update docs;
- device revocation, backup/restore, diagnostics;
- clear license attribution.

Time: 80-120 engineer-days, roughly 16-24 calendar weeks for one engineer.

Public relay, cloud push, and mosh-like roaming should be separate follow-on
projects. A relay research spike is likely 8-15 engineer-days; an MVP-quality
self-hosted relay is likely another 20-35 engineer-days after the spike.

## Critical Path

1. Native repository and license decision.
2. CCB data model and fake transport.
3. Socket-aware tmux terminal.
4. QR pairing/host profile.
5. Cloudflare Tunnel route provider.
6. ProjectView and agent/window focus.
7. Markdown/content endpoint.
8. Notifications and deep links.
9. Lifecycle controls.
10. Revocation/scopes and release hardening.

## Main Schedule Risks

- License choice can change whether ServerBox/Paseo code can be reused.
- Mobile terminal resize can disturb the desktop tmux layout if attach behavior
  is not tested carefully.
- Direct SSH mode may drift into generic SSH/tmux if the UI is not CCB-first.
- Gateway mode needs pairing/scopes earlier.
- Completion notifications need a stable CCB event source; terminal scraping is
  not reliable enough.
- Markdown/math quality depends on content ids and artifact validation.
- iOS backgrounding/push restrictions can add platform-specific work.

## Recommended Scope Cut

Build in this order:

1. native baseline and fake CCB model;
2. socket-aware tmux terminal vertical slice;
3. QR pairing and live ProjectView;
4. Cloudflare Tunnel route provider for not-on-LAN access;
5. agent/window focus;
6. Markdown/math content drawer;
7. notifications;
8. lifecycle wake/stop;
9. revocation/scopes and multi-host hardening.

This keeps the first month focused on proving native tmux control of real CCB
server panes and Cloudflare-backed remote access instead of spending it on a
custom relay, cloud push, or full lifecycle automation.
