#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path
from poliastro.bodies import Earth
from poliastro.twobody import Orbit
from astropy import units as u
from astropy.time import Time
out = Path('/var/lib/pdf-trajectory'); out.mkdir(parents=True, exist_ok=True)
orb = Orbit.circular(Earth, alt=500*u.km, epoch=Time(datetime.utcnow()))
data={'generated_at':datetime.utcnow().isoformat()+'Z','scenario':'baseline-leo-validation','altitude_km':500,'period_min':orb.period.to(u.min).value,'inclination_deg':orb.inc.to(u.deg).value,'raan_deg':orb.raan.to(u.deg).value}
(out/'trajectory-baseline.json').write_text(json.dumps(data,indent=2))
(out/'trajectory-baseline.txt').write_text(f"Generated: {data['generated_at']}\nScenario: {data['scenario']}\nPeriod(min): {data['period_min']:.3f}\nInclination(deg): {data['inclination_deg']:.3f}\nRAAN(deg): {data['raan_deg']:.3f}\n")
print('ok baseline')
