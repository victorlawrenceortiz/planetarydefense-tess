# Hosting (Local, IP-only)

This stack is designed to run **fully locally** on your LAN.

## No DNS requirement
You can access everything via IP + port. No local DNS (AdGuard / Pi-hole) is required.

## CT 121 services (example)

### Orbit visualization
- Confirmed view: `http://192.168.1.241:8790/confirmed`

### API
- Status: `http://192.168.1.241:8787/status`

### Static pages (nginx)
- Index: `http://192.168.1.241:8088/`
- NEOCP: `http://192.168.1.241:8088/tess-neo.html`
- Orbits: `http://192.168.1.241:8088/tess-orbits.html`
- Radio: `http://192.168.1.241:8088/tess-radio.html`
- Bundle: `http://192.168.1.241:8088/tess/`

## Notes
- Replace the IPs/ports above with your actual CT IPs if different.
- This document intentionally does **not** include credentials.
