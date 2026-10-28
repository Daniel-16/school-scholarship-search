# /funding - Can You Actually Pay For This?

`$ARGUMENTS`: an application key, or nothing to review every tracked plan.

## Build or update a plan

```bash
python3 tools/funding_model.py --template > funding/<key>.json
# edit it, then:
python3 tools/funding_model.py --in funding/<key>.json
```

Exit 0 = the plan closes. Exit 3 = it does not. Plans are gitignored;
`funding/rates.json` is tracked.

## Fill the plan from real figures

Never from memory and never from an aggregator. Per `09-web-research.md`:

- tuition from the institution's own fees page, **for the intake being
  applied to**;
- living costs from the institution's own estimate where it publishes one,
  since that is the figure the visa authority will use;
- the proof-of-funds requirement from the **official immigration site** for
  the current year — these change annually and secondary sources lag;
- the scholarship's actual coverage, and whether it is automatic, competitive,
  or a separate application with its own earlier deadline.

Where a figure cannot be verified, leave it out and say so. A plan built on a
guessed tuition figure produces a confident wrong answer.

## Report the three verdicts separately

Per `10-funding-and-costs.md`:

1. **The whole-programme gap**, and the monthly shortfall.
2. **The year-one gap.** A plan can balance over three years and be unpayable
   in month one — the model flags this as `front-loaded`, and it is the
   failure people do not see coming.
3. **The proof-of-funds shortfall.** Separate because a full scholarship does
   not exempt you from it unless the award letter is accepted as the
   evidence, which varies by country.

## Rules

- **Term-time work is already discounted by half** in the model, and that is
  deliberate: the permit is a ceiling, not a schedule. Never present
  term-time work as the thing that makes a programme affordable.
- Refresh `funding/rates.json` before a decision the user will act on, and
  say when it was last updated.
- Where the plan does not close, say what would close it — a specific
  scholarship with its deadline, a different country, a funded PhD instead of
  a taught master's — rather than reporting a number and stopping.

## Comparing

With no arguments, model every tracked application and present them side by
side: total cost, total funding, gap, year-one gap, proof-of-funds position.
This is usually the most useful form, because the answer is rarely "can I
afford this one" and almost always "which of these can I afford".
