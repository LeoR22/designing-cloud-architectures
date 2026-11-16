"""Domain entities. Pure Python: no I/O and no third-party imports."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Provider(str, Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    MULTI = "multi"


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class Group:
    id: str
    label: str


@dataclass(frozen=True)
class Component:
    id: str
    label: str
    service: str  # "<prefix>.<name>", e.g. "aws.s3", "gcp.bigquery", "saas.crm"
    group: str

    @property
    def prefix(self) -> str:
        return self.service.split(".", 1)[0]


@dataclass(frozen=True)
class Connection:
    source: str
    target: str
    label: str = ""


@dataclass(frozen=True)
class Architecture:
    name: str
    provider: Provider
    groups: tuple[Group, ...]
    components: tuple[Component, ...]
    connections: tuple[Connection, ...]


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    severity: Severity


@dataclass(frozen=True)
class Question:
    id: str
    pillar: str
    text: str
    weight: int = 1
    critical: bool = False  # a "not implemented" answer becomes a high risk


@dataclass(frozen=True)
class Rubric:
    questions: tuple[Question, ...]


@dataclass(frozen=True)
class Assessment:
    score: float  # 0-100
    by_pillar: tuple[tuple[str, float], ...]
    high_risks: tuple[Question, ...]
    gaps: tuple[Question, ...]  # everything below "fully implemented"
