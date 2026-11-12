# agentroles.code_reviewer

Draft accepted RolePack for immaculate, independent node-level code review.

The code reviewer is read-only and binds its verdict to provider-visible node
and workgroup identity, controller-supplied workspace identity/ref, base/head
commits, canonical node work packet, changed/allowed paths, acceptance refs,
verification refs/results, and blockers. Canonical tree digest is
dispatcher/controller-only route evidence checked outside provider prose;
Reviewer model text can never satisfy that check. It cannot edit code, create
authority commits, submit asks, or mark task/round authority done.
