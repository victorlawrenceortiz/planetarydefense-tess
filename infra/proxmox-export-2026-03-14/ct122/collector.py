#!/usr/bin/env python3
import json, os, urllib.request, urllib.parse
from datetime import date, timedelta, datetime

API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
DAYS = int(os.getenv("LOOKAHEAD_DAYS", "1"))
OUT_DIR = os.getenv("OUT_DIR", "/var/lib/pdf-neo-watchtower")

start = date.today()
end = start + timedelta(days=max(0, DAYS))
params = urllib.parse.urlencode({
    "start_date": start.isoformat(),
    "end_date": end.isoformat(),
    "api_key": API_KEY,
})
url = f"https://api.nasa.gov/neo/rest/v1/feed?{params}"

with urllib.request.urlopen(url, timeout=30) as r:
    data = json.loads(r.read().decode("utf-8"))

neos = []
for d, objs in data.get("near_earth_objects", {}).items():
    for o in objs:
        cad_list = o.get("close_approach_data") or [{}]
        cad = cad_list[0]
        miss_km = float(cad.get("miss_distance", {}).get("kilometers", "1e99"))
        v_kps = float(cad.get("relative_velocity", {}).get("kilometers_per_second", "0"))
        neos.append({
            "date": d,
            "name": o.get("name"),
            "nasa_jpl_url": o.get("nasa_jpl_url"),
            "is_potentially_hazardous": bool(o.get("is_potentially_hazardous_asteroid")),
            "absolute_magnitude_h": o.get("absolute_magnitude_h"),
            "estimated_diameter_m_min": o.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_min"),
            "estimated_diameter_m_max": o.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_max"),
            "close_approach_date_full": cad.get("close_approach_date_full"),
            "miss_distance_km": miss_km,
            "relative_velocity_kps": v_kps,
            "orbiting_body": cad.get("orbiting_body"),
        })

neos.sort(key=lambda x: x["miss_distance_km"])
summary = {
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "window": {"start": start.isoformat(), "end": end.isoformat()},
    "element_count": len(neos),
    "hazardous_count": sum(1 for n in neos if n["is_potentially_hazardous"]),
    "closest": neos[:10],
}

os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "neo-feed-latest.json"), "w") as f:
    json.dump({"summary": summary, "objects": neos}, f, indent=2)
with open(os.path.join(OUT_DIR, "neo-summary.txt"), "w") as f:
    f.write(f"Generated: {summary['generated_at']}\n")
    f.write(f"Window: {start} to {end}\n")
    f.write(f"Objects: {summary['element_count']} | Hazardous: {summary['hazardous_count']}\n")
    if neos:
        c = neos[0]
        f.write(f"Closest: {c['name']} at {c['miss_distance_km']:.0f} km, v={c['relative_velocity_kps']:.2f} km/s\n")
print("ok", summary["element_count"], "objects")
