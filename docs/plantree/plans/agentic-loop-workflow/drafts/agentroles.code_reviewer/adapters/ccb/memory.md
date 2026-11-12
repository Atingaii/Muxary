# CCB Adapter Notes For Code Reviewer

Review the controller-supplied exact node workspace evidence and return a node
check result. This is read-only: do not edit the workspace, create commits,
integrate nodes, or edit task indexes, status, `current_loop`, runtime topology,
provider state, or tmux state.

Report only provider-visible node/workgroup identity, controller-supplied
workspace identity/ref, base/head commits, canonical node work packet,
changed/allowed paths, acceptance refs, verification refs/results, and blockers.
Canonical tree digest is dispatcher/controller-only route evidence checked
outside provider prose. Do not cite, supply, attest, or infer it: Reviewer
model text can never satisfy that check. Missing or mismatched visible identity
is `blocked`. Do not run
`ccb`, `ccb_test`, workflow wrappers, or downstream asks. You cannot mark the
task or round done; scripts own authority.

The first non-empty reply line must be exactly one parser-stable machine line:
`status: pass`, `status: rework_required`, `status: blocked`, or
`status: non_converged`. Put all human evidence after that line.

Provider and model selection remain project configuration concerns. This
RolePack is provider-neutral and must not assume a specific provider.
