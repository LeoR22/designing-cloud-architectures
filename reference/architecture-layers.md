# Code architecture

The scripts follow clean architecture. Dependencies point inward only.

```
scripts/archdesign/
├── domain/        entities, validation rules, scoring (stdlib only)
├── application/   use cases and ports (interfaces)
├── adapters/      JSON input, Mermaid and SVG output, Markdown reports
└── cli.py         composition root: the only file that names concrete adapters
```

| Layer | May import | Must not import |
|---|---|---|
| domain | stdlib, itself | application, adapters, cli |
| application | domain | adapters, cli |
| adapters | domain, application | cli |
| cli | everything | n/a |

`tests/test_archdesign.py` enforces the first two rows.

## Extending

- **New output format** (for example draw.io): add a class in `adapters/` with an `extension` attribute and `render(architecture) -> str`, then register it in `RENDERERS` in `cli.py`. No other file changes.
- **New input format** (for example YAML or Terraform state): implement `ArchitectureSource.load(path)` in `adapters/`, and select it in `cli.py`.
- **New validation rule**: add a check in `domain/rules.py` with a new `ARCHnnn` code and an actionable message, plus a test.
- **New use case**: add a class in `application/use_cases.py` that receives ports in its constructor.

Use cases are tested with fakes (see `test_use_case_works_with_fakes_only`), so new ones should be too.

## Commands

```
PYTHONPATH=scripts python3 -m unittest discover -s tests
```
