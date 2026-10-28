import { parse, renderHelp, type OptionMap, type Flags } from "../argv.js"
import { LEVEL_CODES, SEARCH_API, emit, fetchJson, normalizeCourse, writeError } from "../helpers.js"

export const OPTIONS: OptionMap = {
  level: {
    type: "string",
    short: "l",
    description: "Degree level",
    choices: ["masters", "phd"],
    default: "masters",
  },
  query: { type: "string", short: "q", description: "Free-text search over programme names and subjects" },
  subject: { type: "string", description: "DAAD subject-group code (see url-reference.md)", repeatable: true },
  language: {
    type: "string",
    description: "Language of instruction",
    choices: ["english", "german", "mixed"],
  },
  "tuition-free": { type: "boolean", description: "Only programmes with no tuition fees" },
  "with-scholarship": { type: "boolean", description: "Only programmes DAAD records a scholarship option for" },
  limit: { type: "number", description: "Results to return (1-100)", default: 25 },
  offset: { type: "number", description: "Skip this many results", default: 0 },
  format: { type: "string", short: "f", description: "Output format", choices: ["json", "table", "plain"], default: "json" },
  help: { type: "boolean", short: "h", description: "Show this help" },
}

const LANGUAGE_CODES: Record<string, string> = { english: "2", german: "1", mixed: "3" }

/** DAAD fee bracket 1 = "no tuition fees". See buildUrl for why this is named. */
export const TUITION_FREE_BRACKET = "1"

export function buildUrl(flags: Flags): string {
  const params = new URLSearchParams()
  params.set("display", "list")
  params.set("sort", "4")
  const limit = Math.max(1, Math.min(100, Number(flags["limit"] ?? 25)))
  params.set("limit", String(limit))
  params.set("offset", String(Math.max(0, Number(flags["offset"] ?? 0))))

  const level = String(flags["level"] ?? "masters")
  for (const code of LEVEL_CODES[level] ?? []) params.append("degree[]", code)

  if (flags["query"]) params.set("q", String(flags["query"]))
  const subjects = flags["subject"]
  if (Array.isArray(subjects)) {
    for (const value of subjects.flatMap((v) => v.split(","))) params.append("subjects[]", value.trim())
  }
  const language = flags["language"]
  if (typeof language === "string") params.append("lang[]", LANGUAGE_CODES[language]!)
  // DAAD's fee filter is a bracket, 1-4, and the brackets are cumulative
  // ceilings: 1 = no tuition fees (68 results on a sample query), 2 = 75,
  // 3 = 100, 4 = 116. There is no bracket 0.
  //
  // This was `fee=0` first, which the API accepts and answers with a 200 and
  // an empty result set - a search that looks successful and returns nothing.
  // That is the exact silent-filter failure this codebase refuses elsewhere,
  // arriving through a parameter *value* rather than a parameter name, and it
  // is why TUITION_FREE_BRACKET is a named constant with a test on it.
  if (flags["tuition-free"] === true) params.set("fee", TUITION_FREE_BRACKET)
  if (flags["with-scholarship"] === true) params.set("hasScholarship", "1")

  return `${SEARCH_API}?${params.toString()}`
}

export async function run(argv: readonly string[]): Promise<number> {
  const flags = parse(argv, OPTIONS)
  if (flags["help"]) {
    process.stdout.write(renderHelp("daad-programmes search", OPTIONS) + "\n")
    return 0
  }

  const url = buildUrl(flags)
  let payload: unknown
  try {
    payload = await fetchJson(url)
  } catch (error) {
    writeError(error instanceof Error ? error.message : String(error), "API_ERROR")
    return 1
  }

  const doc = (payload ?? {}) as Record<string, unknown>
  const courses = Array.isArray(doc["courses"]) ? (doc["courses"] as Record<string, unknown>[]) : []
  const level = String(flags["level"] ?? "masters")
  const rows = courses.map((course) => normalizeCourse(course, level))

  if (flags["format"] === "json") {
    process.stdout.write(
      JSON.stringify({ total: doc["numResults"] ?? null, count: rows.length, results: rows }, null, 2) + "\n",
    )
    return 0
  }
  emit(rows, String(flags["format"]), ["award", "provider", "level", "deadline", "url"])
  return 0
}
