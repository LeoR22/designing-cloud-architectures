"""Validation rules for an Architecture. Pure functions over domain entities."""

from __future__ import annotations

from collections import Counter

from . import resilience
from .models import Architecture, Issue, Provider, Severity

# Short labels keep boxes readable once the diagram is rendered.
MAX_LABEL_LENGTH = 24

CLOUD_PREFIXES = frozenset({"aws", "gcp", "azure"})
# Service prefixes that are valid on any provider (not a cloud-native service).
NEUTRAL_PREFIXES = frozenset({"saas", "onprem", "generic", "user"})

_SEVERITY_ORDER = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}


def _allowed_prefixes(provider: Provider) -> frozenset[str]:
    if provider is Provider.MULTI:
        return CLOUD_PREFIXES | NEUTRAL_PREFIXES
    return frozenset({provider.value}) | NEUTRAL_PREFIXES


def validate(arch: Architecture) -> list[Issue]:
    """Return every issue found, most severe first."""
    issues: list[Issue] = []
    group_ids = [g.id for g in arch.groups]
    comp_ids = [c.id for c in arch.components]

    for dup, n in Counter(group_ids).items():
        if n > 1:
            issues.append(Issue("ARCH001", f"Group id '{dup}' is used {n} times; ids must be unique.", Severity.HIGH))
    for dup, n in Counter(comp_ids).items():
        if n > 1:
            issues.append(Issue("ARCH001", f"Component id '{dup}' is used {n} times; ids must be unique.", Severity.HIGH))

    known_groups = set(group_ids)
    known_comps = set(comp_ids)

    for c in arch.components:
        if c.group not in known_groups:
            issues.append(Issue(
                "ARCH002",
                f"Component '{c.id}' uses unknown group '{c.group}'. Declared groups: {sorted(known_groups)}.",
                Severity.HIGH,
            ))

    connected: set[str] = set()
    for e in arch.connections:
        for end in (e.source, e.target):
            if end not in known_comps:
                issues.append(Issue(
                    "ARCH003",
                    f"Connection {e.source} -> {e.target} references unknown component '{end}'. "
                    f"Declared components: {sorted(known_comps)}.",
                    Severity.HIGH,
                ))
        if e.source == e.target:
            issues.append(Issue("ARCH005", f"Component '{e.source}' connects to itself.", Severity.MEDIUM))
        connected.update((e.source, e.target))

    if len(arch.components) > 1:
        for c in arch.components:
            if c.id not in connected:
                issues.append(Issue("ARCH004", f"Component '{c.id}' has no connections.", Severity.MEDIUM))

    allowed = _allowed_prefixes(arch.provider)
    for c in arch.components:
        if "." not in c.service:
            issues.append(Issue(
                "ARCH009",
                f"Service '{c.service}' of '{c.id}' must look like '<prefix>.<name>', e.g. 'aws.s3'.",
                Severity.MEDIUM,
            ))
        elif c.prefix not in allowed:
            issues.append(Issue(
                "ARCH006",
                f"Component '{c.id}' uses '{c.service}' but the architecture provider is "
                f"'{arch.provider.value}'. Allowed prefixes: {sorted(allowed)}. "
                f"Set provider to 'multi' if mixing clouds is intended.",
                Severity.MEDIUM,
            ))
        if len(c.label) > MAX_LABEL_LENGTH:
            issues.append(Issue(
                "ARCH007",
                f"Label of '{c.id}' has {len(c.label)} characters (max {MAX_LABEL_LENGTH}); shorten it.",
                Severity.LOW,
            ))

    used_groups = {c.group for c in arch.components}
    for g in arch.groups:
        if g.id not in used_groups:
            issues.append(Issue("ARCH008", f"Group '{g.id}' has no components.", Severity.LOW))

    issues.extend(resilience.check(arch))
    return sorted(issues, key=lambda i: _SEVERITY_ORDER[i.severity])
