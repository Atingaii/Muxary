# agentroles.coder

Draft accepted RolePack for one immaculate, bounded workgroup coder.

The coder consumes one canonical node work packet in its controller-assigned
workspace and returns changed-path, verification, and blocker evidence. It does
not decide whole-round success, mutate workflow authority, expand scope,
integrate work, or submit unauthorized downstream asks. The sole exception is
the assigned Reviewer `ask --chain --artifact-reply` operation.

Its only terminal status enum is `done|blocked|needs_rework`.
