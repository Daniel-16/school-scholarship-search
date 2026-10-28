#!/usr/bin/env python3
"""Backward-plan every tracked application and print one chronological board.

The tracker stores a submission deadline per application. That date is not the
thing an applicant has to act on, and treating it as though it were is how a
cycle gets lost: on the day the deadline is comfortable, the transcript that
has to arrive before it has already needed ordering for two weeks.

So this expands each deadline into the milestones that have to land before it,
offset by how long each one really takes for an applicant applying out of
Nigeria to a foreign institution:

  * a transcript is issued by the home university and sent to the destination,
    which is the slowest artefact in the whole application and the one nobody
    budgets for;
  * referees need notice, and the notice has to come with a packet (CV, draft
    statement, the programme's own link) or the letter is generic;
  * a language test has to be booked into an available slot, sat, and then
    reported to the institution, which is three separate waits;
  * the statement needs a draft, a gap, and a re-read - written in one sitting
    the week of the deadline, it reads like it.

Each milestone's offset is a default that a programme can override in the
tracker's `notes` (see MILESTONES below for the syntax). Nothing here invents
a deadline: an application with no deadline in the tracker produces no
milestones and is reported under `no_deadline`, because a guessed date on an
admissions board is worse than a visible hole.

The board is the output. Milestones are merged across every application and
sorted by date, so the answer to "what do I do this week" is the top of one
list rather than a mental join across eight programmes.

Usage:
  python3 tools/deadline_board.py [--tracker FILE] [--today YYYY-MM-DD]
                                  [--horizon DAYS] [--key KEY] [--json]
  python3 tools/deadline_board.py --ics out.ics   # import into any calendar

Exit 0 when the board is produced, 1 on a tracker that cannot be read, and 2
when any milestone is already overdue - so a scheduled run can alert on it.
"""

import argparse
import csv
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACKER = ROOT / "application_tracker.csv"

# Statuses whose applications are still in flight. A submitted application has
# no document run left to plan, and a rejected one has nothing at all; both
# stay out of the board so it does not fill with history.
ACTIVE_STATUSES = {
    "researching", "drafting", "awaiting_documents", "awaiting_references",
}

# Milestones, as (id, days-before-deadline, label). Order is by offset so the
# board reads outward from the deadline; the offsets themselves are the
# argument of this module and are documented one by one above.
MILESTONES = (
    ("language_test", 70, "Book language test (IELTS/TOEFL) if no valid score in hand"),
    ("transcripts", 45, "Order official transcripts and degree certificate from Bingham University"),
    ("referees", 30, "Ask referees and send each a recommender packet"),
    ("statement_draft", 21, "First full draft of the statement of purpose / personal statement"),
    ("supporting_essays", 14, "Draft any scholarship essays and the research proposal"),
    ("statement_final", 7, "Final statement: proofread, word count checked, PDF compiled"),
    ("assemble", 3, "Assemble the portal upload set and pay the application fee"),
    ("submit", 0, "Submit"),
)
MILESTONE_IDS = {m[0] for m in MILESTONES}

# A programme can override or drop a milestone from the tracker's notes field:
#   lead:transcripts=60   move that milestone to 60 days before the deadline
#   lead:language_test=0  drop it (a score already in hand needs no booking)
# Chosen over extra columns because the tracker is edited by hand in a
# spreadsheet, and a column that is empty on 90% of rows gets deleted.
LEAD_OVERRIDE = re.compile(r"\blead:([a-z_]+)=(\d{1,3})\b", re.I)

DUE_SOON_DAYS = 14


