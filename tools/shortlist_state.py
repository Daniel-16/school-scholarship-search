#!/usr/bin/env python3
"""State helper for /rank: select candidates and write results back.

/rank reads the whole of seen_programs.json into the model's context to filter
it by eye (Step 1), then re-emits the whole file to record scores (Step 4).
That cost is paid on every run regardless of how many programmes are actually
scored, and it grows for the life of the workspace, since seen_programs.json
is append-only by design and most stored entries are `skipped`.

This moves the state-file traffic into code. Three subcommands:

  candidates   select the eligible entries for this run and project only the
               fields a scoring agent needs
  sweep        rule 6's expiry pass over entries this run did not re-score -
               a stored-date comparison, no fetch, no agent - plus the
               lead-time pass that is specific to admissions (below)
  apply        write scoring results back to seen_programs.json and print the
               ranked/vetoed/expired/unreachable/gave_up rows Step 5's
               report is built from

Three things here are admissions-shaped rather than inherited:

  The rubric. Funding carries the largest single weight. An unfunded offer
  from a world-class department is not an opportunity for a self-funding
  applicant from Nigeria - it is a rejection with extra steps - so `funding`
  outweighs `academic_fit`, and a confirmed inability to pay vetoes on the
  same footing as failing the entry requirements.

  The gates. Three of them, any one of which vetoes: `eligibility_gate` (entry
  requirements, nationality restrictions, degree-level rules), `language_gate`
  (IELTS/TOEFL/language of instruction) and `funding_gate`. A job listing has
  one location gate; an application has these three, and each one on its own
  makes the application a wasted fee.

  Lead time. A job can be applied for the night before it closes. A graduate
  application cannot: transcripts take weeks to be issued and sent, referees
  need notice, and a language test has to be booked, sat and reported. So the
  sweep does not only retire past deadlines - it flags a deadline that is
  still in the future but too close to assemble a complete application for,
  which is the failure that actually costs an applicant a cycle.

Selection and projection follow Step 1's existing rules exactly (status
filter, tracker exclusion, focus filter, `--limit`/`--all`); the write-back
follows Step 4's existing rules exactly (the legacy verdict migration, the
deadline null-is-not-a-correction rule, verbatim strengths/gaps persistence,
idempotent skip of already-ranked entries); the sweep follows rule 6 exactly
(defensive date parsing, an absent deadline left alone, `--all` making a
retired entry revivable).

Nothing here fetches a listing or judges a fit. Scoring stays with the model;
this only removes the state file from the conversation.

Usage:
  python3 tools/shortlist_state.py candidates [--all] [--focus TEXT] [--limit N]
  python3 tools/shortlist_state.py sweep [--write] [--exclude KEY,KEY]
  python3 tools/shortlist_state.py apply --results results.json [--dry-run] [--now ISO-DATETIME]

All subcommands print JSON on stdout. Exit 0 on success, 1 on a usage or
state error, or on `apply` when any result could not be written.
"""

import argparse
import json
import os
import re
import sys
import tempfile
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "program_search" / "seen_programs.json"
TRACKER = ROOT / "application_tracker.csv"

# 04-program-evaluation.md. Funding is the heaviest single weight on purpose:
# see the module docstring. The five sum to 1.00; overall_score() checks it.
WEIGHTS = {
    "funding": 0.30,
    "academic_fit": 0.25,
    "admission_odds": 0.20,
    "career_value": 0.15,
    "logistics": 0.10,
}
BANDS = ((75, "Strong Match"), (60, "Good Match"), (45, "Moderate Match"),
         (30, "Weak Match"), (0, "Poor Match"))

DEFAULT_LIMIT = 10

# A deadline inside this window is "closing soon" in the sweep's report.
URGENT_DAYS = 30

# The floor on assembling a complete application from a standing start. It is
# set by the slowest artefact, not the fastest: a Nigerian university
# transcript issued and couriered to a foreign institution routinely takes
# 4-6 weeks, three referees need a fortnight of notice each, and an IELTS slot
# plus its report turnaround is about three weeks. Anything closer than this
# is reported as `insufficient_lead_time` - still applicable, because a fee
# waiver, a scanned transcript or an in-hand test score can close the gap, but
# never silently treated as a normal open deadline.
LEAD_TIME_DAYS = 45
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# The statuses a /rank scoring agent may return (rank.md Step 2). This module
# owns the set; tests/test_rank_command.py asserts rank.md's JSON contract
# names exactly these, so the spec and the tool cannot drift apart.
AGENT_STATUSES = ("scored", "expired", "unreachable")

