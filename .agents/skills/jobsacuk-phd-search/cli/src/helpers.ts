/** Fetch and HTML normalisation for the jobs.ac.uk PhD studentship listings. */

export const BASE = "https://www.jobs.ac.uk"
export const USER_AGENT = "Mozilla/5.0 (compatible; jobsacuk-phd-cli/1.0)"
export const TIMEOUT_MS = 30_000
export const ACCEPT = "text/html"

export interface Studentship {
  readonly id: string | null
  readonly award: string
  readonly provider: string
  readonly kind: "program"
  readonly level: string
  readonly country: string | null
  readonly location: string | null
  readonly department: string | null
  readonly field: string | null
  readonly funding: string | null
  readonly funded: boolean | null
  readonly posted: string | null
  readonly deadline: string | null
  readonly deadline_text: string | null
  readonly url: string
  readonly portal: "jobs.ac.uk"
}

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

/**
 * Retry what is worth retrying: 429, 5xx, **and transport failures**.
 *
 * The transport half is not defensive padding. A timeout or a reset arrives
 * as a thrown exception rather than a Response, so a loop that only inspects
 * `response.status` does not retry it at all - and that is the failure mode
 * these portals actually have. jobs.ac.uk serves a 490 KB search page and
 * intermittently hangs on it: two identical requests a second apart, one
 * returning in 2.7 s and the next timing out, was reproducible while this
 * was written. Without this branch a whole `/discover` run reports the
 * portal as down because of one bad socket.
 *
 * A 404 or a 403 is still an answer, and is returned rather than retried:
 * hammering a wrong URL turns a mistake into a rate-limit ban.
 */
export async function fetchWithRetry(url: string, maxRetries = 4): Promise<Response> {
  let delay = 500
  let lastError: unknown
  for (let attempt = 0; ; attempt++) {
    try {
      const response = await fetch(url, {
        headers: { "User-Agent": USER_AGENT, Accept: ACCEPT },
        signal: AbortSignal.timeout(TIMEOUT_MS),
      })
      if (response.status !== 429 && response.status < 500) return response
      lastError = new Error(`HTTP ${response.status} ${response.statusText}`)
    } catch (error) {
      lastError = error
    }
    if (attempt >= maxRetries) {
      const reason = lastError instanceof Error ? lastError.message : String(lastError)
      throw new Error(`Request failed after ${maxRetries + 1} attempts: ${reason}`)
    }
    await new Promise((resolve) => setTimeout(resolve, delay + Math.floor(Math.random() * 400)))
    delay = Math.min(delay * 2, 5000)
  }
}

const ENTITIES: Record<string, string> = {
  amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " ", shy: "",
  pound: "£", euro: "€", ndash: "–", mdash: "—", hellip: "…",
  lsquo: "‘", rsquo: "’", ldquo: "“", rdquo: "”", deg: "°",
  eacute: "é", uuml: "ü", ouml: "ö", auml: "ä",
}

export function decodeEntities(text: string): string {
  return text.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (whole, body: string) => {
    if (body.startsWith("#")) {
      const code = body[1] === "x" || body[1] === "X"
        ? Number.parseInt(body.slice(2), 16)
        : Number.parseInt(body.slice(1), 10)
      if (!Number.isFinite(code) || code <= 0 || code > 0x10ffff) return whole
      try {
        return String.fromCodePoint(code)
      } catch {
        return whole
      }
    }
    return ENTITIES[body] ?? ENTITIES[body.toLowerCase()] ?? whole
  })
}

export function cleanText(value: string | null | undefined): string | null {
  if (typeof value !== "string") return null
  const text = decodeEntities(value.replace(/<[^>]+>/g, " ")).replace(/\s+/g, " ").trim()
  return text || null
}

const MONTHS: Record<string, string> = {
  jan: "01", feb: "02", mar: "03", apr: "04", may: "05", jun: "06",
  jul: "07", aug: "08", sep: "09", oct: "10", nov: "11", dec: "12",
}

