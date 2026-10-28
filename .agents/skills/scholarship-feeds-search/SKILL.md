---
name: scholarship-feeds-search
version: 1.0.0
description: >
  Use this skill whenever the user is looking for scholarships, fellowships or
  funding for a master's or PhD - especially fully funded awards open to
  applicants from Nigeria, Africa or the Global South - and no specific
  country or university has been named yet. Also use it to sweep for newly
  announced calls. Trigger phrases include: scholarship, fully funded
  scholarship, scholarships for nigerians, scholarships for africans, study
  abroad funding, fellowship, grant for masters, grant for phd, chevening,
  commonwealth scholarship, erasmus mundus, mastercard foundation scholars,
  daad epos, swedish institute scholarship, mext, fulbright, new scholarships,
  scholarship deadlines, funding opportunities, bursary, tuition waiver.
context: fork
allowed-tools: Bash(bun run .agents/skills/scholarship-feeds-search/cli/src/cli.ts *)
---

# Scholarship Feeds Search

Aggregates the scholarship announcement feeds that applicants from Africa
actually read, and filters them down to master's and doctoral funding.

```bash
bun run .agents/skills/scholarship-feeds-search/cli/src/cli.ts sources
```

| Source | Good for |
|---|---|
| `scholars4dev` | development-focused awards for applicants from developing countries |
| `opportunitydesk` | broad; filter hard, much of it is not degree funding |
| `scholarshipregion` | heavy coverage of calls open to African applicants |
| `opportunitiesforafricans` | Africa-specific, including in-country and in-region schemes |

All four are WordPress sites, which is why this works without a scraper:
`?s=<query>&feed=rss2` is a real search feed, so the query runs on *their*
index instead of being filtered out of a generic "latest 10" feed.

## Read this before using anything it returns

**These are aggregators, not funders.** Every item is a third party's
republication of somebody else's call. In this corpus that routinely means:

- deadlines that passed two intakes ago, with the post never updated;
- eligibility summarised wrongly, which is the expensive kind of wrong;
- outright scam reprints, which is why `tools/listing_guard.py` has a
  scholarship-fraud scanner and why `/discover` runs every item through it.

So every row carries `requires_verification: true`, and the table output says
so on each one. These are **leads**, not shortlist entries. Nothing from here
reaches the tracker until the funder's own page has confirmed the award, the
eligibility and the deadline.

## Commands

### Search

```bash
... search [flags]
```

| Flag | Meaning |
|---|---|
| `--query <text>` | search terms; omit to sweep each feed's latest items |
| `--level masters\|phd\|any-postgraduate` | default `any-postgraduate` |
| `--source <id>` | limit to one feed; repeatable |
| `--since <YYYY-MM-DD>` | drop items published earlier |
| `--with-deadline` | only items with a parseable deadline |
| `--calls-only` | drop items that look like blog articles |
| `--limit <n>` | default 40 |
| `--format json\|table\|plain` | default `json` |

```bash
# Fully funded master's calls, articles filtered out
... search --query "fully funded masters scholarship" --level masters --calls-only

# What appeared this week
... search --since 2026-10-21 --calls-only
```

### Sources

```bash
... sources
```

## Three judgement calls worth knowing about

**Undergraduate is detected in order to be dropped.** It is the bulk of what
these feeds carry. An item detected as undergraduate-only never appears;
a combined "undergraduate and master's" call does.

**An undetectable level is kept, not dropped.** These feeds are prose and many
genuine master's calls never use the word. A silent drop would hide them with
no trace, so the uncertainty is surfaced as `level: []` and left to `/rank`.

**`--calls-only` is opt-in.** Alongside the calls, these blogs publish
listicles ("Top 10 UK Universities Offering Scholarships"), how-to posts and
success stories, and all three match every scholarship keyword there is. The
filter looks for what a *call* has — a stated deadline, an explicit
open-for-applications phrase, a funding claim — and `call_signals` on each row
shows the evidence. It is opt-in because the cost of it being wrong is a
missed award.

## Output contract

Every `search` row carries `award`, `provider` (always `null` — see below),
`kind`, `level`, `country`, `deadline`, `url`, plus `deadline_text`,
`published`, `source`, `call_signals`, `summary`, `portal` and
`requires_verification`.

`provider` is never guessed. The aggregator is not the funder, and the funder
is rarely stated in parseable form; a wrong funder name in the archive is
worse than a missing one, so `/rank` resolves it from the real page.

`deadline` requires an **explicit year**. A scholarship announcement is
routinely republished for an intake two years out, so a year-less date is left
unparsed with the raw sentence in `deadline_text`. `dd/mm/yyyy` is accepted
only above the 12th, where it cannot be confused with `mm/dd/yyyy`.

`country` is read from the title first and the body only as a fallback.

## Failure behaviour

One feed being down is a degraded run, not a failed one: the others still
return, and `failed_sources` names what was missed. Exit 1 only when *every*
requested feed failed.

## Dependencies

None at runtime.
