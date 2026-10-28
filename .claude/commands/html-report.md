# /html-report - Application Dashboard

Build a single self-contained HTML page from the workspace state and save it
to `reports/applications-YYYY-MM-DD.html` (gitignored).

## Sources

```bash
python3 tools/deadline_board.py --json
python3 tools/docs_checklist.py inventory --json
cat application_tracker.csv
cat program_search/seen_programs.json
```

## What the page shows

In this order — the order is the point, because it matches what actually
costs an applicant a cycle:

1. **Overdue and imminent milestones.** Top of the page, impossible to miss.
   Overdue in red, due within 14 days in amber.
2. **The deadline board**, chronological, grouped by date.
3. **Applications**, one row each: institution, programme, level, country,
   status, fit score, funding status, deadline, days remaining.
4. **Document inventory** — what is present, what is missing, what expires
   before a deadline it is needed for.
5. **Funding summary**, where plans exist: total gap and proof-of-funds
   position per application.
6. **The shortlist** — ranked but not yet applied to, with bands and gates.

## Rules

- **Single file, no external requests.** Inline the CSS; no CDN, no web font,
  no analytics. The page holds personal data and must not phone anywhere.
- No JavaScript that fetches. Sorting and filtering in-page is fine.
- Works at phone width.
- Dark and light both legible.
- Every date shown as ISO plus "in N days", because the relative figure is
  what gets acted on.

Tell the user the path when it is written, and that it is gitignored.
