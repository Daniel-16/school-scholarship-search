# /reset - Clear Personal Data

`$ARGUMENTS` names what to clear. **Never run without arguments**, and never
without confirming first.

## Confirm before deleting anything

Show exactly which files will be affected and how many rows or entries each
holds, then ask. Several of these are irrecoverable: a transcript PDF deleted
from `documents/` is gone, and `application_tracker.csv` is the only record
that an application was ever made.

Never delete without the user saying yes to that specific list.

## Targets

| Argument | Clears |
|---|---|
| `discovery` | `program_search/seen_programs.json` → `{"seen": {}}` |
| `tracker` | `application_tracker.csv` → header row only |
| `documents` | Everything under `documents/*/` except `.gitkeep` and the READMEs |
| `applications` | `documents/applications/*` only |
| `generated` | `cv/main_*.tex`, `statements/sop_*.tex`, `statements/essay_*.tex` and their build artefacts — never the `_example` files |
| `funding` | `funding/*.json` except `rates.json` |
| `reports` | `reports/`, `deadlines/`, `profile_gap/` |
| `profile` | Restore `[CONFIRM]` markers in `01-applicant-profile.md` |
| `all` | Everything above. Confirm twice. |

## Rules

- **Never delete `cv/main_example.tex`, `statements/sop_example.tex`,
  `statements/statement.cls` or `funding/rates.json`.** These are the
  templates and shared configuration, not personal data.
- Never touch `.claude/`, `.agents/`, `tools/` or `tests/`.
- `discovery` resets the file to `{"seen": {}}` rather than deleting it —
  a missing state file makes the next `/discover` fail rather than start
  fresh.
- Offer a backup first. A `cp -r documents documents.backup` costs nothing
  and `documents` is the only target that cannot be rebuilt.

## After

Report what was cleared, with counts, and what the user should run next —
usually `/setup` after `profile`, `/discover` after `discovery`.
