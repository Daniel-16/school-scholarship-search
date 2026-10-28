# /deadlines - The Backward-Planned Board

```bash
python3 tools/deadline_board.py [--horizon 60] [--key TEXT] [--json]
python3 tools/deadline_board.py --ics deadlines/applications.ics
```

`$ARGUMENTS` may carry a horizon in days or a substring to filter on.

## What it does

A submission deadline is the last milestone, not the first. The board expands
each tracked deadline into the milestones that have to land before it:

| Milestone | Days before | Why that long |
|---|---|---|
| Book language test | 70 | Slot, sit, and report turnaround are three separate waits |
| Order transcripts | 45 | Issued by the home university and sent abroad — the slowest artefact in the whole application |
| Ask referees | 30 | Academics are slow; a referee who declines at day 10 must be replaceable |
| Statement first draft | 21 | Needs a gap before the re-read |
| Scholarship essays, research proposal | 14 | |
| Statement final | 7 | Proofread, word count checked, compiled |
| Assemble and pay | 3 | |
| Submit | 0 | |

Milestones merge across every application and sort by date, so "what do I do
this week" is the top of one list rather than a mental join across eight
programmes.

Exit 2 when anything is overdue — a scheduled run can alert on it.

## Overriding a milestone

Defaults are defaults. Put an override in the tracker's `notes` field:

- `lead:transcripts=60` — move it to 60 days before
- `lead:language_test=0` — drop it (a valid score is already in hand)

Chosen over extra columns because the tracker is edited by hand in a
spreadsheet, and a column empty on 90% of rows gets deleted.

## Report

1. **Overdue milestones**, first, with how late each is and whether the
   application is still recoverable. Be specific about what recovery means —
   an expedited transcript, a scanned copy accepted provisionally, a referee
   given five days instead of thirty.
2. This week, then this month.
3. Applications with **no deadline recorded** — nothing can be planned for
   these, and that is worth saying rather than leaving them invisible.
4. Offer the `.ics` export. Importing the board into a real calendar is
   usually the single most useful thing this command does.

## Honesty rule

If a deadline is genuinely unreachable — the transcript cannot arrive, the
test cannot be sat — say so plainly and say what the realistic next intake is.
Drafting into an impossible deadline wastes a fee and a month.
