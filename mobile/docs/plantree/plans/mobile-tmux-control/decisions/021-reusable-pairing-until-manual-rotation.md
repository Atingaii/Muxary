# Decision 021: Reusable Pairing Until Manual Rotation

Date: 2026-07-13
Status: Accepted

## Decision

The CCB Mobile pairing handoff is reusable and has no automatic expiry or
claim-count limit. Any number of devices may claim the current pairing code/QR
until the operator explicitly executes `ccb update mobile`, which rotates the
pairing generation and invalidates the previous handoff.

Already-issued per-device credentials are independent of the handoff. Manual
handoff rotation does not revoke paired devices; devices are revoked
individually through device management.

## Required Semantics

- successful claim does not consume or rotate the pairing code;
- gateway restart preserves the current pairing generation/code;
- only explicit `ccb update mobile` rotates the handoff;
- concurrent claims are supported and audited;
- each claim receives an independent device id/token/scopes record;
- token hashes and audit metadata are stored, never raw tokens in logs;
- authorization failure/revocation is distinct from route unavailability;
- app profile recovery never falls back to pairing merely because a health
  request timed out.

## Security Tradeoff

A copied pairing QR remains useful until manual rotation. This is an explicit
product choice favoring simple multi-device onboarding. Compensating controls
are private loopback/Tailnet/approved relay routing, scoped device tokens,
claim audit, device listing/revocation, redacted logs, and a clear manual
rotation action.

The UI and documentation must state that operators should run
`ccb update mobile` after unintended QR exposure.

## Supersedes

This resolves the prior open question about periodic host re-approval and
supersedes any implementation that consumes a pairing handoff after one claim
or silently refreshes it solely because it was claimed/expired.

