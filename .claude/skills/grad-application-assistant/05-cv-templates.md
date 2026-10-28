# Academic CV

## The template

`cv/main_example.tex` is the **master copy**: everything the applicant can
truthfully claim. `/apply` never edits it. It copies it to `cv/main_<key>.tex`
and cuts the copy down for one programme.

- Class: `moderncv`, `banking` style, blue.
- Font: **Carlito only** (metric-compatible Calibri clone). No Lato, Raleway
  or Latin Modern.
- Engine: **lualatex**. `pdflatex` often fails on modern MiKTeX with
  `fontawesome5` font-expansion errors.
- Length: **exactly 2 pages.** Not 1, not 3.

```bash
cd cv && lualatex -interaction=nonstopmode -halt-on-error main_<key>.tex
```

If a custom template has been registered with `/add-template`, compile with
its declared command instead — see the `ACTIVE-TEMPLATE` block below if one
is present.

## Section order, and why it differs from a résumé

An academic CV is not a résumé with more entries. The reader is deciding
whether you can do research, so research comes before employment:

1. **Research Interests** — three or four lines, rewritten for every
   application. This is the first thing read and the only part most readers
   finish. It must name the problem, not the field.
2. **Education** — with the thesis title, the supervisor, and what the thesis
   actually did. Degree classification stated plainly.
3. **Research Experience and Projects** — the thesis and anything with a
   research shape. For this applicant, AutoBee and Alris.
4. **Professional Experience** — reframed toward the research thread where it
   honestly supports it. The MathWallet agent CLI is a verification problem,
   and saying so is accurate, not spin.
5. **Additional Projects**
6. **Technical Skills** — grouped, with robotics and AI broken out rather
   than buried in one list.
7. **Awards and Leadership**
8. **Publications** — present even when empty. "None to date" is honest and
   expected; omitting the section reads as hiding it.
9. **Teaching, Outreach and Service** — weighted heavily by development
   scholarships.
10. **References** — "Available on request", unless the programme asks for
    details, in which case use `documents/references/referees.json`.

Reorder for the target: a research-led PhD application can move Publications
and Research Experience above Education; a professional MSc can move
Professional Experience up.

## Tailoring rules

- **Rewrite the Research Interests block every time.** A generic one wastes
  the most valuable space on the document.
- **Cut, do not compress.** Dropping a whole weak entry beats shrinking six
  strong ones into unreadable density.
- **Keep the thesis entry in full, always.** It is the research evidence.
- **Never add a skill, tool or claim that is not in
  `01-applicant-profile.md`.** If the programme wants something absent, the
  gap is handled in the statement, not invented on the CV.

## Layout failures, and the fixes

The most common failure is an **orphaned `\cventry`**: a job or education
title at the bottom of a page with its bullets on the next. A `\cventry`
renders as a tabular and is one unbreakable block, so when it does not fit the
whole thing moves — or its header strands.

- Put `\needspace{5\baselineskip}` before every `\cventry`. The template
  already does.
- Use `\enlargethispage{2-3\baselineskip}` to rescue a trailing section that
  just barely spills.
- Never fix a page with a negative `\vspace` that pushes text into the page
  number band.

Check it rather than eyeballing it:

```bash
python3 tools/verify_layout.py cv/main_<key>.pdf
```

It reports orphaned entries, mid-page holes left by an ejected entry, pages
that end early, a final page that is mostly empty, and footer collisions.

## Verification

```bash
python3 tools/verify_pdf.py cv/main_<key>.pdf --pages 2 --min-chars 100 \
  --contains "Oloruntoba" --contains "iamdanieltoba@gmail.com"
python3 tools/verify_layout.py cv/main_<key>.pdf
```

Then **read the PDF** with the Read tool. "It looks fine in the `.tex`" is not
acceptable: LaTeX page-break decisions are not predictable from the source.

### The name-extraction trap

moderncv's banking title separates first and last name with a kern that every
text extractor drops — the text layer read `DanielOloruntoba`, so a search of
the file for the surname found nothing. The template inserts a thin space
(`\name{Daniel}{\,Oloruntoba}`) which costs nothing visually and fixes it.
Keep it.

### On `--ascii-dates`

`verify_pdf.py --ascii-dates` fails a document whose date ranges use an
en-dash. That check exists for **job** applications parsed by an ATS such as
Workday, which splits ranges on U+002D and drops the date entirely.

**It is not part of the graduate checklist.** En-dashed ranges (`2022–2026`)
are correct academic typography, and graduate portals — Slate,
ApplyYourself, uni-assist — require education history to be typed into form
fields rather than parsed out of the CV. Run it only if a specific programme
states that it machine-parses uploaded CVs.

## What goes to the institution

Export as `Daniel_Oloruntoba_CV.pdf`. Portals routinely display the filename
to reviewers, and `main_tu_delft_msc_robotics.pdf` tells them you are running
a pipeline.

<!-- ACTIVE-TEMPLATE: none. /add-template writes a block here naming the
     registered template, its build directory and its compile command. When
     one is present it overrides the moderncv instructions above. -->
