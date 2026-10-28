import { describe, expect, test } from "bun:test"
import { dedupe, normalizeId, parseDetail, pickClass } from "../src/commands/detail.js"

const PAGE = `
<html><body>
  <h1 class="sr-only">Services</h1>
  <h1 class="c-banner-image__title">International Programmes 2026/2027</h1>
  <h1 class="c-detail-header__title">MSc in Artificial Intelligence MSc in Artificial Intelligence</h1>
  <h2 class="c-profile__title">Technical University of Applied Sciences</h2>
  <dl>
    <dt>Degree</dt><dd>Master of Science</dd>
    <dt>Course location</dt><dd>W&uuml;rzburg</dd>
    <dt>Teaching language</dt><dd>English</dd>
    <dt>Tuition fees per semester</dt><dd>None</dd>
    <dt>Application periods</dt><dd>15 October 2026 - 15 December 2026</dd>
    <dt>Academic admission requirements</dt><dd>A completed university degree with 210 ECTS</dd>
  </dl>
</body></html>`

describe("normalizeId", () => {
  test("accepts a bare id", () => {
    expect(normalizeId(" 7852 ")).toBe("7852")
  })

  test("accepts a DAAD detail URL", () => {
    expect(normalizeId("https://www2.daad.de/deutschland/studienangebote/international-programmes/en/detail/7852/"))
      .toBe("7852")
  })

  // The archive records where a listing came from. A matching path on another
  // host would be fetched and stored under a DAAD provenance it never had.
  test("rejects the same path on another host", () => {
    expect(normalizeId("https://evil.example.com/en/detail/7852/")).toBeNull()
  })

  test("rejects a non-http scheme and unparseable input", () => {
    expect(normalizeId("file:///etc/passwd")).toBeNull()
    expect(normalizeId("not a url")).toBeNull()
  })
})

describe("dedupe", () => {
  test("collapses DAAD's doubled header title", () => {
    expect(dedupe("MSc in AI MSc in AI")).toBe("MSc in AI")
  })

  test("leaves an ordinary title alone", () => {
    expect(dedupe("MSc in Artificial Intelligence")).toBe("MSc in Artificial Intelligence")
  })
})

describe("parseDetail", () => {
  const detail = parseDetail(PAGE, "7852")

  // Heading order reads the site's own chrome as the programme name; the
  // class anchor is what makes the field trustworthy.
  test("takes the title from its class, not from heading order", () => {
    expect(detail["award"]).toBe("MSc in Artificial Intelligence")
    expect(detail["provider"]).toBe("Technical University of Applied Sciences")
  })

  test("reads the definition list, unescaping entities", () => {
    expect(detail["city"]).toBe("Würzburg")
    expect(detail["degree"]).toBe("Master of Science")
    expect(detail["tuition"]).toBe("None")
    expect(detail["admission_requirements"]).toContain("210 ECTS")
  })

  test("parses the earliest dated deadline and keeps the raw text beside it", () => {
    expect(detail["deadline"]).toBe("2026-10-15")
    expect(detail["deadline_text"]).toContain("15 October 2026")
  })

  test("pickClass returns null rather than guessing when the anchor is absent", () => {
    expect(pickClass(PAGE, "c-no-such-class")).toBeNull()
  })
})
