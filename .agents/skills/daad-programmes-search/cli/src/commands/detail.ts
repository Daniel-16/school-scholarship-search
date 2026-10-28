import { parse, renderHelp, type OptionMap } from "../argv.js"
import { BASE, cleanText, fetchWithRetry, parseDeadline, writeError } from "../helpers.js"

export const OPTIONS: OptionMap = {
  id: { type: "string", short: "i", description: "Programme id, or a full DAAD detail URL" },
  format: { type: "string", short: "f", description: "Output format", choices: ["json", "text"], default: "json" },
  help: { type: "boolean", short: "h", description: "Show this help" },
}

/**
 * Accept an id or a URL, but only a DAAD URL.
 *
 * A matching path on another host is not a DAAD programme: taking the id out
 * of an arbitrary URL would let a listing from somewhere else be fetched and
 * archived under a DAAD provenance, which is exactly the provenance the
 * /discover audit trail depends on.
 */
export function normalizeId(input: string): string | null {
  const trimmed = input.trim()
  if (/^\d+$/.test(trimmed)) return trimmed
  let url: URL
  try {
    url = new URL(/^[a-z0-9.-]+\.[a-z]{2,}(\/|$)/i.test(trimmed) ? `https://${trimmed}` : trimmed)
  } catch {
    return null
  }
  if (url.protocol !== "https:" && url.protocol !== "http:") return null
  if (url.hostname !== "www2.daad.de" && url.hostname !== "daad.de") return null
  const match = url.pathname.match(/\/detail\/(\d+)\/?$/)
  return match ? match[1]! : null
}

/**
 * Pull one class-anchored element's text out of the page.
 *
 * The anchors are DAAD's own BEM class names, which are far more stable than
 * element position: the first <h1> on the page is a screen-reader "Services"
 * label and the second is a seasonal banner, so heading order would read the
 * site's chrome as the programme's name - and did, until this was anchored.
 */
export function pickClass(html: string, className: string): string | null {
  const pattern = new RegExp(`<[a-z0-9]+[^>]*class="[^"]*\\b${className}\\b[^"]*"[^>]*>([\\s\\S]*?)</[a-z0-9]+>`, "i")
  const match = html.match(pattern)
  return match ? dedupe(cleanText(match[1])) : null
}

/**
 * DAAD renders the detail title twice inside one element, once for the
 * desktop layout and once for mobile, so the raw text comes out as "X X".
 *
 * Collapsing it is a halving of any exactly-doubled string, and that is
 * accepted rather than worked around: a programme genuinely named "Logic
 * Logic" would be halved too. The alternative is carrying every title twice
 * into the shortlist and the archive, which is wrong on every record instead
 * of on an imaginary one, and `fields` plus the live URL keep the raw page a
 * click away either way.
 */
export function dedupe(text: string | null): string | null {
  if (!text) return null
  const half = text.length / 2
  if (text.length % 2 === 1 && text[Math.floor(half)] === " ") {
    const left = text.slice(0, Math.floor(half))
    const right = text.slice(Math.ceil(half))
    if (left === right) return left
  }
  return text
}

/** Below the header, the record is a run of <dt>/<dd> pairs; that is the whole model. */
export function parseDetail(html: string, id: string): Record<string, unknown> {
  const fields: Record<string, string> = {}
  for (const match of html.matchAll(/<dt[^>]*>([\s\S]*?)<\/dt>\s*<dd[^>]*>([\s\S]*?)<\/dd>/g)) {
    const key = cleanText(match[1])
    const value = cleanText(match[2])
    if (key && value && !(key in fields)) fields[key] = value
  }

  const pick = (...needles: string[]): string | null => {
    for (const needle of needles) {
      const key = Object.keys(fields).find((k) => k.toLowerCase().includes(needle))
      if (key) return fields[key]!
    }
    return null
  }

  const deadlineText = pick("application period", "application deadline", "registration deadline")
  return {
    id,
    url: `${BASE}/en/detail/${id}/`,
    award: pickClass(html, "c-detail-header__title"),
    provider: pickClass(html, "c-profile__title"),
    degree: pick("degree"),
    city: pick("course location", "location"),
    language: pick("teaching language"),
    duration: pick("programme duration", "duration"),
    beginning: pick("beginning"),
    tuition: pick("tuition fee"),
    semester_contribution: pick("semester contribution"),
    living_costs: pick("costs of living"),
    funding: pick("funding opportunities", "funding"),
    admission_requirements: pick("academic admission requirements", "admission requirements"),
    english_requirements: pick("english language skills"),
    german_requirements: pick("german language skills"),
    deadline: parseDeadline(deadlineText),
    deadline_text: deadlineText,
    description: pick("description/content", "course objectives"),
    fields,
  }
}

export async function run(argv: readonly string[]): Promise<number> {
  const flags = parse(argv, OPTIONS)
  if (flags["help"]) {
    process.stdout.write(renderHelp("daad-programmes detail", OPTIONS) + "\n")
    return 0
  }
  const raw = flags["id"]
  if (typeof raw !== "string" || !raw.trim()) {
    writeError("--id is required (a programme id or a www2.daad.de detail URL)", "MISSING_REQUIRED")
    return 1
  }
  const id = normalizeId(raw)
  if (!id) {
    writeError(`not a DAAD programme id or detail URL: ${raw}`, "BAD_ARG")
    return 1
  }

  let html: string
  try {
    const response = await fetchWithRetry(`${BASE}/en/detail/${id}/`)
    if (!response.ok) {
      writeError(`DAAD returned ${response.status} for programme ${id}`, "API_ERROR")
      return 1
    }
    html = await response.text()
  } catch (error) {
    writeError(error instanceof Error ? error.message : String(error), "API_ERROR")
    return 1
  }

  const detail = parseDetail(html, id)
  if (flags["format"] === "json") {
    process.stdout.write(JSON.stringify(detail, null, 2) + "\n")
    return 0
  }
  for (const [key, value] of Object.entries(detail)) {
    if (key === "fields" || value === null) continue
    process.stdout.write(`${key}: ${String(value)}\n`)
  }
  return 0
}
