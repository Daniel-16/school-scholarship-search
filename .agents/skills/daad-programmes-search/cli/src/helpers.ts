/** Shared fetch, normalisation and output for the DAAD programmes CLI. */

export const BASE = "https://www2.daad.de/deutschland/studienangebote/international-programmes"
export const SEARCH_API = `${BASE}/api/solr/en/search.json`
export const USER_AGENT = "Mozilla/5.0 (compatible; daad-programmes-cli/1.0)"
export const TIMEOUT_MS = 20_000
export const ACCEPT = "application/json, text/html"

/** Level -> DAAD `degree[]` codes.
 *
 * Undergraduate codes (1 = Bachelor, 5/6/7/8/10 = language, short and
 * preparatory courses) are deliberately absent, not merely unused: this
 * workspace is for master's and doctoral study only, and a CLI that can be
 * asked for a Bachelor's programme will eventually be asked for one.
 *
 * `phd` sends 3 and 4 because DAAD splits doctoral study into standalone
 * PhD/doctoral programmes (3) and structured graduate schools (4). An
 * applicant looking for a doctorate wants both, and only the portal's own
 * taxonomy thinks they are different things.
 */
export const LEVEL_CODES: Record<string, readonly string[]> = {
  masters: ["2"],
  phd: ["3", "4"],
}

export interface Programme {
  readonly id: number | null
  readonly award: string
  readonly provider: string
  readonly kind: "program"
  readonly level: string
  readonly country: "Germany"
  readonly city: string | null
  readonly field: string | null
  readonly languages: string[]
  readonly duration: string | null
  readonly tuition: string | null
  readonly funding: string | null
  readonly deadline: string | null
  readonly deadline_text: string | null
  readonly url: string
  readonly portal: "daad-international-programmes"
}

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

export async function fetchJson(url: string): Promise<unknown> {
  const response = await fetchWithRetry(url)
  if (!response.ok) {
    throw new Error(`DAAD API returned ${response.status} ${response.statusText}`)
  }
  return response.json()
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

const MONTHS: Record<string, string> = {
  january: "01", february: "02", march: "03", april: "04", may: "05", june: "06",
  july: "07", august: "08", september: "09", october: "10", november: "11", december: "12",
}

/**
 * The earliest ISO date in a DAAD deadline string, or null.
 *
 * DAAD writes deadlines as prose: "Register by 31 May 2027 + 3 more",
 * "15 January 2027 (winter semester)". The *earliest* date is the one that
 * matters - it is the next door to close - and anything that does not parse
 * returns null rather than a guess, because the raw string is kept beside it
 * in `deadline_text` and a wrong date in a deadline board is worse than none.
 */
export function parseDeadline(text: string | null | undefined): string | null {
  if (!text) return null
  const found: string[] = []
  const pattern = /(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})/g
  for (const match of text.matchAll(pattern)) {
    const month = MONTHS[match[2]!.toLowerCase()]
    if (!month) continue
    const day = match[1]!.padStart(2, "0")
    found.push(`${match[3]}-${month}-${day}`)
  }
  for (const match of text.matchAll(/(\d{4})-(\d{2})-(\d{2})/g)) {
    found.push(match[0]!)
  }
  if (found.length === 0) return null
  return found.sort()[0]!
}

/**
 * Named HTML entities worth decoding by hand.
 *
 * The full HTML5 entity table is ~2200 names; this is the set that actually
 * appears in European university prose. Everything else is covered by the
 * numeric escape below, so an unlisted name degrades to being left visible
 * rather than silently mangled - and a visible "&zwnj;" in a programme title
 * is a bug report, where a dropped character is not.
 */
const ENTITIES: Record<string, string> = {
  amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " ", shy: "",
  auml: "\u00e4", ouml: "\u00f6", uuml: "\u00fc", Auml: "\u00c4", Ouml: "\u00d6",
  Uuml: "\u00dc", szlig: "\u00df", aring: "\u00e5", Aring: "\u00c5",
  aelig: "\u00e6", AElig: "\u00c6", oslash: "\u00f8", Oslash: "\u00d8",
  eacute: "\u00e9", egrave: "\u00e8", ecirc: "\u00ea", agrave: "\u00e0",
  ccedil: "\u00e7", ntilde: "\u00f1", iacute: "\u00ed", oacute: "\u00f3",
  uacute: "\u00fa", ndash: "\u2013", mdash: "\u2014", hellip: "\u2026",
  lsquo: "\u2018", rsquo: "\u2019", ldquo: "\u201c", rdquo: "\u201d",
  euro: "\u20ac", pound: "\u00a3", deg: "\u00b0", middot: "\u00b7", bull: "\u2022",
}

