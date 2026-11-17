"""Ports: the interfaces use cases depend on. Adapters implement them."""

from __future__ import annotations

from typing import Protocol

from ..domain.documents import ExtractionResult, SourceDocument
from ..domain.models import Architecture, Rubric


class ArchitectureSource(Protocol):
    def load(self, path: str) -> Architecture: ...


class DiagramRenderer(Protocol):
    extension: str

    def render(self, architecture: Architecture) -> str: ...


class AssessmentSource(Protocol):
    def load_rubric(self, path: str) -> Rubric: ...

    def load_answers(self, path: str) -> dict[str, int]: ...


class DocumentReader(Protocol):
    suffixes: tuple[str, ...]

    def read(self, path: str) -> SourceDocument: ...


class ExtractionStore(Protocol):
    def save(self, document: SourceDocument) -> ExtractionResult: ...

    def write_manifest(self, results: list[ExtractionResult]) -> str: ...


class SkillInstaller(Protocol):
    def install(self, source: str, destination: str, force: bool) -> str:
        """Copy the skill folder; return 'installed', 'replaced' or 'skipped (...)'."""
        ...

    def register_agents_md(self, project_root: str, skill_name: str, skill_path: str) -> str:
        """Add or refresh a pointer block in AGENTS.md; return 'created' or 'updated'."""
        ...
