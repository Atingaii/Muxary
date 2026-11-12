# Decision 022: Device-Bound Push Completion Delivery

Date: 2026-07-13
Status: Accepted

## Protocol

- A paired device holding `notify` may `PUT` or `DELETE`
  `/v1/devices/me/push-token`. Registration replaces only that authenticated
  device's token; the token is never returned by any API, device list, audit,
  SSE event, or error.
- The gateway emits one canonical completion record. Its SSE representation and
  push representation share the exact `dedupe_key`; their public payload is
  exactly `id`, `kind`, `project_id`, `project_short_name`, `agent`,
  `completed_at`, and `dedupe_key`.
- A device whose fresh presence is `visible` and focused on that exact
  project/agent suppresses only its own push. Other paired devices remain
  eligible. SSE remains unchanged, so clients dedupe Push and SSE into one
  unread marker/system notification.
- A sender is an injected host-side callable with a bounded timeout. The
  gateway carries no Firebase credentials, service account, endpoint, SDK, or
  environment-to-credential fallback. Invalid-token results delete only the
  affected device token.

## Threat And Authorization Decisions

- Push registration, deletion, and delivery require the existing `notify`
  capability. Older profiles without it receive `403`; this does not revoke or
  mutate their profile. A missing, invalid, or revoked bearer remains `401` and
  requires normal re-pair after authoritative revocation.
- Tokens are private authorization material: they are persisted in the
  gateway's owner-only mobile state and omitted from public/audit output. A
  device may modify only its own token. Revoking a device atomically removes
  its presence, terminal handles, and push token.
- Completion text, prompts, replies, paths, output, errors, and credentials
  are prohibited from both outbound payloads and audit records.

## Dependency And Migration Decisions

- This package adds no Firebase or cloud dependency. An operator may later
  inject a sender built around Firebase Admin or another provider outside this
  repository; validating credentials, cloud project policy, and real-device
  delivery is external operator evidence.
- Existing `devices.json` records remain valid without a push token. Existing
  profiles retain their original scopes; only newly paired default profiles
  include the already-established `notify` scope. No automatic profile/token
  mutation or terminal-input replay occurs during reconnect.

## Verification Boundary

Focused gateway tests prove scope enforcement, device isolation, visible-target
suppression, shared dedupe/payload redaction, bounded sender timeout, invalid
token cleanup, revoke cleanup, and no sender credential configuration. Android
FCM/background/Doze evidence remains blocked on operator-provided Firebase
sender credentials and a real device environment.
