"""Backward planning from a submission deadline.

The whole point of this tool is that the deadline is not the thing to act on.
These cases pin the two behaviours that make that true: the milestone offsets
are real durations rather than decoration, and an application with no deadline
produces no plan rather than a guessed one.
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

import deadline_board  # noqa: E402

HEADER = ("date,institution,program,level,kind,country,channel,status,contact_person,"
          "fit_score,funding_status,deadline,decision_date,notes,cv_file,statement_file,source")


def row(institution="TU Delft", program="MSc Robotics", status="drafting",
        deadline="2027-01-15", notes=""):
    return (f"2026-10-28,{institution},{program},masters,program,Netherlands,portal,"
            f"{status},,,,{deadline},,\"{notes}\",,,")


class PlanTests(unittest.TestCase):
    TODAY = date(2026, 10, 28)

    def plan(self, **kwargs):
        import csv, io
        text = HEADER + "\n" + row(**kwargs) + "\n"
        return deadline_board.plan_row(next(csv.DictReader(io.StringIO(text))), self.TODAY)

    def test_every_milestone_is_planned_and_ordered(self):
        entry = self.plan()
        ids = [m["id"] for m in entry["milestones"]]
        self.assertEqual(ids, [m[0] for m in sorted(deadline_board.MILESTONES, key=lambda m: -m[1])])
        dues = [m["due"] for m in entry["milestones"]]
        self.assertEqual(dues, sorted(dues))

    def test_submit_lands_on_the_deadline_itself(self):
        submit = [m for m in self.plan()["milestones"] if m["id"] == "submit"][0]
        self.assertEqual(submit["due"], "2027-01-15")

    def test_the_slow_artefacts_are_planned_weeks_out(self):
        # These offsets are the argument of the module, not decoration: a
        # Nigerian transcript takes 4-6 weeks and referees need notice.
        offsets = dict((name, days) for name, days, _ in deadline_board.MILESTONES)
        self.assertGreaterEqual(offsets["transcripts"], 42)
        self.assertGreaterEqual(offsets["referees"], 28)
        self.assertGreaterEqual(offsets["language_test"], 60)

    # A guessed date on a deadline board is worse than a visible hole.
    def test_no_deadline_produces_no_milestones(self):
        entry = self.plan(deadline="")
        self.assertIsNone(entry["deadline"])
        self.assertEqual(entry["milestones"], [])

    def test_an_unparseable_deadline_is_treated_as_absent(self):
        for bad in ("15/01/2027", "January 2027", "soon"):
            with self.subTest(bad=bad):
                self.assertEqual(self.plan(deadline=bad)["milestones"], [])

    def test_overdue_is_computed_against_today(self):
        entry = self.plan(deadline="2026-11-15")
        overdue = [m["id"] for m in entry["milestones"] if m["overdue"]]
        self.assertIn("language_test", overdue)
        self.assertIn("transcripts", overdue)


class OverrideTests(unittest.TestCase):
    def test_an_override_moves_a_milestone(self):
        self.assertEqual(deadline_board.overrides("lead:transcripts=60"), {"transcripts": 60})

    def test_zero_drops_a_milestone(self):
        import csv, io
        text = HEADER + "\n" + row(notes="lead:language_test=0 IELTS already in hand") + "\n"
        entry = deadline_board.plan_row(next(csv.DictReader(io.StringIO(text))), date(2026, 10, 28))
        self.assertNotIn("language_test", [m["id"] for m in entry["milestones"]])

    def test_submit_cannot_be_dropped(self):
        import csv, io
        text = HEADER + "\n" + row(notes="lead:submit=0") + "\n"
        entry = deadline_board.plan_row(next(csv.DictReader(io.StringIO(text))), date(2026, 10, 28))
        self.assertIn("submit", [m["id"] for m in entry["milestones"]])

    # The notes field is free text a human writes sentences in. A typo there
    # must not take down the board for every other application.
    def test_an_unknown_milestone_id_is_ignored(self):
        self.assertEqual(deadline_board.overrides("lead:nonsense=10 lead:referees=14"),
                         {"referees": 14})

    def test_prose_in_the_notes_field_is_harmless(self):
        self.assertEqual(deadline_board.overrides("Waiting on supervisor. Deadline is firm."), {})


class BuildTests(unittest.TestCase):
    TODAY = date(2026, 10, 28)

    def rows(self, *csv_rows):
        import csv, io
        return list(csv.DictReader(io.StringIO(HEADER + "\n" + "\n".join(csv_rows) + "\n")))

    def test_submitted_applications_leave_the_board(self):
        result = deadline_board.build(
            self.rows(row(status="submitted"), row(institution="KTH", status="drafting")),
            self.TODAY, None, None,
        )
        self.assertEqual(result["applications"], 1)
        self.assertEqual(result["skipped_inactive"], 1)

    def test_only_in_flight_statuses_are_planned(self):
        self.assertEqual(
            deadline_board.ACTIVE_STATUSES,
            {"researching", "drafting", "awaiting_documents", "awaiting_references"},
        )

    def test_milestones_merge_across_applications_in_date_order(self):
        result = deadline_board.build(
            self.rows(row(), row(institution="KTH", deadline="2026-12-01")),
            self.TODAY, None, None,
        )
        dues = [item["due"] for item in result["board"]]
        self.assertEqual(dues, sorted(dues))
        self.assertGreater(len({item["application"] for item in result["board"]}), 1)

    def test_no_deadline_rows_are_reported_rather_than_hidden(self):
        result = deadline_board.build(self.rows(row(deadline="")), self.TODAY, None, None)
        self.assertEqual(len(result["no_deadline"]), 1)
        self.assertEqual(result["board"], [])

    def test_horizon_limits_the_board(self):
        result = deadline_board.build(self.rows(row()), self.TODAY, 7, None)
        self.assertTrue(all(item["days_from_today"] <= 7 for item in result["board"]))

    def test_key_filters_by_application(self):
        result = deadline_board.build(
            self.rows(row(), row(institution="KTH")), self.TODAY, None, "KTH"
        )
        self.assertEqual(result["applications"], 1)


class IcsTests(unittest.TestCase):
    def test_the_export_is_well_formed_all_day_events(self):
        import csv, io
        rows = list(csv.DictReader(io.StringIO(HEADER + "\n" + row() + "\n")))
        result = deadline_board.build(rows, date(2026, 10, 28), None, None)
        ics = deadline_board.to_ics(result)
        self.assertTrue(ics.startswith("BEGIN:VCALENDAR"))
        self.assertIn("END:VCALENDAR", ics)
        self.assertEqual(ics.count("BEGIN:VEVENT"), len(result["board"]))
        self.assertIn("DTSTART;VALUE=DATE:", ics)
        # DTEND is exclusive in RFC 5545, so an all-day event ends the next day.
        self.assertIn("DTEND;VALUE=DATE:", ics)

    def test_special_characters_are_escaped(self):
        self.assertEqual(deadline_board._ics_escape("A, B; C"), r"A\, B\; C")

    def test_long_lines_are_folded_to_the_octet_limit(self):
        # RFC 5545 caps a content line at 75 octets. Unfolded lines are
        # tolerated by most clients and rejected by some.
        folded = deadline_board._ics_fold("SUMMARY:" + "x" * 200)
        for segment in folded.split("\r\n"):
            self.assertLessEqual(len(segment.encode("utf-8")), 75)
        self.assertTrue(all(s.startswith(" ") for s in folded.split("\r\n")[1:]))

    # The limit is in octets, and these summaries carry university names with
    # non-ASCII letters. A naive character-count fold splits one in half.
    def test_folding_never_splits_a_multibyte_character(self):
        folded = deadline_board._ics_fold("SUMMARY:" + "\u00fc" * 120)
        for segment in folded.split("\r\n"):
            self.assertLessEqual(len(segment.encode("utf-8")), 75)
        self.assertEqual(folded.replace("\r\n ", ""), "SUMMARY:" + "\u00fc" * 120)

    def test_a_short_line_is_untouched(self):
        self.assertEqual(deadline_board._ics_fold("VERSION:2.0"), "VERSION:2.0")

    def test_the_real_export_has_no_overlong_line(self):
        import csv, io
        rows = list(csv.DictReader(io.StringIO(
            HEADER + "\n" + row(institution="Technical University of Applied Sciences W\u00fcrzburg") + "\n"
        )))
        result = deadline_board.build(rows, date(2026, 10, 28), None, None)
        for line in deadline_board.to_ics(result).split("\r\n"):
            self.assertLessEqual(len(line.encode("utf-8")), 75, line)


class CliTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)
        self.tracker = self.tmp / "tracker.csv"

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(REPO / "tools" / "deadline_board.py"),
             "--tracker", str(self.tracker), *args],
            capture_output=True, text=True,
        )

    def test_exit_two_when_a_milestone_is_overdue(self):
        self.tracker.write_text(HEADER + "\n" + row(deadline="2026-11-15") + "\n", encoding="utf-8")
        result = self.run_cli("--today", "2026-10-28")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("overdue", result.stdout)

    def test_exit_zero_when_nothing_is_overdue(self):
        self.tracker.write_text(HEADER + "\n" + row(deadline="2027-06-01") + "\n", encoding="utf-8")
        self.assertEqual(self.run_cli("--today", "2026-10-28").returncode, 0)

    def test_json_output_parses(self):
        self.tracker.write_text(HEADER + "\n" + row() + "\n", encoding="utf-8")
        payload = json.loads(self.run_cli("--today", "2026-10-28", "--json").stdout)
        self.assertEqual(payload["applications"], 1)
        self.assertIn("board", payload)

    def test_a_missing_tracker_fails_cleanly(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("not found", result.stderr)

    def test_a_non_utf8_tracker_says_so(self):
        self.tracker.write_bytes(
            (HEADER + "\n" + row(institution="Universit\xe9 de Montr\xe9al") + "\n").encode("cp1252")
        )
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("UTF-8", result.stderr)


if __name__ == "__main__":
    unittest.main()
