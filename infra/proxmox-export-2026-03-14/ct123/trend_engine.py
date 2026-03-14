#!/opt/pdf/alert-brain/.venv/bin/python
import json, sqlite3
from pathlib import Path
from datetime import datetime

DB = Path('/var/lib/pdf-mission-control/historian.sqlite')
OUT = Path('/var/lib/pdf-mission-control/trend-latest.json')
con = sqlite3.connect(DB)
con.execute('''CREATE TABLE IF NOT EXISTS snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  source TEXT,
  watch_plus INTEGER,
  new_alerts INTEGER,
  critical INTEGER,
  watch INTEGER,
  raw_json TEXT
)''')
rows = con.execute('SELECT ts,watch_plus,new_alerts,critical,watch FROM snapshots ORDER BY id DESC LIMIT 24').fetchall()
con.close()
rows = list(reversed(rows))
if not rows:
    out = {'generated_at': datetime.utcnow().isoformat()+'Z','status':'no-data'}
else:
    wp = [r[1] or 0 for r in rows]
    crit = [r[3] or 0 for r in rows]
    last = wp[-1]
    avg = sum(wp)/len(wp)
    slope = (wp[-1]-wp[0])/(len(wp)-1) if len(wp)>1 else 0
    trend = 'stable'
    if slope > 0.4: trend = 'rising'
    if slope < -0.4: trend = 'falling'
    risk = 'LOW'
    if last >= 10 or max(crit) >= 2: risk = 'HIGH'
    elif last >= 5 or max(crit) >= 1: risk = 'MEDIUM'
    out = {
      'generated_at': datetime.utcnow().isoformat()+'Z',
      'samples': len(rows),
      'watch_plus_last': last,
      'watch_plus_avg': round(avg,2),
      'watch_plus_slope': round(slope,3),
      'critical_peak': max(crit) if crit else 0,
      'trend': trend,
      'risk_band': risk
    }
OUT.write_text(json.dumps(out, indent=2))
print('ok trend', out.get('trend','n/a'), out.get('risk_band','n/a'))