# A listing that could not be fetched is `unreachable`, not `expired`, and is
# retried on later runs (#534). It gives up to `expired` only after this many
# failed attempts with at least this long between the first and the last, so a
# scheduled run plus a manual one on the same day cannot burn every attempt on
# one outage.
UNREACHABLE_MAX_ATTEMPTS = 3
UNREACHABLE_MIN_SPAN = timedelta(hours=48)
FETCH_ERROR_MAX = 200
RETRY_FIELDS = ("fetch_attempts", "first_unreachable", "last_fetch_error")
TIMESTAMP = "%Y-%m-%dT%H:%M:%SZ"


def load_state(path: Path) -> tuple[dict, dict]:
    """Return (document, seen-map). The map is mutated in place by callers."""
    if not path.is_file():
        sys.exit(f"{path} not found - run /discover first")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"{path} is not valid JSON: {exc}")
    seen = doc.get("seen") if isinstance(doc, dict) and "seen" in doc else doc
    if not isinstance(seen, dict):
        sys.exit(f"{path}: expected an object of listing entries")
    return doc, seen


def save_state(path: Path, doc: dict) -> None:
    """Atomic replace: a half-written seen_programs.json loses the discovery history."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".seen_programs.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def parse_timestamp(value) -> datetime | None:
    """A stored UTC timestamp, or None for anything else (absent, malformed, a
    bare date) - the defensive-parse rule again: never compared, never guessed."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.strptime(value.strip(), TIMESTAMP)
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc)


