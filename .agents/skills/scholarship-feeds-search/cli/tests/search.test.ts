import { describe, expect, test } from "bun:test"
import { EXCLUDED_LEVEL, feedUrl, keepLevel, toAnnouncement } from "../src/commands/search.js"
import { SOURCES, sourceById } from "../src/sources.js"
import { callSignals, detectCountry, detectLevels, parseDeadline, parseRss } from "../src/helpers.js"

const SOURCE = sourceById("scholars4dev")!

const FEED = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<item>
  <title><![CDATA[Swedish Institute Scholarship 2027 (Fully Funded)]]></title>
  <link>https://example.org/si-2027/</link>
  <pubDate>Wed, 22 Oct 2026 10:20:25 +0000</pubDate>
  <description><![CDATA[<p>Applications are open for master's study. Deadline: 15 January 2027.</p>]]></description>
  <category><![CDATA[Masters]]></category>
</item>
<item>
  <title>Top 10 UK Universities Offering Scholarships</title>
  <link>https://example.org/top-10/</link>
  <pubDate>Tue, 21 Oct 2026 09:00:00 +0000</pubDate>
  <description>A roundup of universities in the UK.</description>
</item>
</channel></rss>`

describe("parseRss", () => {
  const items = parseRss(FEED)

  test("reads CDATA and plain tags alike", () => {
    expect(items).toHaveLength(2)
    expect(items[0]!.title).toBe("Swedish Institute Scholarship 2027 (Fully Funded)")
    expect(items[1]!.title).toBe("Top 10 UK Universities Offering Scholarships")
    expect(items[0]!.categories).toEqual(["Masters"])
  })

  test("an empty or broken feed yields nothing rather than throwing", () => {
    expect(parseRss("")).toEqual([])
    expect(parseRss("<rss><channel><item><title>x</title>")).toEqual([])
  })
})

describe("toAnnouncement", () => {
  const row = toAnnouncement(parseRss(FEED)[0]!, SOURCE)

  test("emits the /discover contract fields and flags itself unverified", () => {
    expect(row.award).toContain("Swedish Institute")
    expect(row.kind).toBe("scholarship")
    expect(row.level).toEqual(["masters"])
    expect(row.deadline).toBe("2027-01-15")
    expect(row.published).toBe("2026-10-22")
    expect(row.requires_verification).toBe(true)
  })

  // The aggregator is not the funder, and guessing the funder from blog
  // prose puts a wrong name in the archive. Null is the honest answer.
  test("never guesses the funder", () => {
    expect(row.provider).toBeNull()
  })
})

describe("keepLevel", () => {
  test("keeps the requested postgraduate level", () => {
    expect(keepLevel(["masters"], "masters")).toBe(true)
    expect(keepLevel(["masters", "phd"], "phd")).toBe(true)
    expect(keepLevel(["phd"], "masters")).toBe(false)
  })

  test("any-postgraduate keeps both", () => {
    expect(keepLevel(["masters"], "any-postgraduate")).toBe(true)
    expect(keepLevel(["phd"], "any-postgraduate")).toBe(true)
  })

  // Undergraduate-only is always dropped; this workspace has no use for it
  // and it is the bulk of what these feeds carry.
  test("drops undergraduate-only announcements at every level", () => {
    expect(keepLevel([EXCLUDED_LEVEL], "any-postgraduate")).toBe(false)
    expect(keepLevel([EXCLUDED_LEVEL], "masters")).toBe(false)
  })

  test("keeps a combined undergraduate-and-masters call", () => {
    expect(keepLevel([EXCLUDED_LEVEL, "masters"], "masters")).toBe(true)
  })

  // These feeds are prose. A silent drop of an undetectable item would hide
  // genuine calls with no trace, so an unknown level is kept.
  test("keeps an item whose level could not be detected", () => {
    expect(keepLevel([], "masters")).toBe(true)
  })

  test("drops a postdoc-only call", () => {
    expect(keepLevel(["postdoc"], "any-postgraduate")).toBe(false)
  })
})

describe("detectLevels", () => {
  test("finds several levels in one announcement", () => {
    expect(detectLevels("Masters and PhD scholarships").sort()).toEqual(["masters", "phd"])
  })

  test("recognises undergraduate so it can be excluded", () => {
    expect(detectLevels("Bachelor's degree scholarship")).toContain("undergraduate")
  })

  test("returns nothing rather than assuming", () => {
    expect(detectLevels("Scholarship opportunity")).toEqual([])
  })
})

describe("detectCountry", () => {
  // Scanning the whole post and taking the first pattern made the answer
  // depend on the pattern order: this title came back as United States.
  test("prefers the title over the body", () => {
    expect(detectCountry("Swedish Institute Scholarship", "open to students across the Americas"))
      .toBe("Sweden")
  })

  test("falls back to the body when the title names nothing", () => {
    expect(detectCountry("Fully Funded Scholarship 2027", "Study in the Netherlands")).toBe("Netherlands")
  })

  test("returns null rather than guessing", () => {
    expect(detectCountry("Scholarship 2027", "")).toBeNull()
  })
})

describe("callSignals", () => {
  test("a real call carries evidence", () => {
    expect(callSignals("SI Scholarship 2027", "Applications are open. Fully funded.", true))
      .toContain("applications_open")
  })

  // Listicles and how-to posts match every scholarship keyword there is.
  test("a listicle or how-to title is not a call", () => {
    expect(callSignals("Top 10 UK Universities Offering Scholarships", "Fully funded options", false))
      .toEqual([])
    expect(callSignals("How To Apply For A Scholarship", "eligibility explained", false)).toEqual([])
  })

  test("a dated article still keeps its deadline evidence", () => {
    expect(callSignals("Top 10 Scholarships", "Deadline: 1 March 2027", true)).toEqual(["deadline_stated"])
  })
})

describe("parseDeadline", () => {
  test("reads the common announcement formats", () => {
    expect(parseDeadline("Deadline: 15 January 2027")).toBe("2027-01-15")
    expect(parseDeadline("Application Deadline: January 15, 2027")).toBe("2027-01-15")
    expect(parseDeadline("closes 2027-01-15")).toBe("2027-01-15")
  })

  test("picks the earliest of several", () => {
    expect(parseDeadline("Round 1: 15 January 2027, Round 2: 3 March 2027")).toBe("2027-01-15")
  })

  // An announcement is routinely republished for an intake two years out,
  // so a year-less date cannot be inferred the way a job board's can.
  test("refuses a date with no year", () => {
    expect(parseDeadline("Deadline: 15 January")).toBeNull()
  })

  // dd/mm and mm/dd are indistinguishable below the 13th, and a coin flip
  // between two readings is not a deadline.
  test("accepts a slash date only when it is unambiguous", () => {
    expect(parseDeadline("closes 15/01/2027")).toBe("2027-01-15")
    expect(parseDeadline("closes 05/01/2027")).toBeNull()
  })
})

describe("feedUrl", () => {
  test("uses the search feed when there is a query, the latest feed otherwise", () => {
    expect(feedUrl(SOURCE, "data science")).toContain("s=data%20science")
    expect(feedUrl(SOURCE, undefined)).toBe(SOURCE.latest)
  })

  test("every source declares both feeds and a note", () => {
    for (const source of SOURCES) {
      expect(source.search).toContain("{q}")
      expect(source.latest).toStartWith("https://")
      expect(source.note.length).toBeGreaterThan(10)
    }
  })
})
