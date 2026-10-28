# /rank - Score Discovered Listings into a Shortlist

Turn `status: "new"` entries in `program_search/seen_programs.json` into a
ranked shortlist, using `tools/shortlist_state.py` so the state file never
enters the conversation.

`$ARGUMENTS` may contain `--all` (include every non-skipped status), a focus
substring, or a limit.

## Step 1 — Select candidates

```bash
python3 tools/shortlist_state.py candidates [--all] [--focus TEXT] [--limit N]
```

Returns only the fields a scorer needs. Do not read the state file yourself.

## Step 2 — Score in batches

Dispatch `listing-scorer` agents with the candidates inline, together with
the rubric from `04-program-evaluation.md`. Each agent fetches the listing,
runs `python3 tools/listing_guard.py` over it, and scores it; none of them
writes state.

Each result carries the three gates — **eligibility**, **language** and
**funding** — alongside the scores. Any one of them FAILing vetoes the
listing.

Every result needs all five scores — `funding`, `academic_fit`,
`admission_odds`, `career_value`, `logistics` — and the three gates. A
dimension the listing is silent about is **not a zero**; it is a gap, noted,
scored on what is known.

## Step 3 — Write results back

```bash
python3 tools/shortlist_state.py apply --results results.json
```

The tool computes the weighted score, assigns the band, handles the deadline
and retry rules, and prints `ranked` / `vetoed` / `expired` / `unreachable` /
`gave_up` / `errors`. Exit 1 means something did not write — fix it, do not
report a partial run as complete.

## Step 4 — Sweep

```bash
python3 tools/shortlist_state.py sweep --write --exclude <keys scored this run>
```

Retires passed deadlines without fetching anything, and reports
`insufficient_lead_time`.

## Step 5 — Report

In this order:

1. **Vetoed**, with which of the three gates failed and why. A veto is useful
   information, not noise — it stops a fee being spent.
2. **Ranked**, highest first: award, provider, level, country, score, band,
   deadline, top strength, top gap.
3. **Short lead time** — scored entries whose deadline is inside 45 days.
   Name what would have to be short-circuited (an in-hand test score, a
   scanned transcript, referees already briefed) and let the user decide. Do
   not quietly drop them and do not quietly recommend them.
4. **Flagged gates** — every FLAG, phrased as the question it actually is.
   These are for the user to answer, not for you to resolve by assumption.
5. Expired, unreachable and gave-up counts.

## Honesty rules

- A shortlist that is all reaches has no outcome. If `admission_odds` is below
  55 across the board, say so and say what a target-band programme would look
  like.
- If `funding_gate` is FLAG or FAIL on everything, the shortlist is not a
  shortlist. Say that too.
- Never inflate a score to make a list look better.
