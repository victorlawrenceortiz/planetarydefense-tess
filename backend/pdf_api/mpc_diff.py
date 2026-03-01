import json, sys, os, hashlib
import datetime as dt
import psycopg2

from mpc_parse import parse_line, priority


def load(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def dump(path, obj):
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)

def lines_hash(lines):
    m = hashlib.sha256()
    for ln in lines:
        m.update((ln + '\n').encode('utf-8', errors='ignore'))
    return m.hexdigest()

def db():
    return psycopg2.connect(dbname='pdf', user='pdf', password='pdf', host='127.0.0.1')

def insert_snapshot(payload: dict, sha: str):
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO mpc_neocp_snapshot(fetched_at_utc, line_count, sha256, payload)
                VALUES (COALESCE(%s::timestamptz, now()), %s, %s, %s::jsonb)
                """,
                (payload.get('fetched_at_utc'), payload.get('line_count') or len(payload.get('lines') or []), sha, json.dumps(payload))
            )


def main():
    src = '/var/lib/pdef/mpc_neocp.json'
    latest = '/var/lib/pdf/mpc/latest.json'
    outdir = '/var/lib/pdf/mpc'

    cur = load(src)
    if not cur:
        print(json.dumps({'ok': False, 'error': 'missing_source'}))
        return 2

    prev = load(latest) or {}
    cur_lines = cur.get('lines') or []
    prev_lines = prev.get('lines') or []

    cur_hash = lines_hash(cur_lines)
    prev_hash = lines_hash(prev_lines) if prev_lines else None

    insert_snapshot(cur, cur_hash)

    # parse to structured rows
    cur_rows = [r for r in (parse_line(l) for l in cur_lines) if r]
    prev_rows = [r for r in (parse_line(l) for l in prev_lines) if r]

    cur_by = {r.desig: r for r in cur_rows}
    prev_by = {r.desig: r for r in prev_rows}

    new_desigs = [d for d in cur_by.keys() if d not in prev_by]
    new_items=[]
    for d in new_desigs:
        r=cur_by[d]
        new_items.append({
            'desig': r.desig,
            'score': r.score,
            'v': r.v,
            'nobs': r.nobs,
            'arc': r.arc,
            'status': r.status,
            'date_utc': r.date_utc,
            'priority': priority(r),
        })

    new_items.sort(key=lambda x: x.get('priority',0), reverse=True)

    ts = dt.datetime.now(dt.timezone.utc)
    stamp = ts.strftime('%Y%m%dT%H%M%SZ')
    dump(os.path.join(outdir, f'snap-{stamp}.json'), cur)
    dump(latest, cur)

    out = {
        'fetched_at_utc': cur.get('fetched_at_utc') or ts.isoformat(),
        'source': cur.get('source'),
        'line_count': cur.get('line_count') or len(cur_lines),
        'changed': (prev_hash is not None and cur_hash != prev_hash),
        'new_count': len(new_items),
        'items': new_items[:20],
        'note': 'new objects since last run (key=desig); triage priority heuristic 0-100',
    }
    print(json.dumps(out, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())
