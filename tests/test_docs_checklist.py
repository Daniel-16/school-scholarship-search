"""What the applicant has supplied, and what each application still needs.

The behaviour worth pinning is the expiry rule: a test report is checked
against the *deadline*, not against today, because a report that is valid now
and expired by the deadline is the failure this tool exists for and it is
invisible without the arithmetic.
"""
import json
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import docs_checklist  # noqa: E402


class Fixture(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)
        self.docs = self.tmp / "documents"
        for category in docs_checklist.CATEGORIES:
            (self.docs / category).mkdir(parents=True)
        (self.docs / "applications").mkdir(parents=True, exist_ok=True)

    def put(self, category, name, taken=None):
        path = self.docs / category / name
        path.write_text("x", encoding="utf-8")
        if taken:
            path.with_name(name + ".meta.json").write_text(
                json.dumps({"taken": taken}), encoding="utf-8"
            )
        return path

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(REPO / "tools" / "docs_checklist.py"),
             *map(str, args), "--documents", str(self.docs)],
            capture_output=True, text=True,
        )


class InventoryTests(Fixture):
    def test_an_empty_tree_reports_every_category_missing(self):
        result = self.run_cli("inventory", "--json")
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["missing_categories"]), len(docs_checklist.CATEGORIES))
        self.assertEqual(result.returncode, 3)

    def test_a_supplied_file_satisfies_its_category(self):
        self.put("transcripts", "bingham_transcript.pdf")
        payload = json.loads(self.run_cli("inventory", "--json").stdout)
        entry = next(c for c in payload["categories"] if c["category"] == "transcripts")
        self.assertTrue(entry["satisfied"])
        self.assertEqual(entry["count"], 1)

    # These are the repo's own placeholders. Counting them as supplied material
    # would report an empty workspace as fully stocked.
    def test_placeholders_and_sidecars_are_not_counted(self):
        (self.docs / "transcripts" / ".gitkeep").write_text("", encoding="utf-8")
        (self.docs / "transcripts" / "README.md").write_text("", encoding="utf-8")
        self.put("test_scores", "ielts.pdf", taken="2026-01-01")
        payload = json.loads(self.run_cli("inventory", "--json").stdout)
        by_name = {c["category"]: c for c in payload["categories"]}
        self.assertFalse(by_name["transcripts"]["satisfied"])
        self.assertEqual(by_name["test_scores"]["count"], 1)  # the .meta.json is not a document

    def test_every_category_declares_what_it_wants(self):
        for name, spec in docs_checklist.CATEGORIES.items():
            with self.subTest(category=name):
                self.assertTrue(spec["label"])
                self.assertGreater(len(spec["wants"]), 20)


class TemplateTests(unittest.TestCase):
    def test_every_template_is_postgraduate_and_well_formed(self):
        for name, items in docs_checklist.TEMPLATES.items():
            with self.subTest(template=name):
                self.assertTrue(items)
                self.assertNotIn("undergrad", name)
                for item_id, category, required, _ in items:
                    self.assertTrue(item_id)
                    self.assertIsInstance(required, bool)
                    if category is not None:
                        self.assertIn(category, docs_checklist.CATEGORIES)

    def test_the_destinations_that_matter_are_covered(self):
        for expected in ("uk-masters", "uk-phd", "us-masters", "us-phd",
                         "germany-masters", "eu-phd-vacancy", "scholarship-generic"):
            self.assertIn(expected, docs_checklist.TEMPLATES)

    def test_every_template_requires_a_transcript_or_a_cv(self):
        for name, items in docs_checklist.TEMPLATES.items():
            with self.subTest(template=name):
                required = {i for i, _, r, _ in items if r}
                self.assertTrue({"transcript", "cv"} & required, name)


