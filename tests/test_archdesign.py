"""Run from the skill root: PYTHONPATH=scripts python3 -m unittest discover -s tests"""

import ast
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from archdesign.adapters.json_files import JsonArchitectureSource, JsonAssessmentSource
from archdesign.adapters.mermaid_renderer import MermaidRenderer
from archdesign.adapters.svg_renderer import SvgRenderer
from archdesign.application.use_cases import ArchitectureInvalid, AssessArchitecture, RenderDiagram
from archdesign.domain.assessment import assess
from archdesign.domain.errors import SpecError
from archdesign.domain.models import (
    Architecture, Component, Connection, Group, Provider, Question, Rubric, Severity,
)
from archdesign.domain.resilience import quorum_size, tolerated_failures
from archdesign.domain.rules import validate

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "scripts" / "archdesign"
EXAMPLE = str(ROOT / "examples" / "debt-collection-lakehouse.json")
RUBRIC = str(ROOT / "reference" / "rubric.json")


def arch(components, connections, provider=Provider.AWS, groups=("g",)):
    return Architecture(
        "t", provider, tuple(Group(g, g) for g in groups),
        tuple(Component(*c) for c in components), tuple(Connection(*e) for e in connections),
    )


class RulesTest(unittest.TestCase):
    def codes(self, a):
        return {i.code for i in validate(a)}

    def test_clean_architecture_has_no_issues(self):
        a = arch([("a", "A", "aws.s3", "g"), ("b", "B", "aws.lambda", "g")], [("a", "b", "")])
        self.assertEqual(validate(a), [])

    def test_dangling_connection_is_high(self):
        a = arch([("a", "A", "aws.s3", "g")], [("a", "zzz", "")])
        self.assertIn("ARCH003", self.codes(a))
        self.assertEqual(validate(a)[0].severity, Severity.HIGH)

    def test_foreign_provider_flagged_unless_multi(self):
        comps = [("a", "A", "aws.s3", "g"), ("b", "B", "gcp.bigquery", "g")]
        self.assertIn("ARCH006", self.codes(arch(comps, [("a", "b", "")])))
        self.assertNotIn("ARCH006", self.codes(arch(comps, [("a", "b", "")], Provider.MULTI)))

    def test_duplicate_orphan_and_long_label(self):
        a = arch([("a", "x" * 40, "aws.s3", "g"), ("a", "A", "aws.s3", "g"), ("c", "C", "aws.s3", "g")], [("a", "a", "")])
        self.assertTrue({"ARCH001", "ARCH004", "ARCH005", "ARCH007"} <= self.codes(a))


class ResilienceTest(unittest.TestCase):
    def test_quorum_math(self):
        self.assertEqual((quorum_size(5), tolerated_failures(5)), (3, 2))
        self.assertEqual((quorum_size(3), tolerated_failures(3)), (2, 1))
        self.assertEqual(tolerated_failures(4), tolerated_failures(3))

    def test_five_node_cluster_is_clean(self):
        loaded = JsonArchitectureSource().load(str(ROOT / "examples" / "quorum-cluster.json"))
        self.assertEqual(validate(loaded), [])

    def test_stateful_single_replica_is_flagged_unless_self_healing(self):
        c = Component("db", "DB", "aws.rds", "g", stateful=True)
        self.assertIn("ARCH010", {i.code for i in validate(Architecture("t", Provider.AWS, (Group("g", "g"),), (c,), ()))})
        healed = Component("db", "DB", "aws.rds", "g", stateful=True, self_healing=True)
        found = {i.code for i in validate(Architecture("t", Provider.AWS, (Group("g", "g"),), (healed,), ()))}
        self.assertNotIn("ARCH010", found)

    def test_quorum_needs_three_odd_replicas(self):
        def codes(replicas):
            c = Component("k", "K", "aws.ec2", "g", stateful=True, replicas=replicas, quorum=True)
            return {i.code for i in validate(Architecture("t", Provider.AWS, (Group("g", "g"),), (c,), ()))}
        self.assertIn("ARCH012", codes(2))
        self.assertIn("ARCH011", codes(4))
        self.assertFalse(codes(5) & {"ARCH010", "ARCH011", "ARCH012"})

    def test_loader_rejects_bad_replicas(self):
        import json, tempfile
        spec = {"name": "x", "provider": "aws", "groups": [{"id": "g", "label": "g"}],
                "components": [{"id": "a", "label": "A", "service": "aws.s3", "group": "g", "replicas": 0}],
                "connections": []}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(spec, fh)
        with self.assertRaises(SpecError) as ctx:
            JsonArchitectureSource().load(fh.name)
        self.assertIn("replicas", str(ctx.exception))


