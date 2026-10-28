import { parse, renderHelp, type OptionMap } from "../argv.js"
import { SOURCES, sourceById, type Source } from "../sources.js"
import {
  callSignals, cleanText, deadlineContext, detectCountry, detectLevels, emit,
  fetchWithRetry, parseDeadline, parseRss, writeError, type Announcement, type RssItem,
} from "../helpers.js"

export const OPTIONS: OptionMap = {
  query: { type: "string", short: "q", description: "Search terms; omit to sweep each feed's latest items" },
  level: {
    type: "string",
    short: "l",
    description: "Keep only announcements for this level",
    choices: ["masters", "phd", "any-postgraduate"],
    default: "any-postgraduate",
  },
  source: {
    type: "string",
    description: `Limit to one feed (${SOURCES.map((s) => s.id).join(", ")}); repeatable`,
    repeatable: true,
  },
  since: { type: "string", description: "Drop items published before this ISO date" },
  "with-deadline": { type: "boolean", description: "Keep only items with a parseable deadline" },
  "calls-only": {
    type: "boolean",
    description: "Drop items that look like blog articles rather than funding calls",
  },
  limit: { type: "number", description: "Cap the rows returned", default: 40 },
  format: { type: "string", short: "f", description: "Output format", choices: ["json", "table", "plain"], default: "json" },
  help: { type: "boolean", short: "h", description: "Show this help" },
}

/** Undergraduate-only items are dropped before anything else sees them. */
export const EXCLUDED_LEVEL = "undergraduate"

export function feedUrl(source: Source, query: string | undefined): string {
  if (!query) return source.latest
  return source.search.replace("{q}", encodeURIComponent(query))
}

export function toAnnouncement(item: RssItem, source: Source): Announcement {
  const summary = cleanText(item.description)
  const haystack = `${item.title} ${summary ?? ""} ${item.categories.join(" ")}`
  const published = item.pubDate ? new Date(item.pubDate) : null
  const context = deadlineContext(haystack)
  const deadline = parseDeadline(context ?? haystack)
  return {
    award: item.title || "(untitled)",
    // The aggregator is not the funder, and the funder is rarely stated in a
    // parseable way. Left null rather than guessed at: /rank resolves it from
    // the real page, and a wrong funder name in the archive is worse than a
    // missing one.
    provider: null,
    kind: "scholarship",
    level: detectLevels(haystack),
    country: detectCountry(item.title, `${summary ?? ""} ${item.categories.join(" ")}`),
    field: null,
    deadline,
    deadline_text: context,
    published: published && !Number.isNaN(published.getTime()) ? published.toISOString().slice(0, 10) : null,
    url: item.link,
    source: source.name,
    portal: "scholarship-feeds",
    requires_verification: true,
    call_signals: callSignals(item.title, summary ?? "", Boolean(deadline)),
    summary: summary ? summary.slice(0, 600) : null,
  }
}

/**
 * Level filtering.
 *
 * An item whose level could not be detected is **kept**, not dropped: these
 * feeds are prose, many genuine master's calls never use the word, and a
 * silent drop would hide them with no trace. An item detected as
 * undergraduate-only is always dropped - this workspace has no use for it,
 * and it is the bulk of what the feeds carry.
 */
export function keepLevel(levels: string[], wanted: string): boolean {
  if (levels.length === 0) return true
  const postgraduate = levels.filter((l) => l !== EXCLUDED_LEVEL && l !== "postdoc")
  if (postgraduate.length === 0) return false
  if (wanted === "any-postgraduate") return true
  return postgraduate.includes(wanted)
}

export async function run(argv: readonly string[]): Promise<number> {
  const flags = parse(argv, OPTIONS)
  if (flags["help"]) {
    process.stdout.write(renderHelp("scholarship-feeds search", OPTIONS) + "\n")
    return 0
  }

  const requested = flags["source"]
  let sources: readonly Source[] = SOURCES
  if (Array.isArray(requested)) {
    const ids = requested.flatMap((s) => s.split(",")).map((s) => s.trim())
    const resolved: Source[] = []
    for (const id of ids) {
      const found = sourceById(id)
      if (!found) {
        writeError(`unknown source "${id}" - one of ${SOURCES.map((s) => s.id).join(", ")}`, "BAD_ARG")
        return 1
      }
      resolved.push(found)
    }
    sources = resolved
  }

  const query = typeof flags["query"] === "string" ? flags["query"] : undefined
  const wanted = String(flags["level"] ?? "any-postgraduate")
  const since = typeof flags["since"] === "string" ? flags["since"] : undefined
  const rows: Announcement[] = []
  const failures: { source: string; error: string }[] = []
  const seen = new Set<string>()

  // Feeds are fetched independently and a failure is reported, never fatal:
  // one aggregator being down must not cost the user the other three.
  for (const source of sources) {
    try {
      const response = await fetchWithRetry(feedUrl(source, query))
      if (!response.ok) {
        failures.push({ source: source.id, error: `HTTP ${response.status}` })
        continue
      }
      for (const item of parseRss(await response.text())) {
        if (!item.link || seen.has(item.link)) continue
        seen.add(item.link)
        const row = toAnnouncement(item, source)
        if (!keepLevel(row.level, wanted)) continue
        if (since && row.published && row.published < since) continue
        if (flags["with-deadline"] === true && !row.deadline) continue
        if (flags["calls-only"] === true && row.call_signals.length === 0) continue
        rows.push(row)
      }
    } catch (error) {
      failures.push({ source: source.id, error: error instanceof Error ? error.message : String(error) })
    }
  }

  rows.sort((a, b) => (b.published ?? "").localeCompare(a.published ?? ""))
  const limited = rows.slice(0, Math.max(1, Number(flags["limit"] ?? 40)))

  if (flags["format"] === "json") {
    process.stdout.write(
      JSON.stringify(
        {
          count: limited.length,
          sources: sources.map((s) => s.id),
          failed_sources: failures,
          verification_required: "Every row is an aggregator's republication. Confirm the award, "
            + "the eligibility and the deadline on the funder's own site before applying.",
          results: limited,
        },
        null,
        2,
      ) + "\n",
    )
  } else {
    emit(limited, String(flags["format"]))
    if (failures.length) {
      process.stdout.write(`(${failures.length} feed(s) unavailable: ${failures.map((f) => f.source).join(", ")})\n`)
    }
  }
  // Every feed failing is a failure; some failing is a degraded run.
  return failures.length === sources.length && sources.length > 0 ? 1 : 0
}