class ScaffoldAndCheckTests(Fixture):
    KEY = "tu_delft_msc_robotics"

    def scaffold(self, template="eu-phd-vacancy", deadline="2027-01-15"):
        folder = self.docs / "applications" / self.KEY
        folder.mkdir(parents=True, exist_ok=True)
        spec = {
            "application": self.KEY, "template": template, "deadline": deadline,
            "items": [{"id": i, "category": c, "required": r, "note": n}
                      for i, c, r, n in docs_checklist.TEMPLATES[template]],
        }
        (folder / "requirements.json").write_text(json.dumps(spec), encoding="utf-8")
        return folder

    def check(self, today="2026-10-28"):
        self.scaffold() if not (self.docs / "applications" / self.KEY).exists() else None
        # cmd_check resolves the application folder from the module constant,
        # so point it at the fixture for the duration of the call.
        original = docs_checklist.APPLICATIONS
        docs_checklist.APPLICATIONS = self.docs / "applications"
        try:
            import argparse, io, contextlib
            args = argparse.Namespace(
                key=self.KEY, documents=self.docs, json=True,
                today=date.fromisoformat(today),
            )
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = docs_checklist.cmd_check(args)
            return code, json.loads(buffer.getvalue())
        finally:
            docs_checklist.APPLICATIONS = original

    def test_missing_required_items_block(self):
        self.scaffold()
        code, payload = self.check()
        self.assertEqual(code, 3)
        self.assertIn("transcript", payload["blocking"])

    def test_a_supplied_document_satisfies_its_item(self):
        self.scaffold()
        self.put("transcripts", "bingham.pdf")
        _, payload = self.check()
        self.assertNotIn("transcript", payload["blocking"])

    def test_workflow_produced_items_are_not_expected_in_documents(self):
        self.scaffold()
        _, payload = self.check()
        motivation = next(i for i in payload["items"] if i["item"] == "motivation_letter")
        self.assertEqual(motivation["status"], "produced_by_workflow")

    # The point of the whole module. A report taken 2025-01-01 is valid until
    # 2027-01-01: still valid on the day you look at it, already expired on
    # the day the application is read. Checking against today hides this
    # completely, which is why the check is against the deadline.
    def test_a_report_valid_today_but_expired_by_the_deadline_is_flagged(self):
        self.scaffold(deadline="2027-03-01")
        self.put("test_scores", "ielts.pdf", taken="2025-01-01")
        _, payload = self.check(today="2026-10-28")
        english = next(i for i in payload["items"] if i["item"] == "english_test")
        self.assertEqual(english["status"], "expired")

    def test_the_same_report_passes_against_an_earlier_deadline(self):
        self.scaffold(deadline="2026-12-01")
        self.put("test_scores", "ielts.pdf", taken="2025-01-01")
        _, payload = self.check(today="2026-10-28")
        english = next(i for i in payload["items"] if i["item"] == "english_test")
        self.assertEqual(english["status"], "ok")
        self.assertIn("2027-01-01", english["detail"])

    # Several reports: the newest one is what counts, not the oldest.
    def test_one_valid_report_covers_an_expired_sibling(self):
        self.scaffold(deadline="2027-01-15")
        self.put("test_scores", "old_ielts.pdf", taken="2023-05-10")
        self.put("test_scores", "new_ielts.pdf", taken="2026-05-10")
        _, payload = self.check(today="2026-10-28")
        english = next(i for i in payload["items"] if i["item"] == "english_test")
        self.assertEqual(english["status"], "ok")

    def test_every_report_expiring_before_the_deadline_is_an_expiry(self):
        self.scaffold(deadline="2027-01-15")
        self.put("test_scores", "old_ielts.pdf", taken="2023-05-10")
        _, payload = self.check(today="2026-10-28")
        english = next(i for i in payload["items"] if i["item"] == "english_test")
        self.assertEqual(english["status"], "expired")
        self.assertIn("2027-01-15", english["detail"])

    def test_a_report_without_a_sidecar_reports_unknown_validity(self):
        # Honest, and deliberately not the same as passing.
        self.scaffold()
        self.put("test_scores", "ielts.pdf")
        _, payload = self.check()
        english = next(i for i in payload["items"] if i["item"] == "english_test")
        self.assertEqual(english["status"], "unknown_validity")

    def test_a_missing_requirements_file_fails_cleanly(self):
        original = docs_checklist.APPLICATIONS
        docs_checklist.APPLICATIONS = self.docs / "applications"
        try:
            import argparse
            args = argparse.Namespace(key="nope", documents=self.docs, json=True,
                                      today=date(2026, 10, 28))
            self.assertEqual(docs_checklist.cmd_check(args), 1)
        finally:
            docs_checklist.APPLICATIONS = original


class CliScaffoldTests(unittest.TestCase):
    def test_an_unknown_template_is_rejected_and_lists_the_real_ones(self):
        result = subprocess.run(
            [sys.executable, str(REPO / "tools" / "docs_checklist.py"),
             "scaffold", "x", "--template", "mars-phd"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("uk-phd", result.stderr)

    def test_templates_lists_every_set(self):
        result = subprocess.run(
            [sys.executable, str(REPO / "tools" / "docs_checklist.py"), "templates"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        for name in docs_checklist.TEMPLATES:
            self.assertIn(name, result.stdout)


if __name__ == "__main__":
    unittest.main()
