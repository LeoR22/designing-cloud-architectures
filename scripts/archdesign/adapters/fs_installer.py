"""Filesystem adapter that installs the skill folder and edits AGENTS.md."""

from __future__ import annotations

import shutil
from pathlib import Path

from ..domain.errors import SpecError

# Runtime files only: tests, caches and generated output are not part of an installed skill.
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "tests", ".git", "*.zip", "*.bundle", "extracted", "architecture")


class FilesystemSkillInstaller:
    def install(self, source: str, destination: str, force: bool) -> str:
        src, dest = Path(source).resolve(), Path(destination).resolve()
        if src == dest:
            return "skipped (this is already the skill folder)"
        if src in dest.parents:
            raise SpecError(f"Refusing to install inside the skill folder itself: {dest}. Use --project-root elsewhere.")
        status = "installed"
        if dest.exists():
            if not force:
                return "skipped (already exists; use --force to replace)"
            if not (dest / "SKILL.md").is_file():
                raise SpecError(f"Refusing to replace {dest}: it has no SKILL.md, so it does not look like a skill folder.")
            shutil.rmtree(dest)
            status = "replaced"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dest, ignore=IGNORE)
        return status

    def register_agents_md(self, project_root: str, skill_name: str, skill_path: str) -> str:
        start, end = f"<!-- {skill_name}:start -->", f"<!-- {skill_name}:end -->"
        block = (
            f"{start}\n"
            "## Cloud architecture design\n"
            "For requests to design, diagram, document or review a cloud architecture, "
            f"follow `{skill_path}`.\n"
            f"{end}\n"
        )
        path = Path(project_root) / "AGENTS.md"
        if not path.exists():
            path.write_text(block, encoding="utf-8")
            return "created"
        text = path.read_text(encoding="utf-8")
        if start in text and end in text:
            head, rest = text.split(start, 1)
            tail = rest.split(end, 1)[1].lstrip("\n")
            path.write_text(head + block + tail, encoding="utf-8")
        else:
            path.write_text(text.rstrip("\n") + "\n\n" + block, encoding="utf-8")
        return "updated"
