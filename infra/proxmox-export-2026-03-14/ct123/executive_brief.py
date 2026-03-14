#!/opt/pdf/alert-brain/.venv/bin/python
import json, urllib.request
from pathlib import Path
from datetime import datetime

ALERTS=Path('/var/lib/pdf-alert-brain/alerts-latest.json')
TREND=Path('/var/lib/pdf-mission-control/trend-latest.json')
OUT=Path('/var/lib/pdf-next3'); OUT.mkdir(parents=True, exist_ok=True)
WEBHOOK='http://192.168.1.178:5678/webhook/pdf-ops'

a=json.loads(ALERTS.read_text()) if ALERTS.exists() else {}
t=json.loads(TREND.read_text()) if TREND.exists() else {}
counts=a.get('counts',{})
text=(
f"PDF Executive Brief {datetime.utcnow().isoformat()}Z\n"
f"Source: {a.get('source','n/a')}\n"
f"Watch+: {counts.get('watch_or_higher',0)} | New: {counts.get('new_alerts',0)} | Critical: {counts.get('critical',0)}\n"
f"Trend: {t.get('trend','n/a')} | Risk band: {t.get('risk_band','n/a')}\n"
)
(OUT/'executive-brief-latest.txt').write_text(text)
body={'text':text,'counts':counts,'trend':t}
req=urllib.request.Request(WEBHOOK,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
try:
  urllib.request.urlopen(req, timeout=20)
except Exception:
  pass
print('ok brief')
