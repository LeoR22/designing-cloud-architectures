"""Use cases. Each one orchestrates domain logic through ports."""

from __future__ import annotations

from ..domain.assessment import assess
from ..domain.models import Assessment, Issue, Severity
from ..domain.rules import validate
from .ports import ArchitectureSource, AssessmentSource, DiagramRenderer


class ArchitectureInvalid(Exception):
    """Raised when blocking (high severity) issues prevent rendering."""

    def __init__(self, issues: list[Issue]):
        self.issues = tuple(issues)
        super().__init__("; ".join(f"[{i.code}] {i.message}" for i in issues))


class ValidateArchitecture:
    def __init__(self, source: ArchitectureSource):
        self._source = source

    def execute(self, path: str) -> list[Issue]:
        return validate(self._source.load(path))


class RenderDiagram:
    def __init__(self, source: ArchitectureSource, renderer: DiagramRenderer):
        self._source = source
        self._renderer = renderer

    def execute(self, path: str) -> str:
        architecture = self._source.load(path)
        blocking = [i for i in validate(architecture) if i.severity is Severity.HIGH]
        if blocking:
            raise ArchitectureInvalid(blocking)
        return self._renderer.render(architecture)


class AssessArchitecture:
    def __init__(self, source: AssessmentSource):
        self._source = source

    def execute(self, rubric_path: str, answers_path: str) -> Assessment:
        rubric = self._source.load_rubric(rubric_path)
        answers = self._source.load_answers(answers_path)
        return assess(rubric, answers)
