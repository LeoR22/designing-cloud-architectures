"""Writes extraction results to disk: <root>/<name>/text.md, media/NN-<name>, and <root>/manifest.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..domain.documents import ExtractionResult, SourceDocument


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._") or "file"


class FilesystemExtractionStore:
    def __init__(self, root: str):
        self._root = Path(root)

    def save(self, document: SourceDocument) -> ExtractionResult:
        base = _safe(Path(document.name).stem)
        folder, n = self._root / base, 2
        while folder.exists():
            folder = self._root / f"{base}_{n}"
            n += 1
        folder.mkdir(parents=True)
        (folder / "text.md").write_text(document.text, encoding="utf-8")

        saved = []
        if document.images:
            (folder / "media").mkdir()
        for index, image in enumerate(document.images, start=1):
            target = folder / "media" / f"{index:02d}-{_safe(image.name)}"
            target.write_bytes(image.data)
            saved.append(str(target))
        return ExtractionResult(
            document.name, document.kind, str(folder), len(document.text), tuple(saved), document.warnings
        )

    def write_manifest(self, results: list[ExtractionResult]) -> str:
        self._root.mkdir(parents=True, exist_ok=True)
        manifest = self._root / "manifest.json"
        payload = [
            {
                "name": r.name,
                "kind": r.kind.value,
                "directory": r.directory,
                "characters": r.characters,
                "images": list(r.images),
                "warnings": list(r.warnings),
            }
            for r in results
        ]
        manifest.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return str(manifest)
