# Node Check Result

status: pass|rework_required|blocked|non_converged

node id: <node-id>
workgroup id: <workgroup-id>
code reviewer: <agent-name>

## Exact Node Workspace - Provider-Visible Review Identity

- workspace identity: <controller-supplied identity>
- workspace ref: <controller-supplied ref>
- base commit: <sha>
- head commit: <sha>
- canonical node work packet: <ref>
- changed paths: <paths>
- allowed paths: <paths>
- acceptance refs: <refs>
- verification refs: <refs>
- verification results: <results>
- blockers: <none or exact blocker>

## Check Plan

- <focused verification>

## Findings

- <finding or none>

## Boundary Checks

- provider-visible identity matched: yes|no
- scope violations: <none or paths>
- hidden fallback or degradation: <none or finding>
- missing acceptance/verification evidence: <none or refs>
- blockers: <none or exact blocker>
- reviewed tree modified by reviewer: no

## Required Rework

- <specific rework or none>

This evidence is read-only. The reviewer cannot mark the task or round done,
create authority commits, integrate the node, or submit downstream asks.
