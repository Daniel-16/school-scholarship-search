# Security Policy

## Reporting a vulnerability

Please report security findings privately via **[GitHub private vulnerability reporting](https://github.com/Daniel-16/school-scholarship-search/security/advisories/new)** rather than a public issue. You will get a response within a few days, credit in the fix unless you prefer otherwise, and public disclosure coordinated with the patch.

If the private form is unavailable, open a public issue that describes the *class* of problem without a working recipe, and note that you have details to share privately.

## Threat model, honestly stated

This is an agentic workflow: an LLM with file access reads untrusted web content (programme pages, funder pages, scholarship announcements) alongside unusually sensitive personal data - transcripts, passport scans, bank statements, referee contact details. That combination is the main risk surface, and it cannot be eliminated, only narrowed.

Two distinct threats, answered differently:

- **A listing can carry hidden text written to steer the agent.** Answered on two levels: instruction-level rules telling the agent that listings are data rather than instructions, and permission-level rules bounding what the agent can do even when it is steered.
- **A listing can be a scam aimed at the user rather than the agent.** Scholarship fraud is the dominant attack on applicants from the Global South, and `tools/listing_guard.py` scans every fetched listing for it: payment over irreversible rails, a fee demanded in order to receive an award, and pressure or proof-of-legitimacy signals. The gate advises; it never blocks, and it never decides on the user's behalf.

### Instruction level

`/apply`, `/rank`, `/discover`, `/interview` and the skill's own `09-web-research.md` treat listing text as data, never instructions: agents are told not to follow directions embedded in listings and not to fetch URLs found inside listing text (the user-supplied listing URL is the one exception). Reviewer research starts from the institution or funder identity the user confirmed, never from links in the listing body. `/apply` Step 0 also runs the fraud scan before any drafting, and stops on a hit rather than continuing with a caveat.

### Permission level

Every grant the template ships, where it lives, how long it lasts, and what checks it. "Guard" is `tools/security_guards.py`, which CI runs on every PR and which fails on any entry it does not know.

| Surface | What is granted | Lifetime | Guard |
|---|---|---|---|
| `.claude/settings.json` `permissions.allow` | Each shipped portal CLI by exact path, the `tools/` scripts (`shortlist_state`, `program_key`, `listing_guard`, `deadline_board`, `docs_checklist`, `funding_model`, `verify_pdf`, `verify_layout`, `robots_check`, `fetch_page`), `pdftotext`, and `Skill(grad-application-assistant)` | Whole session | Exact allowlist; any addition fails CI unless added to `ALLOWED_PERMISSIONS` in the same PR |
| `.claude/settings.json` `permissions.ask` | Always prompt, even over an allow rule or a skill grant: edits to `settings.json`, `settings.local.json`, any `.claude/skills/*/SKILL.md`, any `.claude/commands/*.md`, `.claude/agents/**`, `.github/**`, `tools/security_guards.py`; and `git push` | Whole session | Each rule is required; removal fails CI |
| `.claude/settings.json` `permissions.deny` | Blocked in every mode, `bypassPermissions` included: `curl`/`wget` with data, form or upload flags, `scp`, `sftp`, `ssh`, `nc`; reads of `.env`, `.env.*`, `~/.ssh/**`, `~/.aws/**`, `~/.gnupg/**` (Read denies also cover Bash `cat`/`head`/`tail`/`sed`) | Whole session | Each rule is required; removal fails CI |
| Skill `allowed-tools` (`.claude/skills/*/SKILL.md`) | `grad-application-assistant`: Read, Glob, Grep, WebFetch, WebSearch, Edit, Write, AskUserQuestion. `program-scout`: the same plus `tools/program_key.py`. `profile-gap`: Read, Glob, Grep, WebFetch, WebSearch, Write. Each portal skill grants exactly its own CLI. No bare `Bash` anywhere. | The turn that invokes the skill; clears on your next message. Not gated by workspace trust. | Exact allowlist (`ALLOWED_SKILL_TOOLS`); bare tools and wildcards fail CI |
| Portal skill `allowed-tools` (`.agents/skills/<name>/SKILL.md`) | Exactly that portal's own `cli/src/cli.ts` and nothing else | Invoking turn | Checked by path, so a skill that grants another portal's CLI, or a glob, fails CI |
| Slash commands (`.claude/commands/*.md`) | No `allowed-tools` frontmatter; they run under the session's rules above | - | Same frontmatter check as skills |
| Subagents (`.claude/agents/*.md`) | `listing-fetcher` (`/apply` Step 0), `listing-scorer` (`/rank` Step 2) and `application-reviewer` (`/apply` Step 3): Read, Glob/Grep where needed, WebFetch, WebSearch, Bash - never Edit, Write or Agent. Bash inside them is scoped by the allow list above, because an agent's `tools:` list is tool-name granularity. `/discover` runs the portal CLIs directly rather than through an agent. | While the agent runs | Check 5: every agent must declare `tools:` drawn from `ALLOWED_AGENT_TOOLS`; a missing key (= every tool) or a `Bash(pattern)` entry fails CI |
| The listing integrity gate (`tools/listing_guard.py`) | Runs on every listing before `/apply` Step 1 (URL or pasted), inside each `/rank` scorer, and on the archived listing in `/interview`: removes hidden HTML and invisible characters, quotes instruction-shaped lines and hidden URLs, lists mixed-script words, prints a one-line verdict. Advises; the user decides. The archive keeps counts, never the removed excerpts. | - | Pinned by `tests/test_listing_guard.py` and `tests/test_posting_gate_wiring.py` |
| Hooks (`.claude/settings.json` `hooks`) | None. The template ships no hooks: a hook runs with no prompt the moment its event fires, which is the vector the Shai-Hulud worm used in August 2026. | - | Any hook fails CI |
| Compiling (`lualatex`, `xelatex`, a custom template's command) | Not pre-approved: a `lualatex:*` grant would also approve `-shell-escape`. In default mode each compile prompts. Answering "don't ask again" would persist exactly that `lualatex` rule to your `settings.local.json`, so answer per call. | - | - |
| Portal CLI manifests (`.agents/**/package.json`) | No lifecycle scripts (`preinstall`, `postinstall`, ...) and no `trustedDependencies`, so `bun install` runs no code | - | Fails CI; `tools/install_portal_clis.py` also skips a manifest that carries one |
| The browser-header retry (`tools/fetch_page.py`) | A GET with a fixed argv, http(s) only, 45 s / 5 redirects / 10 MB, `robots.txt` enforced with no bypass flag, output refused inside the repo | - | Pinned by `tests/test_fetch_page.py`; the grant names the script, not `curl` |

### What this does not do

- **It is not a sandbox.** Claude Code's Bash sandbox does not run on native Windows at all, and on macOS and Linux it is off by default. If you are on macOS or Linux, turning it on in your user settings is the single strongest addition you can make; nothing in this repo conflicts with it.
- **Prefix rules are tripwires, not walls.** `Bash(curl -d:*)` matches a command that starts that way; `curl -sS -d` does not match it. The deny list catches the obvious shapes and makes the rest need deliberate evasion, which is a different bar from preventing it.
- **WebFetch is unrestricted by domain.** Company research needs it, and a GET to an arbitrary host can carry data in the URL. The instruction-level rule (never fetch URLs from the listing body) is what stands between a hidden link and a fetch; the permission layer does not.
- **`/rank` scorers still hold the rubric and the listing in one context.** Each scoring agent fetches and scores a batch, so the candidate rubric and the untrusted listing share a context that also has WebFetch. What the agent definition removes is Edit, Write and unscoped shell. Fully separating fetch from scoring would route every listing through the orchestrator, which `/rank` is built to avoid.
- **The gate is deterministic, not an oracle.** `listing_guard.py` catches the payload classes that leave a trace: hidden markup, invisible characters, agent-addressed phrasing, hidden links, look-alike letters. A manipulation written to read naturally to a human and an agent alike leaves none, and the instruction-level rules remain the only defence for that.
- **Edit and Write are what the skill does.** Tailoring a CV means editing files, so those tools stay granted. What the `ask` list guarantees is that an agent cannot silently turn that into a wider grant: the files that define permissions always prompt.

Instruction-level defenses raise the bar; permission-level defenses bound the damage. Neither is a guarantee. If you run this workflow against portals you do not trust at all, review what the agent fetched and wrote before sending anything out.