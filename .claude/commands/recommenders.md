# /recommenders - Plan and Run the Reference Requests

`$ARGUMENTS`: an application key, or nothing to plan across every open
application.

## Step 1 — State

Read `documents/references/referees.json` (format in
`documents/README.md`). If it does not exist, build it with the user — this
is usually the real blocker, not the letters.

Then:

```bash
python3 tools/deadline_board.py --json
```

and pull out every `referees` milestone with its date.

## Step 2 — Check the set against each application

Per `11-recommenders.md`. Most programmes want two or three referees with at
least one academic; US PhD programmes want three academics.

Report honestly where the set is short. For this applicant the likely finding
is that only the thesis supervisor is a genuine academic referee, which is a
real weakness for US PhD applications and should be weighed in
`admission_odds` — not discovered in February.

Flag any referee without an **institutional** email address. A Gmail address
in a recommender field is rejected outright by many portals and is the single
most common reason a reference never gets counted.

## Step 3 — Draft the asks

One email per referee, named and specific, never a group email. List **every**
programme at once — referees strongly prefer one request covering six
programmes to six separate requests. Give the deadline as a week before the
real one.

Each ask goes out with the packet:

1. programme, institution, deadline, and how the letter is submitted;
2. the current CV;
3. the statement, draft is fine — referees often mirror its themes, which is
   what you want;
4. the programme page and what it selects for;
5. **a short factual reminder of the work together** — the project, what the
   applicant did, what came of it, with dates. This is the item that most
   improves the letter;
6. what the applicant would be glad to see emphasised, phrased as a
   suggestion rather than an instruction.

Write each to `documents/applications/<key>/recommender_packet_<name>.md`.

## Step 4 — Never draft the letter

If a referee asks the applicant to write it themselves — which happens — say
plainly that many institutions treat a self-drafted letter as misconduct and
that the writing style gives it away. Offer the factual reminder in item 5
instead, which is what the referee actually needs.

## Step 5 — Follow up

Report what is due: who to ask today, who to chase at 14 days and again at 7,
and which portals should be checked for whether the letter has arrived. Do not
assume a submitted reference — portals show the status, and an unsubmitted
reference is the most common reason a "complete" application is incomplete.
