#!/opt/pdf/alert-brain/.venv/bin/python
import json,csv
from pathlib import Path
A=Path('/var/lib/pdf-alert-brain/alerts-latest.json')
O=Path('/var/lib/pdf-exports'); O.mkdir(parents=True,exist_ok=True)
p=json.loads(A.read_text()) if A.exists() else {}
alerts=p.get('new_alerts',[])
(Path(O/'public-feed.json')).write_text(json.dumps({'generated_at':p.get('generated_at'),'alerts':alerts},indent=2))
with open(O/'public-feed.csv','w',newline='') as f:
  w=csv.writer(f); w.writerow(['name','severity','miss_km','v_kps','date'])
  for a in alerts: w.writerow([a.get('name'),a.get('severity'),a.get('miss_km'),a.get('v_kps'),a.get('date')])
print('ok export',len(alerts))
