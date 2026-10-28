#!/usr/bin/env python3
"""Decide whether an application is actually affordable, before it is written.

The question a graduate applicant has to answer is not "what does this cost".
It is "what is left over after the funding, and can I show it". Four numbers
decide it, and three of them are routinely left out of the brochure:

  cost of attendance   tuition for the whole programme plus living costs for
                       its whole duration - not one year of either. A
                       two-year MSc quoted at "EUR 18,000 per year" is a
                       EUR 36,000 decision.
  one-off costs        the application fee, the visa fee, the health surcharge
                       or mandatory insurance, flights, and the deposit. Small
                       individually; together they are often a month of
                       stipend, and they all fall due before any money arrives.
  funding              a scholarship is not automatically "full". Most are
                       tuition-only, some are partial-tuition, and a stipend
                       is paid monthly in arrears from the start date, which
                       is not when the first rent is due.
  proof of funds       the sum a visa requires you to *show*, in an account,
                       before the visa is granted. It is not spent; it is
                       blocked or evidenced. This is the number that sinks
                       funded applicants: a full scholarship does not exempt
                       you from it unless the award letter is accepted as the
                       evidence, which varies by country.

So the output is a gap, a monthly shortfall, and a separate proof-of-funds
verdict - never a single "affordable: yes". An application can be affordable
over three years and still be impossible in month one.

Currency. Rates come from `funding/rates.json`, which the user maintains, and
never from a live lookup. A verdict that silently changes between two runs
because a rate moved is worse than one the user set and can see; the file
records when it was last updated and this tool says so in its output.

Usage:
  python3 tools/funding_model.py --in funding/<application>.json
  python3 tools/funding_model.py --in ... --json
  python3 tools/funding_model.py --template > funding/my_application.json

Exit 0 when the plan closes (gap <= 0 and proof of funds satisfied), 1 on a
usage or input error, and 3 when there is an unfunded gap or the proof-of-funds
requirement is not met - so a shortlist pass can branch on it.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RATES = ROOT / "funding" / "rates.json"

TEMPLATE = {
    "application": "University of Example - MSc Example",
    "currency": "USD",
    "duration_months": 24,
    "costs": {
        "tuition_per_year": 18000,
        "tuition_currency": "EUR",
        "living_per_month": 1100,
        "living_currency": "EUR",
        "one_off": {
            "application_fee": 100,
            "visa_fee": 90,
            "health_insurance": 1400,
            "flights": 900,
            "settling_in": 600,
        },
        "one_off_currency": "EUR",
    },
    "funding": {
        "scholarship_total": 0,
        "scholarship_covers": "none",
        "scholarship_currency": "EUR",
        "stipend_per_month": 0,
        "stipend_currency": "EUR",
        "tuition_waiver_percent": 0,
        "own_contribution": 0,
        "work_hours_per_week": 20,
        "work_hourly_rate": 0,
        "work_currency": "EUR",
    },
    "proof_of_funds": {
        "required": 11904,
        "currency": "EUR",
        "note": "German blocked account, 2027 rate - confirm on the official page",
        "scholarship_counts_as_evidence": False,
    },
}

# What a scholarship actually pays for. "full" is claimed far more often than
# it is true, so the distinction is explicit and the model never infers it.
COVERS = ("none", "tuition", "partial_tuition", "living", "full")


class InputError(Exception):
    """A plan that cannot be modelled, as opposed to one that does not close."""


def load_rates(path: Path) -> tuple[dict, str | None]:
    """Rates to the base currency, plus the date they were set.

    An absent file is not an error while every amount shares one currency -
    the common case - so the error is raised at conversion time, naming the
    currency that could not be converted, rather than up front.
    """
    if not path.is_file():
        return {}, None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc
    rates = doc.get("rates") if isinstance(doc, dict) else None
    if not isinstance(rates, dict):
        raise InputError(f"{path}: expected an object with a 'rates' map")
    return rates, doc.get("updated")


def amount(value, field: str) -> float:
    if value in (None, ""):
        return 0.0
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{field}: expected a number, got {value!r}")
    if value < 0:
        raise InputError(f"{field}: must not be negative")
    return float(value)


def convert(value: float, source: str, base: str, rates: dict, field: str) -> float:
    """Convert to the base currency, or say exactly which rate is missing."""
    source = (source or base).upper()
    base = base.upper()
    if source == base:
        return value
    if value == 0:
        return 0.0  # a zero needs no rate; demanding one blocks sparse plans
    rate = rates.get(f"{source}_{base}") or rates.get(source)
    if rate is None:
        raise InputError(
            f"{field}: no rate for {source} -> {base}. "
            f"Add \"{source}_{base}\": <rate> to funding/rates.json"
        )
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or rate <= 0:
        raise InputError(f"rate {source}_{base} must be a positive number")
    return value * float(rate)


def model(plan: dict, rates: dict) -> dict:
    if not isinstance(plan, dict):
        raise InputError("the plan must be a JSON object")
    base = str(plan.get("currency") or "USD").upper()
    months = amount(plan.get("duration_months"), "duration_months")
    if months <= 0:
        raise InputError("duration_months must be greater than 0")
    years = months / 12.0

    costs = plan.get("costs") or {}
    funding = plan.get("funding") or {}
    if not isinstance(costs, dict) or not isinstance(funding, dict):
        raise InputError("'costs' and 'funding' must be objects")

    def c(section, key, currency_key, field):
        return convert(amount(section.get(key), field), section.get(currency_key, base),
                       base, rates, field)

    tuition = c(costs, "tuition_per_year", "tuition_currency", "costs.tuition_per_year") * years
    living = c(costs, "living_per_month", "living_currency", "costs.living_per_month") * months

    one_off_items = costs.get("one_off") or {}
    if not isinstance(one_off_items, dict):
        raise InputError("costs.one_off must be an object of named amounts")
    one_off_currency = costs.get("one_off_currency", base)
    one_off = sum(
        convert(amount(v, f"costs.one_off.{k}"), one_off_currency, base, rates, f"costs.one_off.{k}")
        for k, v in one_off_items.items()
    )

    waiver = amount(funding.get("tuition_waiver_percent"), "funding.tuition_waiver_percent")
    if waiver > 100:
        raise InputError("funding.tuition_waiver_percent must be between 0 and 100")
    tuition_after_waiver = tuition * (1 - waiver / 100.0)

    covers = str(funding.get("scholarship_covers") or "none").lower()
    if covers not in COVERS:
        raise InputError(f"funding.scholarship_covers must be one of {', '.join(COVERS)}")

    scholarship = c(funding, "scholarship_total", "scholarship_currency", "funding.scholarship_total")
    stipend = c(funding, "stipend_per_month", "stipend_currency", "funding.stipend_per_month") * months
    own = convert(amount(funding.get("own_contribution"), "funding.own_contribution"),
                  funding.get("own_contribution_currency", base), base, rates, "funding.own_contribution")

    # Term-time work is counted at half the nominal entitlement. The permit is
    # a ceiling, not a schedule: coursework, a job that does not exist on
    # arrival, and vacation-only rules all cut into it, and a plan that only
    # closes on the full 20 hours a week has not closed.
    hours = amount(funding.get("work_hours_per_week"), "funding.work_hours_per_week")
    rate = c(funding, "work_hourly_rate", "work_currency", "funding.work_hourly_rate")
    work = hours * rate * (52.0 / 12.0) * months * 0.5

    total_cost = tuition_after_waiver + living + one_off
    total_funding = scholarship + stipend + own + work
    gap = total_cost - total_funding

    # The first-year view. Funding arrives monthly; tuition and every one-off
    # cost do not, so a plan that balances over three years can still be
    # unpayable in month one.
    first_year_months = min(12.0, months)
    first_year_cost = (
        tuition_after_waiver * (first_year_months / months)
        + (living / months) * first_year_months
        + one_off
    )
    first_year_funding = (
        (scholarship / months) * first_year_months
        + (stipend / months) * first_year_months
        + own
        + (work / months) * first_year_months
    )

    pof = plan.get("proof_of_funds") or {}
    if not isinstance(pof, dict):
        raise InputError("proof_of_funds must be an object")
    pof_required = convert(amount(pof.get("required"), "proof_of_funds.required"),
                           pof.get("currency", base), base, rates, "proof_of_funds.required")
    # A scholarship only counts as visa evidence where the embassy says so.
    # Defaulting that to False is the conservative read and the common case.
    pof_evidence = scholarship if pof.get("scholarship_counts_as_evidence") else 0.0
    pof_shortfall = max(0.0, pof_required - pof_evidence - own)

    def r(value):
        return round(value, 2)

    verdicts = []
    if gap > 0:
        verdicts.append(f"unfunded gap of {r(gap):,.0f} {base} over {months:.0f} months")
    if pof_shortfall > 0:
        verdicts.append(f"proof of funds short by {r(pof_shortfall):,.0f} {base}")
    if first_year_cost - first_year_funding > max(0.0, gap) + 1:
        verdicts.append(
            f"front-loaded: year one is short {r(first_year_cost - first_year_funding):,.0f} {base} "
            "even though the whole programme is closer to balance"
        )

    return {
        "application": plan.get("application"),
        "base_currency": base,
        "duration_months": months,
        "cost": {
            "tuition_gross": r(tuition),
            "tuition_after_waiver": r(tuition_after_waiver),
            "living": r(living),
            "one_off": r(one_off),
            "total": r(total_cost),
        },
        "funding": {
            "scholarship": r(scholarship),
            "scholarship_covers": covers,
            "stipend": r(stipend),
            "own_contribution": r(own),
            "term_time_work_discounted": r(work),
            "total": r(total_funding),
        },
        "gap": r(gap),
        "monthly_shortfall": r(max(0.0, gap) / months),
        "first_year": {
            "cost": r(first_year_cost),
            "funding": r(first_year_funding),
            "gap": r(first_year_cost - first_year_funding),
        },
        "proof_of_funds": {
            "required": r(pof_required),
            "counted_as_evidence": r(pof_evidence + own),
            "shortfall": r(pof_shortfall),
            "note": pof.get("note"),
        },
        "affordable": gap <= 0 and pof_shortfall <= 0,
        "verdicts": verdicts,
    }


def render(result: dict, rates_updated: str | None) -> str:
    b = result["base_currency"]
    def money(v):
        return f"{v:>12,.0f} {b}"
    lines = [
        f"Funding model - {result['application'] or '(unnamed application)'}",
        f"  duration {result['duration_months']:.0f} months, amounts in {b}"
        + (f", rates last updated {rates_updated}" if rates_updated else ""),
        "",
        "  Cost",
        f"    tuition (after waiver) {money(result['cost']['tuition_after_waiver'])}",
        f"    living                 {money(result['cost']['living'])}",
        f"    one-off                {money(result['cost']['one_off'])}",
        f"    total                  {money(result['cost']['total'])}",
        "",
        "  Funding",
        f"    {'scholarship (' + result['funding']['scholarship_covers'] + ')':<22}"
        + money(result['funding']['scholarship']),
        f"    stipend                {money(result['funding']['stipend'])}",
        f"    own contribution       {money(result['funding']['own_contribution'])}",
        f"    term-time work (x0.5)  {money(result['funding']['term_time_work_discounted'])}",
        f"    total                  {money(result['funding']['total'])}",
        "",
        f"  Gap                      {money(result['gap'])}"
        + (f"   ({result['monthly_shortfall']:,.0f} {b}/month)" if result["gap"] > 0 else ""),
        f"  Year one gap             {money(result['first_year']['gap'])}",
        f"  Proof of funds short by  {money(result['proof_of_funds']['shortfall'])}",
    ]
    if result["proof_of_funds"]["note"]:
        lines.append(f"      note: {result['proof_of_funds']['note']}")
    lines.append("")
    if result["affordable"]:
        lines.append("  VERDICT: the plan closes.")
    else:
        lines.append("  VERDICT: does not close -")
        lines += [f"    - {v}" for v in result["verdicts"]]
    return "\n".join(lines)


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)  # absent on a StringIO under test
        if reconfigure:
            reconfigure(encoding="utf-8")


def main(argv=None) -> int:
    _force_utf8_output()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="infile", type=Path, help="a funding plan JSON file")
    ap.add_argument("--rates", type=Path, default=RATES)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--template", action="store_true", help="print a blank plan and exit")
    args = ap.parse_args(argv)

    if args.template:
        print(json.dumps(TEMPLATE, indent=2))
        return 0
    if args.infile is None:
        ap.error("give --in FILE, or --template to print a blank plan")

    try:
        plan = json.loads(args.infile.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"funding_model: cannot read {args.infile}: {exc}", file=sys.stderr)
        return 1

    try:
        rates, updated = load_rates(args.rates)
        result = model(plan, rates)
    except InputError as exc:
        print(f"funding_model: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else render(result, updated))
    return 0 if result["affordable"] else 3


if __name__ == "__main__":
    sys.exit(main())
