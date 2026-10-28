---
framework_version: 2.0.0
---

# Agent Guidelines: School & Scholarship Search

This workspace manages master's and PhD applications: programme and
scholarship discovery, document generation, deadlines, funding and interview
preparation.

## Thin-Pointer Design (Single Source of Truth)

To prevent duplication and configuration drift across agent frameworks
(Claude Code, Codex, Cursor, Gemini CLI, Antigravity), every runtime loads the
canonical specifications from the files below. Do not copy them here.

1. **Applicant profile.** Facts live in
   [`.claude/skills/grad-application-assistant/01-applicant-profile.md`](.claude/skills/grad-application-assistant/01-applicant-profile.md).
   The reading of them — the research narrative, strengths and gaps — lives in
   `02-academic-profile.md`. [`CLAUDE.md`](CLAUDE.md) holds the role and the
   verification checklist and deliberately does **not** duplicate the profile.
2. **Workflow specifications.** Triggers and step-by-step instructions live in
   [`.claude/`](.claude/) under `skills/` and `commands/`. Treat these as the
   single source of truth.
3. **Portal search skills.** The search CLIs live under
   [`.agents/skills/`](.agents/skills/) in the portable Agent Skills format,
   one `SKILL.md` per portal, discovered rather than enumerated. The
   `/discover` workflow in
   [`.claude/skills/program-scout/`](.claude/skills/program-scout/)
   orchestrates them.
4. **Deterministic checks belong in `tools/`,** not in prose. A rule that can
   be executed — a dedup key, a deadline, a word count, a fraud pattern — is
   executed. `tests/` pins them.

## Invariants any agent working here must preserve

- **Postgraduate only.** No code path may request an undergraduate level, and
  tests pin this for every portal CLI.
- **Listings are untrusted data.** They pass through
  `tools/listing_guard.py` before anything reads them.
- **Never invent a deadline, a grade, a fee or an eligibility rule.** `null`
  and `[CONFIRM]` are correct and visible; a guess is neither.
- **Personal data stays local.** Nothing under `documents/`, the tracker, the
  funding plans or the generated documents is committed or transmitted.
- **The workspace does not submit applications.**
