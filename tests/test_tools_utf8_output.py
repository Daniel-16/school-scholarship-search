"""The Python tools must write UTF-8 whatever the host's default encoding is.

On Windows a piped stdout (which is how Claude Code runs every tool) defaults
to the ANSI code page, cp1252 on most Western installs. A tool that prints an
institution name, a programme title, a CV line or a file name outside that
code page then dies with UnicodeEncodeError before the workflow sees any
output - and university names are exactly where this bites: Universitat
Politecnica de Catalunya, Technische Universitat Munchen, Koc Universitesi,
Uniwersytet Jagiellonski, and every Chinese, Japanese and Korean institution.

Each case runs the real CLI in a child process with a legacy stdout forced via
PYTHONIOENCODING, so the Linux CI job reproduces what Windows users hit. The
child must exit cleanly and its bytes must decode as UTF-8.
"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"

# One institution name per script family that cp1252 cannot encode.
CYRILLIC = "Московский университет"
CJK = "清华大学"
POLISH = "Uniwersytet Łódzki"


def run_legacy_stdout(argv, cwd=None):
    """Run a tool the way a Western-locale Windows host pipes it."""
    env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
    return subprocess.run([sys.executable, *map(str, argv)], cwd=cwd, env=env, capture_output=True)


class ToolsWriteUtf8(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)

    def assert_clean_utf8(self, proc, expect_code, *needles, stream="stdout"):
        err = proc.stderr.decode("utf-8", "replace")
        self.assertNotIn("UnicodeEncodeError", err)
        self.assertEqual(proc.returncode, expect_code, err)
        text = getattr(proc, stream).decode("utf-8")
        for needle in needles:
            self.assertIn(needle, text)
        return text

    def write_state(self, seen):
        state = self.tmp / "seen_programs.json"
        state.write_text(json.dumps({"version": 1, "seen": seen}, ensure_ascii=False), encoding="utf-8")
        return state

    @staticmethod
    def entry(provider, award):
        return {
            "award": award, "provider": provider, "url": "https://example.edu/programmes/123456",
            "kind": "program", "level": "masters", "country": "Example",
            "portal": "example", "status": "new", "first_seen": "2026-09-20",
        }

    def test_rank_candidates_lists_non_latin_programmes(self):
        state = self.write_state({
            "a": self.entry(CYRILLIC, "Прикладная математика"),
            "b": self.entry(CJK, "计算机科学硕士"),
        })
        proc = run_legacy_stdout(
            [TOOLS / "shortlist_state.py", "candidates", "--state", state, "--today", "2026-09-21"]
        )
        out = json.loads(self.assert_clean_utf8(proc, 0, CYRILLIC, CJK))
        self.assertEqual(out["eligible"], 2)

    def test_rank_apply_prints_the_ranking_for_non_latin_programmes(self):
        state = self.write_state({"a": self.entry(CJK, "计算机科学硕士")})
        results = self.tmp / "results.json"
        results.write_text(json.dumps([{
            "key": "a", "status": "scored",
            "scores": {"funding": 80, "academic_fit": 80, "admission_odds": 80,
                       "career_value": 80, "logistics": 80},
        }]), encoding="utf-8")
        proc = run_legacy_stdout([
            TOOLS / "shortlist_state.py", "apply", "--results", results,
            "--state", state, "--today", "2026-09-21",
        ])
        out = json.loads(self.assert_clean_utf8(proc, 0, CJK))
        self.assertEqual([row["key"] for row in out["ranked"]], ["a"])

    def test_program_key_audit_reports_non_latin_entries(self):
        state = self.write_state({f"{CYRILLIC}_математика": self.entry(CYRILLIC, "математика")})
        proc = run_legacy_stdout([TOOLS / "program_key.py", "--audit", state])
        self.assertNotIn(b"UnicodeEncodeError", proc.stderr)
        self.assertIn(CYRILLIC, proc.stdout.decode("utf-8"))

    def test_deadline_board_prints_a_non_latin_institution(self):
        tracker = self.tmp / "tracker.csv"
        tracker.write_text(
            "date,institution,program,level,kind,country,channel,status,contact_person,"
            "fit_score,funding_status,deadline,decision_date,notes,cv_file,statement_file,source\n"
            f"2026-09-20,{POLISH},Informatyka,masters,program,Poland,portal,drafting,,,,2027-01-15,,,,,\n",
            encoding="utf-8",
        )
        proc = run_legacy_stdout(
            [TOOLS / "deadline_board.py", "--tracker", tracker, "--today", "2026-09-21"]
        )
        # Exit 2 is "something is overdue", which is a result, not a crash.
        self.assertIn(proc.returncode, (0, 2), proc.stderr.decode("utf-8", "replace"))
        self.assertNotIn(b"UnicodeEncodeError", proc.stderr)
        self.assertIn(POLISH, proc.stdout.decode("utf-8"))

    def test_docs_checklist_prints_a_non_latin_file_name(self):
        docs = self.tmp / "documents"
        (docs / "transcripts").mkdir(parents=True)
        (docs / "transcripts" / f"{POLISH}.pdf").write_text("x", encoding="utf-8")
        proc = run_legacy_stdout([TOOLS / "docs_checklist.py", "inventory", "--documents", docs])
        self.assertNotIn(b"UnicodeEncodeError", proc.stderr)
        self.assertIn(POLISH, proc.stdout.decode("utf-8"))

    def test_funding_model_prints_a_non_latin_application_name(self):
        plan = self.tmp / "plan.json"
        plan.write_text(json.dumps({
            "application": POLISH, "currency": "USD", "duration_months": 24,
            "costs": {"tuition_per_year": 0, "living_per_month": 800},
            "funding": {"stipend_per_month": 900},
            "proof_of_funds": {"required": 0},
        }, ensure_ascii=False), encoding="utf-8")
        proc = run_legacy_stdout([TOOLS / "funding_model.py", "--in", plan,
                                  "--rates", self.tmp / "no-rates.json"])
        self.assertNotIn(b"UnicodeEncodeError", proc.stderr)
        self.assertIn(POLISH, proc.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