class AssessmentTest(unittest.TestCase):
    rubric = Rubric((Question("q1", "p", "t", 3, True), Question("q2", "p", "t", 1)))

    def test_score_and_high_risk(self):
        result = assess(self.rubric, {"q1": 0, "q2": 2})
        self.assertEqual(result.score, 25.0)
        self.assertEqual([q.id for q in result.high_risks], ["q1"])

    def test_actionable_errors(self):
        with self.assertRaises(SpecError) as ctx:
            assess(self.rubric, {"q1": 2, "zzz": 1, "q2": 5})
        message = str(ctx.exception)
        self.assertIn("zzz", message)
        self.assertIn("q2", message)

    def test_example_rounds_improve_and_clear_high_risks(self):
        use_case = AssessArchitecture(JsonAssessmentSource())
        first = use_case.execute(RUBRIC, str(ROOT / "examples" / "answers-round1.json"))
        second = use_case.execute(RUBRIC, str(ROOT / "examples" / "answers-round2.json"))
        self.assertGreater(len(first.high_risks), 0)
        self.assertEqual(len(second.high_risks), 0)
        self.assertGreater(second.score, first.score)


class RenderTest(unittest.TestCase):
    def test_example_validates_without_high_issues(self):
        loaded = JsonArchitectureSource().load(EXAMPLE)
        self.assertFalse([i for i in validate(loaded) if i.severity is Severity.HIGH])

    def test_svg_is_well_formed_xml(self):
        text = RenderDiagram(JsonArchitectureSource(), SvgRenderer()).execute(EXAMPLE)
        root = ET.fromstring(text)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("Propensity model", text)

    def test_crm_stays_on_the_left_despite_the_feedback_loop(self):
        from archdesign.adapters.svg_renderer import _ranks
        ranks = _ranks(JsonArchitectureSource().load(EXAMPLE))
        self.assertEqual(ranks["crm"], 0)
        self.assertLess(ranks["landing"], ranks["bronze"])
        self.assertLess(ranks["model"], ranks["writer"])

    def test_mermaid_groups_and_edges(self):
        text = RenderDiagram(JsonArchitectureSource(), MermaidRenderer()).execute(EXAMPLE)
        self.assertTrue(text.startswith("flowchart LR"))
        self.assertIn('subgraph g_lakehouse["Lakehouse"]', text)
        self.assertIn("n_landing --> n_bronze".replace("-->", "-->|auto loader|"), text)

    def test_blocking_issues_prevent_rendering(self):
        class BadSource:
            def load(self, path):
                return arch([("a", "A", "aws.s3", "missing")], [])

        with self.assertRaises(ArchitectureInvalid):
            RenderDiagram(BadSource(), SvgRenderer()).execute("ignored")

    def test_use_case_works_with_fakes_only(self):
        class FakeSource:
            def load(self, path):
                return arch([("a", "A", "aws.s3", "g"), ("b", "B", "aws.lambda", "g")], [("a", "b", "")])

        class FakeRenderer:
            extension = "txt"

            def render(self, architecture):
                return f"{len(architecture.components)} components"

        self.assertEqual(RenderDiagram(FakeSource(), FakeRenderer()).execute("x"), "2 components")


class LoaderTest(unittest.TestCase):
    def test_missing_file_and_bad_provider_messages(self):
        with self.assertRaises(SpecError) as ctx:
            JsonArchitectureSource().load("/nope.json")
        self.assertIn("File not found", str(ctx.exception))


class DependencyRuleTest(unittest.TestCase):
    """domain imports nothing from outer layers; application never imports adapters or cli."""

    def imports(self, folder):
        found = set()
        for path in (PKG / folder).glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.ImportFrom):
                    found.add(("." * node.level) + (node.module or ""))
                elif isinstance(node, ast.Import):
                    found.update(a.name for a in node.names)
        return found

    def test_domain_is_pure(self):
        for name in self.imports("domain"):
            top = name.lstrip(".").split(".")[0]
            self.assertTrue(
                name.startswith(".") and not name.startswith("..") or top in sys.stdlib_module_names or top == "__future__",
                f"domain imports {name}",
            )

    def test_application_does_not_know_adapters(self):
        for name in self.imports("application"):
            self.assertNotIn("adapters", name)
            self.assertNotIn("cli", name.split("."))


if __name__ == "__main__":
    unittest.main()
