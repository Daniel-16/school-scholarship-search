import { describe, expect, test } from "bun:test"
import { extractJsonLd, normalizePath, parseDetail } from "../src/commands/detail.js"

describe("normalizePath", () => {
  test("accepts a bare reference", () => {
    expect(normalizePath("dtk970")).toBe("/job/DTK970/")
  })

  test("accepts a jobs.ac.uk job URL", () => {
    expect(normalizePath("https://www.jobs.ac.uk/job/DTK970/phd-studentship")).toBe("/job/DTK970/phd-studentship")
  })

  // The archive records provenance; a /job/ path elsewhere is not this portal.
  test("rejects the same path on another host", () => {
    expect(normalizePath("https://evil.example.com/job/DTK970/x")).toBeNull()
  })

  test("rejects a non-http scheme and unparseable input", () => {
    expect(normalizePath("file:///etc/passwd")).toBeNull()
    expect(normalizePath("nonsense")).toBeNull()
  })

  // A loose alphanumeric rule turned a typo into a fetch and a 404; the
  // reference shape is letters then digits.
  test("rejects a word that is not reference-shaped", () => {
    expect(normalizePath("robotics")).toBeNull()
    expect(normalizePath("123456")).toBeNull()
  })
})

describe("extractJsonLd", () => {
  test("flattens a nested organisation to its name", () => {
    const html = `<script type="application/ld+json">
      {"@type":"JobPosting","title":"PhD in X","hiringOrganization":{"@type":"Organization","name":"Uni"}}
      </script>`
    expect(extractJsonLd(html)).toMatchObject({ title: "PhD in X", hiringOrganization: "Uni" })
  })

  // Malformed markup on one script must not stop the next one being read.
  test("skips a broken script and keeps going", () => {
    const html =
      `<script type="application/ld+json">{ not json </script>` +
      `<script type="application/ld+json">{"@type":"JobPosting","title":"Second"}</script>`
    expect(extractJsonLd(html)).toMatchObject({ title: "Second" })
  })

  test("returns an empty object when there is none", () => {
    expect(extractJsonLd("<html></html>")).toEqual({})
  })
})

describe("parseDetail", () => {
  test("prefers JSON-LD and falls back to the page", () => {
    const html =
      `<h1>Fallback Title</h1>` +
      `<script type="application/ld+json">{"@type":"JobPosting","title":"PhD in Robotics"}</script>` +
      `<dt>Hours</dt><dd>Full Time</dd>`
    const detail = parseDetail(html, "/job/DTK970/x", new Date(Date.UTC(2026, 9, 28)))
    expect(detail["award"]).toBe("PhD in Robotics")
    expect(detail["reference"]).toBe("DTK970")
    expect(detail["url"]).toBe("https://www.jobs.ac.uk/job/DTK970/x")
  })

  test("falls back to the h1 when there is no JSON-LD", () => {
    expect(parseDetail("<h1>Fallback Title</h1>", "/job/A1/x")["award"]).toBe("Fallback Title")
  })
})
