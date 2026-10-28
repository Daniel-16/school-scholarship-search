import { parse, renderHelp, type OptionMap } from "../argv.js"
import { BASE, cleanText, fetchWithRetry, parseClosingDate, readFunded, writeError } from "../helpers.js"

export const OPTIONS: OptionMap = {
  id: { type: "string", short: "i", description: "Job reference, or a full jobs.ac.uk /job/ URL" },
  format: { type: "string", short: "f", description: "Output format", choices: ["json", "text"], default: "json" },
  help: { type: "boolean", short: "h", description: "Show this help" },
}

/**
 * A job reference or a jobs.ac.uk URL; anything else is rejected.
 *
 * The reference shape is pinned to letters-then-digits (DTK970, DSP806)
 * rather than "alphanumerics". A loose `[A-Z0-9]{4,}` accepted any word at
 * all - "nonsense" became `/job/NONSENSE/` - so a typo produced a fetch and
 * a 404 instead of an immediate, legible argument error.
 *
 * A /job/ path on another host is rejected for the same reason as in the
 * DAAD CLI: the archive records provenance.
 */
export function normalizePath(input: string): string | null {
  const trimmed = input.trim()
  if (/^[A-Z]{2,4}\d{2,6}$/i.test(trimmed)) return `/job/${trimmed.toUpperCase()}/`
  let url: URL
  try {
    url = new URL(/^[a-z0-9.-]+\.[a-z]{2,}(\/|$)/i.test(trimmed) ? `https://${trimmed}` : trimmed)
  } catch {
    return null
  }
  if (url.protocol !== "https:" && url.protocol !== "http:") return null
  if (url.hostname !== "www.jobs.ac.uk" && url.hostname !== "jobs.ac.uk") return null
  return /^\/job\/[^/]+/.test(url.pathname) ? url.pathname : null
}

export function parseDetail(html: string, path: string, reference = new Date()): Record<string, unknown> {
  const jsonLd = extractJsonLd(html)
  const labelled = (label: string): string | null => {
    const match = html.match(
      new RegExp(`<(?:dt|th|strong|span)[^>]*>\\s*${label}[^<]*</(?:dt|th|strong|span)>\\s*` +
                 `<?(?:dd|td|span|div)?[^>]*>?([\\s\\S]{0,400}?)</(?:dd|td|span|div|p)>`, "i"),
    )
    return cleanText(match?.[1])
  }

  const title = cleanText(html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/)?.[1])
  const funding = labelled("Funding for") ?? labelled("Salary") ?? (jsonLd["baseSalary"] as string | undefined) ?? null
  const deadlineText = labelled("Application Deadline") ?? labelled("Closes")

  return {
    reference: path.replace(/^\/job\/([^/]+).*$/, "$1"),
    url: `${BASE}${path}`,
    award: (jsonLd["title"] as string | undefined) ?? title,
    provider: (jsonLd["hiringOrganization"] as string | undefined) ?? labelled("Employer"),
    department: labelled("Department"),
    location: (jsonLd["jobLocation"] as string | undefined) ?? labelled("Location"),
    funding,
    funded: readFunded(typeof funding === "string" ? funding : null),
    hours: labelled("Hours"),
    contract: labelled("Contract Type"),
    qualification: labelled("Qualification Type"),
    deadline: parseClosingDate(deadlineText ?? (jsonLd["validThrough"] as string | undefined), reference),
    deadline_text: deadlineText,
    description: cleanText(
      html.match(/<div[^>]*class="[^"]*\bj-job-detail__main\b[^"]*"[^>]*>([\s\S]*?)<\/div>\s*<\/div>/)?.[1],
    )?.slice(0, 6000) ?? null,
  }
}

/**
 * jobs.ac.uk embeds schema.org JobPosting JSON-LD on most detail pages.
 *
 * It is read as a *hint*, never as the record: the markup is missing on some
 * listings and stale on others, and a nested object is flattened to its
 * `name` so a caller never has to care which shape it got.
 */
export function extractJsonLd(html: string): Record<string, unknown> {
  for (const match of html.matchAll(
    /<script[^>]+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi,
  )) {
    try {
      const parsed = JSON.parse(match[1]!) as unknown
      const nodes = Array.isArray(parsed) ? parsed : [parsed]
      for (const node of nodes) {
        if (!node || typeof node !== "object") continue
        const record = node as Record<string, unknown>
        if (record["@type"] !== "JobPosting") continue
        const flat: Record<string, unknown> = {}
        for (const [key, value] of Object.entries(record)) {
          if (value && typeof value === "object") {
            const name = (value as Record<string, unknown>)["name"]
            flat[key] = typeof name === "string" ? name : undefined
          } else {
            flat[key] = value
          }
        }
        return flat
      }
    } catch {
      // Malformed JSON-LD on one script must not stop the next one.
    }
  }
  return {}
}

export async function run(argv: readonly string[]): Promise<number> {
  const flags = parse(argv, OPTIONS)
  if (flags["help"]) {
    process.stdout.write(renderHelp("jobsacuk-phd detail", OPTIONS) + "\n")
    return 0
  }
  const raw = flags["id"]
  if (typeof raw !== "string" || !raw.trim()) {
    writeError("--id is required (a job reference or a jobs.ac.uk /job/ URL)", "MISSING_REQUIRED")
    return 1
  }
  const path = normalizePath(raw)
  if (!path) {
    writeError(`not a jobs.ac.uk job reference or URL: ${raw}`, "BAD_ARG")
    return 1
  }

  let html: string
  try {
    const response = await fetchWithRetry(`${BASE}${path}`)
    if (!response.ok) {
      writeError(`jobs.ac.uk returned ${response.status} for ${path}`, "API_ERROR")
      return 1
    }
    html = await response.text()
  } catch (error) {
    writeError(error instanceof Error ? error.message : String(error), "API_ERROR")
    return 1
  }

  const detail = parseDetail(html, path)
  if (flags["format"] === "json") {
    process.stdout.write(JSON.stringify(detail, null, 2) + "\n")
    return 0
  }
  for (const [key, value] of Object.entries(detail)) {
    if (value === null || value === undefined) continue
    process.stdout.write(`${key}: ${String(value)}\n`)
  }
  return 0
}
