---
name: program-scout
description: >
  Finds new master's and PhD programmes and scholarship calls matching the
  applicant profile, via the installed portal CLIs (DAAD, jobs.ac.uk,
  scholarship feeds, and any portal added with /add-portal). Deduplicates
  across runs. Triggers on: /discover, find programmes, find scholarships,
  search programmes, new scholarships, programme search, scholarship search,
  what's open, new calls, funding search.
allowed-tools: Read, Glob, Grep, WebFetch, WebSearch, Edit, Write, Bash(python3 tools/program_key.py:*), Bash(python tools/program_key.py:*)
---

# Program Scout

Sweeps every installed portal, drops what has already been seen, and appends
the rest to `program_search/seen_programs.json` for `/rank` to score.

**It does not score and it does not judge fit.** It collects. Keeping the two
apart is what lets a sweep be cheap and a scoring run be careful.

## Step 1 — Load state

```bash
cat program_search/seen_programs.json
```

Shape: `{"seen": {"<key>": {...}}}`. Create it with `{"seen": {}}` if absent.

## Step 2 — Search every installed portal

Discover them rather than assuming: every `.agents/skills/*/SKILL.md` is a
portal. The three that ship:

```bash
# Master's and doctoral programmes in Germany (tuition is usually zero)
bun run .agents/skills/daad-programmes-search/cli/src/cli.ts search \
  --level masters --query "<field>" --language english --limit 25

bun run .agents/skills/daad-programmes-search/cli/src/cli.ts search \
  --level phd --query "<field>" --limit 25

# Funded doctoral studentships, open to international students
bun run .agents/skills/jobsacuk-phd-search/cli/src/cli.ts search \
  --level phd --query "<field>" --eligibility international-students \
  --funded --max-pages 2

# Scholarship calls
bun run .agents/skills/scholarship-feeds-search/cli/src/cli.ts search \
  --query "<field> scholarship" --level masters --calls-only
```

Use the search terms in `search-queries.md`.

Every portal's search output already carries award, provider, level, country,
deadline and url. That is the contract; a portal that stops emitting them is
broken, not merely quiet.

## Step 3 — Gate everything that came from a feed

Portal CLIs that return structured data from an institution's own API (DAAD)
are trusted as far as their source is. **Aggregator feed results are not.**
Run them through the gate before they enter state:

```bash
python3 tools/listing_guard.py --in <text> --text
```

If any `fraud_signals` family fires, do **not** add the entry silently.
Surface it to the user with the quotes, and record the verdict on the entry if
they still want it tracked.

## Step 4 — Deduplicate and append

Key every entry with the canonical function, never by hand:

```bash
python3 tools/program_key.py --provider "<provider>" --award "<award>" --url "<url>"
```

Skip a key already in `seen`. For a new one, append:

```json
{
  "award": "...", "provider": "...", "kind": "program|scholarship",
  "level": "masters|phd", "country": "...", "field": "...",
  "url": "...", "portal": "...", "source": "cli|websearch",
  "first_seen": "YYYY-MM-DD", "deadline": "YYYY-MM-DD|null",
  "opens": "YYYY-MM-DD|null", "status": "new"
}
```

`deadline` is ISO or `null`. **Never invent one.** A guessed date on a
deadline board is worse than a hole, and the board treats a missing deadline
as unplannable, which is the correct and visible behaviour.

## Step 5 — Degraded-portal scan

Before reporting, check for a portal that returned successfully but uselessly:

- zero results where it has previously returned some;
- `provider` null or empty on every result;
- `deadline` null on every result from a portal that normally carries them.

Report these as degraded. A silently broken parser produces an empty sweep
that looks like a quiet week.

## Step 6 — Report

- new entries, grouped by level and country, with deadlines;
- anything the gate flagged, with its quotes;
- degraded or unreachable portals;
- entries whose deadline falls inside `LEAD_TIME_DAYS` (45) — these need a
  decision now, not at the deadline.

Then point at `/rank`.

## Writing to the state file

`program_search/seen_programs.json` is append-only by design. Never rewrite
an existing entry's `first_seen`, and never delete entries — `/rank` and
`/outcome` own status transitions.
