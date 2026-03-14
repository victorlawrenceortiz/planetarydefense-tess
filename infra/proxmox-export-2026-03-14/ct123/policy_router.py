#!/opt/pdf/alert-brain/.venv/bin/python
import os,json,urllib.request
from pathlib import Path
A=Path('/var/lib/pdf-alert-brain/alerts-latest.json')
S=Path('/var/lib/pdf-alert-brain/policy-state.json')
if not A.exists(): raise SystemExit('no alerts')
p=json.loads(A.read_text()); new=p.get('new_alerts',[])
critical=[x for x in new if x.get('severity')=='critical']
watch=[x for x in new if x.get('severity')=='watch']
web_crit=os.getenv('WEBHOOK_CRITICAL','').strip(); web_watch=os.getenv('WEBHOOK_WATCH','').strip()
prev={}
if S.exists():
  try: prev=json.loads(S.read_text())
  except: prev={}
sig=f"{len(critical)}:{len(watch)}:{p.get('generated_at','')}"
if sig!=prev.get('sig'):
  if web_crit and critical:
    urllib.request.urlopen(urllib.request.Request(web_crit,data=json.dumps({'type':'critical','alerts':critical[:10]}).encode(),headers={'Content-Type':'application/json'}),timeout=15)
  if web_watch and watch:
    urllib.request.urlopen(urllib.request.Request(web_watch,data=json.dumps({'type':'watch','alerts':watch[:10]}).encode(),headers={'Content-Type':'application/json'}),timeout=15)
S.write_text(json.dumps({'sig':sig},indent=2))
print('ok policy',sig)
