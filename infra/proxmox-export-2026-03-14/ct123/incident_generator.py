#!/opt/pdf/alert-brain/.venv/bin/python
import json, sqlite3
from pathlib import Path
from datetime import datetime

ALERTS = Path('/var/lib/pdf-alert-brain/alerts-latest.json')
DB = Path('/var/lib/pdf-mission-control/historian.sqlite')
if not ALERTS.exists():
    raise SystemExit('alerts missing')

payload = json.loads(ALERTS.read_text())
new_alerts = payload.get('new_alerts', [])
con = sqlite3.connect(DB)
con.execute('''CREATE TABLE IF NOT EXISTS incidents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_ts TEXT NOT NULL,
  object_id TEXT,
  object_name TEXT,
  severity TEXT,
  miss_km REAL,
  velocity_kps REAL,
  status TEXT DEFAULT 'open',
  notes TEXT DEFAULT ''
)''')

created = 0
for a in new_alerts:
    if (a.get('severity') or '').lower() not in ('watch','critical'):
        continue
    oid = str(a.get('id') or '')
    d = str(a.get('date') or '')
    # dedupe by object+date if open exists
    cur = con.execute("SELECT id FROM incidents WHERE object_id=? AND status='open' LIMIT 1", (f'{oid}:{d}',))
    if cur.fetchone():
        continue
    con.execute('INSERT INTO incidents(created_ts,object_id,object_name,severity,miss_km,velocity_kps,status,notes) VALUES(?,?,?,?,?,?,?,?)', (
      datetime.utcnow().isoformat()+'Z', f'{oid}:{d}', a.get('name'), a.get('severity'), float(a.get('miss_km',0)), float(a.get('v_kps',0)), 'open', 'auto-generated from alert brain'
    ))
    created += 1
con.commit(); con.close()
print('ok incidents created', created)
