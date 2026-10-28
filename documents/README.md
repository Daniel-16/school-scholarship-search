# documents/ — everything the workspace needs from you

Drop your real files in here. Nothing in this directory is committed (see
`.gitignore`): only the folder structure and this README are tracked. The
workspace reads *names and counts* from these folders — it never sends a
transcript or a passport scan anywhere, and `/documents` prints file names,
never file contents.

Run this at any time to see where you stand:

```bash
python3 tools/docs_checklist.py inventory
```

## What goes where

| Folder | What to put in it |
|---|---|
| `transcripts/` | One PDF per institution attended. Official/sealed copy if you have it, plus the unofficial copy for drafting. Name them `bingham_university_transcript.pdf`. |
| `degrees/` | B.Sc. certificate, or the statement of result while the certificate is pending. NYSC certificate or exemption letter too. |
| `test_scores/` | IELTS / TOEFL / Duolingo report, and GRE or GMAT if your targets ask for one. **Add a sidecar** (below) so expiry can be checked. |
| `identity/` | Passport data page (check it is valid well past your intended start date), birth certificate, NIN slip. |
| `cv/` | Any existing CV. The workspace generates the tailored academic CV into `cv/` at the repo root, but your current one is what the profile gets built from. |
| `references/` | `referees.json` (format below) plus any letters already in your possession. |
| `research/` | Your B.Sc. thesis, papers or preprints, writing samples. |
| `portfolio/` | Project write-ups, repository links, demo videos, certificates, award letters. A `links.md` of URLs is fine. |
| `financial/` | Bank statements, sponsor letter and sponsor's statements, scholarship award letters. Needed for the **visa**, usually not for the application. |
| `applications/<key>/` | Written by `/apply`. Holds the listing, the requirements checklist, form answers and the upload set for one application. |

## Sidecars: how expiry gets checked

An IELTS or TOEFL report is valid for **two years from the test date**, and a
GRE score for five. Nothing reliable can be read out of a scanned PDF, so put
the date in a sidecar file next to it:

`documents/test_scores/ielts_2026.pdf.meta.json`

```json
{ "taken": "2026-03-14", "test": "IELTS Academic", "overall": 7.5,
  "sections": { "listening": 8.0, "reading": 7.5, "writing": 6.5, "speaking": 7.5 } }
```

`/documents` then checks validity **against each application's deadline**, not
against today — a report that is valid now and expired by the deadline is the
failure this catches.

## referees.json

```json
[
  {
    "name": "Prof. Jane Example",
    "title": "Professor of Computer Science",
    "institution": "Bingham University",
    "email": "jane.example@binghamuni.edu.ng",
    "relationship": "Supervised my B.Sc. thesis (AutoBee)",
    "known_since": "2024",
    "strongest_on": "research design, independence, ROS 2 work",
    "preferred_notice_days": 21
  }
]
```

Use the referee's **institutional** email address. A Gmail address in a
recommender field is rejected outright by many portals, and it is the single
most common reason a reference never gets counted.
