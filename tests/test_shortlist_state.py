"""Candidate selection, scoring write-back, and the lead-time sweep.

Three things here are admissions-shaped rather than inherited from a job
pipeline, and each has its own section: funding carries the heaviest weight,
three independent gates can veto, and a deadline that is still open can be
too close to assemble an application for.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import shortlist_state  # noqa: E402

TOOL = REPO / "tools" / "shortlist_state.py"
FULL = {"funding": 80, "academic_fit": 80, "admission_odds": 80,
        "career_value": 80, "logistics": 80}


class RubricTests(unittest.TestCase):
    def test_the_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(shortlist_state.WEIGHTS.values()), 1.0, places=9)

    def test_funding_is_the_heaviest_single_weight(self):
        heaviest = max(shortlist_state.WEIGHTS, key=shortlist_state.WEIGHTS.get)
        self.assertEqual(heaviest, "funding")
        self.assertGreater(
            shortlist_state.WEIGHTS["funding"], shortlist_state.WEIGHTS["academic_fit"]
        )

    def test_a_uniform_score_is_that_score(self):
        self.assertEqual(shortlist_state.overall_score(FULL), 80)

    # A scoring agent that omits `funding` because the page was silent would
    # otherwise have its silence recorded as "this funds nothing", which is
    # the single most consequential thing the rubric says.
    def test_a_missing_dimension_is_an_error_not_a_zero(self):
        for dimension in shortlist_state.WEIGHTS:
            with self.subTest(dimension=dimension):
                partial = {k: v for k, v in FULL.items() if k != dimension}
                with self.assertRaises(ValueError) as caught:
                    shortlist_state.overall_score(partial)
                self.assertIn(dimension, str(caught.exception))

    def test_out_of_range_and_non_numeric_scores_are_rejected(self):
        for bad in ({**FULL, "funding": 120}, {**FULL, "funding": -1},
                    {**FULL, "funding": "high"}, {**FULL, "funding": True}):
            with self.subTest(bad=bad["funding"]):
                with self.assertRaises(ValueError):
                    shortlist_state.overall_score(bad)

    def test_bands_are_ordered_and_cover_zero(self):
        self.assertEqual(shortlist_state.band(100), "Strong Match")
        self.assertEqual(shortlist_state.band(75), "Strong Match")
        self.assertEqual(shortlist_state.band(60), "Good Match")
        self.assertEqual(shortlist_state.band(0), "Poor Match")


class LeadTimeTests(unittest.TestCase):
    def test_the_lead_time_floor_is_set_by_the_slowest_artefact(self):
        # Transcripts take 4-6 weeks. A floor below that would mark a deadline
        # reachable when the paperwork cannot arrive.
        self.assertGreaterEqual(shortlist_state.LEAD_TIME_DAYS, 42)
        self.assertGreater(shortlist_state.LEAD_TIME_DAYS, shortlist_state.URGENT_DAYS)


class StateFixture(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)

    def entry(self, **overrides):
        base = {
            "award": "MSc Robotics", "provider": "TU Delft", "kind": "program",
            "level": "masters", "country": "Netherlands", "field": "Robotics",
            "url": "https://example.edu/p/1", "portal": "manual",
            "first_seen": "2026-10-01", "deadline": "2027-06-01", "status": "new",
        }
        base.update(overrides)
        return base

    def write_state(self, seen):
        path = self.tmp / "seen_programs.json"
        path.write_text(json.dumps({"seen": seen}, ensure_ascii=False), encoding="utf-8")
        return path

    # Deliberately not named `run`: unittest.TestCase.run() is what the test
    # runner calls to execute a test, so a helper of that name silently
    # replaced it and every subclass's tests stopped running while the suite
    # reported OK.
    def run_tool(self, *args):
        return subprocess.run(
            [sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True
        )

    def read_state(self, path):
        return json.loads(path.read_text(encoding="utf-8"))["seen"]


class CandidateTests(StateFixture):
    def test_only_new_and_unreachable_are_selected(self):
        state = self.write_state({
            "a": self.entry(status="new"),
            "b": self.entry(status="unreachable"),
            "c": self.entry(status="ranked"),
            "d": self.entry(status="skipped"),
        })
        result = self.run_tool("candidates", "--state", state, "--today", "2026-10-28")
        payload = json.loads(result.stdout)
        self.assertEqual({row["key"] for row in payload["selected"]}, {"a", "b"})

    def test_all_includes_every_non_skipped_status(self):
        state = self.write_state({"a": self.entry(status="ranked"), "b": self.entry(status="skipped")})
        payload = json.loads(
            self.run_tool("candidates", "--state", state, "--all", "--today", "2026-10-28").stdout
        )
        self.assertEqual([row["key"] for row in payload["selected"]], ["a"])

    def test_the_projection_carries_what_a_scorer_needs(self):
        state = self.write_state({"a": self.entry()})
        payload = json.loads(self.run_tool("candidates", "--state", state, "--today", "2026-10-28").stdout)
        row = payload["selected"][0]
        for field in ("key", "award", "provider", "kind", "level", "country", "url", "deadline"):
            self.assertIn(field, row)

    def test_focus_matches_the_field_and_country_too(self):
        state = self.write_state({
            "a": self.entry(field="Robotics"), "b": self.entry(country="Germany", field="Law"),
        })
        payload = json.loads(
            self.run_tool("candidates", "--state", state, "--focus", "germany", "--today", "2026-10-28").stdout
        )
        self.assertEqual([row["key"] for row in payload["selected"]], ["b"])

    def test_tracker_rows_are_excluded(self):
        tracker = self.tmp / "tracker.csv"
        tracker.write_text(
            "date,institution,program,level,kind,country,channel,status,contact_person,"
            "fit_score,funding_status,deadline,decision_date,notes,cv_file,statement_file,source\n"
            "2026-10-01,TU Delft,MSc Robotics,masters,program,Netherlands,portal,submitted,,,,,,,,,\n",
            encoding="utf-8",
        )
        state = self.write_state({"a": self.entry()})
        payload = json.loads(self.run_tool(
            "candidates", "--state", state, "--tracker", tracker, "--today", "2026-10-28"
        ).stdout)
        self.assertEqual(payload["selected"], [])
        self.assertEqual(payload["excluded_by_tracker"], 1)


class GateTests(StateFixture):
    def apply(self, result_obj, entry=None, today="2026-10-28"):
        state = self.write_state({"a": entry or self.entry()})
        results = self.tmp / "results.json"
        results.write_text(json.dumps([{"key": "a", "status": "scored", **result_obj}]),
                           encoding="utf-8")
        proc = self.run_tool("apply", "--state", state, "--results", results, "--today", today)
        return json.loads(proc.stdout), self.read_state(state)

    def test_all_three_gates_default_to_pass(self):
        payload, stored = self.apply({"scores": FULL})
        self.assertEqual(len(payload["ranked"]), 1)
        for gate in ("eligibility_verdict", "language_gate", "funding_gate"):
            self.assertEqual(stored["a"][gate], "PASS")

    def test_each_gate_alone_vetoes(self):
        for gate in ("eligibility_verdict", "language_gate", "funding_gate"):
            with self.subTest(gate=gate):
                payload, _ = self.apply({"scores": FULL, gate: "FAIL"})
                self.assertEqual(len(payload["vetoed"]), 1)
                self.assertEqual(payload["ranked"], [])

    # FLAG means "could not confirm", which is a question for the user, not a
    # decision the tool gets to make on their behalf.
    def test_a_flag_does_not_veto(self):
        payload, _ = self.apply({"scores": FULL, "funding_gate": "FLAG",
                                 "funding_note": "tuition unconfirmed"})
        self.assertEqual(len(payload["ranked"]), 1)
        self.assertEqual(payload["ranked"][0]["funding_note"], "tuition unconfirmed")

    def test_a_note_is_dropped_once_its_gate_passes(self):
        state = self.write_state({"a": self.entry(
            status="new", language_gate="FAIL", language_note="needs IELTS 7.0"
        )})
        results = self.tmp / "results.json"
        results.write_text(json.dumps([{"key": "a", "status": "scored", "scores": FULL}]),
                           encoding="utf-8")
        self.run_tool("apply", "--state", state, "--results", results, "--today", "2026-10-28")
        self.assertNotIn("language_note", self.read_state(state)["a"])


class ApplyTests(StateFixture):
    def apply(self, results_list, seen, today="2026-10-28", extra=()):
        state = self.write_state(seen)
        results = self.tmp / "results.json"
        results.write_text(json.dumps(results_list), encoding="utf-8")
        proc = self.run_tool("apply", "--state", state, "--results", results, "--today", today, *extra)
        return proc, json.loads(proc.stdout or "{}"), self.read_state(state)

    def test_a_passed_deadline_expires_rather_than_ranks(self):
        _, payload, stored = self.apply(
            [{"key": "a", "status": "scored", "scores": FULL}],
            {"a": self.entry(deadline="2026-01-01")},
        )
        self.assertEqual(payload["ranked"], [])
        self.assertEqual(len(payload["expired"]), 1)
        self.assertEqual(stored["a"]["status"], "expired")

    # Absence is not a correction: a fetch that degraded to a listing page
    # returns no deadline, and blanking a stored one makes the entry immortal.
    def test_a_missing_deadline_in_the_result_does_not_erase_the_stored_one(self):
        _, _, stored = self.apply(
            [{"key": "a", "status": "scored", "scores": FULL, "deadline": None}],
            {"a": self.entry(deadline="2027-06-01")},
        )
        self.assertEqual(stored["a"]["deadline"], "2027-06-01")

    def test_short_lead_time_is_flagged_on_a_freshly_scored_row(self):
        # A scored entry is excluded from the sweep by design, so without this
        # the lead-time problem would never be reported for it at all.
        _, payload, _ = self.apply(
            [{"key": "a", "status": "scored", "scores": FULL}],
            {"a": self.entry(deadline="2026-11-20")},
        )
        self.assertTrue(payload["ranked"][0]["short_lead_time"])

    def test_a_comfortable_deadline_is_not_flagged(self):
        _, payload, _ = self.apply(
            [{"key": "a", "status": "scored", "scores": FULL}],
            {"a": self.entry(deadline="2027-06-01")},
        )
        self.assertFalse(payload["ranked"][0]["short_lead_time"])

    def test_unreachable_is_retried_before_it_gives_up(self):
        proc, payload, stored = self.apply(
            [{"key": "a", "status": "unreachable", "fetch_error": "timeout"}],
            {"a": self.entry()},
        )
        self.assertEqual(stored["a"]["status"], "unreachable")
        self.assertEqual(stored["a"]["fetch_attempts"], 1)
        self.assertEqual(len(payload["unreachable"]), 1)

    def test_an_unknown_status_is_an_error_not_a_silent_skip(self):
        proc, payload, _ = self.apply(
            [{"key": "a", "status": "pending", "scores": FULL}], {"a": self.entry()}
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("pending", payload["errors"][0]["error"])

    def test_the_agent_status_vocabulary_is_fixed(self):
        self.assertEqual(shortlist_state.AGENT_STATUSES, ("scored", "expired", "unreachable"))

    def test_the_guard_verdict_is_normalised(self):
        _, _, stored = self.apply(
            [{"key": "a", "status": "scored", "scores": FULL,
              "guard": "listing_guard: clean (1 hidden block removed, none instruction-like)"}],
            {"a": self.entry()},
        )
        self.assertEqual(stored["a"]["guard"], "clean")

    def test_a_fraud_verdict_is_kept_verbatim_minus_the_prefix(self):
        _, _, stored = self.apply(
            [{"key": "a", "status": "scored", "scores": FULL,
              "guard": "listing_guard: ⚠ possible fraud - payment_rails (western_union)"}],
            {"a": self.entry()},
        )
        self.assertIn("payment_rails", stored["a"]["guard"])

    def test_dry_run_writes_nothing(self):
        state = self.write_state({"a": self.entry()})
        results = self.tmp / "results.json"
        results.write_text(json.dumps([{"key": "a", "status": "scored", "scores": FULL}]),
                           encoding="utf-8")
        self.run_tool("apply", "--state", state, "--results", results,
                 "--today", "2026-10-28", "--dry-run")
        self.assertEqual(self.read_state(state)["a"]["status"], "new")


class SweepTests(StateFixture):
    def sweep(self, seen, today="2026-10-28", extra=()):
        state = self.write_state(seen)
        proc = self.run_tool("sweep", "--state", state, "--today", today, *extra)
        return json.loads(proc.stdout), state

    def test_a_passed_deadline_is_retired(self):
        payload, state = self.sweep(
            {"a": self.entry(status="ranked", deadline="2026-01-01")}, extra=("--write",)
        )
        self.assertEqual(len(payload["newly_expired"]), 1)
        self.assertEqual(self.read_state(state)["a"]["status"], "expired")

    # Still open, and already impossible: this is the failure that actually
    # costs an applicant a cycle, and the deadline alone does not show it.
    def test_an_open_deadline_inside_the_lead_time_is_flagged(self):
        payload, _ = self.sweep({"a": self.entry(status="ranked", deadline="2026-11-20")})
        self.assertEqual(payload["newly_expired"], [])
        self.assertEqual(len(payload["insufficient_lead_time"]), 1)
        self.assertGreater(payload["insufficient_lead_time"][0]["shortfall_days"], 0)

    def test_closing_soon_and_lead_time_can_both_fire(self):
        payload, _ = self.sweep({"a": self.entry(status="ranked", deadline="2026-11-10")})
        self.assertEqual(len(payload["closing_soon"]), 1)
        self.assertEqual(len(payload["insufficient_lead_time"]), 1)

    def test_a_comfortable_deadline_fires_neither(self):
        payload, _ = self.sweep({"a": self.entry(status="ranked", deadline="2027-06-01")})
        self.assertEqual(payload["closing_soon"], [])
        self.assertEqual(payload["insufficient_lead_time"], [])

    def test_an_absent_deadline_is_left_alone(self):
        payload, _ = self.sweep({"a": self.entry(status="ranked", deadline=None)})
        self.assertEqual(payload["newly_expired"], [])
        self.assertEqual(payload["insufficient_lead_time"], [])

    def test_an_unparseable_deadline_is_reported_never_guessed(self):
        payload, _ = self.sweep({"a": self.entry(status="ranked", deadline="next spring")})
        self.assertEqual(len(payload["unparseable_deadlines"]), 1)
        self.assertEqual(payload["newly_expired"], [])

    def test_excluded_keys_are_skipped(self):
        payload, _ = self.sweep(
            {"a": self.entry(status="ranked", deadline="2026-01-01")}, extra=("--exclude", "a")
        )
        self.assertEqual(payload["swept"], 0)


class MissingStateTests(StateFixture):
    def test_a_missing_state_file_points_at_discover(self):
        proc = self.run_tool("candidates", "--state", self.tmp / "nope.json")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("/discover", proc.stderr)


if __name__ == "__main__":
    unittest.main()
