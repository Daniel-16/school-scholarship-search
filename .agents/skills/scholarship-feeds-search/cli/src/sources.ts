/**
 * The feeds this CLI aggregates.
 *
 * All four are WordPress sites, which is what makes them usable without a
 * scraper: WordPress exposes `?s=<query>&feed=rss2` as a real, paginated
 * search feed, so the query runs on *their* index rather than being filtered
 * client-side out of a generic "latest 10" feed.
 *
 * These are **announcement aggregators, not funders.** They republish calls
 * from DAAD, Chevening, Commonwealth, universities and foundations, and the
 * republished copy is frequently out of date, occasionally wrong about
 * eligibility, and sometimes an outright scam reprint. Nothing from here is
 * ever treated as authoritative: every row carries `requires_verification:
 * true`, and /discover's gate is what the listing has to survive before it
 * reaches a shortlist.
 *
 * Chosen for coverage of applicants from Africa specifically - scholars4dev
 * and Opportunity Desk are the two most widely read among Nigerian
 * applicants, and Scholarship Region and Opportunities For Africans carry
 * regional calls the global sites skip.
 */
export interface Source {
  readonly id: string
  readonly name: string
  readonly base: string
  /** WordPress search-feed template; `{q}` is the URL-encoded query. */
  readonly search: string
  /** Feed of everything recent, for a no-query sweep. */
  readonly latest: string
  readonly note: string
}

export const SOURCES: readonly Source[] = [
  {
    id: "scholars4dev",
    name: "Scholarships for Development",
    base: "https://www.scholars4dev.com",
    search: "https://www.scholars4dev.com/?s={q}&feed=rss2",
    latest: "https://www.scholars4dev.com/feed/",
    note: "Development-focused; strong on master's and PhD scholarships for applicants from developing countries.",
  },
  {
    id: "opportunitydesk",
    name: "Opportunity Desk",
    base: "https://opportunitydesk.org",
    search: "https://opportunitydesk.org/?s={q}&feed=rss2",
    latest: "https://opportunitydesk.org/feed/",
    note: "Broad opportunities feed; filter hard, most items are not degree funding.",
  },
  {
    id: "scholarshipregion",
    name: "Scholarship Region",
    base: "https://scholarshipregion.com",
    search: "https://scholarshipregion.com/?s={q}&feed=rss2",
    latest: "https://scholarshipregion.com/feed/",
    note: "Heavy coverage of calls open to African applicants.",
  },
  {
    id: "opportunitiesforafricans",
    name: "Opportunities For Africans",
    base: "https://www.opportunitiesforafricans.com",
    search: "https://www.opportunitiesforafricans.com/?s={q}&feed=rss2",
    latest: "https://www.opportunitiesforafricans.com/feed/",
    note: "Africa-specific calls, including in-country and in-region schemes.",
  },
]

export function sourceById(id: string): Source | undefined {
  return SOURCES.find((s) => s.id === id)
}
