# jobs.ac.uk — endpoint notes

## Search

```
GET https://www.jobs.ac.uk/search/
```

HTML. The parameters below were read off the live search form
(`<form action="/search/">`) and from the `searchUri` the page writes into
its own markup, which is the cheapest way to re-derive them:

```bash
curl -s https://www.jobs.ac.uk/search/phd | grep -o "searchUri = '[^']*'"
```

| Parameter | Values |
|---|---|
| `keywords` | free text |
| `jobTypeFacet[]` | `phds`, `masters` |
| `qualificationTypeFacet[]` | `phd`, `international-doctorate`, `professional-doctorate`, `integrated-masters-doctorate` |
| `fundingTypeFacet[]` | `international-students`, `eu-students`, `uk-students`, `self-funded-students` |
| `academicDisciplineFacet[]` | `computer-sciences`, `engineering-and-technology`, `biological-sciences`, `health-and-medical`, `economics`, `law`, … |
| `contractTypeFacet[]`, `hoursTypeFacet[]`, `locationFacet[]`, `salaryBandFacet[]`, `workplaceFacet[]` | further facets, unused here |
| `location`, `distance`, `placeId` | geographic search |
| `pageSize`, `startIndex`, `sortOrder` | paging; `startIndex` is 1-based |

**`/search/phd` ignores `keywords`.** It is a landing page, not a filtered
board, and it mixes university staff vacancies into the results. Searching it
for "machine learning" returned a project-coordinator post and two unrelated
studentships, with a 200 and no error. Always use `/search/` plus
`jobTypeFacet[]`.

**Paging past the last page re-serves the final page** rather than returning
404 or an empty set, so the walk de-duplicates by URL and stops when a page
adds nothing new.

## Result markup

Each result is a `<div class="j-search-result__result">` containing
`j-search-result__text` (link, `__department`, `__employer`, `Location:`,
`__info` with the salary/funding line, `Date Placed:`) and
`j-search-result__date-logos` (a `Closes` label followed by the date).

## Detail

```
GET https://www.jobs.ac.uk/job/<REFERENCE>/<slug>
```

Most detail pages embed schema.org `JobPosting` JSON-LD. It is read as a hint
and the rendered markup is the fallback: the markup is absent on some
listings and stale on others.

## Policy

`robots.txt` disallows only `/job/feedback/` and `/enhanced/fp/`; `/search/`
and `/job/` are permitted. Requests are serial, retried on 429, 5xx **and
transport failures**, and identify themselves as `jobsacuk-phd-cli/1.0`.
