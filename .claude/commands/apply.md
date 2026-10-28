# /apply - Build a Complete Application

`$ARGUMENTS` is a programme or scholarship: a URL, a state key, or pasted
text.

Follow these steps **in order**. Do not skip any.

**Standing rule — write confirmed facts back to the profile.** If the user
confirms, corrects or supplies a fact not already in
`01-applicant-profile.md`, write it there in the same turn. Rule One of the
skill is deliberately strict and cannot tell a fabrication from a real fact
the user mentioned once in chat, so an unwritten fact **will be stripped from
a later draft as unsupported**, silently.

## Step 0 — Fetch and gate

Dispatch `listing-fetcher` with the URL. It fetches the page and runs
`python3 tools/listing_guard.py`, returning the cleaned text and the gate's
verdict line.

**If any fraud family fired, stop and report it before anything else.** Quote
the evidence. Do not continue until the user says to.

For a scholarship from an aggregator, this is also where the funder's own page
is found — independently, never from a link inside the listing text.

## Step 1 — Evaluate fit, and present it

Against `04-program-evaluation.md`. Run the three gates first — eligibility,
language, funding — then the five rubric dimensions. Present:

- the eligibility gate, the language gate and the funding gate, with any FLAG
  phrased as the question it actually is;
- the score and band;
- the real entry bar versus this applicant's record, honestly;
- the funding position, with figures;
- the lead-time position: run `tools/deadline_board.py` and say whether the
  document run is still possible.

**Stop here and let the user decide.** Do not begin drafting on a Weak Match,
a failed gate, or a deadline whose transcript milestone has already passed,
without them saying so.

## Step 2 — Scaffold

Derive the key: `python3 tools/program_key.py --provider "..." --award "..."`.

```bash
python3 tools/docs_checklist.py scaffold <key> --template <set> --deadline YYYY-MM-DD
python3 tools/docs_checklist.py check <key>
```

Report blocking documents now. A missing transcript is a four-to-six week
problem, and discovering it after the statement is written wastes the
statement.

Then draft:
- `cv/main_<key>.tex` — from `cv/main_example.tex`, per `05-cv-templates.md`
- `statements/sop_<key>.tex` — the **right document type** per
  `06-statement-templates.md`
- `statements/essay_<key>_<n>.tex` — one per scholarship question

## Step 3 — Review

Dispatch `application-reviewer` with the drafts and the listing inline. It
researches the department or funder independently and critiques as a committee
member would.

Apply its edits where they are right. **Verify its research claims yourself**
before any of them reaches a document — a reviewer agent's research is input,
not fact.

Run the factual grounding audit: every claim must trace to
`01-applicant-profile.md`, `cv/main_example.tex`, or something the user
confirmed. Remove anything that does not. Do not soften it — remove it.

## Step 4 — Compile and verify

```bash
cd cv && lualatex -interaction=nonstopmode -halt-on-error main_<key>.tex
cd ../statements && xelatex -interaction=nonstopmode -halt-on-error sop_<key>.tex
```

Then the full checklist in `CLAUDE.md`. Non-negotiable items:

- CV is **exactly 2 pages**; `tools/verify_layout.py` reports clean
- statement is within its page or word limit, counted from `pdftotext` output
- fonts are Carlito only (`pdffonts`)
- **read both PDFs** with the Read tool

Iterate until they pass. "It looks right in the `.tex`" is not acceptable.

## Step 5 — Forms

Draft every portal answer into
`documents/applications/<key>/form_fields.txt` per `08-application-forms.md`.
Present them. **Never submit anything.** Declarations, visa-history questions
and misconduct questions are not drafted at all — flag them for the user.

## Step 6 — Archive and record

Write to `documents/applications/<key>/`:
- `listing.md` — gated text plus the guard verdict (counts only, not excerpts)
- `form_fields.txt`
- `requirements.json`
- `upload/` — the exact files, human-named
  (`Daniel_Oloruntoba_CV.pdf`, `Daniel_Oloruntoba_Statement_of_Purpose.pdf`)

Append a row to `application_tracker.csv`:

```
date,institution,program,level,kind,country,channel,status,contact_person,fit_score,funding_status,deadline,decision_date,notes,cv_file,statement_file,source
```

Status starts at `drafting` or `awaiting_documents`. Then:

```bash
python3 tools/deadline_board.py --key "<institution>"
```

and report the milestones that are now live.

## Step 7 — Hand over

Tell the user exactly what is left for them to do: which documents to supply,
which referees to approach today, what to paste where, and the next milestone
with its date.
