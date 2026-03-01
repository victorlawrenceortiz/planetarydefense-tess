import json
from pathlib import Path
import psycopg2
from fastapi import FastAPI

APP = FastAPI(title='PDF Pipeline API')

THRESH = Path('/etc/pdf/thresholds.json')
JPL_LATEST = Path('/var/lib/pdf/jpl/latest.json')
MPC_LATEST = Path('/var/lib/pdf/mpc/latest.json')


def db():
    return psycopg2.connect(dbname='pdf', user='pdf', password='pdf', host='127.0.0.1')


def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text())


@APP.get('/status')
def status():
    return {
        'ok': True,
        'jpl_latest_exists': JPL_LATEST.exists(),
        'mpc_latest_exists': MPC_LATEST.exists(),
        'thresholds': read_json(THRESH),
    }


@APP.get('/jpl/latest')
def jpl_latest():
    return read_json(JPL_LATEST) or {}


@APP.get('/mpc/latest')
def mpc_latest():
    return read_json(MPC_LATEST) or {}


@APP.get('/jpl/upcoming')
def jpl_upcoming(limit: int = 20):
    q = """
    SELECT des, cd, dist_ld, v_rel_km_s
    FROM jpl_close_approach
    ORDER BY cd ASC
    LIMIT %s
    """
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(q, (limit,))
            rows = cur.fetchall()
    return [{'des':r[0],'cd':r[1],'dist_ld':r[2],'v_rel_km_s':r[3]} for r in rows]
