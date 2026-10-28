---
name: daad-programmes-search
version: 1.0.0
description: >
  Use this skill whenever the user is looking for a master's or doctoral
  programme in Germany, or for English-taught or tuition-free postgraduate
  study in Europe where Germany is a plausible destination - even if they
  do not say "DAAD". Also use it for questions about German universities'
  entry requirements, semester contributions, application periods, or
  whether a German programme charges tuition. Trigger phrases include:
  daad, study in germany, masters in germany, phd in germany, german
  university, english-taught masters, tuition-free masters, no tuition fees,
  international programmes germany, uni-assist, german graduate school,
  doctoral programme germany, msc germany, promotion germany, studienkolleg,
  semester contribution, german universities for international students.
context: fork
allowed-tools: Bash(bun run .agents/skills/daad-programmes-search/cli/src/cli.ts *)
---

# DAAD Programmes Search

Searches the [DAAD "International Programmes in Germany"](https://www2.daad.de/deutschland/studienangebote/international-programmes/en/)
database — the official catalogue of degree programmes German universities
offer to international students, maintained by the German Academic Exchange
Service.

**Master's and doctoral study only.** The CLI has no undergraduate level: DAAD's
Bachelor's code is unreachable by construction, not merely absent from the
defaults (`tests/search.test.ts` pins this).

## Why this portal is first among the three

For an applicant who needs funding, Germany is structurally the strongest
destination in the catalogue, and this database is the only one of the three
that answers the funding question *in the search result itself*:

- public universities charge **no tuition** for most programmes, including for
  non-EU students — the result rows carry the real figure, so "no tuition fees"
  is read off the record rather than assumed;
- the semester contribution (typically €150–350, usually including a transport
  pass) is the actual cost, and the detail record states it;
- `--with-scholarship` filters to programmes DAAD itself records a funding
  option for.

What it will *not* tell you is whether **you** are eligible, or whether the
deadline shown is the university's or uni-assist's. Those go through `/rank`
and a fetch of the programme's own page.

## Commands

### Search

```bash
bun run .agents/skills/daad-programmes-search/cli/src/cli.ts search [flags]
```

| Flag | Meaning |
|---|---|
| `--level masters\|phd` | required level; `phd` covers both standalone doctoral programmes and structured graduate schools |
| `--query <text>` | free text over programme names and subjects |
| `--subject <code>` | DAAD subject-group code; repeatable, comma-separated accepted |
| `--language english\|german\|mixed` | language of instruction |
| `--tuition-free` | only programmes with no tuition fees |
| `--with-scholarship` | only programmes with a DAAD-recorded scholarship option |
| `--limit <n>` | 1–100, default 25 |
| `--offset <n>` | paging |
| `--format json\|table\|plain` | default `json` |

```bash
# English-taught, tuition-free master's in AI
... search --level masters --query "artificial intelligence" --language english --tuition-free

# Doctoral programmes with a funding option
... search --level phd --with-scholarship --limit 50
```

### Detail

```bash
... detail --id 7852
... detail --id "https://www2.daad.de/.../en/detail/7852/"
```

Returns degree, location, language, duration, tuition, semester contribution,
cost of living, funding, academic admission requirements, English and German
language requirements, application period, and the raw `fields` map.

A URL on any other host is rejected. The archive records where a listing came
from, and a matching path elsewhere would be stored under a DAAD provenance it
never had.

## Output contract

Every `search` row carries `award`, `provider`, `level`, `country`, `deadline`
and `url` — the fields `/discover` needs to key, dedupe and rank a listing —
plus `kind`, `city`, `field`, `languages`, `duration`, `tuition`, `funding`,
`deadline_text` and `portal`.

`deadline` is ISO or `null`. DAAD writes deadlines as prose ("15 October –
15 December", "Register by 31 May 2027 + 3 more"); the earliest resolvable
date wins, and a date with no year resolves to `null` with the raw string kept
in `deadline_text`. **A guessed date on a deadline board is worse than a hole.**

## Errors

Failures print one JSON object on stderr and exit 1:
`{"error": "...", "code": "UNKNOWN_FLAG" | "BAD_ARG" | "MISSING_REQUIRED" | "API_ERROR" | "UNKNOWN_COMMAND"}`

An unrecognised flag is always an error. A silently discarded filter does not
fail — it returns a larger result set that looks like a successful search.

## Dependencies

None at runtime. `bun run` works on a fresh clone with no install step.
