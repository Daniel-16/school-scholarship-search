# Application Forms

Portal forms ask for things no document covers, and they are where
applications are quietly lost.

## The rule

**Never submit a form answer the user has not seen.** Forms contain
declarations, certifications and funding questions with real consequences.
Draft every answer into `documents/applications/<key>/form_fields.txt`,
present them, and let the user paste them in. The workspace does not submit
applications.

## Fields that need care

**Degree classification and GPA.** State the actual figure and the actual
scale ("3.82 / 5.00, Second Class Upper Division"). Never convert to a
4.0 GPA yourself — the institution does that conversion, and a self-reported
conversion that disagrees with their evaluator looks like misrepresentation.

**Institution name.** Exactly as on the transcript. Portals match against
a database; a mismatch sends the application to manual review and can delay
it past a deadline.

**Dates of study.** Month and year, matching the transcript exactly.

**Referee details.** Institutional email only. A Gmail address in a
recommender field is rejected outright by many portals and is the single most
common reason a reference never gets counted. See `11-recommenders.md`.

**"How will you fund your studies?"** This is scored, not administrative. The
answer must be consistent with `tools/funding_model.py` and with anything
claimed in the statements. Name the scheme applied for, the personal or family
contribution, and the figure. Never "I will seek funding".

**"Have you previously applied / been refused a visa?"** Answer truthfully and
completely. A non-disclosure discovered later ends the application and can
carry a multi-year ban. If the honest answer is complicated, say so to the
user rather than drafting around it.

**Criminal record and academic misconduct declarations.** Never drafted. Flag
them for the user to complete personally.

**Short-answer boxes (100–300 words).** These are essays, not form fields.
Apply `03-writing-style.md`. Count the words.

## Character limits

Portal fields truncate silently. Where a limit is stated, count characters
including spaces, and come in 5% under. Where none is stated, assume 2000
characters and flag it.

## The supporting-document upload set

Most portals want:
- CV (PDF)
- Statement / personal statement (PDF)
- Transcript (PDF, sometimes one file per institution)
- Degree certificate
- English test report
- Passport data page
- Scholarship essays, where separate

Export with human filenames — `Daniel_Oloruntoba_CV.pdf`,
`Daniel_Oloruntoba_Statement_of_Purpose.pdf`. Portals display filenames to
reviewers, and `sop_tu_delft_msc_robotics.pdf` tells them you are running a
pipeline. Keep the set in `documents/applications/<key>/upload/`.

Check it before submitting:

```bash
python3 tools/docs_checklist.py check <key>
```

## Application fees and waivers

Fees run USD 50–150 at US institutions, often nil in Germany (though
uni-assist charges its own), and vary in the UK.

**Always ask about a waiver.** Many institutions waive fees for applicants
from low-income countries, for first-generation applicants, or on request to
the graduate coordinator, and most never advertise it. A short, polite email
to the admissions contact costs nothing and works more often than people
expect. Draft it when the fee is material.

A fee paid **to the institution through its own portal** is normal. A fee
demanded to *receive* an award is not — `tools/listing_guard.py` flags that
shape, and it should stop the application.

## Archive what was submitted

After submitting, write to `documents/applications/<key>/`:
- `listing.md` — the gated listing text and the guard verdict
- `form_fields.txt` — every answer as submitted
- `requirements.json` — the checklist
- `upload/` — the exact files uploaded

Interviews come months later and reference what you wrote. Reconstructing it
from memory is how a candidate contradicts their own application.