def parse_now(value: str) -> datetime:
    """--now: an ISO 8601 date-time; a naive value is taken as UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse_iso(value) -> date | None:
    """Rule 6's defensive-parse rule: anything that is not YYYY-MM-DD is treated
    exactly like an absent value - never compared, never guessed at."""
    if not isinstance(value, str) or not ISO.match(value.strip()):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def norm(text) -> str:
    """Ignore case and separators without discarding non-Latin identity."""
    text = unicodedata.normalize("NFC", str(text or "").casefold())
    # Combining marks can distinguish names even after NFC (e.g. Indic vowels).
    return "".join(
        char for char in text
        if char.isalnum() or unicodedata.category(char).startswith("M")
    )


def tracker_pairs(path: Path) -> set[tuple[str, str]]:
    """institution+programme pairs already in the tracker - out of scope for ranking."""
    if not path.is_file():
        return set()
    import csv

    pairs = set()
    try:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                provider, award = norm(row.get("institution")), norm(row.get("program"))
                if provider:
                    pairs.add((provider, award))
    except UnicodeDecodeError:
        # A spreadsheet's plain "CSV" save writes the ANSI code page (cp1252 on
        # most Western installs), so any accented institution name stops decoding.
        sys.exit(f"{path} is not UTF-8 text - re-save it as CSV UTF-8")
    return pairs


def entry_eligibility_verdict(entry: dict) -> str | None:
    """eligibility_verdict, falling back to a legacy verdict stored under
    `eligibility` (an entry ranked before the rename may carry a bare
    PASS/FAIL/FLAG string there rather than a sentence of reasoning)."""
    verdict = entry.get("eligibility_verdict")
    if verdict:
        return verdict
    legacy = entry.get("eligibility")
    return legacy if legacy in ("PASS", "FAIL", "FLAG") else None


def cmd_candidates(args) -> int:
    _, seen = load_state(args.state)
    excluded = tracker_pairs(args.tracker)

    selected, skipped_tracker = [], 0
    for key, entry in seen.items():
        status = entry.get("status")
        if args.all:
            if status == "skipped":
                continue
        elif status not in ("new", "unreachable"):
            continue
        if (norm(entry.get("provider")), norm(entry.get("award"))) in excluded:
            skipped_tracker += 1
            continue
        if args.focus:
            haystack = " ".join(
                [str(entry.get("award") or ""), str(entry.get("provider") or ""),
                 str(entry.get("field") or ""), str(entry.get("country") or "")]
                + [str(b) for b in entry.get("strengths") or []]
                + [str(b) for b in entry.get("gaps") or []]
            ).lower()
            if args.focus.lower() not in haystack:
                continue
        selected.append(
            {
                "key": key,
                "award": entry.get("award"),
                "provider": entry.get("provider"),
                # `program` or `scholarship`: the scoring agent reads a
                # scholarship scheme against eligibility rules and a programme
                # against entry requirements, and they are not the same read.
                "kind": entry.get("kind"),
                "level": entry.get("level"),
                "country": entry.get("country"),
                "field": entry.get("field"),
                "url": entry.get("url"),
                "portal": entry.get("portal"),
                "deadline": entry.get("deadline"),
                "opens": entry.get("opens"),
                "first_seen": entry.get("first_seen"),
            }
        )

    eligible = len(selected)
    if args.limit > 0:
        selected = selected[: args.limit]
    print(
        json.dumps(
            {
                "eligible": eligible,
                "selected": selected,
                "deferred": max(0, eligible - len(selected)),
                "excluded_by_tracker": skipped_tracker,
                "total_entries": len(seen),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_sweep(args) -> int:
    doc, seen = load_state(args.state)
    today = args.today
    # "a_b, c_d" is as natural a comma-separated list as "a_b,c_d"; keys never
    # carry surrounding whitespace, so a space must not un-exclude a key.
    exclude = {k.strip() for k in (args.exclude or "").split(",") if k.strip()}

    expired, closing, too_late, unparseable, checked = [], [], [], [], 0
    for key, entry in seen.items():
        if entry.get("status") != "ranked" or key in exclude:
            continue
        checked += 1
        raw = entry.get("deadline")
        if raw in (None, ""):
            continue
        parsed = parse_iso(raw)
        if parsed is None:
            unparseable.append({"key": key, "portal": entry.get("portal"), "deadline": raw})
            continue
        days_left = (parsed - today).days
        row = {
            "key": key,
            "award": entry.get("award"),
            "provider": entry.get("provider"),
            "url": entry.get("url"),
            "deadline": raw,
            "days_left": days_left,
        }
        if parsed < today:
            expired.append(row)
        else:
            if days_left <= URGENT_DAYS:
                closing.append(row)
            # Reported alongside `closing_soon`, not instead of it: a deadline
            # 20 days out is both. The lead-time row is what tells the user the
            # application needs a shortcut (an in-hand test score, a scanned
            # transcript, referees already briefed) rather than the normal
            # document run, and it is the one that is easy to miss, because
            # the deadline itself still looks comfortably open.
            if days_left < LEAD_TIME_DAYS:
                too_late.append({**row, "shortfall_days": LEAD_TIME_DAYS - days_left})

    if args.write and expired:
        for row in expired:
            seen[row["key"]]["status"] = "expired"
        save_state(args.state, doc)

    print(
        json.dumps(
            {
                "swept": checked,
                "newly_expired": expired,
                "closing_soon": sorted(closing, key=lambda r: r["deadline"]),
                "insufficient_lead_time": sorted(too_late, key=lambda r: r["deadline"]),
                "lead_time_days": LEAD_TIME_DAYS,
                "unparseable_deadlines": unparseable,
                "written": bool(args.write and expired),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def overall_score(scores: dict) -> int:
    """Weighted 0-100 score. Every dimension in WEIGHTS must be present.

    A missing dimension is an error, never a zero: a scoring agent that omits
    `funding` because the listing did not mention money would otherwise have
    its silence recorded as "this programme funds nothing", which is the
    single most consequential thing the rubric says.
    """
    if not isinstance(scores, dict):
        raise ValueError("scores must be an object")
    total = 0.0
    for dim, weight in WEIGHTS.items():
        value = scores.get(dim)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"missing or non-numeric score '{dim}'")
        if not 0 <= value <= 100:
            raise ValueError(f"score '{dim}' must be finite and between 0 and 100")
        total += float(value) * weight
    return int(total + 0.5)


def band(score: int) -> str:
    for floor, name in BANDS:
        if score >= floor:
            return name
    return "Poor Fit"


def cmd_apply(args) -> int:
    doc, seen = load_state(args.state)
    today = args.today
    now = args.now
    try:
        results = json.loads(Path(args.results).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"cannot read results file {args.results}: {exc}")
    if isinstance(results, dict):
        results = results.get("results", [])
    if not isinstance(results, list):
        sys.exit("results file must be a JSON array of scoring objects")

    rows, expired, unreachable, gave_up, errors = [], [], [], [], []
    for result in results:
        if not isinstance(result, dict):
            errors.append({"key": None, "error": "result is not an object"})
            continue
        key = result.get("key")
        entry = seen.get(key) if isinstance(key, str) else None
        if entry is None:
            errors.append({"key": key, "error": "no such key in seen_programs.json"})
            continue

        # A missing status is a score, as it always was; a misspelt one is an
        # error rather than a fall-through that reports a "missing score".
        status = result.get("status", "scored")
        if status not in AGENT_STATUSES:
            errors.append(
                {"key": key, "error": f"unknown status {status!r}; expected one of {', '.join(AGENT_STATUSES)}"}
            )
            continue

        if status == "unreachable":
            # A stored deadline that has already passed is positive evidence the
            # listing is closed, whatever the fetch did: expire it, as the scored
            # path and rule 6 would, instead of retrying it and later listing it
            # as possibly live.
            deadline = parse_iso(entry.get("deadline"))
            if deadline is not None and deadline < today:
                entry["status"] = "expired"
                for field in (*RETRY_FIELDS, "expired_reason"):
                    entry.pop(field, None)
                expired.append(
                    {"key": key, "award": entry.get("award"), "provider": entry.get("provider"), "url": entry.get("url")}
                )
                continue

            previous = entry.get("fetch_attempts")
            valid = isinstance(previous, int) and not isinstance(previous, bool)
            attempts = (previous if valid else 0) + 1
            first = parse_timestamp(entry.get("first_unreachable")) or now
            # Plain, bounded text: it is shown in the report, never acted on.
            error = " ".join(str(result.get("fetch_error") or "").split())[:FETCH_ERROR_MAX]
            entry["fetch_attempts"] = attempts
            entry["first_unreachable"] = first.strftime(TIMESTAMP)
            if error:
                entry["last_fetch_error"] = error
            row = {
                "key": key,
                "award": entry.get("award"),
                "provider": entry.get("provider"),
                "url": entry.get("url"),
                "fetch_attempts": attempts,
                "last_fetch_error": entry.get("last_fetch_error"),
            }
            if attempts >= UNREACHABLE_MAX_ATTEMPTS and now - first >= UNREACHABLE_MIN_SPAN:
                # The retry fields stay on the entry as its history; `--all`
                # can still revive it, like any other expired entry.
                entry["status"] = "expired"
                entry["expired_reason"] = "unreachable"
                gave_up.append(row)
            else:
                entry["status"] = "unreachable"
                unreachable.append(row)
            continue

        if status == "expired":
            entry["status"] = "expired"
            for field in (*RETRY_FIELDS, "expired_reason"):
                entry.pop(field, None)
            expired.append(
                {"key": key, "award": entry.get("award"), "provider": entry.get("provider"), "url": entry.get("url")}
            )
            continue

        try:
            score = overall_score(result.get("scores") or {})
        except ValueError as exc:
            errors.append({"key": key, "error": str(exc)})
            continue

        # A missing deadline from the fresh fetch is not a correction to the
        # stored date. Scored keys are excluded from the later sweep, so apply
        # must retire a passed deadline before updating any ranking metadata.
        parsed = parse_iso(result.get("deadline") or entry.get("deadline"))
        if parsed is not None and parsed < today:
            entry["status"] = "expired"
            for field in (*RETRY_FIELDS, "expired_reason"):
                entry.pop(field, None)  # fetched after all: closed on its deadline
            if result.get("deadline"):
                entry["deadline"] = result["deadline"]
            expired.append(
                {"key": key, "award": entry.get("award"), "provider": entry.get("provider"), "url": entry.get("url")}
            )
            continue

        legacy = entry_eligibility_verdict(entry)
        if entry.get("eligibility") in ("PASS", "FAIL", "FLAG"):
            entry.pop("eligibility", None)  # legacy bare verdict, never reasoning
        for field in (*RETRY_FIELDS, "expired_reason"):
            entry.pop(field, None)  # fetched after all: the retry history is moot
        entry["status"] = "ranked"
        entry["rank_score"] = score
        entry["rank_verdict"] = band(score)
        entry["rank_date"] = today.isoformat()
        entry["eligibility_verdict"] = result.get("eligibility_verdict") or legacy or "PASS"
        # Each gate carries an optional note, kept only while the gate is not
        # PASS. A stale "needs IELTS 7.0" left on an entry whose gate later
        # passed would be read as a live blocker on the next report.
        for gate, note in (("language_gate", "language_note"),
                           ("funding_gate", "funding_note"),
                           ("eligibility_verdict", "eligibility_note")):
            if gate != "eligibility_verdict":
                entry[gate] = result.get(gate) or "PASS"
            if entry[gate] == "PASS":
                entry.pop(note, None)
            else:
                entry[note] = result.get(note)
        # Absence is not a correction: a fetch that degraded to a listing page
        # returns no deadline, and blanking a stored one would erase a real
        # date and make the entry immortal to rule 6's sweep.
        if result.get("deadline"):
            entry["deadline"] = result["deadline"]
        for field in ("strengths", "gaps"):
            value = result.get(field)
            if isinstance(value, list):
                entry[field] = [str(b) for b in value][:3]
        # The scoring agent's listing_guard verdict line ("clean" or the ⚠ line).
        # Additive and optional: an agent on an older prompt returns none, and
        # nothing is written. Stored so a later reader can see why a row carried
        # a marker without re-fetching the listing.
        # Normalised so Step 5's "anything other than clean" rule holds whether
        # the agent returned "clean" or the gate's first line verbatim: any clean
        # verdict (with or without its context parenthetical) stores as "clean";
        # a ⚠ verdict stores without the "listing_guard:" prefix. A rescoring
        # result without a guard drops a stale one - absence means "not run",
        # and last run's verdict would mislabel this run's fetch.
        guard = result.get("guard")
        if isinstance(guard, str) and guard.strip():
            text = guard.strip()
            if text.lower().startswith("listing_guard:"):
                text = text[len("listing_guard:"):].strip()
            entry["guard"] = "clean" if text.lower().startswith("clean") else text[:200]
        else:
            entry.pop("guard", None)

        rows.append(
            {
                "key": key,
                "award": entry.get("award"),
                "provider": entry.get("provider"),
                "kind": entry.get("kind"),
                "level": entry.get("level"),
                "country": entry.get("country"),
                "url": entry.get("url"),
                "score": score,
                "verdict": entry["rank_verdict"],
                "eligibility_verdict": entry["eligibility_verdict"],
                "eligibility_note": entry.get("eligibility_note"),
                "language_gate": entry["language_gate"],
                "language_note": entry.get("language_note"),
                "funding_gate": entry["funding_gate"],
                "funding_note": entry.get("funding_note"),
                "deadline": entry.get("deadline"),
                "urgent": bool(parsed and today <= parsed <= today + timedelta(days=URGENT_DAYS)),
                # An application that is still open but no longer has room for
                # the document run. Carried on the row rather than left to the
                # sweep, because a freshly scored entry is excluded from the
                # sweep by design and would otherwise never be flagged.
                "short_lead_time": bool(parsed and today <= parsed < today + timedelta(days=LEAD_TIME_DAYS)),
                "strengths": entry.get("strengths", []),
                "gaps": entry.get("gaps", []),
                "guard": entry.get("guard"),
            }
        )

    if not args.dry_run:
        save_state(args.state, doc)

    rows.sort(key=lambda r: (r["score"], r["urgent"]), reverse=True)
    # Any one of the three gates vetoes. A FLAG does not: it means the rule
    # could not be confirmed from the listing, which is a question for the
    # user, not a decision this tool gets to make on their behalf.
    def veto(r):
        return "FAIL" in (r["eligibility_verdict"], r["language_gate"], r["funding_gate"])
    vetoed = [r for r in rows if veto(r)]
    ranked = [r for r in rows if not veto(r)]
    print(
        json.dumps(
            {
                "ranked": ranked,
                "vetoed": vetoed,
                "expired": expired,
                "unreachable": unreachable,
                "gave_up": gave_up,
                "errors": errors,
                "written": not args.dry_run,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 1 if errors else 0


def _force_utf8_output() -> None:
    """Write UTF-8 whatever the host's default encoding is.

    A piped stdout on Windows defaults to the ANSI code page (cp1252 on most
    Western installs), so printing an institution, award or file name outside it
    raised UnicodeEncodeError before the workflow saw any output.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)  # absent on a StringIO under test
        if reconfigure:
            reconfigure(encoding="utf-8")


