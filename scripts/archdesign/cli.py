"""Composition root: the only place that knows concrete adapters."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from .adapters.docx_reader import DocxReader
from .adapters.fs_installer import FilesystemSkillInstaller
from .adapters.fs_store import FilesystemExtractionStore
from .adapters.image_reader import ImageReader
from .adapters.json_files import JsonArchitectureSource, JsonAssessmentSource
from .adapters.markdown_report import assessment_to_markdown, issues_to_text
from .adapters.mermaid_renderer import MermaidRenderer
from .adapters.pdf_reader import PdfReader
from .adapters.svg_renderer import SvgRenderer
from .adapters.text_reader import TextReader
from .application.use_cases import (
    ArchitectureInvalid,
    AssessArchitecture,
    ExtractDocuments,
    InstallSkill,
    RenderDiagram,
    ValidateArchitecture,
)
from .domain.errors import SpecError
from .domain.models import Severity
from .domain.targets import TARGETS

RENDERERS = {"svg": SvgRenderer, "mermaid": MermaidRenderer}

SKILL_ROOT = Path(__file__).resolve().parents[2]  # the folder that contains SKILL.md
DEFAULT_RUBRIC = SKILL_ROOT / "reference" / "rubric.json"


def _skill_name() -> str:
    skill_md = SKILL_ROOT / "SKILL.md"
    try:
        head = skill_md.read_text(encoding="utf-8").splitlines()[:10]
    except OSError:
        raise SpecError(f"Cannot find SKILL.md in {SKILL_ROOT}; run this script from an intact skill folder.") from None
    for line in head:
        match = re.match(r"name:\s*(\S+)", line)
        if match:
            return match.group(1)
    raise SpecError(f"{skill_md} has no 'name:' in its frontmatter.")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run.py", description="Validate, render and assess cloud architecture specs.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("extract", help="Extract text and images from use-case files (txt, md, docx, pdf, images).")
    p.add_argument("files", nargs="+")
    p.add_argument("--out", default="extracted", help="Output folder (default: extracted).")

    p = sub.add_parser("install", help="Copy this skill into the folders IDEs and agents read skills from.")
    p.add_argument("--target", default="agents", help=f"Comma-separated: {', '.join(t.name for t in TARGETS)}, or all (default: agents).")
    p.add_argument("--scope", choices=["project", "user"], default="project")
    p.add_argument("--project-root", default=".", help="Project folder for project scope (default: current folder).")
    p.add_argument("--force", action="store_true", help="Replace an existing installed copy.")
    p.add_argument("--agents-md", action="store_true", help="Also add a pointer block to the project's AGENTS.md.")

    p = sub.add_parser("validate", help="Check an architecture spec; exit 1 on high severity issues.")
    p.add_argument("spec")

    p = sub.add_parser("diagram", help="Render an architecture spec to SVG or Mermaid.")
    p.add_argument("spec")
    p.add_argument("--format", choices=sorted(RENDERERS), default="svg")
    p.add_argument("--out", help="Output file (default: next to the spec).")

    p = sub.add_parser("assess", help="Score answers against a rubric.")
    p.add_argument("--rubric", default=str(DEFAULT_RUBRIC), help="Rubric JSON (default: the bundled rubric).")
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
        if args.command == "install":
            outcomes = InstallSkill(FilesystemSkillInstaller(), str(Path.home())).execute(
                str(SKILL_ROOT), _skill_name(), [t.strip() for t in args.target.split(",") if t.strip()],
                args.scope, args.project_root, args.force, args.agents_md,
            )
            for o in outcomes:
                print(f"{o.target}: {o.status} -> {o.destination}")
            return 0

        if args.command == "extract":
            use_case = ExtractDocuments(
                [TextReader(), DocxReader(), PdfReader(), ImageReader()], FilesystemExtractionStore(args.out)
            )
            for r in use_case.execute(args.files):
                print(f"{r.name}: {r.kind.value}, {r.characters} characters, {len(r.images)} image(s) -> {r.directory}")
                for warning in r.warnings:
                    print(f"  WARNING: {warning}")
            print(f"Manifest: {Path(args.out) / 'manifest.json'}")
            return 0

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
