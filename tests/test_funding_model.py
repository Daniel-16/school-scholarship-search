"""Cost, funding gap and proof of funds.

Three properties carry the tool: a programme's cost is its *whole* duration
rather than one year of it, a plan that balances overall can still be
unpayable in year one, and the proof-of-funds requirement is a separate
verdict because a full scholarship does not automatically satisfy it.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import funding_model  # noqa: E402

RATES = {"EUR_USD": 1.08, "GBP_USD": 1.27}


def plan(**overrides):
    base = {
        "application": "Example", "currency": "USD", "duration_months": 24,
        "costs": {"tuition_per_year": 10000, "living_per_month": 1000, "one_off": {}},
        "funding": {}, "proof_of_funds": {},
    }
    base.update(overrides)
    return base


class CostTests(unittest.TestCase):
    def test_tuition_covers_the_whole_duration_not_one_year(self):
        # A two-year MSc quoted "per year" is a two-year decision. Reading the
        # brochure figure as the total is the commonest costing error there is.
        result = funding_model.model(plan(), RATES)
        self.assertEqual(result["cost"]["tuition_gross"], 20000)
        self.assertEqual(result["cost"]["living"], 24000)

    def test_a_part_year_programme_is_prorated(self):
        result = funding_model.model(plan(duration_months=18), RATES)
        self.assertEqual(result["cost"]["tuition_gross"], 15000)

    def test_one_off_costs_are_summed(self):
        result = funding_model.model(
            plan(costs={"tuition_per_year": 0, "living_per_month": 0,
                        "one_off": {"visa": 100, "flights": 900, "insurance": 500}}),
            RATES,
        )
        self.assertEqual(result["cost"]["one_off"], 1500)

    def test_a_tuition_waiver_reduces_the_cost(self):
        result = funding_model.model(
            plan(funding={"tuition_waiver_percent": 100}), RATES
        )
        self.assertEqual(result["cost"]["tuition_after_waiver"], 0)
        self.assertEqual(result["cost"]["tuition_gross"], 20000)


class CurrencyTests(unittest.TestCase):
    def test_amounts_convert_to_the_base_currency(self):
        result = funding_model.model(
            plan(costs={"tuition_per_year": 10000, "tuition_currency": "EUR",
                        "living_per_month": 0, "one_off": {}}),
            RATES,
        )
        self.assertAlmostEqual(result["cost"]["tuition_gross"], 21600, places=2)

    def test_a_missing_rate_names_the_rate_to_add(self):
        with self.assertRaises(funding_model.InputError) as caught:
            funding_model.model(
                plan(costs={"tuition_per_year": 100, "tuition_currency": "JPY",
                            "living_per_month": 0, "one_off": {}}),
                RATES,
            )
        self.assertIn("JPY_USD", str(caught.exception))

    # A sparse plan should not be blocked by a rate it does not need.
    def test_a_zero_amount_needs_no_rate(self):
        result = funding_model.model(
            plan(costs={"tuition_per_year": 0, "tuition_currency": "JPY",
                        "living_per_month": 0, "one_off": {}}),
            RATES,
        )
        self.assertEqual(result["cost"]["tuition_gross"], 0)


class FundingTests(unittest.TestCase):
    def test_a_fully_funded_plan_closes(self):
        result = funding_model.model(
            plan(costs={"tuition_per_year": 0, "living_per_month": 1000, "one_off": {}},
                 funding={"stipend_per_month": 1500}),
            RATES,
        )
        self.assertTrue(result["affordable"])
        self.assertLess(result["gap"], 0)

    def test_term_time_work_is_discounted_by_half(self):
        # The permit is a ceiling, not a schedule. A plan that only closes on
        # the full entitlement has not closed.
        result = funding_model.model(
            plan(costs={"tuition_per_year": 0, "living_per_month": 0, "one_off": {}},
                 funding={"work_hours_per_week": 20, "work_hourly_rate": 10}),
            RATES,
        )
        nominal = 20 * 10 * (52 / 12) * 24
        self.assertAlmostEqual(result["funding"]["term_time_work_discounted"], nominal / 2, places=0)

    def test_an_unknown_scholarship_coverage_is_rejected(self):
        with self.assertRaises(funding_model.InputError):
            funding_model.model(plan(funding={"scholarship_covers": "mostly"}), RATES)

    def test_every_declared_coverage_value_is_accepted(self):
        for covers in funding_model.COVERS:
            with self.subTest(covers=covers):
                funding_model.model(plan(funding={"scholarship_covers": covers}), RATES)


class FrontLoadingTests(unittest.TestCase):
    def test_a_plan_that_balances_overall_can_fail_in_year_one(self):
        # Tuition and every one-off cost fall due before the stipend arrives.
        result = funding_model.model(
            plan(duration_months=36,
                 costs={"tuition_per_year": 0, "living_per_month": 1000,
                        "one_off": {"deposit": 20000}},
                 funding={"stipend_per_month": 1600}),
            RATES,
        )
        self.assertLessEqual(result["gap"], 0)
        self.assertGreater(result["first_year"]["gap"], 0)
        self.assertTrue(any("front-loaded" in v for v in result["verdicts"]))


class ProofOfFundsTests(unittest.TestCase):
    def test_proof_of_funds_is_a_separate_verdict(self):
        # Fully funded on paper, and still unable to get a visa.
        result = funding_model.model(
            plan(costs={"tuition_per_year": 0, "living_per_month": 500, "one_off": {}},
                 funding={"stipend_per_month": 2000},
                 proof_of_funds={"required": 12000}),
            RATES,
        )
        self.assertLess(result["gap"], 0)
        self.assertEqual(result["proof_of_funds"]["shortfall"], 12000)
        self.assertFalse(result["affordable"])

    def test_a_scholarship_counts_as_evidence_only_when_declared(self):
        shared = dict(
            costs={"tuition_per_year": 0, "living_per_month": 0, "one_off": {}},
            proof_of_funds={"required": 10000},
        )
        strict = funding_model.model(
            plan(funding={"scholarship_total": 15000, "scholarship_covers": "full"}, **shared), RATES
        )
        lenient = funding_model.model(
            plan(funding={"scholarship_total": 15000, "scholarship_covers": "full"},
                 **{**shared, "proof_of_funds": {"required": 10000,
                                                 "scholarship_counts_as_evidence": True}}),
            RATES,
        )
        self.assertEqual(strict["proof_of_funds"]["shortfall"], 10000)
        self.assertEqual(lenient["proof_of_funds"]["shortfall"], 0)

    def test_own_contribution_always_counts_as_evidence(self):
        result = funding_model.model(
            plan(costs={"tuition_per_year": 0, "living_per_month": 0, "one_off": {}},
                 funding={"own_contribution": 10000},
                 proof_of_funds={"required": 10000}),
            RATES,
        )
        self.assertEqual(result["proof_of_funds"]["shortfall"], 0)


class ValidationTests(unittest.TestCase):
    def test_a_zero_duration_is_rejected(self):
        with self.assertRaises(funding_model.InputError):
            funding_model.model(plan(duration_months=0), RATES)

    def test_a_negative_amount_is_rejected(self):
        with self.assertRaises(funding_model.InputError):
            funding_model.model(
                plan(costs={"tuition_per_year": -100, "living_per_month": 0, "one_off": {}}), RATES
            )

    def test_a_non_numeric_amount_names_the_field(self):
        with self.assertRaises(funding_model.InputError) as caught:
            funding_model.model(
                plan(costs={"tuition_per_year": "lots", "living_per_month": 0, "one_off": {}}), RATES
            )
        self.assertIn("tuition_per_year", str(caught.exception))

    def test_a_waiver_over_one_hundred_percent_is_rejected(self):
        with self.assertRaises(funding_model.InputError):
            funding_model.model(plan(funding={"tuition_waiver_percent": 150}), RATES)


class CliTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(REPO / "tools" / "funding_model.py"), *map(str, args)],
            capture_output=True, text=True,
        )

    def write(self, payload):
        path = self.tmp / "plan.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_the_template_is_a_valid_plan(self):
        result = self.run_cli("--template")
        self.assertEqual(result.returncode, 0)
        funding_model.model(json.loads(result.stdout), RATES)

    def test_exit_three_when_the_plan_does_not_close(self):
        path = self.write(plan())
        result = self.run_cli("--in", path, "--rates", self.tmp / "none.json")
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn("does not close", result.stdout)

    def test_exit_zero_when_it_closes(self):
        path = self.write(plan(
            costs={"tuition_per_year": 0, "living_per_month": 100, "one_off": {}},
            funding={"stipend_per_month": 2000},
        ))
        result = self.run_cli("--in", path, "--rates", self.tmp / "none.json")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("closes", result.stdout)

    def test_exit_one_on_an_unreadable_plan(self):
        result = self.run_cli("--in", self.tmp / "missing.json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot read", result.stderr)

    def test_the_shipped_rates_file_loads(self):
        rates, updated = funding_model.load_rates(REPO / "funding" / "rates.json")
        self.assertIn("EUR_USD", rates)
        self.assertTrue(updated)


if __name__ == "__main__":
    unittest.main()
