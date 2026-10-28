# Academic Profile — the research narrative

`01-applicant-profile.md` holds the facts. This file holds the *reading* of
them: what story the record tells an admissions committee, where it is
strong, where it is thin, and how to handle the thin parts without lying.

## The honest shape of this candidacy

A strong **engineer** with a genuine, specific research artefact, applying
from outside the academic pipeline.

What that means in practice: the application will be read against two very
different comparison sets depending on the programme, and the same CV
performs very differently in each.

| Programme type | How this profile reads |
|---|---|
| Taught MSc in AI/CS at a research university | **Strong.** Four years of production engineering is well above the typical applicant, and the thesis shows research capability. The 2:1 is the main friction. |
| Professional / industry-facing MSc | **Very strong.** This is the target audience. |
| Direct-entry PhD, UK or Europe | **Viable but uphill.** No publications, no master's, a 2:1. Needs a supervisor who wants the engineering depth. |
| Direct-entry PhD, top-tier US | **Weak without a master's first.** US CS PhD admissions select heavily on publications and research references. |
| Development-focused scholarships (DAAD EPOS, Commonwealth, Chevening) | **Strong.** Leadership, outreach and a clear return-home impact story are what these score on, and this profile has all three. |

Say this to the user plainly when it is relevant. An applicant who sends five
US PhD applications on this profile loses five fees and a cycle.

## The research thread

There is a real one, and it is not "AI" — that is too broad to be credible.
It is:

> **Natural-language control of physical and digital systems, with
> deterministic safety layers between the model and the actuator.**

Three pieces of evidence, which is unusually coherent:

1. **AutoBee** — an LLM plans a drone's task; a deterministic validation layer
   sits between the plan and the flight controller and refuses unsafe
   commands. This is the thesis, and it is squarely a current research
   problem: LLM-driven agents acting on the world without verified bounds.
2. **Alris** — the same structure in software. An agent drives a real browser
   through Playwright under a constrained action interface.
3. **MathWallet's agent CLI** — the same structure again, where the actuator
   is an irreversible financial transaction. This is the most
   consequence-bearing version of the problem.

This maps onto live research areas with established groups: LLM agent safety,
grounded language for robotics, formal/runtime verification of learned
policies, human-robot interaction, tool-use and agentic evaluation.

Use this thread. Do not claim it was a planned research programme — it was
not — but do point out that the same problem recurs across the work, because
it genuinely does, and committees reward a candidate who can see the shape of
their own record.

## Strengths to lead with

- **Systems that ran in production, at scale.** 2M+ users, 10,000+ daily
  transactions. Most applicants in a CS graduate pool have coursework.
- **Breadth with depth in the right place.** Rust and C++ next to Python and
  ROS 2 is a credible robotics/systems profile, not a web-developer one.
- **Zero-to-one record.** Founding engineer, YC pitch, led a team of five.
  Reads as independence, which is the trait PhD supervisors select for.
- **Leadership and outreach that is documented, not claimed.** Two terms as
  chapter president, founded two initiatives, TEDx, GDG facilitator.
- **The safety layer.** Caring about what happens when the model is wrong is
  a research instinct, and it is rarer than engineering skill.

## Gaps, and how to handle each

**No publications.** The real one. Do not disguise it.
- For a taught MSc: it is not expected. Ignore it.
- For a PhD: address it by *demonstrating* research capability instead — the
  thesis, its method, what it found, what it could not resolve. A supervisor
  who can see you formulate a problem will forgive the absence of a paper.
- Consider: a workshop paper or arXiv preprint from the AutoBee thesis before
  the next cycle is the single highest-leverage thing available. Raise it.

**2:1 rather than a First.** Below the stated bar at some programmes.
- Never apologise for it in a statement. It reads as weakness and draws the
  reader's eye to it.
- Counter with evidence that postdates it: production seniority, the thesis,
  the open-source work. A degree classification is four years old by the time
  it is read.
- Where a programme states a First, check whether it also accepts "a 2:1 with
  relevant professional experience" — many do, and it is usually in the
  international-equivalency page rather than the entry requirements.

**Short tenures.** Several roles under a year.
- True and visible. Frame as startup and contract work, which it was, and
  which is normal in that sector.
- The MathWallet role is 20 months at senior level; let it carry the weight.

**Degree completed alongside full-time work.** Often read as a negative
(divided attention) when it is the opposite.
- State it once, factually, where a form offers the space. It explains the
  classification and demonstrates exactly the load-bearing capacity a
  graduate programme demands.

**No academic referees beyond the supervisor.** Likely. See
`11-recommenders.md` — this needs solving early, not in deadline week.

## Supervisor fit — for research applications

A UK or European PhD application without prior supervisor contact usually
fails. The email is a research artefact, not a formality:

- Reference **two specific papers** by that supervisor and what you take from
  them. Not their general area.
- State what you would want to work on and why your existing work is the
  reason you can.
- Attach the CV. Keep the email under 250 words.
- Say whether you are seeking funding, and which scheme.

Never send the same email to two people in one group.
