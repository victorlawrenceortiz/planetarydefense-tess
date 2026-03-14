#!/opt/pdf/alert-brain/.venv/bin/python
import sqlite3,json
from pathlib import Path
from datetime import datetime
DB=Path('/var/lib/pdf-mission-control/historian.sqlite'); OUT=Path('/var/lib/pdf-kpi'); OUT.mkdir(parents=True,exist_ok=True)
con=sqlite3.connect(DB)
rows=con.execute('SELECT ts,watch_plus,new_alerts,critical,watch FROM snapshots ORDER BY id DESC LIMIT 100').fetchall(); con.close()
rows=list(reversed(rows))
samples=len(rows)
avg=(sum(r[1] or 0 for r in rows)/samples) if samples else 0
peak=max((r[1] or 0 for r in rows), default=0)
crit=max((r[3] or 0 for r in rows), default=0)
k={'generated_at':datetime.utcnow().isoformat()+'Z','samples':samples,'watch_plus_avg':round(avg,2),'watch_plus_peak':peak,'critical_peak':crit}
(OUT/'kpi.json').write_text(json.dumps(k,indent=2))
html=f"<html><body style='font-family:Arial;background:#0b1020;color:#e6edf3'><h2>PDF KPI Board</h2><pre>{json.dumps(k,indent=2)}</pre></body></html>"
(OUT/'index.html').write_text(html)
print('ok kpi',samples)
