#!/usr/bin/env bash
set -euo pipefail
OUT="/root/pdf-drill/report-$(date +%F-%H%M%S).txt"
{
echo "PDF DR Drill Report"
date -u
echo "Host: $(hostname)"
echo "== Target CTs =="
for id in 121 122 123 124; do pct status $id || true; done
echo "== PBS store status =="
pvesm status | grep ProxmoxBackupServer || true
echo "== Recent backup tasks =="
journalctl -u pvescheduler --since "-24 hours" --no-pager | tail -n 80 || true
echo "== Snapshot availability check (pbs task list) =="
pvesh get /cluster/backup --output-format json 2>/dev/null | head -c 2000 || true
echo
} > "$OUT"
ln -sf "$OUT" /root/pdf-drill/latest-report.txt
echo "wrote $OUT"
