# Funding and Costs

The question is never "what does this cost". It is "what is left after the
funding, and can I show it".

## The tool

```bash
python3 tools/funding_model.py --template > funding/<key>.json   # then edit
python3 tools/funding_model.py --in funding/<key>.json
```

Exit 0 = the plan closes. Exit 3 = it does not. Plans live in `funding/` and
are gitignored; `funding/rates.json` is shared configuration and is tracked.

Rates are maintained by hand, never looked up live. A verdict that changes
between two runs because a rate moved is worse than one the user set and can
see — refresh them deliberately before a decision you act on.

## The four numbers

**Cost of attendance** — tuition for the *whole programme* plus living costs
for its *whole duration*. A two-year MSc quoted at "€18,000 per year" is a
€36,000 decision.

**One-off costs** — application fee, visa fee, health surcharge or mandatory
insurance, flights, deposit, uni-assist fee. Small individually; together
often a month of stipend, and they all fall due *before* any funding arrives.

**Funding** — a scholarship is rarely "full". Most are tuition-only. A stipend
is paid monthly from the start date, which is not when the first rent is due.
The model takes `scholarship_covers` as one of `none`, `tuition`,
`partial_tuition`, `living`, `full`, and never infers it.

**Proof of funds** — the sum a visa requires you to *show*. This is the number
that sinks funded applicants. A full scholarship does not exempt you unless
the award letter is accepted as the evidence, which varies by country. The
model keeps it as a separate verdict for exactly that reason.

## Three outputs, not one

`affordable: true` requires both the gap and the proof-of-funds shortfall to
clear. The model also reports:

- **the whole-programme gap** and the monthly shortfall;
- **the year-one gap** — a plan can balance over three years and be
  unpayable in month one, which the model flags as `front-loaded`;
- **the proof-of-funds shortfall**, separately.

## Term-time work is discounted by half, deliberately

The work permit is a ceiling, not a schedule. Coursework, a job that does not
exist on arrival, and vacation-only rules all cut into it. A plan that only
closes on the full 20 hours a week has not closed. Never present term-time
work as the thing that makes a programme affordable.

## Proof of funds, by destination

Confirm every figure on the official immigration site for the current year —
these change annually and secondary sources lag.

| Destination | Shape of the requirement |
|---|---|
| **Germany** | Blocked account (*Sperrkonto*) holding roughly one year of living costs, or a recognised scholarship award letter in its place. |
| **UK** | Course fees for year one plus a set monthly maintenance amount, held for 28 consecutive days ending no more than 31 days before applying. The 28-day rule is where applications fail. |
| **Canada** | GIC plus first-year tuition, under the Student Direct Stream where eligible. |
| **Netherlands / Nordics** | Proof held or transferred to the institution, often before enrolment. |
| **US** | Financial documents for the I-20, usually *after* admission rather than at application. |

The 28-day and blocked-account rules mean the money must be **in place weeks
before the visa application**, which is itself weeks before travel. Work this
backwards from the start date, not forwards from the offer.

## Where the money actually is for this applicant

Ranked by realistic prospect, not by prestige:

1. **Funded PhD positions** (jobs.ac.uk, EU institutions). Employment or a
   stipend with fees waived. No funding gap, and the proof-of-funds problem
   mostly disappears. The strongest route if a PhD is on the table.
2. **German public universities.** No tuition for most programmes including
   non-EU students; the cost is living plus the blocked account. Covered by
   `daad-programmes-search`.
3. **Development-focused schemes** — DAAD EPOS, Commonwealth, Chevening,
   Mastercard Foundation Scholars. Fully funded including travel and stipend,
   competitive, and scored on leadership and return-home impact, where this
   profile is strong.
4. **Institutional scholarships** attached to an MSc offer. Usually partial;
   read whether a separate application is required.
5. **Self-funding an MSc abroad.** The most expensive option and the one most
   applicants default to. Treat it as the fallback it is.

## Questions the user must answer before any of this is useful

Carried from `01-applicant-profile.md`, where they are still `[CONFIRM]`:

- Maximum self-funded contribution, in USD.
- Whether a partial award is workable or only fully funded is.
- Liquid funds available for proof of funds, and whether a sponsor's account
  can be used.
- Whether dependants are relocating.

Without these the model cannot produce a verdict, and a shortlist built
without them is a shortlist of programmes that may be unaffordable.
