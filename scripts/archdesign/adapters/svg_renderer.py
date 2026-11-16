"""Renders an Architecture as a standalone SVG using swimlanes.

Layout: one horizontal lane per group, one column per dependency rank, so the
flow always reads left to right and edges never cross a lane label.
"""

from __future__ import annotations

from collections import defaultdict
from xml.sax.saxutils import escape

from ..domain.models import Architecture, Component

NODE_W, NODE_H = 150, 56
COL_GAP, ROW_GAP = 70, 20
LANE_PAD, LANE_GAP, LANE_LABEL_W, MARGIN = 16, 10, 150, 20
LOOP_STEP = 14  # spacing between feedback-edge corridors below the lanes

# (fill, stroke) per service prefix; anything else is neutral grey.
PALETTE = {
    "aws": ("#FFF4E0", "#E08A00"),
    "gcp": ("#E8F0FE", "#1A73E8"),
    "azure": ("#E6F2FB", "#0078D4"),
}
NEUTRAL = ("#F1F3F4", "#5F6368")


def _layering(arch: Architecture) -> tuple[dict[str, int], set[tuple[str, str]]]:
    """Longest-path rank per component, plus the edges that close a cycle.

    A DFS in declaration order finds the edges that close a cycle (for example
    scores flowing back to the CRM); those are dropped for ranking only, so the
    first-declared components stay on the left.
    """
    succ: dict[str, list[str]] = {c.id: [] for c in arch.components}
    for e in arch.connections:
        succ[e.source].append(e.target)

    state: dict[str, int] = {}  # 1 = on the DFS stack, 2 = finished
    back_edges: set[tuple[str, str]] = set()

    def visit(node: str) -> None:
        state[node] = 1
        for nxt in succ[node]:
            if state.get(nxt) == 1:
                back_edges.add((node, nxt))
            elif nxt not in state:
                visit(nxt)
        state[node] = 2

    for c in arch.components:
        if c.id not in state:
            visit(c.id)

    preds: dict[str, list[str]] = {c.id: [] for c in arch.components}
    for e in arch.connections:
        if (e.source, e.target) not in back_edges:
            preds[e.target].append(e.source)

    memo: dict[str, int] = {}

    def rank(node: str) -> int:
        if node not in memo:
            memo[node] = max((rank(p) + 1 for p in preds[node]), default=0)
        return memo[node]

    return {c.id: rank(c.id) for c in arch.components}, back_edges


def _ranks(arch: Architecture) -> dict[str, int]:
    return _layering(arch)[0]


class SvgRenderer:
    extension = "svg"

    def render(self, architecture: Architecture) -> str:
        ranks, back_edges = _layering(architecture)
        placement: dict[str, tuple[int, int]] = {}
        stack: dict[tuple[str, int], int] = defaultdict(int)
        lane_rows: dict[str, int] = defaultdict(int)
        for c in architecture.components:
            slot = stack[(c.group, ranks[c.id])]
            stack[(c.group, ranks[c.id])] += 1
            placement[c.id] = (ranks[c.id], slot)
            lane_rows[c.group] = max(lane_rows[c.group], slot + 1)

        lanes: dict[str, tuple[int, int]] = {}
        y = MARGIN
        for g in architecture.groups:
            rows = max(lane_rows[g.id], 1)
            height = 2 * LANE_PAD + rows * NODE_H + (rows - 1) * ROW_GAP
            lanes[g.id] = (y, height)
            y += height + LANE_GAP
        lanes_bottom = y - LANE_GAP
        total_h = lanes_bottom + MARGIN + LOOP_STEP * len(back_edges)
        max_rank = max(ranks.values(), default=0)
        total_w = 2 * MARGIN + LANE_LABEL_W + (max_rank + 1) * NODE_W + max_rank * COL_GAP
        if back_edges:
            total_w += 20  # room for feedback edges leaving the last column

        def origin(c: Component) -> tuple[int, int]:
            rank, slot = placement[c.id]
            top, _ = lanes[c.group]
            return (
                MARGIN + LANE_LABEL_W + rank * (NODE_W + COL_GAP),
                top + LANE_PAD + slot * (NODE_H + ROW_GAP),
            )

        by_id = {c.id: c for c in architecture.components}
        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" '
            f'viewBox="0 0 {total_w} {total_h}" font-family="sans-serif" role="img">',
            f"<title>{escape(architecture.name)}</title>",
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            'markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#5F6368"/></marker></defs>',
            f'<rect width="{total_w}" height="{total_h}" fill="#FFFFFF"/>',
        ]

        for g in architecture.groups:
            top, height = lanes[g.id]
            out.append(
                f'<rect x="{MARGIN}" y="{top}" width="{total_w - 2 * MARGIN}" height="{height}" '
                f'rx="8" fill="#FAFAFA" stroke="#DADCE0"/>'
            )
            out.append(
                f'<text x="{MARGIN + 10}" y="{top + height // 2 + 4}" font-size="12" '
                f'font-weight="bold" fill="#3C4043">{escape(g.label)}</text>'
            )

        loop_index = 0
        out_count: dict[str, int] = defaultdict(int)  # stacks labels of edges leaving one node
        for e in architecture.connections:
            sx, sy = origin(by_id[e.source])
            tx, ty = origin(by_id[e.target])
            x1, y1, x2, y2 = sx + NODE_W, sy + NODE_H // 2, tx, ty + NODE_H // 2
            if (e.source, e.target) in back_edges:
                # Feedback edge: leave right, run along a corridor under the lanes, enter left.
                corridor = lanes_bottom + 12 + LOOP_STEP * loop_index
                loop_index += 1
                path = f"M{x1},{y1} H{x1 + 10} V{corridor} H{x2 - 8} V{y2} H{x2}"
                label_xy = ((x1 + x2) // 2, corridor - 3)
            else:
                # Forward edge: all edges into one target share a vertical channel in the gap before it.
                channel = x2 - COL_GAP // 2
                path = f"M{x1},{y1} H{channel} V{y2} H{x2}"
                label_xy = (x1 + 4, y1 - 4 - 11 * out_count[e.source])
                out_count[e.source] += 1
            out.append(
                f'<path d="{path}" fill="none" stroke="#5F6368" stroke-width="1.5" '
                f'stroke-linejoin="round" marker-end="url(#arrow)"/>'
            )
            if e.label:
                anchor = "middle" if (e.source, e.target) in back_edges else "start"
                out.append(
                    f'<text x="{label_xy[0]}" y="{label_xy[1]}" font-size="10" '
                    f'text-anchor="{anchor}" fill="#5F6368">{escape(e.label)}</text>'
                )

        for c in architecture.components:
            x, yy = origin(c)
            fill, stroke = PALETTE.get(c.prefix, NEUTRAL)
            out.append(
                f'<rect x="{x}" y="{yy}" width="{NODE_W}" height="{NODE_H}" rx="8" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            )
            out.append(
                f'<text x="{x + NODE_W // 2}" y="{yy + 24}" font-size="13" font-weight="bold" '
                f'text-anchor="middle" fill="#202124">{escape(c.label)}</text>'
            )
            out.append(
                f'<text x="{x + NODE_W // 2}" y="{yy + 42}" font-size="10" '
                f'text-anchor="middle" fill="#5F6368">{escape(c.service)}</text>'
            )

        out.append("</svg>")
        return "\n".join(out) + "\n"
