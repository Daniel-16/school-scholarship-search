/** Feed fetching, RSS parsing and level/deadline extraction for scholarship announcements. */

export const USER_AGENT = "Mozilla/5.0 (compatible; scholarship-feeds-cli/1.0)"
export const ACCEPT = "application/rss+xml, application/xml, text/xml"
export const TIMEOUT_MS = 25_000

export interface Announcement {
  readonly award: string
  readonly provider: string | null
  readonly kind: "scholarship"
  readonly level: string[]
  readonly country: string | null
  readonly field: string | null
  readonly deadline: string | null
  readonly deadline_text: string | null
  readonly published: string | null
  readonly url: string
  readonly source: string
  readonly portal: "scholarship-feeds"
  /** Always true. An aggregator republishes; it does not administer. */
  readonly requires_verification: true
  /** Evidence that this is a call rather than a blog article; see callSignals. */
  readonly call_signals: string[]
  readonly summary: string | null
}

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

export async function fetchWithRetry(url: string, maxRetries = 3): Promise<Response> {
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
    delay = Math.min(delay * 2, 4000)
  }
}

const ENTITIES: Record<string, string> = {
  amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " ", shy: "",
  pound: "£", euro: "€", ndash: "–", mdash: "—", hellip: "…",
  lsquo: "‘", rsquo: "’", ldquo: "“", rdquo: "”", deg: "°",
  eacute: "é", uuml: "ü", ouml: "ö", auml: "ä", ccedil: "ç",
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

export interface RssItem {
  title: string
  link: string
  description: string
  pubDate: string
  categories: string[]
}

function tagText(xml: string, tag: string): string {
  const cdata = xml.match(new RegExp(`<${tag}[^>]*><!\\[CDATA\\[([\\s\\S]*?)\\]\\]></${tag}>`))
  if (cdata) return cdata[1]!.trim()
  const plain = xml.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`))
  return plain ? plain[1]!.trim() : ""
}

export function parseRss(xml: string): RssItem[] {
  const items: RssItem[] = []
  for (const match of xml.matchAll(/<item[\s>][\s\S]*?<\/item>/g)) {
    const block = match[0]!
    const categories = [...block.matchAll(/<category[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/category>/g)]
      .map((m) => cleanText(m[1]))
      .filter((c): c is string => Boolean(c))
    items.push({
      title: cleanText(tagText(block, "title")) ?? "",
      link: tagText(block, "link"),
      description: tagText(block, "description"),
      pubDate: tagText(block, "pubDate"),
      categories,
    })
  }
  return items
}

const MONTHS: Record<string, string> = {
  january: "01", february: "02", march: "03", april: "04", may: "05", june: "06",
  july: "07", august: "08", september: "09", october: "10", november: "11", december: "12",
  jan: "01", feb: "02", mar: "03", apr: "04", jun: "06", jul: "07", aug: "08",
  sep: "09", sept: "09", oct: "10", nov: "11", dec: "12",
}

/**
 * A deadline out of announcement prose, or null.
 *
 * Aggregator copy writes deadlines every way there is: "Deadline: 15 January
 * 2027", "Application Deadline: January 15, 2027", "closes 15/01/2027". Only
 * a date carrying an explicit **year** is accepted. A year-less date cannot
 * be inferred here the way a job board's can - a scholarship announcement is
 * routinely republished for an intake two years out - and a wrong deadline
 * on a scholarship is a missed cycle, not a minor error.
 */
export function parseDeadline(text: string | null | undefined): string | null {
  if (!text) return null
  const found: string[] = []

  for (const m of text.matchAll(/(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})/g)) {
    const month = MONTHS[m[2]!.toLowerCase()]
    if (month) found.push(`${m[3]}-${month}-${m[1]!.padStart(2, "0")}`)
  }
  for (const m of text.matchAll(/([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})/g)) {
    const month = MONTHS[m[1]!.toLowerCase()]
    if (month) found.push(`${m[3]}-${month}-${m[2]!.padStart(2, "0")}`)
  }
  for (const m of text.matchAll(/(\d{4})-(\d{2})-(\d{2})/g)) found.push(m[0]!)
  // dd/mm/yyyy only. US-style mm/dd/yyyy is indistinguishable from it below
  // the 13th, and a coin-flip between two readings is not a deadline.
  for (const m of text.matchAll(/\b(\d{1,2})\/(\d{1,2})\/(\d{4})\b/g)) {
    const day = Number(m[1]), month = Number(m[2])
    if (day > 12 && month <= 12) {
      found.push(`${m[3]}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`)
    }
  }
  if (found.length === 0) return null
  return found.sort()[0]!
}

/** The deadline sentence, kept beside the parsed date so a human can check it. */
export function deadlineContext(text: string): string | null {
  const match = text.match(/[^.\n]{0,120}\b(?:deadline|closes?|closing date|apply by|last date)\b[^.\n]{0,120}/i)
  return cleanText(match?.[0]) ?? null
}

/**
 * Which degree levels an announcement is for.
 *
 * Returns the levels found, which may be several ("Masters and PhD
 * scholarships" is the single most common shape in this corpus) or none.
 * Undergraduate is detected *in order to exclude*, never to offer: it is the
 * bulk of what these feeds carry, and `--level` filtering depends on being
 * able to recognise it.
 */
export function detectLevels(text: string): string[] {
  const haystack = text.toLowerCase()
  const levels: string[] = []
  if (/\b(master'?s?|msc|m\.sc|ma\b|mba|mphil|postgraduate taught|graduate programme)\b/.test(haystack)) {
    levels.push("masters")
  }
  if (/\b(ph\.?d|doctoral|doctorate|dphil)\b/.test(haystack)) levels.push("phd")
  if (/\b(undergraduate|bachelor'?s?|bsc|b\.sc|ba\b|first degree|diploma)\b/.test(haystack)) {
    levels.push("undergraduate")
  }
  if (/\b(post[- ]?doc|postdoctoral)\b/.test(haystack)) levels.push("postdoc")
  return [...new Set(levels)]
}

/**
 * Country or region, read from the title first and the body only as a
 * fallback.
 *
 * Scanning the whole announcement and taking the first pattern to match made
 * the answer depend on the order of the pattern list rather than on the
 * announcement: "Swedish Institute Scholarship for Global Professionals"
 * came back as United States, because the body mentioned America and the US
 * pattern happened to be checked before the Swedish one. The title is where
 * an announcement names its destination, so the title is scanned on its own
 * first, and a title that names nothing is a better reason to return the
 * body's guess than the body is to override the title.
 *
 * `u.s.` and `america` are gone from the patterns: both fire on prose about
 * applicants rather than destinations ("open to students across the
 * Americas"), and the precise forms still match.
 */
const COUNTRY_PATTERNS: ReadonlyArray<readonly [RegExp, string]> = [
  [/\b(united kingdom|britain|england|scotland|wales)\b|\bUK\b/, "United Kingdom"],
  [/\bunited states\b|\bUSA\b/, "United States"],
  [/\bgerman(?:y|ic)?\b|\bDAAD\b/i, "Germany"],
  [/\b(netherlands|dutch|holland)\b/i, "Netherlands"],
  [/\b(sweden|swedish)\b/i, "Sweden"],
  [/\b(norway|norwegian)\b/i, "Norway"],
  [/\b(denmark|danish)\b/i, "Denmark"],
  [/\b(finland|finnish)\b/i, "Finland"],
  [/\b(switzerland|swiss)\b/i, "Switzerland"],
  [/\b(belgium|belgian)\b/i, "Belgium"],
  [/\b(ireland|irish)\b/i, "Ireland"],
  [/\b(canada|canadian)\b/i, "Canada"],
  [/\b(australia|australian)\b/i, "Australia"],
  [/\b(france|french)\b/i, "France"],
  [/\b(italy|italian)\b/i, "Italy"],
  [/\b(spain|spanish)\b/i, "Spain"],
  [/\b(japan|japanese)\b|\bMEXT\b/, "Japan"],
  [/\b(china|chinese)\b/i, "China"],
  [/\b(korea|korean)\b/i, "South Korea"],
  [/\bnew zealand\b/i, "New Zealand"],
  [/\b(turkey|t(?:ü|u)rkiye)\b/i, "Turkey"],
  [/\berasmus mundus\b|\beurope(?:an)?\b/i, "Europe"],
]

function matchCountry(text: string): string | null {
  for (const [pattern, country] of COUNTRY_PATTERNS) {
    if (pattern.test(text)) return country
  }
  return null
}

export function detectCountry(title: string, body = ""): string | null {
  return matchCountry(title) ?? (body ? matchCountry(body) : null)
}

/**
 * Does this item look like an actual funding call?
 *
 * These feeds are blogs. Alongside the calls they carry listicles ("Top UK
 * Universities Offering Scholarships"), how-to posts and success stories
 * ("Young Lady won Erasmus Mundus Scholarship, here is how she did it"),
 * and all three match every scholarship keyword there is.
 *
 * So the signals are the things a *call* has and an article does not: a
 * stated deadline, an explicit open-for-applications phrase, or a funding
 * claim attached to a year. The returned list is the evidence, so a user can
 * see why an item was or was not treated as a call rather than trusting a
 * bare boolean - and `--calls-only` is opt-in, because the cost of this
 * being wrong is a missed award.
 */
export function callSignals(title: string, body: string, hasDeadline: boolean): string[] {
  const signals: string[] = []
  const text = `${title} ${body}`
  if (hasDeadline) signals.push("deadline_stated")
  if (/\b(applications?\s+(?:are\s+)?(?:now\s+)?open|now\s+accepting|call for applications|apply now|invites applications)\b/i.test(text)) {
    signals.push("applications_open")
  }
  if (/\b(fully[- ]funded|fully funded|full scholarship|covers? (?:tuition|full tuition)|monthly stipend)\b/i.test(text)) {
    signals.push("funding_stated")
  }
  if (/\b(eligibility|eligible candidates?|who can apply|requirements?)\b/i.test(text)) {
    signals.push("eligibility_stated")
  }
  // A title that is a question or a superlative is an article, not a call.
  if (/^(top|best|how to|why|what|\d+\s+(?:best|top))\b/i.test(title.trim()) || /\?$/.test(title.trim())) {
    return signals.filter((s) => s === "deadline_stated")
  }
  return signals
}

export function emit(rows: Announcement[], format: string): void {
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
      process.stdout.write([row.award, row.level.join("+"), row.deadline ?? "", row.url].join("\t") + "\n")
      continue
    }
    process.stdout.write(`${row.award}\n`)
    const bits = [
      row.level.length ? row.level.join(", ") : "level unclear",
      row.country ?? "country unclear",
      `deadline: ${row.deadline ?? row.deadline_text ?? "not stated"}`,
    ]
    process.stdout.write(`  ${bits.join("  |  ")}\n`)
    const article = row.call_signals.length === 0 ? "  (looks like an article, not a call)\n" : ""
    process.stdout.write(article)
    process.stdout.write(`  via ${row.source} - VERIFY on the funder's own site before applying\n`)
    process.stdout.write(`  ${row.url}\n\n`)
  }
}