def main() -> int:
    _force_utf8_output()
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--state", type=Path, default=STATE)
    common.add_argument("--today", type=date.fromisoformat, default=date.today())
    common.add_argument(
        "--now", type=parse_now, default=datetime.now(timezone.utc),
        help="date-time for the unreachable retry floor (default: now, UTC)",
    )

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)

    cand = sub.add_parser("candidates", parents=[common], help="select the entries to score")
    cand.add_argument("--tracker", type=Path, default=TRACKER)
    cand.add_argument("--all", action="store_true", help="include every non-skipped status")
    cand.add_argument("--focus", help="substring filter over award, provider, field, country and stored notes")
    cand.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="0 for no cap")
    cand.set_defaults(func=cmd_candidates)

    sweep = sub.add_parser("sweep", parents=[common], help="rule 6's expiry pass, no fetch")
    sweep.add_argument("--write", action="store_true", help="persist the expiries")
    sweep.add_argument("--exclude", help="comma-separated keys re-scored this run")
    sweep.set_defaults(func=cmd_sweep)

    app = sub.add_parser("apply", parents=[common], help="write scoring results back and print the ranking")
    app.add_argument("--results", required=True, help="JSON array from the scoring agents")
    app.add_argument("--dry-run", action="store_true")
    app.set_defaults(func=cmd_apply)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
