#!/opt/pdf/trajectory/.venv/bin/python
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title='PDF Impact Scenario API', version='1.0.0')

@app.get('/health')
def health():
    return {'ok': True, 'time': datetime.utcnow().isoformat()+'Z'}

@app.get('/scenario/baseline')
def baseline(miss_km: float = 1500000.0, velocity_kps: float = 12.5):
    # lightweight heuristic scoring for triage/testing
    score = min(100.0, max(0.0, (5000000.0 / max(miss_km,1.0))*10 + (velocity_kps*1.2)))
    band = 'LOW'
    if score >= 70: band = 'HIGH'
    elif score >= 40: band = 'MEDIUM'
    return {
      'generated_at': datetime.utcnow().isoformat()+'Z',
      'input': {'miss_km': miss_km, 'velocity_kps': velocity_kps},
      'heuristic_score': round(score,2),
      'band': band,
      'note': 'Heuristic triage score for rapid scenario ranking (not official impact probability).'
    }
