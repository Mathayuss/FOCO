from datetime import datetime, timedelta, timezone
from random import Random
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.occurrence import Occurrence, OccurrenceVehicle
from app.models.unit import Unit
from app.models.vehicle import Vehicle

rng = Random(20260901)

TYPES = ["Emergência Clínica", "Sinistro de Trânsito", "Incêndio", "Queda / Acidente", "Remoção / Transporte"]
CITIES = ["Campo Grande", "Dourados", "Ponta Porã", "Corumbá", "Três Lagoas"]
VEHICLE_TYPES = ["UR", "ABT", "ABS", "AT"]

COORDS = {
    "Campo Grande": (-20.4697, -54.6201),
    "Dourados": (-22.2231, -54.8120),
    "Ponta Porã": (-22.5361, -55.7256),
    "Corumbá": (-19.008, -57.651),
    "Três Lagoas": (-20.751, -51.678),
}

def seed_demo(db: Session):
    if db.scalar(select(Occurrence.id).where(Occurrence.source == "DADO_DEMO").limit(1)):
        return

    units = {}
    for name, command in [("CMB/1ºGBM", "CMB"), ("2º GBM", "CBFron"), ("3º GBM", "CBDiv")]:
        u = Unit(name=name, command=command)
        db.add(u); db.flush(); units[name] = u

    vehicles = []
    for i in range(1, 13):
        vt = VEHICLE_TYPES[(i - 1) % len(VEHICLE_TYPES)]
        u = list(units.values())[(i - 1) % len(units)]
        v = Vehicle(code=f"{vt}-{i:03d}", vehicle_type=vt, unit_id=u.id)
        db.add(v); db.flush(); vehicles.append(v)

    start = datetime(2026, 8, 1, 6, 0, tzinfo=timezone.utc)
    for i in range(180):
        opened = start + timedelta(hours=i * 3.6 + rng.uniform(0, 1.8))
        dispatch = opened + timedelta(minutes=rng.uniform(1.5, 4.8))
        departure = dispatch + timedelta(minutes=rng.uniform(1.0, 5.5))
        travel = max(3.0, rng.gauss(8.2, 4.0))
        if i % 11 == 0: travel += rng.uniform(8, 18)
        arrival = departure + timedelta(minutes=travel)
        released = arrival + timedelta(minutes=max(10, rng.gauss(36, 17)))
        returned = released + timedelta(minutes=max(3, rng.gauss(9, 4)))
        available = returned + timedelta(minutes=max(1, rng.gauss(4, 2)))
        city = CITIES[i % len(CITIES)]
        lat, lon = COORDS[city]
        unit = list(units.values())[i % len(units)]
        occ = Occurrence(
            source="DADO_DEMO", source_id=f"DADO_DEMO-{i+1:05d}", external_number=f"2026-D-{i+1:05d}",
            opened_at=opened, dispatched_at=dispatch, departure_at=departure, arrival_at=arrival,
            released_at=released, returned_at=returned, available_at=available,
            type_name=TYPES[i % len(TYPES)], subtype_name=None,
            municipality=city, latitude=lat+rng.uniform(-.05,.05), longitude=lon+rng.uniform(-.05,.05),
            unit_id=unit.id, status="fechada", quality_score=1.0,
        )
        db.add(occ); db.flush()
        chosen = [vehicles[i % len(vehicles)]]
        if i % 7 == 0: chosen.append(vehicles[(i + 3) % len(vehicles)])
        for vehicle in chosen:
            db.add(OccurrenceVehicle(
                occurrence_id=occ.id, vehicle_id=vehicle.id,
                dispatched_at=dispatch, departure_at=departure, arrival_at=arrival,
                released_at=released, returned_at=returned, available_at=available,
            ))
    db.commit()
