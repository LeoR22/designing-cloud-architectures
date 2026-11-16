---
name: designing-cloud-architectures
description: Designs cloud architectures on AWS, GCP, Azure or multi-cloud and produces a validated diagram (SVG and Mermaid), ADRs, a Dev/QA/Prod inventory, sequence diagrams, an implementation guide, and a scored well-architected self-assessment with remediation rounds. Use when the user asks to design, diagram, document or review a cloud architecture, data platform or migration.
---

# Designing cloud architectures

Turns a short request into a validated architecture spec, then renders and assesses it with the bundled scripts. Write deliverables in the user's language; keep JSON keys and service ids in English.

## Workflow

Copy this checklist and tick it off:

```
- [ ] 1. Clarify requirements
- [ ] 2. Pick services
- [ ] 3. Write the architecture spec and validate it
- [ ] 4. Render the diagram and inspect it
- [ ] 5. Write the documentation
- [ ] 6. Assess, remediate, re-assess
- [ ] 7. Deliver
```

**1. Clarify requirements.** Ask only for what is missing: business goal, provider (AWS, GCP, Azure or multi), data volume and latency needs, compliance constraints, environments. If the request already covers these, do not ask.

**2. Pick services.** Read the file for the chosen provider: [AWS](reference/aws.md), [GCP](reference/gcp.md), [Azure](reference/azure.md). Prefer managed services, one service per responsibility. For multi-cloud, justify every cross-cloud link in an ADR. Third-party platforms use `saas.<name>` (for example `saas.databricks`).

**3. Write the spec and validate.** Save `architecture.json` (format below; full example in [examples/debt-collection-lakehouse.json](examples/debt-collection-lakehouse.json)), then run:

```
python scripts/run.py validate architecture.json
```

Fix every HIGH issue and rerun until it passes. Fix MEDIUM issues unless there is a stated reason.

**4. Render and inspect.**

```
python scripts/run.py diagram architecture.json                    # SVG
python scripts/run.py diagram architecture.json --format mermaid   # Mermaid
```

If `rsvg-convert` exists, convert the SVG to PNG and look at it. Shorten labels or split a crowded group if lines cross or text overflows.

**5. Write the documentation.**
- One ADR per significant decision, using [reference/adr-template.md](reference/adr-template.md).
- Inventory table per environment (Dev, QA, Prod): component, service, sizing, owner.
- Three Mermaid sequence diagrams for the main flows.
- Implementation guide: numbered steps, each with how to verify it.

**6. Assess, remediate, re-assess.**
1. Answer each question in [reference/rubric.json](reference/rubric.json) with 0 (not implemented), 1 (partial) or 2 (full), citing evidence from the spec. Do not inflate answers. Save them as `answers-round1.json` (shape in [examples/answers-round1.json](examples/answers-round1.json)).
2. Run:
   ```
   python scripts/run.py assess --rubric reference/rubric.json --answers answers-round1.json --out report-round1.md
   ```
3. For each high risk, add the missing components to the spec, validate, re-render, and answer again as `answers-round2.json`. Stop after two rounds and list any remaining gaps.

Users can extend the rubric with their own questions in the same JSON shape; set `"critical": true` on items whose absence is a high risk.

**7. Deliver.** Send the files with a short summary: score before and after, high risks cleared, remaining gaps. State that the result is a self-assessment against this rubric, not an official provider audit.

## Spec format

```json
{
  "name": "Order analytics",
  "provider": "aws",
  "groups": [{"id": "ingest", "label": "Ingestion"}],
  "components": [
    {"id": "queue", "label": "Orders queue", "service": "aws.sqs", "group": "ingest"}
  ],
  "connections": [{"from": "queue", "to": "writer", "label": "events"}]
}
```

- Ids: letters, digits and underscores, starting with a letter.
- `provider`: `aws`, `gcp`, `azure` or `multi`. Only `multi` allows services from more than one cloud.
- `service`: `<prefix>.<name>` where prefix is `aws`, `gcp`, `azure`, `saas`, `onprem`, `generic` or `user`.
- Every component belongs to one declared group and has at least one connection. Labels up to 24 characters.
- Groups become horizontal lanes and the flow reads left to right. Order groups by data flow: sources, ingestion, processing, serving, then security and recovery.

## Output layout

```
architecture/
├── architecture.json / .svg / .mmd
├── docs/adr/0001-<decision>.md
├── docs/inventory.md
├── docs/sequences.md
├── docs/implementation-guide.md
└── assessment/answers-round1.json, report-round1.md, answers-round2.json, report-round2.md
```

## Scripts

Run them; do not read their source unless changing them. They use only the Python 3.10+ standard library. Exit codes: 0 success, 1 blocking architecture issues, 2 invalid input. Error messages list the valid values, so fix the input and rerun.

To change or extend the code (new renderer, new input format), read [reference/architecture-layers.md](reference/architecture-layers.md) first. Tests:

```
PYTHONPATH=scripts python3 -m unittest discover -s tests
```
