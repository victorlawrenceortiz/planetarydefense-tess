#!/opt/pdf/alert-brain/.venv/bin/python
import sqlite3,json
from pathlib import Path
DB=Path('/var/lib/pdf-mission-control/historian.sqlite')
OUT=Path('/var/lib/pdf-mission-control/tuning-lab.json')
con=sqlite3.connect(DB)
rows=con.execute('SELECT raw_json FROM snapshots ORDER BY id DESC LIMIT 200').fetchall(); con.close()
cases=[]
for (r,) in rows:
  try: j=json.loads(r or '{}'); cases.extend(j.get('new_alerts',[]))
  except: pass
grids=[2e6,5e6,1e7]
res=[]
for mk in grids:
  c=sum(1 for a in cases if float(a.get('miss_km',1e99))<=mk)
  res.append({'miss_km_threshold':mk,'hits':c})
OUT.write_text(json.dumps({'cases':len(cases),'grid_results':res},indent=2))
print('ok tuning',len(cases))
