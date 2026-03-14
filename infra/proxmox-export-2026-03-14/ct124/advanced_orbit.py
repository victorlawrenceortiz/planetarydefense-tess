#!/opt/pdf/trajectory/.venv/bin/python
import json, urllib.request
from pathlib import Path
from datetime import datetime
SRC='http://192.168.1.238:9080/neo-feed-latest.json'
OUT=Path('/var/lib/pdf-orbital-diagram'); OUT.mkdir(parents=True,exist_ok=True)
with urllib.request.urlopen(SRC, timeout=20) as r: data=json.loads(r.read().decode())
objs=data.get('objects',[])
# keep simple payload for front-end filtering
(Path(OUT/'advanced-data.json')).write_text(json.dumps({'generated_at':datetime.utcnow().isoformat()+'Z','objects':objs},indent=2))
html="""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>PDF Advanced Orbit</title><script src='https://cdn.plot.ly/plotly-2.35.2.min.js'></script>
<style>body{font-family:Arial;background:#0b1020;color:#e6edf3;margin:16px} .bar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}</style></head><body>
<h2>Advanced Orbit Visualization</h2><div id='meta'>loading...</div>
<div class='bar'>
<label>Max miss km <input id='maxm' type='number' value='5000000'></label>
<label>Haz only <input id='haz' type='checkbox'></label>
<button onclick='draw()'>Apply</button>
</div><div id='p' style='height:650px'></div>
<script>
let payload=null;
async function load(){payload=await (await fetch('advanced-data.json')).json(); document.getElementById('meta').textContent='Updated '+payload.generated_at+' | objects '+payload.objects.length; draw();}
function draw(){if(!payload)return; const maxm=Number(document.getElementById('maxm').value||1e99); const haz=document.getElementById('haz').checked;
const arr=payload.objects.filter(o=>Number(o.miss_distance_km||1e99)<=maxm && (!haz || o.is_potentially_hazardous));
const r=arr.map(o=>Number(o.miss_distance_km||1)/6371.0); const t=arr.map((o,i)=>i*137.5%360);
const c=arr.map(o=>o.is_potentially_hazardous?'#ff4d4f':'#4ea8de');
const txt=arr.map(o=>`${o.name}<br>miss:${Math.round(o.miss_distance_km)} km<br>v:${Number(o.relative_velocity_kps||0).toFixed(2)} km/s`);
Plotly.newPlot('p',[{type:'scatterpolar',mode:'markers',r:r,theta:t,text:txt,hoverinfo:'text',marker:{size:8,color:c}}],{paper_bgcolor:'#111827',plot_bgcolor:'#111827',font:{color:'#e6edf3'},polar:{radialaxis:{type:'log'}}},{responsive:true});}
load(); setInterval(load,300000);
</script></body></html>"""
(Path(OUT/'advanced.html')).write_text(html)
print('ok advanced',len(objs))
