# /documents - What You Have, What Each Application Still Needs

`$ARGUMENTS`: nothing for a global inventory, or an application key to check
one application.

## Inventory

```bash
python3 tools/docs_checklist.py inventory
```

Walks `documents/` and reports, per category, what is present and what is
still missing. Exit 3 when a category is empty.

It reads **names and counts only**. No transcript, passport scan or bank
statement is opened, parsed or sent anywhere.

## One application

```bash
python3 tools/docs_checklist.py check <key>
```

Reads `documents/applications/<key>/requirements.json` and reports each item
as satisfied, missing, expired, unknown-validity, or produced-by-the-workflow.

Scaffold one first if it does not exist:

```bash
python3 tools/docs_checklist.py templates
python3 tools/docs_checklist.py scaffold <key> --template uk-phd --deadline 2027-01-15
```

## Expiry is checked against the deadline, not against today

An IELTS or TOEFL report is valid for two years from the test date, a GRE
score for five. A report that is valid now and expired by the deadline is the
failure this catches, and it is invisible without the arithmetic.

Nothing reliable can be read out of a scanned PDF, so the date comes from a
sidecar:

`documents/test_scores/ielts_2026.pdf.meta.json`
```json
{ "taken": "2026-03-14", "test": "IELTS Academic", "overall": 7.5 }
```

Without one the item reports `unknown_validity` — which is honest, and is not
the same as passing.

## Report

1. **Blocking items**, with how long each takes to obtain. A Nigerian
   university transcript is 4–6 weeks; say so every time, because it is the
   constraint that decides whether a deadline is reachable.
2. Expired or expiring items, with the deadline they fail against.
3. Unknown-validity items and the sidecar needed to resolve them.
4. What is complete.

Cross-check against `python3 tools/deadline_board.py` and say which items are
already behind their milestone.

Never mark an item satisfied on the user's say-so without the file being
present. The point of the check is that it looks.