/**
 * Resolve jobs.ac.uk's year-less closing dates, e.g. "10 Nov".
 *
 * The year has to be inferred, and both possible errors are real:
 *
 *   roll forward too eagerly   a listing that closed last week is recorded
 *                              as closing in eleven months, so it enters the
 *                              shortlist with a comfortable deadline and is
 *                              never swept as expired;
 *   never roll forward         a December listing read in January is dated
 *                              to a month that has already gone.
 *
 * So a day-month in the recent past keeps the current year - boards do keep
 * a listing visible for a few days after it closes, and dating it correctly
 * lets the sweep expire it - while anything further back rolls forward.
 * GRACE_DAYS is where the two errors trade off.
 *
 * `reference` is injectable so the rule is testable without waiting a year.
 */
export const GRACE_DAYS = 7

export function parseClosingDate(text: string | null | undefined, reference = new Date()): string | null {
  if (!text) return null
  const iso = text.match(/(\d{4})-(\d{2})-(\d{2})/)
  if (iso) return iso[0]!

  const match = text.match(/(\d{1,2})\s+([A-Za-z]{3})[a-z]*\.?(?:\s+(\d{4}))?/)
  if (!match) return null
  const month = MONTHS[match[2]!.toLowerCase()]
  if (!month) return null
  const day = match[1]!.padStart(2, "0")
  if (match[3]) return `${match[3]}-${month}-${day}`

  const year = reference.getUTCFullYear()
  const candidate = Date.UTC(year, Number(month) - 1, Number(day))
  const daysBehind = (Date.UTC(year, reference.getUTCMonth(), reference.getUTCDate()) - candidate) / 86_400_000
  const resolved = daysBehind > GRACE_DAYS ? year + 1 : year
  return `${resolved}-${month}-${day}`
}


/**
 * Is the studentship funded, from the funding line alone?
 *
 * Three answers, not two. `false` is reserved for a listing that says it is
 * unfunded or self-funded; a line this cannot read returns `null`, because
 * "we could not tell" and "there is no money" are different facts and only
 * one of them should keep a listing out of a shortlist.
 */
export function readFunded(funding: string | null): boolean | null {
  if (!funding) return null
  const text = funding.toLowerCase()
  if (/\b(self[- ]funded|unfunded|no funding|fees only.*no stipend)\b/.test(text)) return false
  if (/\b(stipend|fully funded|funded|studentship|bursary|tax[- ]free|scholarship)\b/.test(text)) return true
  if (/[£$€]\s?[\d,]{4,}/.test(text)) return true
  return null
}

/**
 * Country from a location string, or null.
 *
 * jobs.ac.uk is a UK board but not a UK-only one - Aarhus, Delft and Max
 * Planck positions appear on it routinely. Defaulting an unrecognised
 * location to "United Kingdom" put a Danish studentship in the shortlist as
 * British, which is exactly the kind of quiet wrong answer that survives all
 * the way to a visa plan.
 *
 * So only an explicit, unambiguous signal names a country. Everything else
 * is null, and `location` carries the raw string for /rank to resolve.
 */
export function inferCountry(location: string | null): string | null {
  if (!location) return null
  const text = location.toLowerCase()
  for (const [pattern, country] of NON_UK_HINTS) {
    if (pattern.test(text)) return country
  }
  if (/\b(united kingdom|uk|england|scotland|wales|northern ireland)\b/.test(text)) return "United Kingdom"
  if (/\b(ireland|dublin|cork|galway)\b/.test(text)) return "Ireland"
  return null
}

/**
 * A short list, on purpose. It exists to stop the most common
 * misattributions, not to be a gazetteer: an unlisted city returns null,
 * which is the correct answer rather than a degraded one.
 */
