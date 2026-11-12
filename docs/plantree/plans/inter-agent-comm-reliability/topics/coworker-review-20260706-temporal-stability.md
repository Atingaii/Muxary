# Coworker Review: Temporal Stability And Tailer Design

Date: 2026-07-06

Status: accepted review input; plan adjusted.

Artifact:

- `.ccb/ccbd/artifacts/text/completion-reply/job_b5689ffafbf1-art_389afb425c1c40c2.txt`

## Conclusion

Review result: `CONCERNS`, not blocking.

The review agrees with the core correctness direction:

- provider acceptance must be separate from daemon/job acceptance;
- provider epoch boundaries are needed;
- clear must be a CCB-owned barrier;
- terminal completion must require same-epoch accepted-turn evidence;
- fallback scans must be recovery/diagnostic, not normal completion.

The review rejects tailer-first as the first implementation path.

## Accepted Simplification

Do not start implementation with a new persistent tailer subsystem.

Rationale:

- existing provider polling already incrementally reads provider streams from a
  cursor;
- tailer-first would add a new long-lived runtime component, evidence store
  integration, supervisor ownership, and possible dispatcher/ack path changes;
- the immediate instability can be addressed with smaller changes:
  provider-acceptance fields, epoch enforcement, clear barrier, terminal
  predicate hardening, and recovery-only fallback;
- benchmark data should decide whether a separate persistent tailer is needed.

## Adjusted First Implementation Path

1. Add epoch identity and provider acceptance fields without behavior change.
2. Add `ccb_clear` barrier and epoch enforcement.
3. Move fallback scans out of normal completion into explicit recovery/diagnostic
   paths.
4. Keep compact evidence on the existing provider polling/completion item path.
5. Consider persistent tailer only if benchmarks prove polling still cannot meet
   latency goals after fallback is removed from the normal path.

## Probe Simplification

The review also flags post-clear probe as potentially overdesigned.

Accepted adjustment:

- keep `ccb_clear` epoch barrier as mandatory;
- make post-clear probe minimal and optional for readiness checking;
- probe states should be success/failure only;
- no `ready_no_stream_proof` state;
- the next real ask can serve as the practical proof of post-clear stream
  readiness when no explicit probe is requested.

## Decision

Preserve persistent tailer as a documented optimization candidate, but do not
make it the first landing slice.

The first landing slice should stay within the existing polling/dispatcher
architecture and avoid introducing a new long-lived service until there is
measured latency evidence that it is necessary.
