# designing-cloud-architectures

An agent skill that designs cloud architectures on AWS, GCP, Azure or multi-cloud, and produces:

- a validated architecture spec and a diagram (SVG and Mermaid)
- ADRs, a Dev/QA/Prod inventory, sequence diagrams and an implementation guide
- a failure-mode analysis (self-healing or redundancy, quorum math) enforced by validation rules
- a scored well-architected self-assessment with remediation rounds

The assessment is a self-evaluation against the bundled rubric, not an official provider audit.

## Layout

```
SKILL.md              instructions the agent loads when the skill applies
reference/            provider service ids, resilience guide, ADR template, rubric, code architecture guide
examples/             sample spec and two assessment rounds
scripts/archdesign/   Python code (clean architecture: domain, application, adapters, cli)
tests/                unit tests, including a dependency-rule check
```

## Usage

Requires Python 3.10+ and nothing else.

```
python scripts/run.py validate examples/debt-collection-lakehouse.json
python scripts/run.py diagram  examples/debt-collection-lakehouse.json
python scripts/run.py assess --rubric reference/rubric.json --answers examples/answers-round1.json
```

## Tests

```
PYTHONPATH=scripts python3 -m unittest discover -s tests
```

## Install as a skill

Zip the repository folder and upload it in your Claude skills settings, or copy it into your agent's skills directory.