def parse_iso(value) -> date | None:
    """YYYY-MM-DD or nothing. Anything else is treated exactly as absent -
    never guessed at, because a misread deadline is worse than a missing one."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def read_tracker(path: Path) -> list[dict]:
    if not path.is_file():
        sys.exit(f"{path} not found - run /setup, or pass --tracker")
    try:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            return list(csv.DictReader(fh))
    except UnicodeDecodeError:
        sys.exit(f"{path} is not UTF-8 text - re-save it as CSV UTF-8")
    except OSError as exc:
        sys.exit(f"cannot read {path}: {exc}")


def overrides(notes: str) -> dict[str, int]:
    """Per-application milestone offsets parsed out of the notes field.

    An unknown milestone id is ignored rather than rejected: the notes field is
    free text an applicant also writes sentences in, and a typo there must not
    take down the board for every other application.
    """
    found = {}
    for name, days in LEAD_OVERRIDE.findall(notes or ""):
        name = name.lower()
        if name in MILESTONE_IDS:
            found[name] = int(days)
    return found


def row_label(row: dict) -> str:
    institution = (row.get("institution") or "").strip() or "(unnamed)"
    program = (row.get("program") or "").strip()
    return f"{institution} - {program}" if program else institution


def plan_row(row: dict, today: date) -> dict:
    """Every milestone for one application, plus why it was or was not planned."""
    deadline = parse_iso(row.get("deadline"))
    entry = {
        "application": row_label(row),
        "institution": (row.get("institution") or "").strip(),
        "program": (row.get("program") or "").strip(),
        "level": (row.get("level") or "").strip(),
        "status": (row.get("status") or "").strip().lower(),
        "deadline": deadline.isoformat() if deadline else None,
        "milestones": [],
    }
    if deadline is None:
        return entry
    custom = overrides(row.get("notes", ""))
    for name, default_days, label in MILESTONES:
        days = custom.get(name, default_days)
        if name in custom and days == 0 and name != "submit":
            continue  # explicitly dropped for this application
        due = deadline - timedelta(days=days)
        entry["milestones"].append({
            "id": name,
            "label": label,
            "due": due.isoformat(),
            "days_from_today": (due - today).days,
            "overdue": due < today,
            "lead_days": days,
            "overridden": name in custom,
        })
    entry["milestones"].sort(key=lambda m: m["due"])
    return entry


def build(rows: list[dict], today: date, horizon: int | None, key: str | None) -> dict:
    planned, no_deadline, inactive = [], [], 0
    for row in rows:
        status = (row.get("status") or "").strip().lower()
        if status and status not in ACTIVE_STATUSES:
            inactive += 1
            continue
        if key and key.lower() not in row_label(row).lower():
            continue
        entry = plan_row(row, today)
        if entry["deadline"] is None:
            no_deadline.append({"application": entry["application"], "status": entry["status"]})
            continue
        planned.append(entry)

    board = []
    for entry in planned:
        for milestone in entry["milestones"]:
            if horizon is not None and milestone["days_from_today"] > horizon:
                continue
            board.append({
                "due": milestone["due"],
                "days_from_today": milestone["days_from_today"],
                "overdue": milestone["overdue"],
                "due_soon": not milestone["overdue"] and milestone["days_from_today"] <= DUE_SOON_DAYS,
                "application": entry["application"],
                "deadline": entry["deadline"],
                "milestone": milestone["id"],
                "label": milestone["label"],
            })
    board.sort(key=lambda m: (m["due"], m["application"]))
    return {
        "today": today.isoformat(),
        "applications": len(planned),
        "skipped_inactive": inactive,
        "no_deadline": no_deadline,
        "overdue": [m for m in board if m["overdue"]],
        "board": board,
    }


def render(result: dict) -> str:
    lines = [f"Deadline board - {result['today']} ({result['applications']} active application(s))", ""]
    if not result["board"]:
        lines.append("  Nothing scheduled in the requested window.")
    current = None
    for item in result["board"]:
        if item["due"] != current:
            current = item["due"]
            days = item["days_from_today"]
            when = f"{abs(days)} day(s) {'ago' if days < 0 else 'from now'}" if days else "today"
            lines.append(f"{item['due']}  ({when})")
        mark = "!!" if item["overdue"] else ("* " if item["due_soon"] else "  ")
        lines.append(f"  {mark} {item['application']}")
        lines.append(f"       {item['label']}  [deadline {item['deadline']}]")
    if result["no_deadline"]:
        lines += ["", "No deadline recorded - nothing can be planned for these:"]
        lines += [f"  - {e['application']} ({e['status'] or 'no status'})" for e in result["no_deadline"]]
    if result["overdue"]:
        lines += ["", f"{len(result['overdue'])} milestone(s) already overdue."]
    return "\n".join(lines)


def _ics_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,").replace("\n", r"\n")


def _ics_fold(line: str) -> str:
    """Fold a content line to RFC 5545's 75-octet limit.

    The limit is in *octets*, not characters, so the fold has to be measured
    on the UTF-8 encoding and must never split a multi-byte character - and
    these summaries carry university names like "Wurzburg-Schweinfurt" with
    non-ASCII letters in them.

    Unfolded long lines are tolerated by most calendar clients and rejected
    by some, which is the worst kind of bug to ship in an export: it works
    when you test it and fails on the one machine that matters.
    """
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line
    out, rest, limit = [], encoded, 75
    while len(rest) > limit:
        cut = limit
        # Back off until the cut lands on a character boundary.
        while cut > 0 and (rest[cut] & 0xC0) == 0x80:
            cut -= 1
        out.append(rest[:cut].decode("utf-8"))
        rest = rest[cut:]
        limit = 74  # a continuation line spends one octet on its leading space
    out.append(rest.decode("utf-8"))
    return "\r\n ".join(out)


def to_ics(result: dict) -> str:
    """All-day VEVENTs, one per milestone, for import into any calendar.

    All-day rather than timed: a milestone is "this has to be done by today",
    not an appointment, and a timed event imports into whatever timezone the
    calendar guesses. DTEND is exclusive in RFC 5545, hence the +1 day.
    """
    stamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    out = ["BEGIN:VCALENDAR", "VERSION:2.0",
           "PRODID:-//school-scholarship-search//deadline_board//EN", "CALSCALE:GREGORIAN"]
    for index, item in enumerate(result["board"]):
        start = date.fromisoformat(item["due"])
        out += [
            "BEGIN:VEVENT",
            f"UID:{item['milestone']}-{index}-{item['due']}@school-scholarship-search",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{(start + timedelta(days=1)).strftime('%Y%m%d')}",
            f"SUMMARY:{_ics_escape(item['application'] + ' - ' + item['label'])}",
            f"DESCRIPTION:{_ics_escape('Application deadline ' + item['deadline'])}",
            "END:VEVENT",
        ]
    out.append("END:VCALENDAR")
    return "\r\n".join(_ics_fold(line) for line in out) + "\r\n"


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)  # absent on a StringIO under test
        if reconfigure:
            reconfigure(encoding="utf-8")


def main(argv=None) -> int:
    _force_utf8_output()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tracker", type=Path, default=TRACKER)
    ap.add_argument("--today", type=date.fromisoformat, default=date.today())
    ap.add_argument("--horizon", type=int, default=None, help="only milestones within N days")
    ap.add_argument("--key", help="substring filter over 'institution - program'")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ics", type=Path, help="also write an iCalendar file here")
    args = ap.parse_args(argv)

    result = build(read_tracker(args.tracker), args.today, args.horizon, args.key)
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else render(result))
    if args.ics:
        args.ics.parent.mkdir(parents=True, exist_ok=True)
        args.ics.write_text(to_ics(result), encoding="utf-8")
        print(f"\nsaved={args.ics}")
    return 2 if result["overdue"] else 0


if __name__ == "__main__":
    sys.exit(main())
