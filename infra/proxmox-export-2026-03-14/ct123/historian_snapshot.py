#!/opt/pdf/alert-brain/.venv/bin/python
import urllib.request
req = urllib.request.Request('http://127.0.0.1:9100/historian/snapshot', method='POST', data=b'{}', headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req, timeout=8) as r:
    print('ok snapshot', r.status)
