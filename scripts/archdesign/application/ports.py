"""Ports: the interfaces use cases depend on. Adapters implement them."""

from __future__ import annotations

from typing import Protocol

from ..domain.models import Architecture, Rubric


class ArchitectureSource(Protocol):
    def load(self, path: str) -> Architecture: ...


class DiagramRenderer(Protocol):
    extension: str

    def render(self, architecture: Architecture) -> str: ...


class AssessmentSource(Protocol):
    def load_rubric(self, path: str) -> Rubric: ...

    def load_answers(self, path: str) -> dict[str, int]: ...
