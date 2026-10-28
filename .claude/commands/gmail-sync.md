# /gmail-sync - Update Application Status from Email

Reads the Gmail connector, finds messages about tracked applications, and
proposes status updates.

**Read-only on your mailbox. Nothing is sent, replied to, labelled or
deleted.** Proposals go to the user; the user decides.

## Step 1 — Build the search

From `application_tracker.csv`, take every institution and funder with a
status that is not terminal. Search per sender domain and name rather than
with one broad query — admissions mail comes from `@slate.org`,
`@applyyourself.com`, `@uni-assist.de` and similar, not from the university's
own domain.

Bound it by date: nothing before the earliest `date` in the tracker.

## Step 2 — Classify, conservatively

| Signal | Proposed status |
|---|---|
| "we have received your application" | `under_review` |
| "invite you to an interview" | `interview_invited` |
| "pleased to offer", "conditional offer" | `offer_conditional` / `offer_unconditional` |
| "unable to offer", "unsuccessful" | `rejected` |
| "waiting list" | `waitlisted` |
| "scholarship awarded", "pleased to award" | `funding_awarded` |
| "unsuccessful in the scholarship competition" | `funding_rejected` |
| a missing-document request | `awaiting_documents` |

Where a message is ambiguous, propose nothing and show it to the user. A
wrong automatic status change is worse than no change — it can take an
application off the deadline board while it is still live.

## Step 3 — Extract the dates that have clocks on them

These matter more than the status:

- an **offer acceptance deadline** — short, and missed often;
- a **deposit deadline**;
- a **condition deadline** on a conditional offer;
- an **interview date and time zone** — confirm both cities are named;
- a **document request deadline**.

## Step 4 — Propose

Show each proposed change with the message subject, date and sender, and the
exact tracker edit. Apply only what the user approves.

Then re-run `python3 tools/deadline_board.py` and report what moved.

## Privacy

Message IDs and subjects are personal data. Anything cached goes in
`gmail_sync/`, which is gitignored. Never quote message bodies into a tracked
file.
