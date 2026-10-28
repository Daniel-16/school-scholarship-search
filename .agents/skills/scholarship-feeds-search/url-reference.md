# Scholarship announcement feeds — endpoint notes

Every source is WordPress, which gives two stable endpoints per site with no
scraping:

```
GET <base>/feed/                      # latest items (~10)
GET <base>/?s=<urlencoded>&feed=rss2  # search feed, runs on the site's index
```

Verified 2026-10-28:

| Source | Base | Search feed returns |
|---|---|---|
| scholars4dev | `https://www.scholars4dev.com` | 10 items |
| opportunitydesk | `https://opportunitydesk.org` | 10 items |
| scholarshipregion | `https://scholarshipregion.com` | 10 items |
| opportunitiesforafricans | `https://www.opportunitiesforafricans.com` | 10 items |

Items are standard RSS 2.0: `<title>`, `<link>`, `<description>`,
`<pubDate>`, repeated `<category>`. Titles and descriptions are usually
CDATA-wrapped; the parser handles both forms.

## Why not the obvious portals

Checked and rejected while this was built:

| Portal | Why not |
|---|---|
| findaphd.com / findamasters.com | Cloudflare managed challenge on every request, including `robots.txt`. Not reachable without a browser. |
| scholarshipportal.com | Redirects; sibling `mastersportal.com` disallows `/search/*?kw`, which is exactly the keyword search. |
| euraxess.ec.europa.eu | `/jobs/search` renders results client-side; the HTML carries no listings and there is no public API. Worth revisiting with a browser tool. |
| DAAD scholarship database | JS-rendered. The DAAD *programmes* database has a real JSON API and is covered by `daad-programmes-search` instead. |

## Policy

All four feeds are published for syndication. Requests are serial, retried on
429, 5xx and transport failures, and identify themselves as
`scholarship-feeds-cli/1.0`. One failing feed does not stop the others.
