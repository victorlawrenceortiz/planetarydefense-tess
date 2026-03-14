#!/opt/pdf/alert-brain/.venv/bin/python
import json
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI

app=FastAPI(title='PDF Observer Tasking',version='1.0')
ALERTS=Path('/var/lib/pdf-alert-brain/alerts-latest.json')

@app.get('/health')
def health(): return {'ok':True,'time':datetime.utcnow().isoformat()+'Z'}

@app.get('/tasks')
def tasks(limit:int=10):
    p=json.loads(ALERTS.read_text()) if ALERTS.exists() else {}
    arr=p.get('new_alerts',[])
    def score(a):
        miss=float(a.get('miss_km',1e99)); v=float(a.get('v_kps',0)); sev=2 if a.get('severity')=='critical' else 1
        return sev*100 + (2_000_000/max(miss,1))*10 + v
    arr=sorted(arr,key=score,reverse=True)[:limit]
    out=[]
    for i,a in enumerate(arr,1):
        out.append({'rank':i,'name':a.get('name'),'severity':a.get('severity'),'miss_km':a.get('miss_km'),'velocity_kps':a.get('v_kps'),'recommended_action':'Prioritize follow-up observations'})
    return {'generated_at':datetime.utcnow().isoformat()+'Z','tasks':out}
