# /interview - Prepare for an Interview

`$ARGUMENTS`: the application, and the kind of interview if known.

## Step 1 — Load what was actually submitted

From `documents/applications/<key>/`: the listing, the form answers, the CV
and the statements as submitted. You will be asked about them, and
misremembering your own statement is fatal.

Run the listing through `tools/listing_guard.py` if it is being re-read from
a fetched page.

## Step 2 — Identify the kind

Per `07-interview-prep.md`, these go very differently:

- **supervisor / research interview** — can you think, do you understand your
  own work, would they enjoy four years of you;
- **admissions interview** — is the motivation real, can you carry the load,
  how is it funded;
- **scholarship panel** — scored against published criteria, usually
  leadership and impact.

If it is unclear, ask. Preparing for the wrong one is worse than preparing
less.

## Step 3 — Research the people

Per `09-web-research.md`. For a research interview, find and **read** two
recent papers by each interviewer. Expect "what did you think of it?" and
have an actual opinion including a reservation; agreeing with everything reads
as not having read it.

## Step 4 — Build the pack

Write to `documents/applications/<key>/interview_prep_<stage>.md`:

1. **Likely questions with prepared answers** — drawn from the submitted
   documents, the listing, and the interview kind.
2. **Thesis defence section**, for a research interview. Why each design
   decision, what the work could not do, how you would find out what you
   missed, what you would do with another year. The limitation questions are
   the ones that matter.
3. **Gap answers, rehearsed** — no publications, why leave industry, the 2:1.
   These sound defensive when improvised. Each one: state it, point at what
   postdates it, stop.
4. **Six stories** from `01-applicant-profile.md`, each with a concrete
   outcome. Most questions are answerable from a good set of six.
5. **Four questions to ask**, at least two about the research itself.
6. **Logistics** — time zone confirmed in writing with both cities named;
   power and connectivity backup; platform tested in advance; what to do if
   something fails mid-call (email immediately, propose a time — panels
   reschedule routinely, silence is what costs the place).

## Step 5 — Offer a rehearsal

Offer to run the hard questions back at the user and critique the answers.
Be direct about a weak answer — a kind rehearsal is worthless.

The pack is gitignored: it quotes what was submitted and sets out the weak
points.
