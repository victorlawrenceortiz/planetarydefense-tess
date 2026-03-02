# Planetary Defense - TESS

Homelab-based planetary defense tooling (PDF) built by TESS:
- Data ingestion + diffing (JPL CAD, MPC NEOCP)
- Discord alerting via n8n
- Lightweight API
- Live 3D orbit visualization (inner planets + confirmed objects)

## Streams

This project is organized as three separate streams (JPL CAD, MPC NEOCP, Sentry).
See: `docs/Streams.md`

## Components

### CT 121 (pd-tess-sol)
- Runs ingestion/diff scripts + Postgres + API + viz.

### n8n (CT 117)
- Receives webhooks and posts to Discord.

## Repo Layout
- `backend/pdf_api/` — API + diff/triage scripts
- `backend/orbit_viz/` — 3D viz backend + static frontend
- `deploy/` — systemd service unit files
- `config/` — thresholds + cron schedules

## Quick start (Ubuntu 22.04)

### 1) Python venv
```bash
python3 -m venv /opt/pdf/venv
/opt/pdf/venv/bin/pip install --upgrade pip
/opt/pdf/venv/bin/pip install fastapi uvicorn[standard] numpy skyfield jplephem psycopg2-binary requests
```

### 2) Run API
```bash
cd backend/pdf_api
/opt/pdf/venv/bin/uvicorn api:APP --host 0.0.0.0 --port 8787
```

### 3) Run orbit viz
```bash
cd backend/orbit_viz/app
/opt/pdf/venv/bin/uvicorn server:APP --host 0.0.0.0 --port 8790
```

Then open:
- `http://<host>:8790/confirmed`

## Notes
- The viz uses Skyfield DE421 ephemeris for planet orbits.
- Confirmed object orbital elements are fetched from JPL SBDB.
- NEOCP candidates are shown separately because their orbits are typically provisional.
