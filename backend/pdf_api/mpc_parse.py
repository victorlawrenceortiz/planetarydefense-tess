import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class NeocpRow:
    desig: str
    score: Optional[int]
    date_utc: str
    ra: float
    dec: float
    v: Optional[float]
    status: str
    nobs: Optional[int]
    arc: Optional[float]
    h: Optional[float]
    last: Optional[float]

LINE_RE = re.compile(r"^\S+")


def parse_line(line: str) -> Optional[NeocpRow]:
    line=line.strip()
    if not line or line.startswith('#'):
        return None

    parts=line.split()
    if len(parts) < 10:
        return None

    # fixed prefix
    desig = parts[0]
    try:
        score = int(parts[1])
    except Exception:
        score = None

    # date parts
    try:
        yyyy=int(parts[2]); mm=int(parts[3]); dd=float(parts[4])
        date_utc=f"{yyyy:04d}-{mm:02d}-{dd:.1f}"
    except Exception:
        date_utc=""

    try:
        ra=float(parts[5]); dec=float(parts[6])
    except Exception:
        return None

    try:
        v=float(parts[7])
    except Exception:
        v=None

    # status text spans until we hit an integer nobs
    status_tokens=[]
    nobs=None
    arc=None
    h=None
    last=None

    i=8
    while i < len(parts):
        tok=parts[i]
        if tok.isdigit():
            nobs=int(tok)
            i+=1
            break
        status_tokens.append(tok)
        i+=1

    status=" ".join(status_tokens).strip()

    # remaining: arc, H, last
    def f(j):
        try:
            return float(parts[j])
        except Exception:
            return None

    if nobs is not None and i < len(parts):
        arc=f(i); i+=1
    if i < len(parts):
        h=f(i); i+=1
    if i < len(parts):
        last=f(i)

    return NeocpRow(
        desig=desig, score=score, date_utc=date_utc, ra=ra, dec=dec, v=v,
        status=status, nobs=nobs, arc=arc, h=h, last=last
    )


def priority(row: NeocpRow) -> int:
    # Heuristic triage score 0-100
    p=0
    if row.score is not None:
        p += int(row.score*0.6)  # score is already 0-100-ish
    if row.nobs is not None:
        if row.nobs <= 4: p += 15
        elif row.nobs <= 8: p += 8
    if row.arc is not None:
        if row.arc <= 0.1: p += 15
        elif row.arc <= 0.5: p += 10
        elif row.arc <= 2.0: p += 5
    if row.v is not None:
        if row.v <= 19.0: p += 10
        elif row.v <= 21.0: p += 5
    if 'Added' in row.status: p += 5
    if 'Updated' in row.status: p += 2
    return max(0, min(100, p))
