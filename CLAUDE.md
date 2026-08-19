# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static, dependency-free set of HTML documents for AYSO Region 58 (Van Nuys / Sherman Oaks) covering its migration from SportsConnect to PlayMetrics. Every tracked file is a hand-written `.html` page plus one logo PNG. There is no build step, no package manager, no test suite, and no server-side code — what is in the repo is exactly what ships.

Published via GitHub Pages at `https://sdavis9248.github.io/playmetrics-migration-region58/`; `main` is the published branch, so merging to `main` *is* the deploy. Preview locally with `python -m http.server 8000` and open `http://localhost:8000/`.

The audience is volunteers (registrar, division coordinators, scheduler), not developers. Prose accuracy and printability matter more than markup elegance.

## The pages

`index.html` is the hand-maintained hub — a card grid linking every guide. It is not generated; **a new guide is invisible until you add a card to it**, and card blurbs are the only place the guides are summarized for a reader choosing among them.

| File | Audience / role |
| --- | --- |
| `PlayMetrics_Migration_Status_Region58.html` | Living project dashboard — percent-complete ring, per-item status tags, go-live checklist |
| `Team_Roster_Setup_Guide_Region58.html` | Steven & Sara + a printable one-page card for Division Coordinators; the most actively edited page |
| `Game_Scheduling_Guide_Region58.html` | Ben Hauser and schedulers |
| `Volunteer_Compliance_Guide_Region58.html` | Two-system compliance model, AB 506 |
| `PlayMetrics_Data_Import_Steps.html` | 12-step historical data import checklist |
| `AYSO_PlayMetrics_Terminology_Guide.html` | SC ↔ PM concept translation table |
| `Website_Migration_Guide_Region58.html` | Public-facing comms; ~20 embedded AYSO assets, hence 6 MB |
| `Leagues_Divisions_Setup_Guide_Region58.html` | **Superseded** by the Team & Player Roster guide, which absorbed its content. Nothing links to it anymore; it is retained only as history. Do not update it — put changes in the roster guide |
| `enrollment_dashboard.html` | **Retired** — a meta-refresh stub redirecting to the Region 58 Portal |

## Shared conventions

Each page is fully self-contained: its own `<style>` block, no shared stylesheet, no JS framework. The design system is copied between files rather than imported, so a token change has to be repeated per file. Every page follows the same skeleton:

- The same `:root` custom properties (`--ink`, `--paper`, `--warm`, `--accent`, plus `--green/--amber/--red` each with a `-soft` companion), Anybody for headings/UI and Source Serif 4 for body, both from Google Fonts.
- A dark `#0a2351` back-link strip above `<header>` pointing at `index.html`, then `<header>` with an `<h1>` and a `.meta` line carrying season and a "Prepared/Updated <date>" stamp. Update that stamp when you meaningfully revise a page.
- `.container` (~780–820px), content built from `<h2>`/`<h3>`, `.callout callout-{blue|green|amber|red}` boxes (blue = context, green = safe/good news, amber = caution, red = don't), `.card`, `.checklist`, `.path` for UI navigation strings, `.status-tag tag-{done|ready|waiting|blocked|optional}` and `.tag tag-{same|different|new|now|later|golive}`.
- A `.ref-links` block of `.ref-link` pills and a `<footer>` citing sources, then `@media print` overrides (white header, smaller body) — these pages get printed and handed out, so keep print styles working.

Screenshots are inlined as `data:image/...;base64` inside `<figure>`, with a `<figcaption>` that opens with a `<span class="ts">MM:SS</span>` timestamp locating the frame in the source webinar. This is why several files are megabytes of one long line. **Strip data URIs before reading or grepping**, e.g. `sed 's/data:image[^"]*"/DATAURI"/g' FILE.html | grep -n '<h2'`.

## Content sourcing rules

The guides derive from transcribed PlayMetrics webinars, the Help Center, and Region 58's own configuration; the footer of each page names its sources. Two conventions carry epistemic status and must be preserved:

- **`CONFIRM IN-PRODUCT`** (uppercase, inline) marks a claim that was *not* demonstrated on a webinar and is inference. Never quietly upgrade one of these to a plain assertion — remove the marker only when someone has actually verified it in PlayMetrics.
- Callouts frequently record *why* a value is a guess, which figure is a Region 58 planning number versus a system-enforced limit, and where two sources contradict each other. Preserve that hedging; flattening it into confident prose is a regression.

Region 58 specifics that recur: 16 team divisions (8 age groups × Boys/Girls) plus 2 non-team programs; age codes are zero-padded so they sort youngest-first (`05U`…`19U`); team names are the gendered division code plus a sequence (`10UG-01`).

## Related systems (other repos, referenced not vendored)

- `AYSORegionAutomation` (github.com/sdavis9248) — the Python automation repo. The roster guide documents `python src\main.py --pm-team-import --team-import-season "Fall 2026"`, which reads `data/playmetrics/packages.json` and writes `reports/teams_import_<date>.csv`. Division facts live in that repo's `DIVISION_CONFIG`. Its `docs/playmetrics-recreational-league-operations.md` is the technical knowledge reference this repo's guides cross-link to. If behavior there changes, the guide prose here goes stale — check both.
- Region 58 Portal (`region58-portal-*.us-west2.run.app`) — live enrollment/compliance app that replaced `enrollment_dashboard.html`.
- `github.com/sdavis9248/playmetrics-import` — referenced from the data-import guide.

## Working in this repo

- Edit HTML directly; there is nothing to compile or lint. Verify by opening the page in a browser and checking print preview.
- Prefer targeted `Edit` calls over rewriting a whole file — the large ones would otherwise churn megabytes of base64.
- Commit messages here are declarative statements of what the docs now say (e.g. "Team names are the gendered code plus sequence (10UG-01)"), not "update file" — match that style.
