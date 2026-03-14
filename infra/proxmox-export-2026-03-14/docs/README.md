# Proxmox Export (2026-03-14)

This folder is an infrastructure-as-code style export of runtime files deployed on Proxmox host and CTs.

## Layout
- `ct122/` NEO watchtower ingest + feed services
- `ct123/` alert brain, mission control, policy, SRE, case UI, public API, token rotation
- `ct124/` trajectory/impact/orbital services
- `host/` DR drill script + timer/service

## Security
- Secrets and tokens are redacted in this export.
- Rehydrate environment values via deployment secrets management before apply.
