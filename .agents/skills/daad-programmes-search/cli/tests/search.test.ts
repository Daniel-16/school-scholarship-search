import { describe, expect, test } from "bun:test"
import { TUITION_FREE_BRACKET, buildUrl } from "../src/commands/search.js"
import { LEVEL_CODES, decodeEntities, normalizeCourse, parseDeadline } from "../src/helpers.js"

describe("buildUrl", () => {
  test("masters maps to DAAD degree 2", () => {
    const url = new URL(buildUrl({ level: "masters", limit: 10, offset: 0 }))
    expect(url.searchParams.getAll("degree[]")).toEqual(["2"])
  })

  test("phd maps to both doctoral codes, because DAAD splits them and an applicant does not", () => {
    const url = new URL(buildUrl({ level: "phd", limit: 10, offset: 0 }))
    expect(url.searchParams.getAll("degree[]")).toEqual(["3", "4"])
  })

  // The workspace is postgraduate-only. Code 1 is DAAD's Bachelor's degree,
  // and it must be unreachable rather than merely undefaulted.
  test("no level reaches the Bachelor's code", () => {
    for (const codes of Object.values(LEVEL_CODES)) {
      expect(codes).not.toContain("1")
    }
  })

  test("clamps limit into the portal's range", () => {
    expect(new URL(buildUrl({ level: "masters", limit: 5000 })).searchParams.get("limit")).toBe("100")
    expect(new URL(buildUrl({ level: "masters", limit: 0 })).searchParams.get("limit")).toBe("1")
  })

  test("tuition-free and with-scholarship become the portal's own parameters", () => {
    const url = new URL(buildUrl({ level: "masters", "tuition-free": true, "with-scholarship": true }))
    expect(url.searchParams.get("fee")).toBe(TUITION_FREE_BRACKET)
    expect(url.searchParams.get("hasScholarship")).toBe("1")
  })

  // DAAD's fee brackets run 1-4 and there is no bracket 0. `fee=0` is
  // accepted, answered with a 200, and returns nothing - a search that looks
  // successful and silently matches no programme at all.
  test("the tuition-free bracket is a real DAAD bracket, never zero", () => {
    expect(TUITION_FREE_BRACKET).toBe("1")
    expect(["1", "2", "3", "4"]).toContain(TUITION_FREE_BRACKET)
  })

  test("an absent filter sends no parameter at all", () => {
    const url = new URL(buildUrl({ level: "masters" }))
    expect(url.searchParams.has("fee")).toBe(false)
    expect(url.searchParams.has("q")).toBe(false)
  })

  test("a repeatable subject flag splits on commas", () => {
    const url = new URL(buildUrl({ level: "masters", subject: ["4,12", "19"] }))
    expect(url.searchParams.getAll("subjects[]")).toEqual(["4", "12", "19"])
  })
})

describe("parseDeadline", () => {
  test("picks the earliest date when DAAD lists several", () => {
    expect(parseDeadline("Register by 31 May 2027 + 3 more, then 15 January 2027")).toBe("2027-01-15")
  })

  test("reads an ISO date", () => {
    expect(parseDeadline("Deadline 2027-03-01")).toBe("2027-03-01")
  })

  // A deadline board built on a guessed date is worse than one with a hole.
  test("a date with no year is not guessed at", () => {
    expect(parseDeadline("15 October - 15 December")).toBeNull()
    expect(parseDeadline("")).toBeNull()
    expect(parseDeadline(null)).toBeNull()
  })
})

describe("normalizeCourse", () => {
  const raw = {
    id: 7852,
    courseName: "MSc in Artificial&nbsp;Intelligence",
    academy: "THWS",
    city: "Würzburg",
    subject: "Computer Science",
    languages: ["English"],
    programmeDuration: "3 semesters",
    tuitionFees: "No tuition fees",
    applicationDeadline: "Register by 31 May 2027",
    date: [{ registrationDeadline: "2027-01-15" }, { registrationDeadline: "2026-12-15" }],
    link: "/deutschland/studienangebote/international-programmes/en/detail/7852/",
  }

  test("emits every field the /discover search contract names", () => {
    const row = normalizeCourse(raw, "masters")
    for (const field of ["award", "provider", "level", "country", "deadline", "url"] as const) {
      expect(row[field]).toBeTruthy()
    }
    expect(row.level).toBe("masters")
    expect(row.country).toBe("Germany")
    expect(row.kind).toBe("program")
  })

  test("prefers the structured registration deadline, earliest first", () => {
    expect(normalizeCourse(raw, "masters").deadline).toBe("2026-12-15")
  })

  test("falls back to parsing the prose deadline when there is no structured one", () => {
    expect(normalizeCourse({ ...raw, date: [] }, "masters").deadline).toBe("2027-05-31")
  })

  test("unescapes entities and builds an absolute URL", () => {
    const row = normalizeCourse(raw, "masters")
    expect(row.award).toBe("MSc in Artificial Intelligence")
    expect(row.url).toStartWith("https://www2.daad.de/")
  })

  test("a course missing every optional field still produces a usable row", () => {
    const row = normalizeCourse({ id: 1, link: "" }, "phd")
    expect(row.award).toBe("(untitled)")
    expect(row.provider).toBe("(unknown institution)")
    expect(row.deadline).toBeNull()
  })
})

describe("decodeEntities", () => {
  test("decodes named, decimal and hex escapes", () => {
    expect(decodeEntities("W&uuml;rzburg &amp; Co &#8211; &#x20AC;500")).toBe(
      "Würzburg & Co – €500",
    )
  })

  // An unknown name must stay visible. A dropped character in a programme
  // title is invisible damage; a stray "&zwnj;" is a bug someone reports.
  test("leaves an unknown entity in place", () => {
    expect(decodeEntities("a &zwnj; b")).toBe("a &zwnj; b")
  })

  test("survives a malformed numeric escape", () => {
    expect(decodeEntities("&#99999999999; &#0;")).toBe("&#99999999999; &#0;")
  })
})
