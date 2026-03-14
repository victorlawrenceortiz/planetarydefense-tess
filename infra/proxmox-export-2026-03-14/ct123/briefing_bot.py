#!/opt/pdf/alert-brain/.venv/bin/python
import json, os, urllib.request
from datetime import datetime
from pathlib import Path

ALERTS = Path('/var/lib/pdf-alert-brain/alerts-latest.json')
STATE = Path('/var/lib/pdf-alert-brain/briefing-state.json')
WEBHOOK = os.getenv('WEBHOOK_URL','').strip()
if not ALERTS.exists():
    raise SystemExit('alerts file missing')

payload = json.loads(ALERTS.read_text())
counts = payload.get('counts', {})
new_n = counts.get('new_alerts',0)
watch_n = counts.get('watch_or_higher',0)
source = payload.get('source','unknown')

prev = {}
if STATE.exists():
    try: prev = json.loads(STATE.read_text())
    except Exception: prev = {}
last_sig = prev.get('sig')
sig = f"{new_n}:{watch_n}:{source}"

msg = {
  'text': f"PDF Briefing {datetime.utcnow().isoformat()}Z | Source={source} | Watch+={watch_n} | New={new_n}",
  'counts': counts,
  'top': (payload.get('new_alerts') or [])[:3]
}

if WEBHOOK and sig != last_sig:
  data = json.dumps(msg).encode('utf-8')
  req = urllib.request.Request(WEBHOOK, data=data, headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(req, timeout=20) as r:
      pass

STATE.write_text(json.dumps({'sig':sig,'ts':datetime.utcnow().isoformat()+'Z'}, indent=2))
print('ok briefing', sig)
