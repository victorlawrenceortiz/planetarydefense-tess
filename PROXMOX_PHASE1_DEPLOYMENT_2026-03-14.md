# Proxmox Phase 1 Deployment (2026-03-14)

## Summary
Implemented an end-to-end Planetary Defense Foundation Phase 1 stack on Proxmox VE:

- **CT122 `pdf-neo-watchtower` (192.168.1.238)**
  - NASA NEO feed collector (systemd timer, 15 min)
  - Outputs:
    - `neo-feed-latest.json`
    - `neo-summary.txt`
  - Internal HTTP service enabled on port `9080`

- **CT123 `pdf-alert-brain` (192.168.1.239)**
  - Alert engine (systemd timer, 15 min)
  - Source preference:
    1. CT122 cached feed (`http://192.168.1.238:9080/neo-feed-latest.json`)
    2. NASA API fallback
  - Dedupe state + severity scoring
  - Optional webhook delivery configured to:
    - `http://192.168.1.178:5678/webhook/pdf-ops`

- **CT124 `pdf-trajectory-sandbox` (192.168.1.240)**
  - Scientific Python venv stack:
    - `numpy`, `astropy`, `scipy`, `matplotlib`, `pandas`, `poliastro`, `jupyterlab`
  - Baseline trajectory job + timer (6h)
  - Live orbital diagram build + HTTP service
    - URL: `http://192.168.1.240:9090`

## Dashboard Integration
Added direct dashboard link:
- `Open : CT124 Live Orbit` -> `http://192.168.1.240:9090`

## Operational URLs
- Main dashboard: `http://192.168.1.241:8088/neocp.html`
- Live orbit diagram: `http://192.168.1.240:9090`
- CT122 feed JSON: `http://192.168.1.238:9080/neo-feed-latest.json`
- CT122 feed summary: `http://192.168.1.238:9080/neo-summary.txt`
- n8n: `http://192.168.1.178:5678`

## Notes
- Proxmox host updates and kernel packages were installed; reboot deferred by request.
- Alert engine avoids rate-limit failures by consuming CT122 cache first.
