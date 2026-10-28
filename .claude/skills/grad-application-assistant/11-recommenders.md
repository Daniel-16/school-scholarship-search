# Referees and Recommendation Letters

The part of the application you do not control, started too late by almost
everyone, and the most common cause of an otherwise complete application
missing a deadline.

## Start 30 days out, minimum

`tools/deadline_board.py` places the referee milestone at **30 days** before
the deadline. That is not padding:

- academics are slow, and term time is worse;
- some referees want a draft of your statement before they write;
- portals email the referee a link, which lands in spam or is ignored;
- a referee who declines at day 10 leaves no time to find another.

Ask early enough that one declining is survivable.

## Who to ask

Most programmes want **two or three**, with at least one academic. For this
applicant that is the real constraint.

| Referee | Strength | Use for |
|---|---|---|
| **B.Sc. thesis supervisor** | The only person who can speak to research capability. Essential and non-negotiable for any PhD application. | Everything |
| **A second Bingham academic** who taught a relevant course and knows the work | Second academic voice | PhD, research MSc |
| **MathWallet manager or senior colleague** | Seniority, scale, independence, technical depth | Taught MSc, professional programmes, scholarships |
| **Planetbase co-founder** | Leadership, zero-to-one, team of five | Scholarship panels specifically |

**Three academic referees is the US PhD norm.** If only one academic referee
is available, that is a genuine weakness for US PhD applications and should
be weighed in `admission_odds` rather than discovered in February.

**Never** a family member, a friend, or a peer with no supervisory
relationship. Committees recognise these immediately and discount the whole
set.

## Institutional email addresses only

A referee's Gmail or Yahoo address in a recommender field is rejected outright
by many portals, and it is the single most common reason a reference never
gets counted. If a referee has no institutional address, ask them to submit
from their department's address or to supply a letter on headed paper with
verifiable contact details.

Store it here:

`documents/references/referees.json`

```json
[
  {
    "name": "Prof. Jane Example",
    "title": "Professor of Computer Science",
    "institution": "Bingham University",
    "email": "jane.example@binghamuni.edu.ng",
    "relationship": "Supervised my B.Sc. thesis (AutoBee)",
    "known_since": "2024",
    "strongest_on": "research design, independence, ROS 2 work",
    "preferred_notice_days": 21
  }
]
```

## The recommender packet

Send this with the ask, every time. A referee writing from memory produces a
generic letter; a referee with a packet produces a specific one, and the
difference is visible to a committee.

1. **The ask itself** — programme, institution, deadline, how the letter is
   submitted (portal link or email), and when they will receive the link.
2. **Your current CV** (PDF).
3. **Your statement**, draft is fine. Referees frequently mirror its themes,
   which is exactly what you want.
4. **The programme page**, and what it selects for.
5. **A short reminder of your work together** — the project, what you did,
   what came of it, with dates. Not a draft of their letter: a reminder of the
   facts. This is the item that most improves the letter.
6. **What you would be glad to see emphasised**, phrased as a suggestion.
   "The programme weights research independence heavily, if that is something
   you are able to speak to."

Never write the letter for them. Where a referee asks you to draft it — which
happens — tell the user plainly: many institutions treat a self-drafted letter
as misconduct, and the writing style gives it away.

## Running the ask

- **One email per referee**, named and specific. Never a group email.
- **List every programme at once** if you know them. Referees strongly prefer
  one request covering six programmes to six requests.
- **Give the deadline as a week before the real one.**
- **Follow up at 14 days and again at 7.** This is normal and expected; the
  referee is not offended, they are busy.
- **Check the portal** for whether the letter has been received. Do not
  assume. Portals show reference status, and an unsubmitted reference is the
  most common reason a "complete" application is incomplete.
- **Thank them, and tell them the outcome.** You will need them again.

## Tracking

Milestones come from `tools/deadline_board.py`. Where a referee has told you
how much notice they want, record it in the tracker's notes as
`lead:referees=<days>` and the board will plan to it.
