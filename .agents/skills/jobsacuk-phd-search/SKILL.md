---
name: jobsacuk-phd-search
version: 1.0.0
description: >
  Use this skill whenever the user is looking for a funded PhD studentship or
  a funded master's studentship in the UK, Ireland or Europe - even if they
  do not say "jobs.ac.uk". Also use it when they ask about UKRI stipend
  rates, home-vs-international fee status, doctoral training partnerships, or
  whether a studentship is open to international students. Trigger phrases
  include: funded phd, phd studentship, fully funded phd, phd uk, doctoral
  studentship, ukri stipend, dtp, cdt, research council funding, phd vacancy,
  phd position europe, international students phd funding, fees and stipend,
  self-funded phd, masters studentship, mphil funding, jobs.ac.uk.
context: fork
allowed-tools: Bash(bun run .agents/skills/jobsacuk-phd-search/cli/src/cli.ts *)
---

# jobs.ac.uk PhD Studentship Search

Searches [jobs.ac.uk](https://www.jobs.ac.uk) — the main board for UK academic
positions, and where most advertised UK doctoral studentships appear. It also
carries a steady stream of European positions (Aarhus, Delft, Max Planck).

**Postgraduate only.** The CLI reaches exactly two levels, `phd` and
`masters`, both of which are *funded studentships* rather than fee-paying
places. There is no undergraduate path.

## Why this portal

An advertised UK studentship usually comes with the money attached — fees plus
a tax-free UKRI-rate stipend — which makes it a completely different
proposition from applying to a taught master's and hunting for funding
afterwards. Two filters do most of the work:

- `--eligibility international-students` — the single most important filter
  here. A large share of UK studentships are restricted to home-fee students,
  and from Nigeria that restriction is absolute. This is the only way to see
  it before fetching the listing.
- `--funded` — drops listings that *say* they are self-funded.

## Commands

### Search

```bash
bun run .agents/skills/jobsacuk-phd-search/cli/src/cli.ts search [flags]
```

| Flag | Meaning |
|---|---|
| `--level phd\|masters` | default `phd` |
| `--query <text>` | keywords over title, description and supervisor |
| `--eligibility <facet>` | `international-students`, `eu-students`, `uk-students`, `self-funded-students` |
| `--discipline <slug>` | e.g. `computer-sciences`, `engineering-and-technology`; repeatable |
| `--location <text>` | region or city as jobs.ac.uk spells it |
| `--funded` | drop listings that state they are self-funded |
| `--max-pages <n>` | pages to walk, 25 results each (max 10) |
| `--limit <n>` | cap the rows returned |
| `--format json\|table\|plain` | default `json` |

```bash
# Funded AI/robotics PhDs open to international students
... search --query "machine learning" --eligibility international-students --funded --max-pages 3
```

### Detail

```bash
... detail --id DTK970
... detail --id "https://www.jobs.ac.uk/job/DTK970/phd-studentship-..."
```

Reads the page's schema.org JSON-LD where present and falls back to the
rendered markup. A URL on any other host is rejected, and a reference that is
not letters-then-digits is an argument error rather than a fetch and a 404.

## Three judgement calls worth knowing about

**`/search/phd` is a trap.** It looks like the PhD board and it silently
ignores `keywords`, returning project-coordinator and operations-manager
vacancies with a 200 and no error. The CLI uses `/search/?jobTypeFacet[]=phds`,
which is what the site's own form submits and what actually filters.

**`funded` has three values, not two.** `true` for a stated stipend or
studentship, `false` only where the listing says self-funded or unfunded, and
`null` where the line could not be read ("Competitive"). `--funded` drops only
the explicit `false`: UK studentships state stipends in free prose, and
discarding the unreadable ones would hide most of what the filter is for.

**`country` is often `null`, on purpose.** This is a UK board but not a
UK-only one. Defaulting an unrecognised location to "United Kingdom" filed a
Danish studentship as British — a wrong answer that survives into a visa plan.
Only an explicit signal names a country; `location` always carries the raw
string.

## Output contract

Every `search` row carries `award`, `provider`, `level`, `country`, `deadline`
and `url`, plus `kind`, `location`, `department`, `field`, `funding`,
`funded`, `posted`, `deadline_text` and `portal`.

`deadline` is ISO or `null`. jobs.ac.uk prints "10 Nov" with no year; a
day-month in the recent past keeps the current year so the sweep can expire
it, and anything further back rolls into next year (`GRACE_DAYS`).

## Errors

One JSON object on stderr, exit 1:
`{"error": "...", "code": "UNKNOWN_FLAG" | "BAD_ARG" | "MISSING_REQUIRED" | "API_ERROR" | "UNKNOWN_COMMAND"}`

## Reliability

jobs.ac.uk intermittently hangs on its 490 KB search page — two identical
requests a second apart, one returning in 2.7 s and the next timing out, was
reproducible while this was written. `fetchWithRetry` therefore retries
transport failures as well as 429/5xx, with exponential backoff.

## Dependencies

None at runtime.
