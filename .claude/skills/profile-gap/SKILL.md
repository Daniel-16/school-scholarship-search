---
name: profile-gap
description: >
  Compares tracked programmes and scholarships against the applicant profile
  to find what is actually blocking admission, and produces a prioritised plan
  to close it before the next cycle. Triggers on: /profile-gap, what should I
  do before applying, am I competitive, strengthen my application, admission
  gaps, what am I missing.
allowed-tools: Read, Glob, Grep, WebFetch, WebSearch, Write
---

# Profile Gap

Not a study plan. A plan for the things that **change an admissions decision**.

The distinction matters: learning another framework does not move a graduate
application, and three months spent on one is three months not spent on the
things that do. The ranked output of this skill is almost always short.

## Step 1 — Gather

- `01-applicant-profile.md` and `02-academic-profile.md`
- `program_search/seen_programs.json` — every `ranked` entry's `gaps`
- `application_tracker.csv` — outcomes, where any exist
- `python3 tools/docs_checklist.py inventory`

## Step 2 — Classify every gap

| Class | Meaning | Action |
|---|---|---|
| **Blocking** | Cannot apply without it | Fix first, always |
| **Decisive** | Can apply; it is why you would be rejected | Fix before the cycle if time allows |
| **Marginal** | Would help; will not change an outcome on its own | Only if the first two are clear |
| **Immovable** | Cannot be changed | Position around it, do not chase it |

Work it honestly. For this applicant, as the profile stands:

- **Blocking:** no English test score on file; no confirmed CGPA; no referee
  list. Each one stops an application from being submittable.
- **Decisive:** no publications (for PhD applications specifically); only one
  likely academic referee.
- **Marginal:** more open-source work, more certifications. The profile
  already has plenty.
- **Immovable:** the 2:1 classification. Never spend effort here — spend it
  on evidence that postdates it.

## Step 3 — Rank by leverage per week

For each gap: how much does closing it move an admission decision, divided by
how long it takes. The highest-leverage items for a profile like this are
usually administrative rather than intellectual, which is counter-intuitive
and worth saying out loud.

Worked example of the top of such a list:

1. **Book and sit IELTS** — ~3 weeks end to end, unblocks nearly every
   application. Highest leverage available, and it is paperwork.
2. **Order transcripts now** — 4–6 weeks from a Nigerian university. Blocking,
   slow, and entirely outside your control once requested.
3. **Approach the thesis supervisor and one other academic** — blocking for
   PhD applications and the thing most likely to be left too late.
4. **Turn the AutoBee thesis into a workshop paper or arXiv preprint** — 4–8
   weeks, and the single largest change available to PhD odds. Converts "no
   publications" into "one preprint, under review".
5. **Email three target supervisors** — weeks, free, and a UK or EU PhD
   application without it usually fails regardless of the rest.

## Step 4 — Write the report

`profile_gap/report-YYYY-MM-DD.md` (gitignored):

- the four classes, with what falls in each and why;
- the ranked actions, each with an estimated duration and what it unblocks;
- which actions are already behind schedule for the next intake, cross-checked
  against `python3 tools/deadline_board.py`;
- what explicitly **not** to spend time on, and why. This section is as
  valuable as the first.

## The standing judgement

For an applicant with four years of production engineering, the gap is almost
never technical skill. It is research evidence, academic references, and
paperwork with long lead times. Say so plainly rather than producing a
comfortable list of courses to take.
