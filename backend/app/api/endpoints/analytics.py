from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.analytics import OverviewResponse, SlaResponse
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service, sejusp_analytics_service
from app.services.sla_service import calculate

router = APIRouter(prefix="/analytics", tags=["análises"])
VALID_SOURCES = {"sejusp"}


def _invalid_source(source_key: str):
    return HTTPException(
        status_code=400,
        detail={
            "code": "INVALID_FILTER",
            "errors": [{"field": "source", "value": source_key, "allowed": sorted(VALID_SOURCES)}],
        },
    )


def filters(
    period: str | None = Query(default="all"),
    type: str | None = Query(default=None),
    municipality: str | None = Query(default=None),
    unit: str | None = Query(default=None),
    subtype: str | None = Query(default=None),
    shift: str | None = Query(default=None),
    source: str | None = Query(default="sejusp"),
    fonte: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    source_key = fonte or source or "sejusp"
    if source_key not in VALID_SOURCES:
        raise _invalid_source(source_key)
    params = {
        "period": period,
        "type_name": type,
        "municipality": municipality,
        "unit": unit,
        "subtype": subtype,
        "shift": shift,
        "source": source_key,
        "db": db,
    }
    with sejusp_analytics_service.dataset_snapshot(db):
        errors = sejusp_analytics_service.validate_filter_params(
            db,
            period=period,
            type_name=type,
            municipality=municipality,
            unit=unit,
            subtype=subtype,
            shift=shift,
        )
        if errors:
            raise HTTPException(status_code=400, detail={"code": "INVALID_FILTER", "errors": errors})
        yield params


def _dispatch(params: dict, name: str):
    values = {key: value for key, value in params.items() if key not in {"source", "db"}}
    return getattr(sejusp_analytics_service, name)(params["db"], **values)


@router.get("/dashboard", response_model=DashboardResponse, response_model_exclude_unset=True)
def dashboard(params: dict = Depends(filters)):
    values = {key: value for key, value in params.items() if key not in {"source", "db"}}
    return dashboard_service.snapshot(params["db"], **values)


@router.get("/overview", response_model=OverviewResponse)
def get_overview(params: dict = Depends(filters)):
    return _dispatch(params, "overview")


@router.get("/monthly")
def monthly(params: dict = Depends(filters)):
    return _dispatch(params, "monthly")


@router.get("/types")
def types(params: dict = Depends(filters)):
    return _dispatch(params, "types")


@router.get("/cities")
def cities(params: dict = Depends(filters)):
    return _dispatch(params, "cities")


@router.get("/hours")
def hours(params: dict = Depends(filters)):
    return _dispatch(params, "hours")


@router.get("/units")
def units(params: dict = Depends(filters)):
    return _dispatch(params, "units")


@router.get("/shifts")
def shifts(params: dict = Depends(filters)):
    return _dispatch(params, "shifts")


@router.get("/filters")
def available_filters(params: dict = Depends(filters)):
    return _dispatch(params, "filter_options")


@router.get("/sla", response_model=SlaResponse)
def sla(db: Session = Depends(get_db)):
    return calculate(db)
