# /notion-sync - Push the Shortlist and Applications to Notion

Mirrors the workspace into a Notion database, for users who want the board on
a phone.

## Prerequisites

A Notion integration token in `.env` as `NOTION_TOKEN`, and a database id as
`NOTION_DATABASE_ID`. Both are gitignored, and `.env` is in the settings
`deny` list — it is never read into the conversation. If either is missing,
say what to create and stop.

## Database shape

| Property | Type | Source |
|---|---|---|
| Name | title | `institution — program` |
| Level | select | masters / phd |
| Kind | select | program / scholarship |
| Country | select | |
| Status | select | the `/outcome` vocabulary, exactly |
| Fit score | number | |
| Funding status | select | |
| Deadline | date | |
| Next milestone | date | from `tools/deadline_board.py` |
| Next action | rich text | the milestone label |
| URL | url | |
| Blocking documents | rich text | from `tools/docs_checklist.py check` |

Create missing properties rather than silently dropping fields.

## Sync

1. Read `application_tracker.csv`, `program_search/seen_programs.json` and the
   deadline board.
2. Match existing Notion pages by URL, which is stable; never by title, which
   is edited.
3. Update matched pages, create unmatched ones.
4. **Never delete a Notion page.** The user may have added notes to it. Report
   orphans instead and let them decide.
5. Record the mapping in `program_search/notion_sync.json` (gitignored).

## Rules

- One-way: workspace → Notion. A status edited in Notion is not read back,
  because two sources of truth for an application status is how an applicant
  misses a deadline.
- Say that explicitly in the report, every run.
- Report created, updated, skipped and orphaned counts.
