# Resilience and failure-mode analysis

Design principle: every critical component either recovers by itself or has enough redundancy to wait until the next business day. A failure that needs a person at night is a design defect, unless an ADR records it as an accepted risk.

## Contents
- Questions per critical component
- Quorum clusters
- Failure-modes table
- After the incident

## Questions per critical component

1. Failure scenarios: transient (network drop, restart, full disk) or permanent (node or zone lost, data corrupted)?
2. Detection: which alert fires, and how soon?
3. Automatic response: restart, failover, reschedule, scale out?
4. Manual action if automation fails: can it wait until the next business day?
5. Recovery objectives: RTO and RPO.

If the answer to 4 is "no", add redundancy or self-healing to the spec and validate again.

## Quorum clusters

A majority-quorum cluster of `n` members needs `n // 2 + 1` alive. Use an odd `n`; an even count tolerates the same failures as `n - 1`.

| Members | Quorum | Failures tolerated |
|---|---|---|
| 3 | 2 | 1 |
| 5 | 3 | 2 |
| 7 | 4 | 3 |

In the spec, set `"stateful": true`, `"replicas": n` and `"quorum": true`. The validator reports fewer than 3 replicas (`ARCH012`) and even counts (`ARCH011`).

Worked case, 5 members with 3 down (2 alive, quorum lost):

- **Transient cause** (network, reboot, full disk): bring back one of the three. That gives 3 of 5, quorum returns, no configuration change and no data loss. The other two can be handled the next business day.
- **All three permanently lost:** run the disaster recovery procedure to restore quorum first. Reconfigure membership only when the failed members will not come back, because forcing a new configuration can discard committed data.

Write both branches into the runbook.

## Failure-modes table

Write `docs/failure-modes.md` with one row per failure scenario:

| Component | Failure | Detection | Automatic response | Manual action | Can wait until next business day? | RTO / RPO |
|---|---|---|---|---|---|---|

Also write a DR runbook: trigger, owner, numbered recovery steps, how to verify, and how to roll back.

## After the incident

1. Find the root cause.
2. Write a plan that stops it from happening again, and execute it.
3. Record the change as an ADR, add the missing control to the spec, validate, and answer the assessment again.
