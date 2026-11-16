"""Renders an Architecture as a Mermaid flowchart (left to right, one subgraph per group)."""

from __future__ import annotations

from collections import defaultdict

from ..domain.models import Architecture


def _esc(text: str) -> str:
    return text.replace('"', "'").replace("|", "/")


class MermaidRenderer:
    extension = "mmd"

    def render(self, architecture: Architecture) -> str:
        by_group = defaultdict(list)
        for c in architecture.components:
            by_group[c.group].append(c)

        lines = ["flowchart LR"]
        for g in architecture.groups:
            lines.append(f'  subgraph g_{g.id}["{_esc(g.label)}"]')
            for c in by_group[g.id]:
                lines.append(f'    n_{c.id}["{_esc(c.label)}<br/>{_esc(c.service)}"]')
            lines.append("  end")
        for e in architecture.connections:
            arrow = f"-->|{_esc(e.label)}|" if e.label else "-->"
            lines.append(f"  n_{e.source} {arrow} n_{e.target}")
        return "\n".join(lines) + "\n"
