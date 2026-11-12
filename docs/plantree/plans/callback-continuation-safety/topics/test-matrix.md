# Test Matrix

Role: validation plan
Status: active
Read when: adding tests or source-under-test validation for chain continuation safety
Related: [runtime guard contract](runtime-guard-and-prompt-contract.md)

Date: 2026-06-22

## Unit Tests

Add focused tests around chain validation:

| Case | Expected Result |
| --- | --- |
| Active parent is not a chain continuation; sender uses `ask --chain` to a child | accepted when existing result chain rules pass |
| Active parent is chain continuation; sender uses `ask --chain` to original caller | rejected with direct-finalization guidance |
| Active parent is chain continuation; sender uses `ask --chain` to a different child needed for follow-up work | accepted unless existing depth/cycle rules reject it |
| Active parent is chain continuation; parent already has outstanding result chain | rejected by existing one-outstanding-edge rule |
| Chain continuation body is generated | includes no-ask/no-chain/no-silence finalization instruction |

## Skill Template Tests

Update inherited ask skill template tests after wording changes:

- Codex, Claude, Droid, Kimi, and OpenCode ask guidance should contain the same
  continuation finalization rule where the provider has an ask skill.
- The rule must not weaken the existing "each waiting hop uses result chain" rule.
- Existing checks for result-intent selection, artifact policy, and no old
  command form should remain intact.

## External Source-Under-Test Validation

Run from the dedicated external project:

```bash
cd /home/bfly/yunwei/test_ccb2
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
/home/bfly/yunwei/ccb_source/ccb_test --diagnose
```

Then validate the source runtime from the same external project and isolated
home.

Required scenarios:

| Scenario | Providers | Expected Result |
| --- | --- | --- |
| Normal two-hop result chain | Codex -> Codex | final result reaches caller |
| Normal mixed result chain | Codex -> Claude -> Codex or Claude -> Codex -> Claude | final result reaches caller |
| Normal three-hop result chain | A -> B -> C -> D with at least one Claude continuation receiver | two sequential continuations finalize and the result reaches A |
| Bad upstream result chain attempt from continuation | Claude continuation receiver | rejected; no second chain edge is created |
| Direct finalization after child result | Claude continuation receiver | final answer auto-propagates upstream |
| Silent independent child work from active task | Any configured provider | unchanged behavior |

## Evidence To Record

Record only stable evidence in history after implementation:

- unit test command and result;
- external `ccb_test` command and result;
- chain edge count before and after the rejected bad attempt;
- provider mix used for the mixed-provider validation;
- any residual manual limitation or provider-specific flake.
