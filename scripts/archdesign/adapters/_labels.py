"""Shared label helpers for renderers."""


def replicas_suffix(replicas: int) -> str:
    return f" \u00d7{replicas}" if replicas > 1 else ""
