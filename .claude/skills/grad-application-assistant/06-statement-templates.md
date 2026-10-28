# Statements, Essays and Proposals

Every piece of prose an application asks for, what each one actually is, and
how to build it.

## The template

`statements/statement.cls` covers all six document types.
`statements/sop_example.tex` is the worked reference.

```latex
\documentclass[12pt,single]{statement}   % 11pt|12pt, single|onehalf|double, numbered
\applicant{Daniel Oloruntoba}
\programme{MSc Artificial Intelligence --- University of Example}
\statementkind{Statement of Purpose}
\wordlimit{1000 words}
\begin{document}
\statementtitle
...
\end{document}
```

Compile with **xelatex** (the class requires `fontspec`).

```bash
cd statements && xelatex -interaction=nonstopmode -halt-on-error sop_<key>.tex
```

Output file names: `statements/sop_<key>.tex`,
`statements/essay_<key>_<n>.tex`, `statements/proposal_<key>.tex`,
`statements/motivation_<key>.tex`.

### Font warning, do not undo

The class tries **Carlito before Calibri**, which looks backwards and is not.
`\IfFontExistsTF{Calibri}` answers yes when *any* Calibri face is installed,
and a bold-only partial install — common on Linux — silently set an entire
statement in bold. It compiled, it passed the page check, and it would have
been uploaded. Carlito is metric-identical and ships complete.

## The six document types

They are not interchangeable, and submitting the wrong one is visible
immediately.

| Document | Who asks | What it is |
|---|---|---|
| **Statement of Purpose** | US, Canada, most PhD | Your *research* case. What problem, what evidence you can work on it, why here, what next. Largely academic. |
| **Personal Statement** | UK taught masters; sometimes US as a *second* essay | Your *motivation and trajectory*. More latitude for background and circumstance. |
| **Motivation Letter** | Europe, Germany, Nordics | Short, often one page, addressed to a committee. Closer to a cover letter: why this programme, why you, what you bring. |
| **Research Proposal** | UK/EU PhD without an advertised project | A real proposal: question, background, method, feasibility, timeline. 1500–3000 words. |
| **Scholarship Essay** | Chevening, Commonwealth, DAAD, foundations | An **answer to a specific question**, to a specific word count. Not a repurposed SOP. |
| **Diversity / Personal History Statement** | US | How your background shaped your path and what you will bring to the community. Separate from the SOP; do not duplicate it. |

**A US SOP submitted to a UK MSc reads wrong, and the reverse reads thin.**
Check which is being asked for before drafting.

## Structure: Statement of Purpose

Six movements. The example file is annotated against these.

1. **The hook — a specific technical problem.** One only this applicant could
   write. Never "I have always been passionate about". For this applicant the
   natural opening is the AutoBee safety layer, because it is concrete, it is
   his, and it states a research problem in two sentences.
2. **What was built, and what it showed — including the limit.** Naming what
   your own work could not do is the strongest research signal in the
   document. It is also the bridge to why you need the programme.
3. **The thread.** The same problem recurring across the record. Three
   systems, three actuators, one unsolved question. This converts a scattered
   industry CV into a research trajectory, honestly.
4. **Why this programme.** Named people, named work, named modules or
   facilities. Never the ranking, never "world-renowned". If you cannot fill
   this paragraph with specifics, you have not researched the department
   enough to apply to it.
5. **What comes after.** Concrete. For a development-focused funder this
   paragraph carries real weight and must address return and impact directly.
6. **The close.** Short. Not a summary of the preceding five paragraphs.

## Structure: Research Proposal

1. **Title and research question** — one sentence, falsifiable.
2. **Background** — what is known, with citations, and the specific gap.
3. **Research question and objectives** — three or four, each testable.
4. **Methodology** — what you would actually do. The section supervisors read
   most carefully, because it reveals whether you know how research is done.
5. **Expected contribution** — and its limits.
6. **Feasibility and timeline** — by year. Be conservative; an over-ambitious
   timeline reads as inexperience.
7. **Fit with the group** — why this supervisor, what of theirs you build on.
8. **References** — real, recent, and actually read.

## Structure: Scholarship Essay

**Answer the question asked.** Chevening asks four distinct questions with
separate word counts; an applicant who submits four variations of one essay is
scored down on all four.

Pattern per answer: situation → what you did → result → what it shows about
the criterion they are scoring.

For development-focused schemes, state explicitly: the problem in your
country, your connection to it, what the study enables, what you will do on
return. Vagueness here is the most common reason these are rejected.

## Word limits are hard limits

Over the limit, a statement is truncated on upload or rejected.

```bash
cd statements && xelatex sop_<key>.tex
pdftotext -layout sop_<key>.pdf sop_<key>.txt
wc -w sop_<key>.txt
```

Count the **rendered text**, never the source file — the source carries
comments and LaTeX markup. Target 95–100% of the limit; well under reads as
having little to say.

Subtract the title block from the count if the portal counts only the body.
When in doubt, be under.

## Verification

- [ ] Compiles with xelatex, no errors in the log
- [ ] Page count matches what was asked for
- [ ] Word count within the limit, measured from `pdftotext` output
- [ ] Fonts are Carlito only (`pdffonts` to confirm)
- [ ] The document type matches what the programme asked for
- [ ] Paragraph 4 names actual people, groups or modules
- [ ] Every factual claim traces to `01-applicant-profile.md`
- [ ] No banned construction from `03-writing-style.md`
- [ ] No placeholder text left in (`[Programme-specific paragraph...]`)
- [ ] Spelling convention matches the destination
- [ ] **Read the compiled PDF** with the Read tool before presenting it
