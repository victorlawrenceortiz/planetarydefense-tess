#!/opt/pdf/trajectory/.venv/bin/python
import json, urllib.request, hashlib
from datetime import datetime
from pathlib import Path

SRC = 'http://192.168.1.238:9080/neo-feed-latest.json'
OUT = Path('/var/lib/pdf-orbital-diagram')
OUT.mkdir(parents=True, exist_ok=True)

with urllib.request.urlopen(SRC, timeout=20) as r:
    data = json.loads(r.read().decode('utf-8'))
objs = data.get('objects', [])[:200]

points = []
for o in objs:
    name = o.get('name', 'unknown')
    miss_km = float(o.get('miss_distance_km', 1e99))
    vel = float(o.get('relative_velocity_kps', 0))
    haz = bool(o.get('is_potentially_hazardous', False))
    h = int(hashlib.sha1(name.encode()).hexdigest()[:6], 16)
    theta = h % 360
    r_earth_radii = miss_km / 6371.0
    points.append({
        'name': name,
        'theta': theta,
        'r': r_earth_radii,
        'miss_km': miss_km,
        'vel': vel,
        'haz': haz,
        'url': o.get('nasa_jpl_url','')
    })

points.sort(key=lambda x: x['r'])
closest = points[:20]

# build html with plotly from CDN
rows = []
for p in closest:
    rows.append(f"<tr><td>{p['name']}</td><td>{p['miss_km']:.0f}</td><td>{p['vel']:.2f}</td><td>{'YES' if p['haz'] else 'no'}</td></tr>")

r_vals = [p['r'] for p in points]
t_vals = [p['theta'] for p in points]
labels = [f"{p['name']}<br>miss: {p['miss_km']:.0f} km<br>v: {p['vel']:.2f} km/s<br>haz: {p['haz']}" for p in points]
colors = ['#ff4d4f' if p['haz'] else '#4ea8de' for p in points]

html = f"""<!doctype html>
<html><head><meta charset='utf-8'>
<meta http-equiv='refresh' content='300'>
<title>PDF Live Orbital Diagram</title>
<script src='https://cdn.plot.ly/plotly-2.35.2.min.js'></script>
<style>body{{background:#0b1020;color:#e6edf3;font-family:Arial,sans-serif;margin:20px}} .card{{background:#111827;padding:16px;border-radius:10px}} table{{width:100%;border-collapse:collapse}} td,th{{padding:8px;border-bottom:1px solid #253045}}</style>
</head>
<body>
<h2>Planetary Defense Foundation — Live Orbital Diagram</h2>
<div>Updated: {datetime.utcnow().isoformat()}Z | Objects: {len(points)} | Source: CT122 feed</div>
<div id='plot' class='card' style='height:620px;margin-top:12px;'></div>
<div class='card' style='margin-top:12px;'>
<h3>Closest 20 approaches</h3>
<table><tr><th>Name</th><th>Miss distance (km)</th><th>Velocity (km/s)</th><th>Hazardous</th></tr>
{''.join(rows)}
</table></div>
<script>
const trace={{type:'scatterpolar',mode:'markers',r:{r_vals},theta:{t_vals},text:{json.dumps(labels)},hoverinfo:'text',marker:{{size:8,color:{json.dumps(colors)},opacity:0.85}}}};
const layout={{paper_bgcolor:'#111827',plot_bgcolor:'#111827',font:{{color:'#e6edf3'}},polar:{{bgcolor:'#111827',radialaxis:{{type:'log',title:'Distance (Earth radii)'}},angularaxis:{{direction:'clockwise'}}}},showlegend:false}};
Plotly.newPlot('plot',[trace],layout,{{responsive:true}});
</script>
</body></html>"""

(OUT/'index.html').write_text(html)
print('ok diagram', len(points))
