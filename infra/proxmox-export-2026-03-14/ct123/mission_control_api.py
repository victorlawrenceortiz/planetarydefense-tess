#!/opt/pdf/alert-brain/.venv/bin/python
import json, sqlite3, os
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title='PDF Mission Control API', version='1.2.0')
ROOT = Path('/var/lib/pdf-mission-control'); ROOT.mkdir(parents=True, exist_ok=True)
DB = ROOT / 'historian.sqlite'
ALERT_SUMMARY = Path('/var/lib/pdf-alert-brain/alerts-summary.txt')
ALERTS_JSON = Path('/var/lib/pdf-alert-brain/alerts-latest.json')
TREND_JSON = ROOT / 'trend-latest.json'
OP_TOKEN = os.getenv('OPERATOR_TOKEN','pdf-operator-change-me')


def db():
    con = sqlite3.connect(DB)
    con.execute('''CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, source TEXT, watch_plus INTEGER, new_alerts INTEGER, critical INTEGER, watch INTEGER, raw_json TEXT)''')
    con.execute('''CREATE TABLE IF NOT EXISTS incidents (id INTEGER PRIMARY KEY AUTOINCREMENT, created_ts TEXT NOT NULL, object_id TEXT, object_name TEXT, severity TEXT, miss_km REAL, velocity_kps REAL, status TEXT DEFAULT 'open', notes TEXT DEFAULT '')''')
    con.execute('''CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, action TEXT, actor TEXT, incident_id INTEGER, details TEXT)''')
    return con

@app.get('/health')
def health(): return {'ok':True,'time':datetime.utcnow().isoformat()+'Z'}

@app.get('/status')
def status():
    payload={}; trend={}
    if ALERTS_JSON.exists():
        try: payload=json.loads(ALERTS_JSON.read_text())
        except: pass
    if TREND_JSON.exists():
        try: trend=json.loads(TREND_JSON.read_text())
        except: pass
    txt=ALERT_SUMMARY.read_text() if ALERT_SUMMARY.exists() else ''
    return {'alert_summary_text':txt,'alerts_payload':payload,'trend':trend}

@app.get('/historian/latest')
def historian_latest(limit:int=20):
    con=db(); cur=con.execute('SELECT ts,source,watch_plus,new_alerts,critical,watch FROM snapshots ORDER BY id DESC LIMIT ?',(limit,))
    rows=[dict(zip(['ts','source','watch_plus','new_alerts','critical','watch'],r)) for r in cur.fetchall()]
    con.close(); return {'rows':rows}

@app.post('/historian/snapshot')
def historian_snapshot():
    payload={}
    if ALERTS_JSON.exists(): payload=json.loads(ALERTS_JSON.read_text())
    c=payload.get('counts',{})
    con=db(); con.execute('INSERT INTO snapshots(ts,source,watch_plus,new_alerts,critical,watch,raw_json) VALUES(?,?,?,?,?,?,?)',
      (datetime.utcnow().isoformat()+'Z',payload.get('source'),c.get('watch_or_higher',0),c.get('new_alerts',0),c.get('critical',0),c.get('watch',0),json.dumps(payload)))
    con.commit(); con.close(); return {'ok':True}

@app.get('/incidents')
def incidents(limit:int=50,status:str='all'):
    con=db()
    if status=='all': cur=con.execute('SELECT id,created_ts,object_id,object_name,severity,miss_km,velocity_kps,status,notes FROM incidents ORDER BY id DESC LIMIT ?',(limit,))
    else: cur=con.execute('SELECT id,created_ts,object_id,object_name,severity,miss_km,velocity_kps,status,notes FROM incidents WHERE status=? ORDER BY id DESC LIMIT ?',(status,limit))
    rows=[dict(zip(['id','created_ts','object_id','object_name','severity','miss_km','velocity_kps','status','notes'],r)) for r in cur.fetchall()]
    con.close(); return {'rows':rows}

@app.post('/incidents/{incident_id}/close')
def incident_close(incident_id:int, token:str=Query(...), actor:str=Query('operator')):
    if token!=OP_TOKEN: raise HTTPException(status_code=401,detail='unauthorized')
    con=db(); con.execute("UPDATE incidents SET status='closed' WHERE id=?",(incident_id,))
    con.execute('INSERT INTO audit_log(ts,action,actor,incident_id,details) VALUES(?,?,?,?,?)',(datetime.utcnow().isoformat()+'Z','close_incident',actor,incident_id,'manual close'))
    con.commit(); con.close(); return {'ok':True,'incident_id':incident_id}

@app.get('/audit/latest')
def audit_latest(limit:int=50):
    con=db(); cur=con.execute('SELECT ts,action,actor,incident_id,details FROM audit_log ORDER BY id DESC LIMIT ?',(limit,))
    rows=[dict(zip(['ts','action','actor','incident_id','details'],r)) for r in cur.fetchall()]
    con.close(); return {'rows':rows}

@app.get('/trends/latest')
def trends_latest():
    if TREND_JSON.exists():
        try: return json.loads(TREND_JSON.read_text())
        except: pass
    return {'status':'no-trend-yet'}
