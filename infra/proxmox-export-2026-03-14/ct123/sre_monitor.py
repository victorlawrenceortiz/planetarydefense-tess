#!/opt/pdf/alert-brain/.venv/bin/python
import json, urllib.request, subprocess
from datetime import datetime
from pathlib import Path

OUT = Path('/var/lib/pdf-sre-monitor')
OUT.mkdir(parents=True, exist_ok=True)

checks = [
  ('ct122-feed-json','http://192.168.1.238:9080/neo-feed-latest.json'),
  ('ct123-mission-control','http://127.0.0.1:9100/health'),
  ('ct123-command-center','http://127.0.0.1:9300'),
  ('ct124-impact-sim','http://192.168.1.240:9200/health'),
  ('ct124-orbit-diagram','http://192.168.1.240:9090'),
  ('ct121-dashboard','http://192.168.1.241:8088/neocp.html'),
]

rows=[]
for name,url in checks:
    ok=False; err=''; code=''; ms=None
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'pdf-sre-monitor'})
        import time; t0=time.time()
        with urllib.request.urlopen(req, timeout=8) as r:
            code=r.status
            _=r.read(200)
        ms=round((time.time()-t0)*1000,1)
        ok = 200 <= int(code) < 400
    except Exception as e:
        err=str(e)
    rows.append({'name':name,'url':url,'ok':ok,'http':code,'latency_ms':ms,'error':err})

# local service checks
units=['pdf-mission-control.service','pdf-historian-snapshot.timer','pdf-alert-brain.timer','pdf-command-center-http.service','pdf-briefing-bot.timer','pdf-incident-generator.timer','pdf-trend-engine.timer']
svc=[]
for u in units:
    p=subprocess.run(['systemctl','is-active',u],capture_output=True,text=True)
    svc.append({'unit':u,'state':p.stdout.strip()})

payload={'generated_at':datetime.utcnow().isoformat()+'Z','checks':rows,'services':svc,'ok_count':sum(1 for r in rows if r['ok']),'total':len(rows)}
(OUT/'status.json').write_text(json.dumps(payload,indent=2))

# html
cards=[]
for r in rows:
    color='#32cd32' if r['ok'] else '#ff6b6b'
    meta=f"HTTP {r['http']} | {r['latency_ms']} ms" if r['ok'] else (r['error'] or 'error')
    cards.append(f"<tr><td>{r['name']}</td><td><a href='{r['url']}' target='_blank'>link</a></td><td style='color:{color}'>{'OK' if r['ok'] else 'DOWN'}</td><td>{meta}</td></tr>")

svc_rows=''.join([f"<tr><td>{s['unit']}</td><td>{s['state']}</td></tr>" for s in svc])
html=f"""<!doctype html><html><head><meta charset='utf-8'><meta http-equiv='refresh' content='30'><title>PDF SRE Monitor</title>
<style>body{{font-family:Arial;background:#0b1020;color:#e6edf3;margin:16px}}table{{width:100%;border-collapse:collapse}}td,th{{border-bottom:1px solid #24324a;padding:8px}}</style></head>
<body><h2>PDF SRE Monitor</h2><div>Updated: {payload['generated_at']} | Healthy: {payload['ok_count']}/{payload['total']}</div>
<h3>Endpoint Checks</h3><table><tr><th>Name</th><th>URL</th><th>Status</th><th>Detail</th></tr>{''.join(cards)}</table>
<h3>CT123 Service States</h3><table><tr><th>Unit</th><th>State</th></tr>{svc_rows}</table></body></html>"""
(OUT/'index.html').write_text(html)
print('ok sre',payload['ok_count'],'/',payload['total'])
