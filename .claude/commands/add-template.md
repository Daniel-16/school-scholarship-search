# /add-template - Register a Custom CV or Statement Template

`$ARGUMENTS`: a path to a template, or a description of the one wanted.

Use this when a programme or funder mandates a format the stock templates do
not produce — a funder's own CV form, a Europass CV, a required
two-column layout, or a Typst/Word pipeline the user already has.

## Step 1 — Establish the build

Determine and record:

- the **engine and exact command** (`lualatex`, `xelatex`, `typst compile`,
  something else);
- the **build directory** it must run from;
- every file it needs beside the source (a `.cls`, a fonts folder, a logo);
- what it produces, and where.

Build it once, unmodified, before anything else. A template that does not
compile as supplied will not compile after being edited.

## Step 2 — Check it against the constraints that matter

- **Fonts embed and the text layer extracts.** Run
  `python3 tools/verify_pdf.py <pdf> --min-chars 100` and `pdffonts`.
- **Reading order matches the visual order.** Single-column templates are
  safe; a two-column CV is where this breaks, and a portal that parses the
  upload will read it scrambled.
- **The contact details appear as literal text**, not only inside an icon or
  a hyperlink. Check the extraction, not the page.
- **Page and word limits** are still measurable from `pdftotext` output.

## Step 3 — Register it

Write an `ACTIVE-TEMPLATE` block into the matching reference file —
`05-cv-templates.md` for a CV, `06-statement-templates.md` for a statement:

```
<!-- ACTIVE-TEMPLATE
name: <name>
kind: cv | statement
source: <path to the template source>
build_dir: <directory to run the command from>
command: <exact command, with <key> as the placeholder>
output: <path to the produced PDF>
notes: <what it must not be edited into, and any constraint it imposes>
-->
```

Both files carry a placeholder block saying `none`. Replace it. While a block
names a template, it **overrides** the stock instructions in that file, and
`/apply` must compile with its command.

## Step 4 — Verify end to end

Generate one real document with it — not the example — compile, run
`verify_pdf.py` and `verify_layout.py`, and **read the PDF**. Then confirm
`/apply` picks up the override by reading the reference file back.

## Rules

- Never delete the stock template. A custom template is an addition; the user
  will need the default again for the next programme.
- The gitignore is already extension-agnostic on the ignore side
  (`cv/main_*.*`), so a `.typ` output is ignored as reliably as a `.tex` one.
  The negations stay `.tex`-only on purpose — a wildcard would re-include
  build artefacts.
- If the template cannot meet a constraint in Step 2, say so and say what
  breaks. Registering a template that extracts as gibberish is worse than not
  having it.
