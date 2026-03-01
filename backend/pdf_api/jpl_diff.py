import json, sys, os
import datetime as dt
import psycopg2


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

def item_key(item):
    return (item.get('des') or '', item.get('cd') or '')

def db():
    return psycopg2.connect(dbname='pdf', user='pdf', password='pdf', host='127.0.0.1')

def insert_items(items, fetched_at_utc: str | None):
    if not items:
        return
    with db() as conn:
        with conn.cursor() as cur:
            for i in items:
                cur.execute(
                    """
                    INSERT INTO jpl_close_approach(des, cd, dist_au, dist_ld, v_rel_km_s, h, fetched_at_utc)
                    VALUES (%s,%s,%s,%s,%s,%s, COALESCE(%s::timestamptz, now()))
                    ON CONFLICT(des, cd) DO NOTHING
                    """,
                    (
                        i.get('des'), i.get('cd'), i.get('dist_au'), i.get('dist_ld'),
                        i.get('v_rel_km_s'), i.get('H'), fetched_at_utc,
                    )
                )


def main():
    src = '/var/lib/pdef/jpl_cad.json'
    latest = '/var/lib/pdf/jpl/latest.json'
    outdir = '/var/lib/pdf/jpl'

    cur = load(src)
    if not cur:
        print(json.dumps({'ok': False, 'error': 'missing_source'}))
        return 2

    prev = load(latest) or {}
    cur_items = cur.get('items') or []
    prev_items = prev.get('items') or []

    # Insert all items into DB for historical queries
    insert_items(cur_items, cur.get('fetched_at_utc'))

    cur_set = set(item_key(i) for i in cur_items)
    prev_set = set(item_key(i) for i in prev_items)
    new_keys = cur_set - prev_set

    new_items = [i for i in cur_items if item_key(i) in new_keys]

    ts = dt.datetime.now(dt.timezone.utc)
    stamp = ts.strftime('%Y%m%dT%H%M%SZ')
    dump(os.path.join(outdir, f'snap-{stamp}.json'), cur)
    dump(latest, cur)

    out = {
        'fetched_at_utc': cur.get('fetched_at_utc') or ts.isoformat(),
        'source': cur.get('source'),
        'dist_max_au': cur.get('dist_max_au'),
        'days_ahead': cur.get('days_ahead'),
        'count': len(cur_items),
        'new_count': len(new_items),
        'items': new_items[:10],
        'note': 'new items since last run (key=des+cd)',
    }
    print(json.dumps(out, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())
