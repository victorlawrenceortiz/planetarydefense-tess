#!/usr/bin/env python3
import json, os, urllib.request, urllib.parse
from datetime import date, timedelta, datetime
from pathlib import Path

OUT_DIR = Path('/var/lib/pdf-alert-brain')
OUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_PATH = OUT_DIR / 'state.json'
ALERTS_PATH = OUT_DIR / 'alerts-latest.json'
SUMMARY_PATH = OUT_DIR / 'alerts-summary.txt'

API_KEY = os.getenv('NASA_API_KEY', 'DEMO_KEY')
DAYS = int(os.getenv('LOOKAHEAD_DAYS', '1'))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '').strip()
SOURCE_URL = os.getenv('SOURCE_URL', 'http://192.168.1.238:9080/neo-feed-latest.json').strip()

THRESH_MISS_KM = float(os.getenv('THRESH_MISS_KM', '5000000'))
THRESH_V_KPS = float(os.getenv('THRESH_V_KPS', '20'))

start = date.today()
end = start + timedelta(days=max(0, DAYS))

data = None
source_used = None
if SOURCE_URL:
    try:
        with urllib.request.urlopen(SOURCE_URL, timeout=15) as r:
            tmp = json.loads(r.read().decode('utf-8'))
            if 'objects' in tmp:
                # normalize into NASA-like shape for parser below
                neo_map = {}
                for o in tmp.get('objects', []):
                    d = o.get('date', start.isoformat())
                    neo_map.setdefault(d, []).append({
                        'id': o.get('id'),
                        'name': o.get('name'),
                        'is_potentially_hazardous_asteroid': o.get('is_potentially_hazardous', False),
                        'nasa_jpl_url': o.get('nasa_jpl_url'),
                        'estimated_diameter': {'meters': {'estimated_diameter_max': o.get('estimated_diameter_m_max')}},
                        'close_approach_data': [{
                            'miss_distance': {'kilometers': str(o.get('miss_distance_km', 1e99))},
                            'relative_velocity': {'kilometers_per_second': str(o.get('relative_velocity_kps', 0))},
                        }]
                    })
                data = {'near_earth_objects': neo_map}
                source_used = 'ct122-cache'
    except Exception:
        data = None

if data is None:
    params = urllib.parse.urlencode({
        'start_date': start.isoformat(),
        'end_date': end.isoformat(),
        'api_key': API_KEY,
    })
    url = f'https://api.nasa.gov/neo/rest/v1/feed?{params}'
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.loads(r.read().decode('utf-8'))
    source_used = 'nasa-api'

objs = []
for d, arr in data.get('near_earth_objects', {}).items():
    for o in arr:
        cad = (o.get('close_approach_data') or [{}])[0]
        miss_km = float(cad.get('miss_distance', {}).get('kilometers', '1e99'))
        v_kps = float(cad.get('relative_velocity', {}).get('kilometers_per_second', '0'))
        rec = {
            'id': o.get('id'),
            'name': o.get('name'),
            'date': d,
            'hazardous': bool(o.get('is_potentially_hazardous_asteroid')),
            'miss_km': miss_km,
            'v_kps': v_kps,
            'url': o.get('nasa_jpl_url'),
            'diam_m_max': o.get('estimated_diameter', {}).get('meters', {}).get('estimated_diameter_max'),
        }
        sev = 'info'
        if rec['hazardous'] and rec['miss_km'] <= THRESH_MISS_KM:
            sev = 'critical'
        elif rec['hazardous'] or rec['miss_km'] <= THRESH_MISS_KM or rec['v_kps'] >= THRESH_V_KPS:
            sev = 'watch'
        rec['severity'] = sev
        if sev != 'info':
            objs.append(rec)

objs.sort(key=lambda x: (0 if x['severity']=='critical' else 1, x['miss_km']))

state = {'sent': []}
if STATE_PATH.exists():
    try:
        state = json.loads(STATE_PATH.read_text())
    except Exception:
        pass
sent = set(state.get('sent', []))
new_alerts = []
for o in objs:
    key = f"{o['id']}:{o['date']}:{o['severity']}"
    if key not in sent:
        new_alerts.append(o)
        sent.add(key)
state['sent'] = list(sorted(sent))[-5000:]
STATE_PATH.write_text(json.dumps(state, indent=2))

payload = {
    'generated_at': datetime.utcnow().isoformat() + 'Z',
    'source': source_used,
    'window': {'start': start.isoformat(), 'end': end.isoformat()},
    'counts': {
        'watch_or_higher': len(objs),
        'new_alerts': len(new_alerts),
        'critical': sum(1 for x in new_alerts if x['severity']=='critical'),
        'watch': sum(1 for x in new_alerts if x['severity']=='watch'),
    },
    'new_alerts': new_alerts[:25],
}
ALERTS_PATH.write_text(json.dumps(payload, indent=2))

with SUMMARY_PATH.open('w') as f:
    f.write(f"Generated: {payload['generated_at']}\n")
    f.write(f"Source: {source_used}\n")
    f.write(f"Window: {start} to {end}\n")
    f.write(f"Watch+: {payload['counts']['watch_or_higher']} | New: {payload['counts']['new_alerts']}\n")
    if new_alerts:
        a = new_alerts[0]
        f.write(f"Top: [{a['severity'].upper()}] {a['name']} miss={a['miss_km']:.0f}km v={a['v_kps']:.2f}km/s\n")

if WEBHOOK_URL and new_alerts:
    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(WEBHOOK_URL, data=body, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20):
            pass
    except Exception as e:
        (OUT_DIR / 'webhook-error.json').write_text(json.dumps({'error': str(e)}, indent=2))

print(f"ok source={source_used} watch+={len(objs)} new={len(new_alerts)}")
