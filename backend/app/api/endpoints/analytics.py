from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.analytics import OverviewResponse, SlaResponse
from app.services import historical_service
from app.services.sla_service import calculate

router = APIRouter(prefix="/analytics", tags=["análises"])

def filters(
    period: str | None = Query(default="all"),
    type: str | None = Query(default=None),
    municipality: str | None = Query(default=None),
    unit: str | None = Query(default=None),
    subtype: str | None = Query(default=None),
    shift: str | None = Query(default=None),
):
    params = {
        "period": period,
        "type_name": type,
        "municipality": municipality,
        "unit": unit,
        "subtype": subtype,
        "shift": shift,
    }
    errors = historical_service.validate_filter_params(
        period=period,
        type_name=type,
        municipality=municipality,
        unit=unit,
        subtype=subtype,
        shift=shift,
    )
    if errors:
        raise HTTPException(status_code=400, detail={"code": "INVALID_FILTER", "errors": errors})
    return params

@router.get("/overview", response_model=OverviewResponse)
def get_overview(params: dict = Depends(filters)):
    return historical_service.overview(**params)

@router.get("/monthly")
def monthly(params: dict = Depends(filters)):
    return historical_service.monthly(**params)

@router.get("/types")
def types(params: dict = Depends(filters)):
    return historical_service.types(**params)

@router.get("/cities")
def cities(params: dict = Depends(filters)):
    return historical_service.cities(**params)

@router.get("/hours")
def hours(params: dict = Depends(filters)):
    return historical_service.hours(**params)

@router.get("/units")
def units(params: dict = Depends(filters)):
    return historical_service.units(**params)

@router.get("/shifts")
def shifts(params: dict = Depends(filters)):
    return historical_service.shifts(**params)

@router.get("/filters")
def available_filters():
    values = historical_service.available_filter_values()
    return {
        "periods": historical_service.period_options(),
        "types": values["types"],
        "municipalities": values["municipalities"],
        "units": values["units"],
        "subtypes": values["subtypes"],
        "shifts": values["shifts"],
        "filterable_dimensions": ["period", "type"],
        "limited_dimensions": ["municipality", "unit", "subtype", "shift"],
        "source_scope": "historical_consolidated",
    }

@router.get("/sla", response_model=SlaResponse)
def sla(db: Session = Depends(get_db)):
    return calculate(db)
