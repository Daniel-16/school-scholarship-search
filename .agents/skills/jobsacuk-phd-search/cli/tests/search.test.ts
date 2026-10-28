import { describe, expect, test } from "bun:test"
import { LEVEL_FACET, PAGE_SIZE, buildUrl } from "../src/commands/search.js"
import { inferCountry, parseClosingDate, parseSearchResults, readFunded } from "../src/helpers.js"

const PAGE = `
<div class="j-search-result__result ie-border-left" data-advert-id="1">
  <div class="j-search-result__text">
    <a href="/job/DTK970/phd-studentship-bioinspired">PhD Studentship: Bioinspired metamaterials</a>
    <div class="j-search-result__department">Biosciences</div>
    <div class="j-search-result__employer"><b>University of Exeter</b></div>
    <div>Location: Devon, Exeter</div>
    <div class="j-search-result__info"><strong>Salary: </strong>
      The studentship provides fees and a stipend of &pound;21,805 per annum</div>
    <div><strong>Date Placed: </strong>27 Oct</div>
  </div>
  <div class="j-search-result__date-logos">
    <span class="j-search-result__date-span j-search-result__date">Closes</span>
    <span class="j-search-result__date-span j-search-result__date--blue ">10 Nov</span>
  </div>
</div>
<div class="j-search-result__result" data-advert-id="2">
  <div class="j-search-result__text">
    <a href="/job/DTA553/phd-physical-ai">PhD Position in Physical AI</a>
    <div class="j-search-result__employer"><b>Aarhus University</b></div>
    <div>Location: Aarhus</div>
    <div class="j-search-result__info"><strong>Salary: </strong>Self-funded students only</div>
  </div>
</div>`

describe("buildUrl", () => {
  // /search/phd looks like the PhD board and silently ignores `keywords`,
  // returning staff vacancies with a 200. The facet is the real filter.
  test("filters the level through jobTypeFacet, not the /search/phd path", () => {
    const url = new URL(buildUrl({ level: "phd", query: "robotics" }))
    expect(url.pathname).toBe("/search/")
    expect(url.searchParams.getAll("jobTypeFacet[]")).toEqual(["phds"])
    expect(url.searchParams.get("keywords")).toBe("robotics")
  })

  test("covers funded master's studentships too", () => {
    expect(new URL(buildUrl({ level: "masters" })).searchParams.getAll("jobTypeFacet[]")).toEqual(["masters"])
  })

  // The workspace is postgraduate-only: no facet value may reach undergraduates.
  test("offers no undergraduate level", () => {
    expect(Object.keys(LEVEL_FACET).sort()).toEqual(["masters", "phd"])
  })

  test("an unknown level falls back to phd rather than dropping the facet", () => {
    expect(new URL(buildUrl({ level: "nonsense" })).searchParams.getAll("jobTypeFacet[]")).toEqual(["phds"])
  })

  test("carries the eligibility facet, which is what excludes home-only funding", () => {
    const url = new URL(buildUrl({ eligibility: "international-students" }))
    expect(url.searchParams.getAll("fundingTypeFacet[]")).toEqual(["international-students"])
  })

  test("repeatable disciplines split on commas", () => {
    const url = new URL(buildUrl({ discipline: ["computer-sciences,engineering-and-technology"] }))
    expect(url.searchParams.getAll("academicDisciplineFacet[]"))
      .toEqual(["computer-sciences", "engineering-and-technology"])
  })

  test("pages with a 1-based startIndex", () => {
    expect(new URL(buildUrl({}, 1)).searchParams.get("startIndex")).toBe("1")
    expect(new URL(buildUrl({}, 3)).searchParams.get("startIndex")).toBe(String(2 * PAGE_SIZE + 1))
  })
})

