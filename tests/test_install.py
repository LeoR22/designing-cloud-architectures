"""Run from the skill root: PYTHONPATH=scripts python3 -m unittest discover -s tests"""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from archdesign.adapters.fs_installer import FilesystemSkillInstaller
from archdesign.application.use_cases import InstallSkill
from archdesign.domain.errors import SpecError
from archdesign.domain.targets import TARGETS

ROOT = Path(__file__).resolve().parent.parent
NAME = "designing-cloud-architectures"


class TmpDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.project = self.tmp / "project"
        self.home = self.tmp / "home"
        self.project.mkdir()
        self.home.mkdir()

    def install(self, targets, scope="project", **kwargs):
        return InstallSkill(FilesystemSkillInstaller(), str(self.home)).execute(
            str(ROOT), NAME, targets, scope, str(self.project), **kwargs
        )


class InstallTest(TmpDirTest):
    def test_every_target_gets_a_working_copy_without_tests(self):
        outcomes = self.install(["all"])
        self.assertEqual(len(outcomes), len(TARGETS))
        for target in TARGETS:
            folder = self.project / target.project_dir / NAME
            self.assertTrue((folder / "SKILL.md").is_file(), target.name)
            self.assertTrue((folder / "scripts" / "run.py").is_file(), target.name)
            self.assertFalse((folder / "tests").exists(), target.name)
            self.assertFalse(list(folder.rglob("__pycache__")), target.name)

    def test_user_scope_uses_the_home_folder(self):
        self.install(["kiro", "copilot"], scope="user")
        self.assertTrue((self.home / ".kiro" / "skills" / NAME / "SKILL.md").is_file())
        self.assertTrue((self.home / ".copilot" / "skills" / NAME / "SKILL.md").is_file())

    def test_existing_copy_is_kept_unless_forced(self):
        self.install(["agents"])
        marker = self.project / ".agents" / "skills" / NAME / "marker.txt"
        marker.write_text("mine")
        self.assertIn("skipped", self.install(["agents"])[0].status)
        self.assertTrue(marker.exists())
        self.assertEqual(self.install(["agents"], force=True)[0].status, "replaced")
        self.assertFalse(marker.exists())

    def test_force_never_deletes_a_folder_that_is_not_a_skill(self):
        victim = self.project / ".agents" / "skills" / NAME
        victim.mkdir(parents=True)
        (victim / "important.txt").write_text("keep me")
        with self.assertRaises(SpecError):
            self.install(["agents"], force=True)
        self.assertTrue((victim / "important.txt").exists())

    def test_refuses_to_install_inside_the_skill_folder(self):
        with self.assertRaises(SpecError):
            InstallSkill(FilesystemSkillInstaller(), str(self.home)).execute(
                str(ROOT), NAME, ["agents"], "project", str(ROOT)
            )

    def test_bad_target_and_scope_are_actionable(self):
        with self.assertRaises(SpecError) as ctx:
            self.install(["vim"])
        self.assertIn("kiro", str(ctx.exception))
        with self.assertRaises(SpecError):
            self.install(["agents"], scope="user", agents_md=True)

    def test_agents_md_block_is_idempotent_and_keeps_user_text(self):
        agents = self.project / "AGENTS.md"
        agents.write_text("# My project\n\nUse tabs.\n")
        self.install(["agents"], agents_md=True)
        self.install(["agents"], agents_md=True)
        text = agents.read_text()
        self.assertEqual(text.count(f"<!-- {NAME}:start -->"), 1)
        self.assertIn("Use tabs.", text)
        self.assertIn(f".agents/skills/{NAME}/SKILL.md", text)


class PortabilityTest(TmpDirTest):
    def test_installed_copy_runs_from_any_working_folder(self):
        self.install(["agents"])
        installed = self.project / ".agents" / "skills" / NAME
        answers = ROOT / "examples" / "answers-round2.json"
        other_cwd = self.tmp / "elsewhere"
        other_cwd.mkdir()
        done = subprocess.run(
            [sys.executable, "-I", str(installed / "scripts" / "run.py"), "assess", "--answers", str(answers)],
            cwd=other_cwd, capture_output=True, text=True,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("Overall score", done.stdout)


class SkillLintTest(unittest.TestCase):
    """Constraints of the Agent Skills format that every IDE relies on."""

    def setUp(self):
        self.text = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_frontmatter(self):
        match = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", self.text)
        self.assertIsNotNone(match)
        name, description = match.groups()
        self.assertEqual(name, NAME)
        self.assertRegex(name, r"^[a-z0-9]+(-[a-z0-9]+)*$")
        self.assertLessEqual(len(name), 64)
        self.assertLessEqual(len(description), 1024)

    def test_size_and_links(self):
        self.assertLessEqual(len(self.text.splitlines()), 500)
        for link in re.findall(r"\]\(([^)#]+)\)", self.text):
            self.assertTrue((ROOT / link).exists(), link)


if __name__ == "__main__":
    unittest.main()
