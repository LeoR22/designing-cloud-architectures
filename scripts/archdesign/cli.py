"""Composition root: the only place that knows concrete adapters."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .adapters.json_files import JsonArchitectureSource, JsonAssessmentSource
from .adapters.markdown_report import assessment_to_markdown, issues_to_text
from .adapters.mermaid_renderer import MermaidRenderer
from .adapters.svg_renderer import SvgRenderer
from .application.use_cases import (
    ArchitectureInvalid,
    AssessArchitecture,
    RenderDiagram,
    ValidateArchitecture,
)
from .domain.errors import SpecError
from .domain.models import Severity

RENDERERS = {"svg": SvgRenderer, "mermaid": MermaidRenderer}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run.py", description="Validate, render and assess cloud architecture specs.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="Check an architecture spec; exit 1 on high severity issues.")
    p.add_argument("spec")

    p = sub.add_parser("diagram", help="Render an architecture spec to SVG or Mermaid.")
    p.add_argument("spec")
    p.add_argument("--format", choices=sorted(RENDERERS), default="svg")
    p.add_argument("--out", help="Output file (default: next to the spec).")

    p = sub.add_parser("assess", help="Score answers against a rubric.")
    p.add_argument("--rubric", required=True)
    p.add_argument("--answers", required=True)
    p.add_argument("--out", help="Write the Markdown report here instead of stdout.")
    return parser


def _write(path: str, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    source = JsonArchitectureSource()
    try:
        if args.command == "validate":
            issues = ValidateArchitecture(source).execute(args.spec)
            print(issues_to_text(issues))
            return 1 if any(i.severity is Severity.HIGH for i in issues) else 0

        if args.command == "diagram":
            renderer = RENDERERS[args.format]()
            text = RenderDiagram(source, renderer).execute(args.spec)
            out = args.out or str(Path(args.spec).with_suffix(f".{renderer.extension}"))
            _write(out, text)
            print(f"Wrote {out}")
            return 0

        assessment = AssessArchitecture(JsonAssessmentSource()).execute(args.rubric, args.answers)
        report = assessment_to_markdown(assessment)
        if args.out:
            _write(args.out, report)
            print(f"Wrote {args.out}")
        else:
            print(report)
        return 0
    except ArchitectureInvalid as exc:
        print(issues_to_text(list(exc.issues)), file=sys.stderr)
        return 1
    except SpecError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
