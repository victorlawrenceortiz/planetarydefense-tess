#!/usr/bin/env bash
set -euo pipefail
SECRETS=/etc/pdf-secrets.env
WEBHOOK_URL=REDACTED_WEBHOOK_URL

new_op=$(openssl rand -hex 24)
new_pub=$(openssl rand -hex 24)

# backup previous secrets with strict perms
if [ -f "$SECRETS" ]; then
  cp -f "$SECRETS" "/etc/pdf-secrets.env.bak.$(date +%F-%H%M%S)"
  chmod 600 /etc/pdf-secrets.env.bak.* || true
fi

cat > "$SECRETS" <<EOF
OPERATOR_TOKEN=REDACTED
PUBLIC_API_TOKEN=REDACTED
EOF
chmod 600 "$SECRETS"

systemctl daemon-reload
systemctl restart pdf-mission-control.service pdf-public-api.service

msg=$(cat <<JSON
{"text":"PDF security: monthly token rotation completed","time":"$(date -u +%FT%TZ)","services":["pdf-mission-control","pdf-public-api"]}
JSON
)

curl -sS -m 10 -H 'Content-Type: application/json' -d "$msg" "$WEBHOOK_URL" >/dev/null || true

echo "rotation complete $(date -u +%FT%TZ)" > /var/lib/pdf-mission-control/token-rotation-last.txt
