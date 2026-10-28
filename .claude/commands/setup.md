# /setup - Onboarding

Fill in what the workspace needs from the user. Run once, then again whenever
something changes.

## What this is for

`01-applicant-profile.md` ships with the engineering record already filled in
and everything admissions-specific marked `[CONFIRM]`. This command resolves
those, because none of the workspace is useful without them: a shortlist built
without a funding ceiling is a list of programmes that may be unaffordable,
and a fit score without a CGPA is a guess.

## Step 1 — Show the state

```bash
grep -n "\[CONFIRM\]" .claude/skills/grad-application-assistant/01-applicant-profile.md
python3 tools/docs_checklist.py inventory
```

Present both: what is unknown about the applicant, and what is missing from
`documents/`.

## Step 2 — Ask, in this order

Ask in small batches with `AskUserQuestion`. Highest-leverage first, so a
user who stops halfway has still unblocked the most.

**Targets** — these change which programmes are even worth collecting:
1. Master's, PhD, or both?
2. Field, narrower than "AI" — what should the research interests paragraph
   say?
3. Which intake? (Autumn 2027 means deadlines from Dec 2026.)
4. Which countries, or "open"?

**Money** — these decide whether a shortlist is real:
5. Maximum you can self-fund, in USD, over the whole programme.
6. Fully funded only, or is a partial award workable?
7. Liquid funds available for proof of funds; can a sponsor's account be used?
8. Dependants relocating?

**Record** — these go on every form:
9. Exact CGPA and the scale.
10. Thesis supervisor's name and the thesis grade.
11. NYSC status.

**Tests:**
12. IELTS/TOEFL — taken? Score and date? If not, when can you sit it?
13. GRE — taken, or willing to?

**Referees:**
14. Who are the two or three, and do you have institutional addresses?

## Step 3 — Write it back immediately

Replace each `[CONFIRM]` in `01-applicant-profile.md` with the real value as
it is given. Do not batch this to the end of the conversation — a fact that
stays in chat is treated as unsupported by every later draft.

Where the user does not know something, leave the `[CONFIRM]` marker and say
so. A marker is honest; a guess is not.

## Step 4 — Scaffold

- `program_search/seen_programs.json` → `{"seen": {}}` if absent
- `application_tracker.csv` → header row if absent
- `funding/rates.json` → confirm it exists and ask the user to refresh the
  rates they care about
- `documents/` → already present; point at `documents/README.md`

## Step 5 — Tell them what to do next

A specific list, in order, with durations:

1. Drop files into `documents/` — name the categories that are empty.
2. Book the English test if there is no valid score (≈3 weeks end to end).
3. Order transcripts (4–6 weeks from a Nigerian university).
4. Approach referees.
5. Run `/discover`.

## Privacy

Everything collected here is personal data and is gitignored. Say so once.
Nothing is sent anywhere: the portal CLIs send only search terms, and
`tools/docs_checklist.py` reads file names, never file contents.