describe("parseSearchResults", () => {
  const rows = parseSearchResults(PAGE, new Date(Date.UTC(2026, 9, 28)))

  test("emits every field the /discover search contract names", () => {
    expect(rows).toHaveLength(2)
    const row = rows[0]!
    expect(row.award).toBe("PhD Studentship: Bioinspired metamaterials")
    expect(row.provider).toBe("University of Exeter")
    expect(row.level).toBe("phd")
    expect(row.url).toBe("https://www.jobs.ac.uk/job/DTK970/phd-studentship-bioinspired")
    expect(row.deadline).toBe("2026-11-10")
    expect(row.funded).toBe(true)
  })

  test("respects the level it was parsed for", () => {
    expect(parseSearchResults(PAGE, new Date(), "masters")[0]!.level).toBe("masters")
  })

  test("marks an explicitly self-funded listing", () => {
    expect(rows[1]!.funded).toBe(false)
  })
})

describe("readFunded", () => {
  test("true for a stated stipend or studentship", () => {
    expect(readFunded("Fully funded studentship")).toBe(true)
    expect(readFunded("tax-free stipend of £19,237")).toBe(true)
    expect(readFunded("£21,805 per annum")).toBe(true)
  })

  test("false only when the listing says so", () => {
    expect(readFunded("Self-funded students only")).toBe(false)
    expect(readFunded("Unfunded")).toBe(false)
  })

  // Three answers, not two: "could not tell" must not be filtered out as
  // "no money", or --funded would hide most of what it exists to find.
  test("null when the line cannot be read", () => {
    expect(readFunded("Competitive")).toBeNull()
    expect(readFunded(null)).toBeNull()
  })
})

describe("parseClosingDate", () => {
  const nov2026 = new Date(Date.UTC(2026, 10, 15))

  test("reads an ISO date verbatim", () => {
    expect(parseClosingDate("2027-01-31", nov2026)).toBe("2027-01-31")
  })

  // jobs.ac.uk prints "10 Nov" with no year. A listing never closes in the
  // past, so a day-month already gone must be next year.
  test("rolls a past day-month into next year", () => {
    expect(parseClosingDate("10 Nov", nov2026)).toBe("2026-11-10")
    expect(parseClosingDate("5 Jan", nov2026)).toBe("2027-01-05")
  })

  test("an explicit year wins over the inference", () => {
    expect(parseClosingDate("5 Jan 2029", nov2026)).toBe("2029-01-05")
  })

  test("unparseable input is null, never a guess", () => {
    expect(parseClosingDate("Open until filled", nov2026)).toBeNull()
    expect(parseClosingDate(null)).toBeNull()
  })
})

describe("inferCountry", () => {
  // Defaulting an unknown location to the UK filed a Danish studentship as
  // British, which survives all the way into a visa plan.
  test("names a country only on an explicit signal", () => {
    expect(inferCountry("Aarhus")).toBe("Denmark")
    expect(inferCountry("Devon, Exeter, England")).toBe("United Kingdom")
    expect(inferCountry("Dublin")).toBe("Ireland")
  })

  test("returns null rather than assuming", () => {
    expect(inferCountry("Remote")).toBeNull()
    expect(inferCountry("Penryn")).toBeNull()
    expect(inferCountry(null)).toBeNull()
  })
})

describe("parseClosingDate grace window", () => {
  const nov15 = new Date(Date.UTC(2026, 10, 15))

  // Inside the grace window the listing keeps this year, so the sweep can
  // expire it. Rolled forward it would sit in the shortlist for 11 months.
  test("a date just gone keeps the current year", () => {
    expect(parseClosingDate("10 Nov", nov15)).toBe("2026-11-10")
  })

  test("a date well past rolls into next year", () => {
    expect(parseClosingDate("1 Oct", nov15)).toBe("2027-10-01")
  })

  test("today and the future are unaffected", () => {
    expect(parseClosingDate("15 Nov", nov15)).toBe("2026-11-15")
    expect(parseClosingDate("20 Dec", nov15)).toBe("2026-12-20")
  })
})
