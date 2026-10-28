<p align="center">
  <img src="assets/mascot/pip_flight_loop.gif" alt="Pip, the courier bird" width="180">
</p>

# School & Scholarship Search

*A master's and PhD application workspace that runs on your machine.*

Finds programmes and funding, scores them against your profile and your
budget, writes your CV and statements, and keeps the deadlines that actually
decide whether you make the cycle.

Built on [Claude Code](https://claude.com/claude-code). Nothing is uploaded:
your transcripts, passport scans and bank statements never leave this folder,
and the tools that check them read **file names and counts only**.

> **Master's and PhD only.** No undergraduate — and that is enforced in code,
> not convention. The portal CLIs have no undergraduate level, and the
> scholarship feed reader detects undergraduate announcements specifically in
> order to drop them.

---

## What you need to give it

This is the part that decides whether the rest works. Run
`python3 tools/docs_checklist.py inventory` at any time to see where you
stand, or just ask Claude: **"what do you still need from me?"**

### 1. Answers (15 minutes, run `/setup`)

Nothing else in the workspace is useful until these exist. A shortlist built
without a funding ceiling is a list of programmes you may not be able to pay
for.

| | Why it is needed |
|---|---|
| Master's, PhD, or both? | Different documents, deadlines and odds |
| Your field, narrower than "AI" | Drives every search and the first paragraph of your CV |
| Target intake (e.g. Autumn 2027) | Decides which deadlines are still reachable |
| Target countries, or "open" | Cost, visa, eligibility |
| **Maximum you can self-fund**, in USD | The figure every programme is tested against |
| Fully funded only, or partial acceptable? | Changes the whole shortlist |
| Liquid funds for **proof of funds** | The thing that blocks visas, separate from affordability |
| **Exact CGPA and scale** (e.g. 3.82/5.00) | Asked on every single form |
| Thesis supervisor's name, thesis grade | Needed for the CV and for referees |
| NYSC status | Asked by Nigerian-facing schemes; affects start dates |
| Dependants relocating? | Cost, visa route, scheme eligibility |

### 2. Documents (drop them in `documents/`)

Nothing here is committed to git. See [`documents/README.md`](documents/README.md)
for the detail.

| Folder | What goes in | How long it takes to get |
|---|---|---|
| `transcripts/` | One PDF per institution attended | **4–6 weeks** from a Nigerian university — order first, always |
| `degrees/` | B.Sc. certificate or statement of result; Any other applicable certificate | Weeks |
| `test_scores/` | IELTS / TOEFL / Duolingo, GRE if needed | **~3 weeks** to book, sit and be reported |
| `identity/` | Passport data page, birth certificate, NIN slip | Have it, or renew now — the passport must outlive your start date |
| `cv/` | Any CV you already have | You have one |
| `references/` | `referees.json` — names, titles, **institutional** emails | Ask **30 days** before a deadline |
| `research/` | Thesis, papers, writing samples | You have these |
| `portfolio/` | Project write-ups, repo links, certificates, award letters | — |
| `financial/` | Bank statements, sponsor letter, award letters | Needed for the **visa**, not usually the application |

**Two things people get wrong every cycle:**

- **Test scores expire.** IELTS and TOEFL are valid two years from the test
  date, GRE five. Put the date in a sidecar
  (`ielts_2026.pdf.meta.json` → `{"taken": "2026-03-14"}`) and the workspace
  checks validity **against each deadline**, not against today.
- **Referees need institutional email addresses.** A Gmail address in a
  recommender field is rejected outright by many portals, and it is the single
  most common reason a reference never gets counted.

---

## How it runs

```
/setup          tell it who you are and what you can afford
/discover       sweep every portal for new programmes and funding
/rank           score them: three gates, five dimensions, a funding verdict
/documents      what you have, what each application still needs
/apply <url>    fit assessment, then CV + statements + form answers
/deadlines      the backward-planned board of what to do this week
/recommenders   plan and run the reference requests
/interview      prepare for a supervisor, admissions or panel interview
/outcome        record a result
```

Plus `/funding`, `/profile-gap`, `/html-report`, `/expand`, `/add-portal`,
`/add-template`, `/gmail-sync`, `/notion-sync`, `/reset`.

---

## The parts that are not obvious

### Deadlines are planned backwards

The submission deadline is the *last* milestone, not the first. On the day a
deadline looks comfortable, the transcript that must arrive before it has
already needed ordering for two weeks.

`/deadlines` expands every deadline into the milestones that precede it —
language test at −70 days, transcripts at −45, referees at −30, statement
draft at −21 — merges them across every application, and sorts by date. One
list, not a mental join across eight programmes. `--ics` exports it to your
calendar.

### It checks for scholarship fraud, in code

Scholarship fraud is the dominant attack on applicants from Nigeria and the
rest of the Global South: an "award" that wants a processing fee before it
releases money it never had. `tools/listing_guard.py` scans every fetched
listing for three families — payment over irreversible rails (Western Union,
crypto, gift cards), a fee demanded in order to *receive* an award, and
pressure signals (unsolicited selection, guaranteed admission, 24-hour
ultimatums, WhatsApp-only contact).

It is deliberately narrow. A university's own application fee is normal and
does not trigger it; only the "pay to get the award" shape does.

### Funding gets three verdicts, not one

`/funding` separates:

1. the **whole-programme gap**,
2. the **year-one gap** — a plan can balance over three years and be
   unpayable in month one,
3. the **proof-of-funds shortfall** — the sum a visa makes you *show*. A full
   scholarship does not exempt you from it unless the award letter is accepted
   as the evidence, which varies by country.

Term-time work is counted at half the legal entitlement, on purpose. The
permit is a ceiling, not a schedule, and a plan that only closes on 20 hours a
week has not closed.

### Funding outranks prestige in the ranking

The rubric weights `funding` at 0.30 — above academic fit. An unfunded offer
from a world-class department is not an opportunity for a self-funding
applicant; it is a rejection with extra steps that costs a fee to receive.

---

## Where it searches

| Portal | Covers |
|---|---|
| **DAAD International Programmes** | Master's and doctoral programmes in Germany, with real tuition and scholarship data in the search result. Public universities charge no tuition for most programmes, including for non-EU students. |
| **jobs.ac.uk** | Funded PhD and master's studentships in the UK, Ireland and Europe, filterable by **open to international students** — the restriction that silently rules out a large share of UK studentships. |
| **Scholarship feeds** | scholars4dev, Opportunity Desk, Scholarship Region, Opportunities For Africans. Every result is marked **unverified**: these are aggregators republishing other people's calls, often a cycle out of date. |

Add your own with `/add-portal`.

Checked and deliberately not used: findaphd.com and findamasters.com (Cloudflare
challenge on every request), scholarshipportal.com (disallows keyword search),
EURAXESS (results render client-side, no public API). The reasoning is recorded
in each skill's `url-reference.md` so nobody repeats the work.

---

## Setup

See [SETUP.md](SETUP.md). Short version:

```bash
# Prerequisites: Python 3.10+, Bun, a LaTeX distribution
python3 tools/install_portal_clis.py     # installs the portal CLIs
python3 tools/docs_checklist.py inventory
```

Then open the folder in Claude Code and run `/setup`.

---

## Privacy

Everything personal is gitignored: `documents/`, `application_tracker.csv`,
`program_search/`, `funding/*.json`, generated CVs and statements, reports.

Nothing is sent anywhere. The portal CLIs transmit only search terms. The
document tools read file names, never file contents. The settings file denies
every outbound upload path (`curl -d`, `scp`, `ssh`, …) and blocks reading
`.env` and your SSH keys.

The workspace **never submits an application**. Form answers are drafted for
you to review and paste. Declarations, visa-history questions and academic
misconduct questions are not drafted at all.

---

## Licence

MIT. See [LICENSE](LICENSE).
