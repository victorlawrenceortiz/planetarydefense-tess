#!/opt/pdf/alert-brain/.venv/bin/python
import json, os, urllib.request
from datetime import datetime
from pathlib import Path

ALERTS=Path('/var/lib/pdf-alert-brain/alerts-latest.json')
STATE=Path('/var/lib/pdf-next3/nightwatch-state.json')
WEBHOOK=os.getenv('WEBHOOK_URL','').strip()
if not ALERTS.exists(): raise SystemExit('alerts missing')
p=json.loads(ALERTS.read_text())
new=p.get('new_alerts',[])
critical=[a for a in new if (a.get('severity')=='critical')]
close_watch=[a for a in new if (a.get('severity')=='watch' and float(a.get('miss_km',1e99))<=2_000_000)]
urgent=critical+close_watch
sig=f"{len(critical)}:{len(close_watch)}:{p.get('generated_at','')}"
old={}
if STATE.exists():
  try: old=json.loads(STATE.read_text())
  except: pass
if WEBHOOK and urgent and sig!=old.get('sig'):
  body={"text":f"PDF Night Watch {datetime.utcnow().isoformat()}Z | urgent={len(urgent)}","urgent":urgent[:10],"source":p.get('source')}
  req=urllib.request.Request(WEBHOOK,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
  urllib.request.urlopen(req, timeout=20)
STATE.write_text(json.dumps({'sig':sig,'ts':datetime.utcnow().isoformat()+'Z'},indent=2))
print('ok nightwatch',len(urgent))
