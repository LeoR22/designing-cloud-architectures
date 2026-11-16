"""Scoring of a self-assessment. Pure function over a rubric and answers."""

from __future__ import annotations

from .errors import SpecError
from .models import Assessment, Rubric

# 0 = not implemented, 1 = partially implemented, 2 = fully implemented.
LEVELS = (0, 1, 2)
_MAX_LEVEL = max(LEVELS)


def _percent(points: float, total: float) -> float:
    return round(100.0 * points / total, 1)


def assess(rubric: Rubric, answers: dict[str, int]) -> Assessment:
    ids = {q.id for q in rubric.questions}
    missing = sorted(ids - answers.keys())
    unknown = sorted(answers.keys() - ids)
    invalid = sorted(k for k, v in answers.items() if v not in LEVELS)
    problems = []
    if missing:
        problems.append(f"missing answers for {missing}")
    if unknown:
        problems.append(f"answers for questions not in the rubric: {unknown}")
    if invalid:
        problems.append(f"answers outside {list(LEVELS)}: {invalid}")
    if problems:
        raise SpecError("Answers do not match the rubric: " + "; ".join(problems) + ".")

    total_weight = sum(q.weight for q in rubric.questions)
    if total_weight <= 0:
        raise SpecError("The rubric must contain at least one question with weight > 0.")

    earned = sum(q.weight * answers[q.id] / _MAX_LEVEL for q in rubric.questions)

    pillars: dict[str, list[float]] = {}
    for q in rubric.questions:
        acc = pillars.setdefault(q.pillar, [0.0, 0.0])
        acc[0] += q.weight * answers[q.id] / _MAX_LEVEL
        acc[1] += q.weight
    by_pillar = tuple((name, _percent(e, w)) for name, (e, w) in sorted(pillars.items()))

    high_risks = tuple(q for q in rubric.questions if q.critical and answers[q.id] == 0)
    gaps = tuple(sorted(
        (q for q in rubric.questions if answers[q.id] < _MAX_LEVEL),
        key=lambda q: (-q.weight, q.id),
    ))
    return Assessment(_percent(earned, total_weight), by_pillar, high_risks, gaps)
