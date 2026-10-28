# /expand - Build the Profile from Documents and Online Presence

`$ARGUMENTS`: a path, a URL, or nothing to use everything available.

Use this after `/setup` or whenever the user has material the profile does not
yet reflect — a CV, a thesis, a LinkedIn export, a portfolio.

## Step 1 — Read what is there

- `documents/cv/` — any existing CV
- `documents/research/` — thesis, papers, writing samples
- `documents/portfolio/` — project write-ups, `links.md`
- any URL the user supplies (per `09-web-research.md`)

## Step 2 — Extract facts, not impressions

For each document, pull out what is **checkable**: dates, titles,
institutions, metrics, technologies, outcomes, grades, award names.

Metrics in particular. "Improved performance" is worth nothing in a
statement; "reduced API response times by 20%" is the sentence that proves a
claim, and it is usually sitting in an old CV nobody has read in two years.

## Step 3 — Confirm before writing

Present what you found, grouped, and ask the user to confirm or correct each
group. Do not write an unconfirmed fact into the profile — the profile is the
audit source, and a wrong fact there propagates into every future document
with no way to tell it apart from a real one.

For anything from the user's own writing, check it is still accurate. A CV
written two years ago describes a role that has since changed.

## Step 4 — Write it back

Update `01-applicant-profile.md` (the facts) and `02-academic-profile.md`
(the reading of them) in the same turn.

Where something resolves a `[CONFIRM]`, replace the marker. Where it
contradicts an existing entry, raise the contradiction with the user rather
than picking one.

## Step 5 — Report

- what was added, by section;
- what was contradictory and needs a decision;
- what is still `[CONFIRM]`;
- anything found that **should not** go in the profile, and why — an
  unverifiable claim, a metric the user cannot substantiate, a project that
  was never finished. Leaving these out is the point of the step.
