import { parse, renderHelp, type Flags, type OptionMap } from "../argv.js"
import { BASE, emit, fetchWithRetry, parseSearchResults, writeError, type Studentship } from "../helpers.js"

/** Facet values read off the live search form; see url-reference.md. */
export const LEVEL_FACET: Record<string, string> = { phd: "phds", masters: "masters" }
export const ELIGIBILITY_FACETS = [
  "international-students",
  "eu-students",
  "uk-students",
  "self-funded-students",
] as const
export const PAGE_SIZE = 25

export const OPTIONS: OptionMap = {
  level: {
    type: "string",
    short: "l",
    description: "Studentship level",
    choices: ["phd", "masters"],
    default: "phd",
  },
  query: { type: "string", short: "q", description: "Keywords (title, description, supervisor)" },
  eligibility: {
    type: "string",
    description: "Who the funding is open to",
    choices: [...ELIGIBILITY_FACETS],
  },
  discipline: {
    type: "string",
    description: "Discipline slug, e.g. computer-sciences (repeatable)",
    repeatable: true,
  },
  location: { type: "string", description: "Region or city, as jobs.ac.uk spells it" },
  funded: {
    type: "boolean",
    description: "Drop listings that say self-funded; keeps 'unclear' ones, which are often funded",
  },
  "max-pages": { type: "number", description: "Result pages to walk (25 per page)", default: 1 },
  limit: { type: "number", description: "Cap the rows returned", default: 50 },
  format: { type: "string", short: "f", description: "Output format", choices: ["json", "table", "plain"], default: "json" },
  help: { type: "boolean", short: "h", description: "Show this help" },
}

/**
 * Build a `/search/` URL.
 *
 * `/search/phd` looks like the PhD board and is not one: it is a landing page
 * that **ignores `keywords` entirely** and mixes in university staff posts.
 * Searching it for "machine learning" returned a project-coordinator vacancy
 * and two unrelated studentships, all with a 200 and no error anywhere - the
 * silent-filter failure this codebase refuses to tolerate at the flag level,
 * happening instead at the HTTP level. The level therefore goes through
 * `jobTypeFacet[]`, which the form itself uses and which actually filters.
 *
 * `eligibility` is the facet that matters most for an applicant outside the
 * UK and EU: a studentship restricted to home students is not an opportunity,
 * and `international-students` is the only way to see that before fetching.
 */
export function buildUrl(flags: Flags, page = 1): string {
  const params = new URLSearchParams()
  if (flags["query"]) params.set("keywords", String(flags["query"]))

  const level = String(flags["level"] ?? "phd")
  params.append("jobTypeFacet[]", LEVEL_FACET[level] ?? LEVEL_FACET["phd"]!)

  if (flags["eligibility"]) params.append("fundingTypeFacet[]", String(flags["eligibility"]))
  const disciplines = flags["discipline"]
  if (Array.isArray(disciplines)) {
    for (const value of disciplines.flatMap((d) => d.split(","))) {
      params.append("academicDisciplineFacet[]", value.trim())
    }
  }
  if (flags["location"]) params.set("location", String(flags["location"]))

  params.set("pageSize", String(PAGE_SIZE))
  params.set("startIndex", String((page - 1) * PAGE_SIZE + 1))
  return `${BASE}/search/?${params.toString()}`
}

export async function run(argv: readonly string[]): Promise<number> {
  const flags = parse(argv, OPTIONS)
  if (flags["help"]) {
    process.stdout.write(renderHelp("jobsacuk-phd search", OPTIONS) + "\n")
    return 0
  }

  const pages = Math.max(1, Math.min(10, Number(flags["max-pages"] ?? 1)))
  const limit = Math.max(1, Number(flags["limit"] ?? 50))
  const level = String(flags["level"] ?? "phd")
  const rows: Studentship[] = []
  const seen = new Set<string>()

  for (let page = 1; page <= pages && rows.length < limit; page++) {
    let html: string
    try {
      const response = await fetchWithRetry(buildUrl(flags, page))
      if (!response.ok) {
        writeError(`jobs.ac.uk returned ${response.status} ${response.statusText}`, "API_ERROR")
        return 1
      }
      html = await response.text()
    } catch (error) {
      writeError(error instanceof Error ? error.message : String(error), "API_ERROR")
      return 1
    }
    const parsed = parseSearchResults(html, new Date(), level)
    // An empty page is the end of the result set, not a parser failure.
    if (parsed.length === 0) break
    // Paging past the last page re-serves the final page rather than 404ing,
    // so without this the walk would duplicate every row on it.
    const fresh = parsed.filter((row) => !seen.has(row.url))
    if (fresh.length === 0) break
    for (const row of fresh) seen.add(row.url)
    rows.push(...fresh)
  }

  // `--funded` drops only an *explicit* self-funded listing. A listing whose
  // funding line could not be read stays in: UK studentships state the
  // stipend in free prose, and dropping the unreadable ones would hide the
  // fully funded positions the filter exists to find.
  const filtered = (flags["funded"] === true ? rows.filter((r) => r.funded !== false) : rows).slice(0, limit)
  emit(filtered, String(flags["format"]))
  return 0
}
