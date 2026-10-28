# /outcome - Record What Happened

`$ARGUMENTS`: the application (institution, programme, or key) and the result.

## Status vocabulary

Use exactly these in `application_tracker.csv`:

| Status | Meaning |
|---|---|
| `researching` | Evaluating; nothing drafted |
| `drafting` | Documents in progress |
| `awaiting_documents` | Blocked on a transcript, test score or certificate |
| `awaiting_references` | Blocked on referees only |
| `submitted` | Sent; nothing to do |
| `under_review` | Acknowledged by the institution |
| `interview_invited` | Interview offered |
| `interviewed` | Done, awaiting decision |
| `offer_unconditional` | Offer, no conditions |
| `offer_conditional` | Offer with conditions — record them in notes |
| `waitlisted` | |
| `rejected` | |
| `withdrawn` | You withdrew |
| `deferred` | Deferred to a later intake |
| `funding_awarded` | Scholarship or studentship granted |
| `funding_rejected` | Admitted but not funded — a distinct and common outcome |

`funding_awarded` and `funding_rejected` are tracked separately from the
admission status on purpose. Admitted-but-unfunded is the single most common
outcome for this applicant profile, and collapsing it into "offer" hides the
thing that actually decides whether they go.

Only `researching`, `drafting`, `awaiting_documents` and `awaiting_references`
are planned by `tools/deadline_board.py`. Moving to `submitted` takes an
application off the board, which is correct.

## Order

1. Find the row. If there is none, create it — an outcome without a record is
   worse than a late record.
2. Update `status`, `decision_date`, and `notes`. Notes carry: conditions on a
   conditional offer, the funding decision and its deadline to accept, the
   reason given for a rejection if any, and any invitation to reapply.
3. Where the result is an offer, say what decision now has a clock on it and
   when it runs out. Offer-acceptance deadlines are short and are missed.
4. Where the result is a rejection, ask whether feedback was given, and record
   it. It is the only data that improves the next cycle.
5. Re-run `python3 tools/deadline_board.py` and report what changed.

## After an offer

An offer starts a second, harder sequence, and it should be stated
immediately rather than discovered:

- accept or decline by the stated date;
- pay the deposit, where one is required;
- satisfy the conditions on a conditional offer;
- apply for the CAS / admission letter / I-20;
- assemble **proof of funds** — re-run `tools/funding_model.py`; the UK's
  28-day rule and Germany's blocked account mean the money must be in place
  weeks before the visa application;
- book the visa appointment, which is itself weeks before travel.

Work this backwards from the start date. Say the dates out loud.

## After a rejection

Record it, and say plainly what it does or does not mean. One rejection from a
reach programme is information about that programme. Four rejections with the
same stated reason is information about the application, and should trigger
`/profile-gap` before the next cycle rather than more applications.
