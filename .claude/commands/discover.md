# /discover - Sweep Every Portal for New Programmes and Scholarships

Invoke the `program-scout` skill and follow it exactly.

`$ARGUMENTS`, when given, narrows the sweep: a field ("robotics"), a level
("phd"), a country ("germany"), or a portal id. With no arguments, sweep
everything in `search-queries.md`.

## What this command is not

It does not score, rank, or judge fit. It collects and deduplicates. Keeping
collection separate from scoring is what makes a sweep cheap enough to run
weekly and a scoring run careful enough to trust.

## Order

1. Load `program_search/seen_programs.json` (create `{"seen": {}}` if absent).
2. Search every installed portal — discover them from
   `.agents/skills/*/SKILL.md` rather than assuming the shipped three.
3. Gate everything that came from an aggregator feed through
   `tools/listing_guard.py`. Surface any `fraud_signals` with their quotes.
4. Key every candidate with `tools/program_key.py`. Skip keys already seen.
5. Append new entries with `status: "new"`.
6. Scan for degraded portals — a successful call returning nothing useful.
7. Report.

## Report

- New entries grouped by level and country, each with its deadline.
- **Anything the gate flagged**, first, with the quoted evidence.
- Degraded or unreachable portals, named.
- Entries whose deadline is inside 45 days — these need a decision now, not
  at the deadline. Say which document milestone is already impossible.

End by pointing at `/rank`.

## Rules

- Never invent a deadline. `null` is correct and visible; a guess is neither.
- Never rewrite an existing entry's `first_seen`.
- Never delete an entry. `/rank` and `/outcome` own status transitions.
- An undergraduate listing is a bug in a portal, not an entry. Report it.
