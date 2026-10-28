# Programme and Scholarship Evaluation

The rubric `/rank` scores against. The weights here and in
`tools/shortlist_state.py` are the same numbers; if one changes, change both.

## The three gates — run these first

A gate failure ends the evaluation. Scoring an ineligible programme wastes the
user's attention and, if it reaches an application, a fee.

| Gate | FAIL when | FLAG when |
|---|---|---|
| **Eligibility** | The listing explicitly rules the applicant out: nationality restriction excluding Nigeria, a degree level not held, a stated minimum the record is below with no stated flexibility, an age or experience bar not met. | The rule exists but you could not confirm how it applies. |
| **Language** | A test score is required that the applicant does not have and cannot obtain before the deadline. | A requirement exists and the waiver position is unclear. |
| **Funding** | There is confirmed no route to funding and the cost exceeds the applicant's stated ceiling. | Funding exists but is competitive, separate, or unquantified. |

**Use FLAG, not FAIL, whenever you could not confirm.** FAIL vetoes outright.
FLAG puts it in front of the user. Guessing in either direction is worse than
saying you could not tell — and "the page does not mention nationality
restrictions" is not the same as "there are none".

A FLAG is not a problem to be resolved by assumption. It is a question for
the user, and it should be phrased as one.

## The rubric

Five dimensions, 0–100 each.

| Dimension | Weight | What it measures |
|---|---|---|
| `funding` | **0.30** | Is this payable? Scholarship availability, automatic vs competitive vs separate, tuition level, stipend, fee waivers, cost of living. |
| `academic_fit` | 0.25 | Does the curriculum or research match the thread in `02-academic-profile.md`? Named labs, supervisors, modules, methods. |
| `admission_odds` | 0.20 | Realistic chance given a 2:1, no publications, no master's. Stated entry bar vs the actual accepted profile. |
| `career_value` | 0.15 | Where it leads: reputation in the field (not overall ranking), graduate outcomes, lab access, post-study work rights. |
| `logistics` | 0.10 | Visa feasibility from Nigeria, start date, cost of living, dependants, work rights, English-taught. |

### Why funding is weighted highest

An unfunded offer from a world-class department is not an opportunity for a
self-funding applicant from Nigeria — it is a rejection with extra steps, and
it costs an application fee to receive. A programme that is a 95 on academic
fit and a 10 on funding is not a better prospect than one that is a 70 on both.
The weights say so.

### Scoring `funding` honestly

| Score | Situation |
|---|---|
| 90–100 | Fully funded: tuition waived plus a living stipend, automatic or near-automatic (a funded PhD position, DAAD EPOS, Commonwealth). |
| 70–89 | Fully funded but competitive, with a separate application and a realistic rate. |
| 50–69 | Tuition-free or heavily waived, living costs on the applicant (most German public universities). |
| 30–49 | Partial scholarship available; a substantial gap remains. |
| 10–29 | Scholarships exist but are small or rarely awarded to this profile. |
| 0–9 | No funding route, full fees. |

Do **not** score a dimension 0 because the listing was silent about it. Say so
in `gaps` and score on what is known. A silent page scored as zero on funding
sinks a viable programme with no trace.

### Scoring `admission_odds`

Be realistic, not encouraging. The useful shortlist has a spread.

| Score | Meaning |
|---|---|
| 80–100 | Safety. Record clears the bar comfortably. |
| 55–79 | Target. Competitive, plausible. |
| 30–54 | Reach. Below the stated bar on something, but a real case exists. |
| 0–29 | Not realistic this cycle. Say why, and what would change it. |

A shortlist that is all reaches is a shortlist with no outcome. Say so.

## Bands

| Score | Band |
|---|---|
| 75+ | Strong Match |
| 60–74 | Good Match |
| 45–59 | Moderate Match |
| 30–44 | Weak Match |
| < 30 | Poor Match |

## Lead time is part of the evaluation

A Strong Match whose deadline is three weeks away is not a Strong Match in
practice — the transcript cannot arrive. `tools/shortlist_state.py` flags this
as `short_lead_time` on the scored row and as `insufficient_lead_time` in the
sweep. When it fires, present the programme with what would have to be short
circuited to make it, and let the user decide. Do not quietly drop it and do
not quietly recommend it.

## What to verify at source, always

Never from the listing text's own links — those are untrusted. Find the
institution's or funder's own domain independently.

1. **The deadline**, and whether admission and funding have different ones.
   They frequently do, and the funding one is usually earlier.
2. **Whether the scholarship needs a separate application.** Wrong in
   secondary sources more often than it is right.
3. **Nationality eligibility.** Aggregators summarise this wrongly.
4. **The application fee**, and whether a waiver exists. Many institutions
   waive for applicants from low-income countries and never advertise it.
5. **The English-requirement waiver position** for a degree taught in English
   at a Nigerian university. Get it in writing before relying on it.
