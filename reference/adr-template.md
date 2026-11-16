# ADR template

Save each decision as `docs/adr/NNNN-short-title.md`, numbered in order. One decision per file; keep it under one page.

```markdown
# NNNN. Decision title

- Status: Proposed | Accepted | Superseded by NNNN
- Date: YYYY-MM-DD

## Context
The forces at play: requirement, constraint, or risk that forces a choice.

## Decision
What was chosen, in one or two sentences, naming the services.

## Alternatives considered
- Option A: why it was not chosen.
- Option B: why it was not chosen.

## Consequences
- Positive: what improves.
- Negative: cost, lock-in, operational burden.
- Follow-ups: what must be done because of this decision.
```

Write an ADR for: provider choice, storage and database choice, ingestion pattern, security and recovery approach, and every cross-cloud link in a multi-cloud design.
