# Planetary Defense - TESS

Homelab-based planetary defense tooling (PDF) built by TESS.

This repo now supports **two deployment paths**:

1. **App-only deployment** (single host / CT121 style)
2. **Full Proxmox stack deployment** using exported runtime units/scripts in `infra/proxmox-export-2026-03-14/`

---

## What this project does

- NEO ingestion + triage (JPL CAD, MPC NEOCP, risk/watch workflows)
- Alert routing via n8n -> Discord
- Mission Control API + historian + incident tracking
- Live orbit visualization + advanced filtering view
- Impact scenario API (fast triage scoring)
- SRE/status pages + KPI board + partner-safe exports

---

## Repository layout

- `backend/pdf_api/` — API + ingest/diff/triage scripts (legacy/core app stream)
- `backend/orbit_viz/` — orbit visualization backend/static app
- `deploy/` — service units for original stack
- `config/` — thresholds/schedules
- `docs/` — architecture and stream docs
- `infra/proxmox-export-2026-03-14/` — **sanitized infra-as-code export** from live Proxmox deployment
  - `ct122/` NEO ingest + feed services
  - `ct123/` alert brain, mission control, case/SRE/public APIs, automation timers
  - `ct124/` trajectory/orbital/impact services
  - `host/` DR drill service/timer/script

---

## Prerequisites

### Required
- Proxmox VE node (tested with 8.x/9.x class environment)
- Debian/Ubuntu templates for LXC
- n8n reachable in LAN (for Discord webhook routing)
- Python 3.10+ on CTs

### Recommended
- Dedicated CTs:
  - CT122: feed/ingest
  - CT123: control plane + alerting + APIs
  - CT124: trajectory/simulation/orbit rendering
- PBS backups configured

---

## Quick install from GitHub (full stack)

## 1) Clone repo

```bash
git clone https://github.com/victorlawrenceortiz/planetarydefense-tess.git
cd planetarydefense-tess
```

## 2) Copy exported infra files to target CTs/host

Use `infra/proxmox-export-2026-03-14/` as source of truth.

- Files in `ct122/` -> CT122
- Files in `ct123/` -> CT123
- Files in `ct124/` -> CT124
- Files in `host/` -> Proxmox host

Example (from Proxmox host):

```bash
# Example: push one file to CT123
pct push 123 infra/proxmox-export-2026-03-14/ct123/mission_control_api.py /opt/pdf/mission-control/mission_control_api.py
```

> Tip: keep paths exactly as in export to match service files.

## 3) Create Python virtual environments

### CT123
```bash
python3 -m venv /opt/pdf/alert-brain/.venv
source /opt/pdf/alert-brain/.venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install fastapi "uvicorn[standard]" requests pydantic python-dateutil
```

### CT124
```bash
python3 -m venv /opt/pdf/trajectory/.venv
source /opt/pdf/trajectory/.venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install numpy astropy scipy matplotlib pandas poliastro jupyterlab fastapi "uvicorn[standard]"
```

## 4) Install systemd services/timers

For each exported unit file:

```bash
# on target machine/CT
cp <service-or-timer-file> /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now <unit-name>
```

Recommended bring-up order:

1. CT122: `pdf-neo-collector.timer`, `pdf-neo-http.service`
2. CT123: `pdf-alert-brain.timer`, `pdf-mission-control.service`, `pdf-historian-snapshot.timer`
3. CT124: `pdf-impact-sim.service`, `pdf-orbital-diagram-build.timer`, `pdf-orbital-diagram-http.service`
4. Optional: SRE/KPI/public API/case UI and “next3” services on CT123

## 5) Configure environment files

### CT123
Create/edit:

- `/etc/pdf-alert-brain.env`
- `/etc/pdf-secrets.env` (chmod 600)

Minimum example:

```env
NASA_API_KEY=DEMO_KEY
LOOKAHEAD_DAYS=1
SOURCE_URL=http://192.168.1.238:9080/neo-feed-latest.json
WEBHOOK_URL=http://<n8n-ip>:5678/webhook/pdf-ops
THRESH_MISS_KM=5000000
THRESH_V_KPS=20
```

Secrets file example:

```env
OPERATOR_TOKEN=<set-strong-random-token>
PUBLIC_API_TOKEN=<set-strong-random-token>
```

## 6) Verify services

### CT122
```bash
systemctl status pdf-neo-collector.timer
systemctl status pdf-neo-http.service
curl -s http://127.0.0.1:9080/neo-summary.txt
```

### CT123
```bash
systemctl status pdf-alert-brain.timer
systemctl status pdf-mission-control.service
curl -s http://127.0.0.1:9100/health
curl -s http://127.0.0.1:9100/status
```

### CT124
```bash
systemctl status pdf-impact-sim.service
systemctl status pdf-orbital-diagram-http.service
curl -s http://127.0.0.1:9200/health
```

---

## Runtime URLs (example LAN)

- Main dashboard: `http://<ct121-ip>:8088/neocp.html`
- Mission Control API: `http://<ct123-ip>:9100`
- Command Center: `http://<ct123-ip>:9300`
- SRE Monitor: `http://<ct123-ip>:9400`
- Case UI: `http://<ct123-ip>:9500`
- Public API (token-protected): `http://<ct123-ip>:9600`
- Partner Exports: `http://<ct123-ip>:9700`
- KPI Board: `http://<ct123-ip>:9800`
- Observer Tasking API: `http://<ct123-ip>:9900`
- CT122 feed JSON: `http://<ct122-ip>:9080/neo-feed-latest.json`
- Orbit diagram: `http://<ct124-ip>:9090`
- Advanced orbit page: `http://<ct124-ip>:9090/advanced.html`

---

## n8n -> Discord test

From CT123:

```bash
curl -H "Content-Type: application/json" \
  -d '{"text":"PDF pipeline test"}' \
  http://<n8n-ip>:5678/webhook/pdf-ops
```

Expected response:

```json
{"message":"Workflow was started"}
```

---

## Security notes

- Tokens/secrets are intentionally redacted in exported infra files.
- Keep `/etc/pdf-secrets.env` mode `600`.
- Rotate tokens periodically (monthly timer supported by exported units).
- Public API should stay LAN-only or behind authenticated reverse proxy.

---

## Minimal app-only quick start (legacy mode)

If you only want core app stream on one host:

```bash
python3 -m venv /opt/pdf/venv
/opt/pdf/venv/bin/pip install --upgrade pip
/opt/pdf/venv/bin/pip install fastapi "uvicorn[standard]" numpy skyfield jplephem psycopg2-binary requests

cd backend/pdf_api
/opt/pdf/venv/bin/uvicorn api:APP --host 0.0.0.0 --port 8787

cd ../orbit_viz/app
/opt/pdf/venv/bin/uvicorn server:APP --host 0.0.0.0 --port 8790
```

Then open:
- `http://<host>:8790/confirmed`

---

## Additional docs

- Streams: `docs/Streams.md`
- Local IP hosting: `docs/Hosting-Local-IP-Only.md`
- Proxmox export details: `infra/proxmox-export-2026-03-14/docs/README.md`
