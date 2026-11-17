"""Use cases. Each one orchestrates domain logic through ports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ..domain.assessment import assess
from ..domain.documents import ExtractionResult
from ..domain.errors import DocumentError, SpecError
from ..domain.models import Assessment, Issue, Severity
from ..domain.rules import validate
from ..domain.targets import TARGETS, TARGETS_BY_NAME
from .ports import ArchitectureSource, AssessmentSource, DiagramRenderer, DocumentReader, ExtractionStore, SkillInstaller


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


class ExtractDocuments:
    """Turns user-supplied files (text, Word, PDF, images) into text and images for interpretation."""

    def __init__(self, readers: Sequence[DocumentReader], store: ExtractionStore):
        self._readers = tuple(readers)
        self._store = store

    @property
    def supported_suffixes(self) -> list[str]:
        return sorted({s for r in self._readers for s in r.suffixes})

    def execute(self, paths: Sequence[str]) -> list[ExtractionResult]:
        results = []
        for path in paths:
            suffix = Path(path).suffix.lower()
            reader = next((r for r in self._readers if suffix in r.suffixes), None)
            if reader is None:
                hint = " Save the file as .docx first." if suffix == ".doc" else ""
                raise DocumentError(
                    f"Unsupported file type '{suffix}' for {Path(path).name}. "
                    f"Supported: {self.supported_suffixes}.{hint}"
                )
            results.append(self._store.save(reader.read(path)))
        self._store.write_manifest(results)
        return results


@dataclass(frozen=True)
class InstallOutcome:
    target: str
    destination: str
    status: str


class InstallSkill:
    """Copies this skill into the folders that IDEs and agents read skills from."""

    def __init__(self, installer: SkillInstaller, home: str):
        self._installer = installer
        self._home = Path(home)

    def execute(
        self,
        source: str,
        skill_name: str,
        target_names: Sequence[str],
        scope: str,
        project_root: str,
        force: bool = False,
        agents_md: bool = False,
    ) -> list[InstallOutcome]:
        if scope not in ("project", "user"):
            raise SpecError(f"Scope '{scope}' is not valid. Use 'project' or 'user'.")
        if agents_md and scope != "project":
            raise SpecError("--agents-md only applies to project scope (AGENTS.md lives in the project root).")
        names = [t.name for t in TARGETS] if "all" in target_names else list(dict.fromkeys(target_names))
        unknown = [n for n in names if n not in TARGETS_BY_NAME]
        if unknown:
            raise SpecError(f"Unknown target(s) {unknown}. Valid: {[t.name for t in TARGETS]} or 'all'.")

        root = Path(project_root).resolve()
        outcomes = []
        for name in names:
            target = TARGETS_BY_NAME[name]
            base = root / target.project_dir if scope == "project" else self._home / target.user_dir
            destination = base / skill_name
            outcomes.append(InstallOutcome(name, str(destination), self._installer.install(source, str(destination), force)))
        if agents_md:
            first = TARGETS_BY_NAME[names[0]]
            relative = f"{first.project_dir}/{skill_name}/SKILL.md"
            outcomes.append(InstallOutcome("AGENTS.md", str(root / "AGENTS.md"), self._installer.register_agents_md(str(root), skill_name, relative)))
        return outcomes
