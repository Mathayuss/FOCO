from statistics import median
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.occurrence import Occurrence

TARGET_MINUTES = 15.0

def _minutes(a, b):
    if not a or not b:
        return None
    return max(0.0, (b - a).total_seconds() / 60.0)

def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = (len(values) - 1) * p
    lo = int(idx)
    hi = min(lo + 1, len(values) - 1)
    frac = idx - lo
    return values[lo] * (1 - frac) + values[hi] * frac

def calculate(db: Session) -> dict:
    rows = db.scalars(select(Occurrence).where(Occurrence.source == "DADO_DEMO")).all()
    response = [m for o in rows if (m := _minutes(o.opened_at, o.arrival_at)) is not None]
    compliant = sum(1 for x in response if x <= TARGET_MINUTES)
    return {
        "sample_size": len(rows),
        "computable": len(response),
        "compliance_pct": round((compliant / len(response) * 100) if response else 0, 1),
        "median_response_minutes": round(median(response), 1) if response else 0,
        "p90_response_minutes": round(percentile(response, .90), 1),
        "target_minutes": TARGET_MINUTES,
        "source_scope": "demo_operational",
    }
