# CCB Mobile Baseline

Date: 2026-06-18

## Scope

This project is for the mobile client and related gateway planning/work.

Known baseline:

- target client: native Flutter Android/iOS/iPadOS app;
- first practical validation target: Android emulator;
- product boundary: remote controller for server-side CCB, not local mobile
  provider runtime;
- first not-on-LAN route: Cloudflare Tunnel;
- future route: self-hosted/open relay behind the same route-provider
  boundary;
- source CCB implementation reference: `/home/bfly/yunwei/ccb_source`.

## Open Baseline Items

- Flutter app base still needs a final license decision: ServerBox fork versus
  smaller permissive app.
- Android SDK/Flutter environment still needs installation and emulator setup.
- iOS/iPadOS validation requires macOS/Xcode or real devices later.
