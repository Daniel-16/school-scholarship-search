# DAAD International Programmes — endpoint notes

Recorded so the CLI's parameter choices can be re-derived rather than guessed
at when the portal changes.

## Search

```
GET https://www2.daad.de/deutschland/studienangebote/international-programmes/api/solr/en/search.json
```

JSON, no authentication, no key. Response: `{courses: [...], numResults: N, filter: {...}}`.

| Parameter | Notes |
|---|---|
| `degree[]` | `1` Bachelor, `2` Master, `3` PhD/doctoral programme, `4` graduate school, `5`–`10` language, short and preparatory courses. Repeatable. **This CLI only ever sends 2, 3 and 4.** |
| `q` | free text |
| `subjects[]` | subject-group code, repeatable |
| `lang[]` | `1` German, `2` English, `3` mixed |
| `fee` | Cumulative bracket, **1-4**. `1` = no tuition fees, rising to `4`. There is no bracket `0`: `fee=0` is accepted and returns an empty result set with a 200. Omitting it means "any". |
| `hasScholarship` | `1` = a scholarship option is recorded |
| `limit`, `offset` | paging; the API accepts up to 100 per page |
| `sort` | `4` is the default relevance/name order the site uses |
| `display` | `list` |

Counts observed 2026-10-28: Bachelor 362, Master 1765, PhD 147–172,
graduate school 25.

**Gotcha:** sending every filter parameter as an empty value (`&fos[]=&cert=&…`,
as the website's own form does) returns zero results. Send only the parameters
that have a value.

`filter.degree` in the response carries the live per-code counts, which is the
cheapest way to re-verify the code mapping above:

```bash
curl -s '.../search.json?limit=0&display=list&sort=4' | python3 -c \
  'import json,sys; print(json.load(sys.stdin)["filter"]["degree"])'
```

## Detail

```
GET https://www2.daad.de/deutschland/studienangebote/international-programmes/en/detail/<id>/
```

HTML, not JSON — there is no detail API. Two class anchors carry the header
(`c-detail-header__title`, `c-profile__title`); everything else is a run of
`<dt>`/`<dt>` pairs. Heading *order* is unusable: the first `<h1>` is a
screen-reader "Services" label and the second is a seasonal banner.

The title is rendered twice inside its element (desktop + mobile), so the raw
text is `"X X"`.

## Policy

`https://www.daad.de/robots.txt` publishes only a sitemap — no `Disallow`.
Requests are serial, retried only on 429/5xx with exponential backoff, and
identify themselves as `daad-programmes-cli/1.0`.
