"""Resilience rules. Principle: a failure must either heal itself or be able to wait
until the next business day; a component that needs a person at night is a design defect."""

from __future__ import annotations

from .models import Architecture, Issue, Severity

MIN_QUORUM_REPLICAS = 3  # the smallest majority cluster that survives one failure


def quorum_size(replicas: int) -> int:
    """Smallest majority of `replicas` members."""
    return replicas // 2 + 1


def tolerated_failures(replicas: int) -> int:
    """How many members can be lost while a majority remains."""
    return replicas - quorum_size(replicas)


def check(arch: Architecture) -> list[Issue]:
    issues: list[Issue] = []
    for c in arch.components:
        if c.quorum and c.replicas < MIN_QUORUM_REPLICAS:
            issues.append(Issue(
                "ARCH012",
                f"'{c.id}' is a quorum cluster with {c.replicas} replica(s); it needs at least "
                f"{MIN_QUORUM_REPLICAS} to survive one failure.",
                Severity.MEDIUM,
            ))
        elif c.quorum and c.replicas % 2 == 0:
            issues.append(Issue(
                "ARCH011",
                f"'{c.id}' has {c.replicas} replicas in a quorum cluster; it tolerates "
                f"{tolerated_failures(c.replicas)} failure(s), the same as {c.replicas - 1}. Use an odd count.",
                Severity.LOW,
            ))
        if c.stateful and c.replicas < 2 and not c.self_healing:
            issues.append(Issue(
                "ARCH010",
                f"'{c.id}' is stateful with a single replica and no self-healing, so one failure needs a "
                f"manual recovery. Add replicas, or set self_healing to true for a managed multi-zone service, "
                f"so a failure can wait until the next business day.",
                Severity.MEDIUM,
            ))
    return issues
