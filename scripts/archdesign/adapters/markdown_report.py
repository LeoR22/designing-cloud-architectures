"""Presents domain results as Markdown."""

from __future__ import annotations

from ..domain.models import Assessment, Issue

DISCLAIMER = "Self-assessment against a custom rubric; not an official provider audit."


def issues_to_text(issues: list[Issue]) -> str:
    if not issues:
        return "OK: no issues found."
    return "\n".join(f"[{i.severity.value.upper()}] {i.code}: {i.message}" for i in issues)


def assessment_to_markdown(assessment: Assessment, title: str = "Architecture self-assessment") -> str:
    lines = [
        f"# {title}",
        "",
        f"**Overall score: {assessment.score}%**  |  High risks: {len(assessment.high_risks)}",
        "",
        "| Pillar | Score |",
        "|---|---|",
        *[f"| {name} | {score}% |" for name, score in assessment.by_pillar],
        "",
        "## High risks",
        *(
            [f"- `{q.id}` ({q.pillar}): {q.text}" for q in assessment.high_risks]
            or ["- None"]
        ),
        "",
        "## Remaining gaps (highest weight first)",
        *(
            [f"- `{q.id}` ({q.pillar}): {q.text}" for q in assessment.gaps]
            or ["- None"]
        ),
        "",
        f"_{DISCLAIMER}_",
        "",
    ]
    return "\n".join(lines)
