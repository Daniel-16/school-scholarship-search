# /profile-gap - What Is Actually Blocking Admission

Invoke the `profile-gap` skill and follow it.

`$ARGUMENTS` may narrow it to a level ("phd") or a destination.

## What this is not

Not a study plan. Learning another framework does not move a graduate
application, and three months spent on one is three months not spent on
something that does. The ranked output is usually short, and usually more
administrative than intellectual — which is counter-intuitive and worth
saying out loud.

## Order

1. Gather: the profile files, every ranked entry's `gaps` in
   `program_search/seen_programs.json`, any outcomes in the tracker, and
   `python3 tools/docs_checklist.py inventory`.
2. Classify every gap as **blocking**, **decisive**, **marginal** or
   **immovable**.
3. Rank by leverage per week of effort.
4. Write `profile_gap/report-YYYY-MM-DD.md`.

## The report must include

- the four classes, with what falls in each;
- ranked actions, each with a duration and what it unblocks;
- which are already behind schedule for the next intake, cross-checked
  against `python3 tools/deadline_board.py`;
- **what not to spend time on, and why.** This section is as valuable as the
  first one, and it is the one that gets left out.

## Honesty rule

Immovable things — a degree classification — get no effort at all. Say so.
Effort goes to evidence that postdates them.
