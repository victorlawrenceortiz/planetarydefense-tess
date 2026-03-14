#!/opt/pdf/alert-brain/.venv/bin/python
import os, json
from fastapi import FastAPI, HTTPException, Query, Request
from pathlib import Path

TOKEN=os.getenv('PUBLIC_API_TOKEN','')
ALERTS=Path('/var/lib/pdf-alert-brain/alerts-latest.json')
TREND=Path('/var/lib/pdf-mission-control/trend-latest.json')
EXPORT=Path('/var/lib/pdf-exports/public-feed.json')
app=FastAPI(title='PDF Public API',version='1.1')

def auth(token:str):
    if not TOKEN or token!=TOKEN:
        raise HTTPException(status_code=401,detail='unauthorized')

def ip_allowed(ip:str)->bool:
    return ip.startswith('127.') or ip.startswith('192.168.')

def readj(p):
    if p.exists():
        try: return json.loads(p.read_text())
        except: return {}
    return {}

@app.get('/health')
def health(): return {'ok':True}

@app.get('/public/summary')
def public_summary(request:Request, token:str=Query(...)):
    if not ip_allowed(request.client.host):
        raise HTTPException(status_code=403,detail='forbidden')
    auth(token)
    a=readj(ALERTS); t=readj(TREND)
    return {'counts':a.get('counts',{}),'trend':t}

@app.get('/public/feed')
def public_feed(request:Request, token:str=Query(...)):
    if not ip_allowed(request.client.host):
        raise HTTPException(status_code=403,detail='forbidden')
    auth(token)
    return readj(EXPORT)
