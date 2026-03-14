#!/opt/pdf/alert-brain/.venv/bin/python
import hashlib,json,time
from pathlib import Path
files=[Path('/var/lib/pdf-alert-brain/alerts-latest.json'),Path('/var/lib/pdf-mission-control/trend-latest.json'),Path('/var/lib/pdf-neo-watchtower/neo-feed-latest.json')]
state=Path('/var/lib/pdf-integrity/chain.json')
prev='GENESIS'; chain=[]
if state.exists():
  try:
    d=json.loads(state.read_text()); chain=d.get('chain',[])
    if chain: prev=chain[-1]['hash']
  except: pass
h=hashlib.sha256(); h.update(prev.encode())
for f in files:
  if f.exists(): h.update(f.read_bytes())
now=str(time.time()); h.update(now.encode())
entry={'ts':now,'prev':prev,'hash':h.hexdigest()}
chain.append(entry); chain=chain[-1000:]
state.write_text(json.dumps({'chain':chain},indent=2))
print('ok integrity',entry['hash'][:12])
