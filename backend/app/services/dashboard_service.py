from typing import Any

from sqlalchemy.orm import Session

from app.services import sejusp_analytics_service as analytics
from app.services.sla_service import calculate


def snapshot(db: Session, **filters: str | None) -> dict[str, Any]:
    with analytics.dataset_snapshot(db):
        return {
            "filters": analytics.filter_options(db, **filters),
            "overview": analytics.overview(db, **filters),
            "monthly": analytics.monthly(db, **filters),
            "types": analytics.types(db, **filters),
            "cities": analytics.cities(db, **filters),
            "hours": analytics.hours(db, **filters),
            "units": analytics.units(db, **filters),
            "shifts": analytics.shifts(db, **filters),
            "sla": calculate(db),
        }
