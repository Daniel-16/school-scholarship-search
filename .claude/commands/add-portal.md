# /add-portal - Generate a Portal Search Skill

`$ARGUMENTS`: the portal — a name, a URL, or a description of what it lists.

Use this when a country, a funder or a database matters to the user and none
of the shipped portals covers it. Examples that would justify one: a national
scholarship board, a university consortium's programme finder, a regional
research-position portal.

## Step 1 — Is it reachable at all?

Most are not, and finding out early saves the rest of the work.

```bash
python3 tools/robots_check.py "<search url>"
python3 tools/fetch_page.py "<search url>" --text
```

Three ways this fails, and each is a stop:

- **robots.txt declines.** Stop. No flag overrides it.
- **A bot challenge** (Cloudflare "Just a moment…"). The page is unreachable
  without a browser. findaphd.com and findamasters.com both fail here.
- **Results render client-side.** The HTML carries no listings. EURAXESS
  fails here. Check before writing a parser, not after.

Record the finding in the new skill's `url-reference.md` either way — a
documented dead end stops the next person repeating the work.

## Step 2 — Find the real contract

Read the site's own search form (`<form action=...>` and its field names)
rather than guessing parameter names. This is where `/search/phd` on
jobs.ac.uk turned out to silently ignore `keywords` and return staff
vacancies with a 200.

Verify by running a query whose results you can check by eye. **A filter that
is silently ignored returns a larger result set that looks like success.**

## Step 3 — Generate

Copy the structure of `.agents/skills/daad-programmes-search/cli/`:

```
.agents/skills/<name>-search/
  SKILL.md
  url-reference.md
  cli/
    package.json      # zero runtime dependencies
    tsconfig.json
    src/argv.ts       # copy verbatim - it is the unknown-flag guard
    src/helpers.ts
    src/cli.ts
    src/commands/search.ts
    src/commands/detail.ts
    tests/*.test.ts
```

Non-negotiable properties:

- **Zero runtime dependencies.** Every fork executes this code.
- **No lifecycle scripts** in `package.json` — `tools/security_guards.py`
  rejects them, because they run code during `bun install`.
- **Unknown flags exit 1** with `{"error","code":"UNKNOWN_FLAG"}` on stderr.
  Copy `argv.ts` rather than reimplementing it.
- **Postgraduate only.** If the portal has an undergraduate level, it must be
  unreachable from the CLI, not merely absent from the defaults — and a test
  must pin that.
- **Search output carries** `award`, `provider`, `level`, `country`,
  `deadline`, `url`. `/discover` depends on it.
- **`deadline` is ISO or null, never a guess.**
- Retry 429, 5xx **and transport failures**.
- A detail URL on another host is rejected.

## Step 4 — Register

- `.claude/settings.json` → add
  `Bash(bun run .agents/skills/<name>-search/cli/src/cli.ts:*)`
- `tools/security_guards.py` → add the same string to `ALLOWED_PERMISSIONS`
- the skill's own `allowed-tools` frontmatter → the same grant

All three, in the same change. The duplication is the review step.

## Step 5 — Verify

```bash
cd .agents/skills/<name>-search/cli && bun install && bun run typecheck && bun test
cd - && python3 tools/lint_skills.py && python3 tools/security_guards.py
python3 tools/install_portal_clis.py --dry-run
```

Then run a real search and read the results. A CLI that typechecks and returns
plausible-looking nonsense is the failure mode here.
