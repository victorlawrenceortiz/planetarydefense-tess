# Streams

This project is organized into **three separate streams**, each with its own:
- input source
- pipeline scripts
- n8n workflow(s)
- Discord alert formatting

## 1) JPL CAD (Close Approaches)

**Purpose:** confirmed close-approach monitoring (Earth encounters).

- Source: https://ssd-api.jpl.nasa.gov/cad.api
- CT pipeline:
  - fetcher output → `/var/lib/pdef/jpl_cad.json`
  - archive/latest → `/var/lib/pdf/jpl/*`
  - diff+post wrapper → `pdf-jpl-diff-to-n8n`
- n8n webhook: `/webhook/pdf-jpl`
- n8n workflow export: `n8n/workflows/PDF_ JPL CAD -_ Discord.json`

## 2) MPC NEOCP (Candidate Objects)

**Purpose:** new candidate detection + triage (provisional objects).

- Source: https://www.minorplanetcenter.net/iau/NEO/neocp.txt
- CT pipeline:
  - fetcher output → `/var/lib/pdef/mpc_neocp.json`
  - archive/latest → `/var/lib/pdf/mpc/*`
  - parser/triage → `backend/pdf_api/mpc_parse.py`
  - diff+post wrapper → `pdf-mpc-diff-to-n8n`
- n8n webhook: `/webhook/pdf-mpc`
- n8n workflow export: `n8n/workflows/PDF_ MPC NEOCP -_ Discord.json`

## 3) JPL Sentry (Impact Risk Watch)

**Purpose:** risk watchlist (Palermo Scale / Impact Probability changes).

- Source: https://ssd-api.jpl.nasa.gov/sentry.api
- CT pipeline:
  - watcher → `/opt/pdf/app/sentry_watch.py`
  - post wrapper → `/usr/local/bin/pdf-sentry-to-n8n`
  - state → `/var/lib/pdf/sentry/latest.json`
- n8n webhook: `/webhook/pdf-sentry`
- n8n workflow name: `PDF: Sentry Risk Watch -> Discord`

## Notes
- Discord webhook URLs are **redacted** in the public repo exports.
- Streams are intentionally separate so you can:
  - route them to different channels
  - apply different thresholds and schedules
  - disable one without impacting the others
