# Decision 023: One-Time Public Relay Admission

Date: 2026-07-15
Status: Accepted

## Context

The hosted CCB Relay should be usable by approved CCB users without requiring a
consumer account system or storing CCB conversations, terminal output, files,
or project data. A public encrypted socket without admission control would,
however, be reusable as an anonymous forwarding service by non-CCB clients.

This decision concerns admission to the hosted relay. It is separate from the
CCB host-to-phone pairing handoff governed by
[Decision 021](021-reusable-pairing-until-manual-rotation.md).

## Decision

Each approved applicant receives a cryptographically random, applicant-specific
relay invitation. The invitation activates exactly one CCB host connector and
is consumed atomically when that connector credential is successfully issued.
It cannot be reused for another host or device.

The activation request must include a newly generated host public key. The
relay binds the issued credential to that key and requires proof of possession
on later connections. The invitation is bootstrap material only and is never a
long-lived password.

The relay may operate without names, email addresses, phone numbers, or user
accounts. It must persist only the minimum anonymous security metadata needed
for one-time consumption, credential verification, quota enforcement, expiry,
and revocation. It must not persist forwarded CCB payloads.

## Required Semantics

- invitation states are `unused`, `consumed`, `expired`, or `revoked`;
- the transition from `unused` to `consumed` and host credential creation is
  one atomic transaction;
- concurrent claims produce exactly one successful credential issuance;
- the raw invitation is never stored or logged; the relay stores a keyed hash
  or equivalent verifier;
- a successful claim binds one relay host id to one host public key;
- a second host requires a new invitation;
- a lost activation response does not make the invitation reusable; an
  operator issues a replacement invitation after revoking any uncertain host
  credential;
- future host connections use proof of possession plus short-lived session
  capabilities, not the invitation;
- mobile devices still use the CCB host pairing flow and per-device scopes;
  claiming or rotating a relay invitation does not replace CCB device auth;
- the public relay accepts only the fixed CCB relay envelope, applies quotas
  and frame limits, and never exposes arbitrary TCP or HTTP proxying.

## Meaning Of "CCB Only"

The relay can require a valid relay credential, the CCB relay protocol, and a
valid CCB host pairing/device path. It cannot prove that an open-source client
binary is unmodified. User-Agent strings, package names, hidden endpoints, TLS
fingerprints, protocol magic values, or a shared secret embedded in CCB are not
authentication and must not be used as the trust boundary.

## Relationship To Reusable Mobile Pairing

[Decision 021](021-reusable-pairing-until-manual-rotation.md) remains active:
the CCB host pairing QR may remain reusable until manual rotation. The one-time
relay invitation activates the host's access to the hosted relay; it is not the
phone pairing code and is not embedded into every mobile pairing QR.

## Consequences

- A small persistent admission database is required even though business
  payload retention remains prohibited.
- Operators need invite issue, list/status, revoke, and host revoke commands.
- A relay credential leak is contained by key binding, expiry, quotas, and
  revocation rather than by rotating a shared global secret.
- Truly anonymous public relay access is out of scope; self-hosted operators
  may choose a different admission policy without changing `RouteProvider`.

## Related Plans

- [Public relay invitation and Alibaba Cloud deployment](../topics/public-relay-invitation-and-aliyun-deployment.md)
- [Public relay Android Emulator acceptance](../topics/public-relay-android-emulator-acceptance.md)
