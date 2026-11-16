"""JSON file adapters: implement ArchitectureSource and AssessmentSource."""

from __future__ import annotations

import json
import re

from ..domain.errors import SpecError
from ..domain.models import (
    Architecture,
    Component,
    Connection,
    Group,
    Provider,
    Question,
    Rubric,
)

# Ids become identifiers in Mermaid and SVG, so keep them simple.
ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _read_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise SpecError(f"File not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise SpecError(f"Invalid JSON in {path} (line {exc.lineno}, column {exc.colno}): {exc.msg}") from None
    if not isinstance(data, dict):
        raise SpecError(f"{path}: the top level must be a JSON object.")
    return data


def _require(obj: dict, key: str, where: str):
    if key not in obj:
        raise SpecError(f"{where}: missing required field '{key}'. Fields present: {sorted(obj)}.")
    return obj[key]


def _items(obj: dict, key: str, where: str) -> list[dict]:
    items = _require(obj, key, where)
    if not isinstance(items, list) or not all(isinstance(i, dict) for i in items):
        raise SpecError(f"{where}: '{key}' must be a list of objects.")
    return items


def _identifier(value: object, where: str) -> str:
    if not isinstance(value, str) or not ID_PATTERN.match(value):
        raise SpecError(f"{where}: id {value!r} must match {ID_PATTERN.pattern} (letters, digits, underscore).")
    return value


class JsonArchitectureSource:
    def load(self, path: str) -> Architecture:
        raw = _read_json(path)
        provider_raw = str(_require(raw, "provider", path)).lower()
        try:
            provider = Provider(provider_raw)
        except ValueError:
            raise SpecError(
                f"{path}: provider '{provider_raw}' is not valid. Use one of {[p.value for p in Provider]}."
            ) from None

        groups = tuple(
            Group(_identifier(_require(g, "id", f"{path} group"), f"{path} group"), str(_require(g, "label", f"{path} group")))
            for g in _items(raw, "groups", path)
        )
        components = []
        for c in _items(raw, "components", path):
            cid = _identifier(_require(c, "id", f"{path} component"), f"{path} component")
            where = f"{path} component '{cid}'"
            components.append(Component(
                cid,
                str(_require(c, "label", where)),
                str(_require(c, "service", where)),
                str(_require(c, "group", where)),
            ))
        connections = tuple(
            Connection(
                str(_require(e, "from", f"{path} connection")),
                str(_require(e, "to", f"{path} connection")),
                str(e.get("label", "")),
            )
            for e in _items(raw, "connections", path)
        )
        return Architecture(str(_require(raw, "name", path)), provider, groups, tuple(components), connections)


class JsonAssessmentSource:
    def load_rubric(self, path: str) -> Rubric:
        raw = _read_json(path)
        questions = []
        for q in _items(raw, "questions", path):
            qid = str(_require(q, "id", f"{path} question"))
            where = f"{path} question '{qid}'"
            questions.append(Question(
                qid,
                str(_require(q, "pillar", where)),
                str(_require(q, "text", where)),
                int(q.get("weight", 1)),
                bool(q.get("critical", False)),
            ))
        return Rubric(tuple(questions))

    def load_answers(self, path: str) -> dict[str, int]:
        raw = _require(_read_json(path), "answers", path)
        if not isinstance(raw, dict):
            raise SpecError(f"{path}: 'answers' must map question ids to 0, 1 or 2.")
        return {str(k): v for k, v in raw.items()}
