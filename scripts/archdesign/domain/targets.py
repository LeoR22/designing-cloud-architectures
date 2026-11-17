"""Where each IDE or agent looks for Agent Skills (SKILL.md folders). Pure data."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstallTarget:
    name: str
    project_dir: str  # relative to the project root
    user_dir: str  # relative to the user's home folder
    used_by: str


TARGETS = (
    InstallTarget("agents", ".agents/skills", ".agents/skills", "neutral folder read by Copilot, VS Code, Cursor, Codex, Gemini CLI and JetBrains Air"),
    InstallTarget("claude", ".claude/skills", ".claude/skills", "Claude Code (also read by Cursor and VS Code)"),
    InstallTarget("cursor", ".cursor/skills", ".cursor/skills", "Cursor"),
    InstallTarget("kiro", ".kiro/skills", ".kiro/skills", "Kiro"),
    InstallTarget("junie", ".junie/skills", ".junie/skills", "JetBrains Junie (IntelliJ IDEA and other JetBrains IDEs)"),
    InstallTarget("copilot", ".github/skills", ".copilot/skills", "GitHub Copilot in VS Code and Visual Studio"),
)

TARGETS_BY_NAME = {t.name: t for t in TARGETS}
