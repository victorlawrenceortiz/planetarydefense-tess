import json
import math
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import urllib.request
import urllib.parse

from skyfield.api import load

APP = FastAPI(title='PDF Orbit Viz')

STATIC_DIR = Path('/opt/pdf/viz/static')
DATA_DIR = Path('/var/lib/pdf')
JPL_LATEST = DATA_DIR / 'jpl' / 'latest.json'
MPC_LATEST = DATA_DIR / 'mpc' / 'latest.json'

TS = load.timescale()
EPH = load('de421.bsp')
SUN = EPH['sun']
PLANETS = {
    'mercury': EPH['mercury'],
    'venus': EPH['venus'],
    'earth': EPH['earth'],
    'mars': EPH['mars'],
}


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def sample_planet_orbit(body_name: str, days: int = 365, step_days: int = 5) -> List[List[float]]:
    body = PLANETS[body_name]
    t = TS.utc(2026, 3, range(1, days + 1, step_days))
    pos = (body.at(t) - SUN.at(t)).position.au
    return pos.T.tolist()


def kepler_orbit_points(el: Dict[str, float], n: int = 256) -> List[List[float]]:
    a = float(el['a'])
    e = float(el['e'])
    inc = math.radians(float(el.get('i', 0.0)))
    om = math.radians(float(el.get('om', 0.0)))
    w = math.radians(float(el.get('w', 0.0)))

    nu = np.linspace(0, 2 * math.pi, n)
    r = (a * (1 - e**2)) / (1 + e * np.cos(nu))

    x_p = r * np.cos(nu)
    y_p = r * np.sin(nu)
    z_p = np.zeros_like(x_p)

    def Rz(th):
        return np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])

    def Rx(th):
        return np.array([[1, 0, 0], [0, math.cos(th), -math.sin(th)], [0, math.sin(th), math.cos(th)]])

    R = Rz(om) @ Rx(inc) @ Rz(w)
    pts = np.vstack([x_p, y_p, z_p])
    out = (R @ pts).T
    return out.tolist()


def sbdb_elements(des: str) -> Dict[str, float] | None:
    url = 'https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=' + urllib.parse.quote(des)
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            payload = json.loads(r.read().decode('utf-8'))
    except Exception:
        return None

    orbit = payload.get('orbit') or {}
    elems = orbit.get('elements') or []
    out = {}
    for e in elems:
        name = e.get('name')
        val = e.get('value')
        if name in ('a', 'e', 'i', 'om', 'w') and val is not None:
            out[name] = float(val)
    if set(out.keys()) >= {'a', 'e'}:
        return out
    return None


@APP.get('/', response_class=HTMLResponse)
def index():
    return (STATIC_DIR / 'index.html').read_text()


@APP.get('/confirmed', response_class=HTMLResponse)
def confirmed_page():
    return (STATIC_DIR / 'confirmed.html').read_text()


@APP.get('/neocp', response_class=HTMLResponse)
def neocp_page():
    return (STATIC_DIR / 'neocp.html').read_text()


@APP.get('/api/planets')
def api_planets():
    out = {name: sample_planet_orbit(name) for name in PLANETS.keys()}
    return {'units': 'AU', 'orbits': out}


@APP.get('/api/confirmed')
def api_confirmed():
    jpl = read_json(JPL_LATEST)
    items = (jpl.get('items') or [])
    seen = []
    for it in items:
        d = it.get('des')
        if d and d not in seen:
            seen.append(d)
    seen = seen[:25]

    objs = []
    for d in seen:
        el = sbdb_elements(d)
        if not el:
            continue
        objs.append({'des': d, 'elements': el, 'orbit': kepler_orbit_points(el)})

    return {'units': 'AU', 'objects': objs, 'source_jpl_cad': jpl.get('source')}


@APP.get('/api/neocp')
def api_neocp():
    mpc = read_json(MPC_LATEST)
    lines = (mpc.get('lines') or [])
    return {'source': mpc.get('source'), 'line_count': mpc.get('line_count'), 'lines': lines[:200]}


APP.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')

@APP.get('/api/planet_positions')
def api_planet_positions():
    # current heliocentric positions (AU) at now
    t = TS.now()
    pos = {}
    for name, body in PLANETS.items():
        p = (body.at(t) - SUN.at(t)).position.au
        pos[name] = [float(p[0]), float(p[1]), float(p[2])]
    return {'units': 'AU', 'positions': pos, 't': str(t.utc_iso())}
