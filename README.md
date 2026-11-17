# designing-cloud-architectures

An agent skill that designs cloud architectures on AWS, GCP, Azure or multi-cloud. The use case can be plain text or attached files (images, PDF, Word). It produces:

- a requirements document extracted from the supplied files
- a validated architecture spec and a diagram (SVG and Mermaid)
- a failure-mode analysis (self-healing or redundancy, quorum math) enforced by validation rules
- ADRs, a Dev/QA/Prod inventory, sequence diagrams and an implementation guide
- a scored well-architected self-assessment with remediation rounds

The assessment is a self-evaluation against the bundled rubric, not an official provider audit.

## Works in any IDE that supports Agent Skills

The folder follows the open Agent Skills format (a `SKILL.md` plus scripts and references), so the same copy works across tools. Only the folder it must live in differs:

| Tool | Project folder | Install target |
|---|---|---|
| VS Code and Visual Studio (GitHub Copilot) | `.github/skills/`, `.claude/skills/` or `.agents/skills/` | `copilot` or `agents` |
| Cursor | `.cursor/skills/` or `.agents/skills/` | `cursor` or `agents` |
| Kiro | `.kiro/skills/` | `kiro` |
| JetBrains IDEs (IntelliJ IDEA and others) with Junie | `.junie/skills/` | `junie` |
| JetBrains Air | `.agents/skills/` (shared) | `agents` |
| Claude Code | `.claude/skills/` | `claude` |

Install from the cloned repository, run in your project folder:

```
python scripts/run.py install --target agents,kiro,junie --project-root . --agents-md
```

- `--target` takes a comma-separated list or `all`.
- `--scope user` installs globally in your home folder instead of the project.
- `--agents-md` adds a pointer block to the project's `AGENTS.md` for tools that read it.
- `--force` replaces an existing copy; without it an existing copy is kept.

Use `py -3` instead of `python` on Windows if needed. Tests and caches are not copied.

If your IDE agent cannot view images, describe diagrams in text; every other step works the same.

## Layout

```
SKILL.md              instructions the agent loads when the skill applies
reference/            provider service ids, intake and resilience guides, ADR template, rubric
examples/             sample specs and two assessment rounds
scripts/archdesign/   Python code (clean architecture: domain, application, adapters, cli)
tests/                unit tests, including a dependency-rule check and a skill lint
```

## Usage

Requires Python 3.10+. PDF text uses poppler (`pdftotext`) or, if absent, the optional `pypdf` package.

```
python scripts/run.py extract case.docx brief.pdf sketch.png --out extracted
python scripts/run.py validate examples/debt-collection-lakehouse.json
python scripts/run.py diagram  examples/debt-collection-lakehouse.json
python scripts/run.py assess --answers examples/answers-round1.json
```

## Tests

```
PYTHONPATH=scripts python3 -m unittest discover -s tests
```
