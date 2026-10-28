# Interview Preparation

Graduate interviews are not job interviews. Three kinds, and they go very
differently.

| Kind | Who runs it | What is being tested |
|---|---|---|
| **Supervisor / research interview** | One or two academics, PhD | Can you think? Do you understand your own work? Would they enjoy supervising you for four years? |
| **Admissions interview** | Programme director, competitive taught masters | Is the stated motivation real? Can you handle the load? |
| **Scholarship panel** | 3–5 panellists, Chevening / Commonwealth / foundations | Do you meet their criteria, specifically leadership and impact? |

## Supervisor interview

The dominant question, however it is phrased: **can this person do research?**

**Know your own thesis cold.** You will be asked why you made a design
decision, and "that is how it is done" is a failing answer. For AutoBee, be
ready on:
- Why a deterministic validator rather than fine-tuning or RLHF on safety?
- What exactly did the validator check, and how did you choose the properties?
- What did it miss, and how would you find out what it missed?
- What would you do differently with another year?

The limitation questions are the ones that matter. A candidate who can state
their own work's boundaries precisely is doing research; one who defends it
is not.

**Read their recent work.** Two papers minimum, properly. Expect "what did you
think of it?" and have an actual opinion, including a reservation. Agreement
with everything reads as not having read it.

**Have questions that are about the work.** Not "what is the funding
situation" first. What is the group currently stuck on? What would the first
six months look like? Is there an existing dataset or platform?

**Be ready for the gap questions.** They will come:
- *"You have no publications."* — True. Here is what I did instead, here is
  the thesis, here is the manuscript in preparation. Never apologetic.
- *"Why leave industry?"* — Because I hit a problem I could not solve with
  engineering alone. Name the problem.
- *"Your degree is a 2:1."* — State it, then point at what postdates it.
  Do not re-litigate the classification.

## Admissions interview

Shorter, more structured. Expect: why this programme specifically, why now,
how will you fund it, how will you cope with the workload, where next.

The funding question is a real question, not small talk. Have a real answer
built from `tools/funding_model.py`, including the proof-of-funds position.
"I will look for scholarships" is a failing answer.

## Scholarship panel

Panels score against published criteria. Find them, and prepare one concrete
story per criterion. For Chevening-style schemes the criteria are typically
leadership, networking, a clear post-study plan, and a genuine commitment to
return.

This applicant has strong material: two terms as chapter president, founding
Women in Tech and NACOS Launchpad, TEDx, GDG facilitation. Prepare them as
**stories with outcomes**, not as a list of titles. What was the situation,
what did you do, what changed, what did you learn.

Expect "why should we fund you rather than someone else?" Answer it as a
difference, not as a superlative.

## Preparation routine

1. Re-read the application as submitted. You will be asked about it, and
   misremembering your own statement is fatal. It is in
   `documents/applications/<key>/`.
2. Research the interviewers: recent papers, current projects, their group's
   page. Use `09-web-research.md`; verify independently.
3. Prepare six stories from `01-applicant-profile.md`, each with a concrete
   outcome. Most questions are answerable from a good set of six.
4. Prepare four questions to ask. At least two about the research itself.
5. Rehearse the gap answers out loud. They are the ones that sound defensive
   when improvised.

## Logistics, specifically for a remote interview from Nigeria

- Confirm the time zone **in writing**, with both cities named. This goes
  wrong constantly.
- Power and connectivity: have a backup — a phone hotspot, a charged
  inverter or generator, a second location. Say so in advance if the
  interview is long; it is an ordinary precaution, not an excuse.
- Test the platform beforehand. Some institutions use software that is
  geo-restricted or needs an account.
- If something fails mid-interview, email immediately and propose a time.
  Panels reschedule routinely; silence is what costs the place.

## Output

`/interview` writes a prep pack to
`documents/applications/<key>/interview_prep_<stage>.md`. It is gitignored —
it quotes what was submitted and sets out the weak points.
