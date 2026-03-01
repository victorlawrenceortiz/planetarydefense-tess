# n8n Workflows (Discord alerts)

These workflow exports are included **without secrets**.

## What’s redacted
- Discord webhook URL is replaced with `{{DISCORD_WEBHOOK_URL}}`.

## Import
1. In n8n: Workflows → Import from File
2. Import the JSON files in `n8n/workflows/`
3. For each workflow, edit the HTTP Request node and set the URL to your Discord webhook.
4. Activate workflows.

## Webhook paths expected
- `/webhook/pdf-jpl`
- `/webhook/pdf-mpc`
- `/webhook/pdf-heartbeat`

## Notes
- These workflows were created/managed via n8n Public API.