const NON_UK_HINTS: ReadonlyArray<readonly [RegExp, string]> = [
  [/\b(denmark|copenhagen|aarhus|odense|lyngby)\b/, "Denmark"],
  [/\b(netherlands|amsterdam|delft|eindhoven|utrecht|leiden|groningen|wageningen)\b/, "Netherlands"],
  [/\b(germany|berlin|munich|m\u00fcnchen|hamburg|heidelberg|aachen|dresden)\b/, "Germany"],
  [/\b(sweden|stockholm|lund|uppsala|gothenburg|g\u00f6teborg)\b/, "Sweden"],
  [/\b(norway|oslo|bergen|trondheim)\b/, "Norway"],
  [/\b(finland|helsinki|espoo|tampere)\b/, "Finland"],
  [/\b(switzerland|zurich|z\u00fcrich|lausanne|geneva|basel)\b/, "Switzerland"],
  [/\b(belgium|brussels|leuven|ghent|antwerp)\b/, "Belgium"],
  [/\b(france|paris|lyon|toulouse|grenoble|marseille)\b/, "France"],
  [/\b(austria|vienna|graz|innsbruck)\b/, "Austria"],
  [/\b(spain|madrid|barcelona|valencia)\b/, "Spain"],
  [/\b(italy|rome|milan|turin|bologna|trento)\b/, "Italy"],
  [/\b(portugal|lisbon|porto)\b/, "Portugal"],
  [/\b(luxembourg)\b/, "Luxembourg"],
  [/\b(qatar|doha|dubai|abu dhabi|saudi|riyadh|kaust)\b/, "Middle East"],
  [/\b(australia|sydney|melbourne|brisbane|perth)\b/, "Australia"],
  [/\b(canada|toronto|vancouver|montreal|ottawa)\b/, "Canada"],
  [/\b(china|hong kong|singapore|japan|tokyo)\b/, "Asia"],
]

/** The search page is a repeating `j-search-result` block; that is the model. */
export function parseSearchResults(
  html: string,
  reference = new Date(),
  level: string = "phd",
): Studentship[] {
  const results: Studentship[] = []
  const blocks = html.split(/<div class="j-search-result__result[^"]*"/).slice(1)

  for (const block of blocks) {
    const link = block.match(/<a href="(\/job\/[^"]+)"[^>]*>([\s\S]*?)<\/a>/)
    if (!link) continue
    const href = link[1]!
    const award = cleanText(link[2])
    if (!award) continue

    const field = (name: string): string | null => {
      const match = block.match(new RegExp(`<div class="j-search-result__${name}"[^>]*>([\\s\\S]*?)</div>`))
      return cleanText(match?.[1])
    }
    const labelled = (label: string): string | null => {
      const match = block.match(new RegExp(`<strong>${label}:\\s*</strong>([\\s\\S]*?)</div>`))
      return cleanText(match?.[1])
    }

    const location = cleanText(block.match(/<div>Location:([\s\S]*?)<\/div>/)?.[1])
    const funding = field("info") ?? labelled("Salary")
    const closingMatch = block.match(
      /j-search-result__date-span[^>]*>\s*Closes\s*<\/span>\s*<span[^>]*>([\s\S]*?)<\/span>/,
    )
    const deadlineText = cleanText(closingMatch?.[1])
    const idMatch = href.match(/^\/job\/([A-Z0-9]+)\//i)

    results.push({
      id: idMatch?.[1] ?? null,
      award,
      provider: field("employer") ?? "(unknown institution)",
      kind: "program",
      level,
      country: inferCountry(location),
      location,
      department: field("department"),
      field: field("department"),
      funding: funding?.replace(/^Salary:\s*/i, "") ?? null,
      funded: readFunded(funding),
      posted: parseClosingDate(labelled("Date Placed"), reference),
      deadline: parseClosingDate(deadlineText, reference),
      deadline_text: deadlineText,
      url: `${BASE}${href}`,
      portal: "jobs.ac.uk",
    })
  }
  return results
}

export function emit(rows: Studentship[], format: string): void {
  if (format === "json") {
    process.stdout.write(JSON.stringify({ count: rows.length, results: rows }, null, 2) + "\n")
    return
  }
  if (rows.length === 0) {
    process.stdout.write("No results.\n")
    return
  }
  for (const row of rows) {
    if (format === "plain") {
      process.stdout.write([row.award, row.provider, row.deadline ?? "", row.url].join("\t") + "\n")
      continue
    }
    process.stdout.write(`${row.award}\n`)
    process.stdout.write(`  ${row.provider}${row.location ? ` - ${row.location}` : ""}\n`)
    const funded = row.funded === true ? "funded" : row.funded === false ? "SELF-FUNDED" : "funding unclear"
    process.stdout.write(`  ${funded}  |  closes: ${row.deadline ?? "not stated"}\n`)
    if (row.funding) process.stdout.write(`  ${row.funding.slice(0, 120)}\n`)
    process.stdout.write(`  ${row.url}\n\n`)
  }
}