export function decodeEntities(text: string): string {
  return text.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (whole, body: string) => {
    if (body.startsWith("#")) {
      const code = body[1] === "x" || body[1] === "X"
        ? Number.parseInt(body.slice(2), 16)
        : Number.parseInt(body.slice(1), 10)
      // Surrogates and out-of-range code points would throw; a malformed
      // escape in a programme description must not take down the search.
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

/** Tag-stripped, entity-decoded, whitespace-folded text, or null if empty. */
export function cleanText(value: unknown): string | null {
  if (typeof value !== "string") return null
  // Tags first, then entities: decoding first would turn "&lt;script&gt;"
  // into a tag that the stripper then removes, losing the literal text the
  // page meant to show.
  const text = decodeEntities(value.replace(/<[^>]+>/g, " "))
    .replace(/\s+/g, " ")
    .trim()
  return text || null
}

/** One API course object -> the search-output contract /discover consumes. */
export function normalizeCourse(raw: Record<string, unknown>, level: string): Programme {
  const link = typeof raw["link"] === "string" ? raw["link"] : ""
  const dates = Array.isArray(raw["date"]) ? (raw["date"] as Record<string, unknown>[]) : []
  const registrationDeadlines = dates
    .map((d) => (typeof d["registrationDeadline"] === "string" ? d["registrationDeadline"] : null))
    .filter((d): d is string => Boolean(d))
    .sort()

  const deadlineText = cleanText(raw["applicationDeadline"])
  // The structured registrationDeadline is already ISO and is preferred over
  // parsing the prose field; the prose is only consulted when there is none.
  const deadline = registrationDeadlines[0] ?? parseDeadline(deadlineText)

  return {
    id: typeof raw["id"] === "number" ? raw["id"] : null,
    award: cleanText(raw["courseName"]) ?? "(untitled)",
    provider: cleanText(raw["academy"]) ?? "(unknown institution)",
    kind: "program",
    level,
    country: "Germany",
    city: cleanText(raw["city"]),
    field: cleanText(raw["subject"]),
    languages: Array.isArray(raw["languages"]) ? (raw["languages"] as string[]) : [],
    duration: cleanText(raw["programmeDuration"]),
    tuition: cleanText(raw["tuitionFees"]) ?? cleanText(raw["costString"]),
    funding: cleanText(raw["financialSupport"]),
    deadline,
    deadline_text: deadlineText,
    url: link ? `https://www2.daad.de${link}` : BASE,
    portal: "daad-international-programmes",
  }
}

/** Print in the format the caller asked for. JSON is the contract; the rest is for humans. */
export function emit(rows: unknown[], format: string, columns: readonly string[]): void {
  if (format === "json") {
    process.stdout.write(JSON.stringify(rows, null, 2) + "\n")
    return
  }
  if (rows.length === 0) {
    process.stdout.write("No results.\n")
    return
  }
  for (const row of rows as Record<string, unknown>[]) {
    if (format === "plain") {
      process.stdout.write(columns.map((c) => String(row[c] ?? "")).join("\t") + "\n")
      continue
    }
    process.stdout.write(`${row["award"]}\n`)
    process.stdout.write(`  ${row["provider"]}${row["city"] ? ` - ${row["city"]}` : ""}\n`)
    const bits = [
      row["level"] ? `level: ${row["level"]}` : "",
      row["deadline"] ? `deadline: ${row["deadline"]}` : "deadline: not stated",
      row["tuition"] ? `tuition: ${row["tuition"]}` : "",
    ].filter(Boolean)
    process.stdout.write(`  ${bits.join("  |  ")}\n`)
    process.stdout.write(`  ${row["url"]}\n\n`)
  }
}
