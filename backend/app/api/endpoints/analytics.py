from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.analytics import OverviewResponse, SlaResponse
from app.services import historical_service, sejusp_analytics_service
from app.services.sla_service import calculate

router = APIRouter(prefix="/analytics", tags=["análises"])
VALID_SOURCES = {"historico", "sejusp"}
SOURCE_OPTIONS = [
    {"key": "historico", "label": "Histórico consolidado"},
    {"key": "sejusp", "label": "SEJUSP importado"},
]


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
    source: str | None = Query(default="historico"),
    fonte: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    source_key = fonte or source or "historico"
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
    if source_key == "sejusp":
        errors = sejusp_analytics_service.validate_filter_params(
            db,
            period=period,
            type_name=type,
            municipality=municipality,
            unit=unit,
            subtype=subtype,
            shift=shift,
        )
    else:
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


def _dispatch(params: dict, name: str):
    source = params["source"]
    values = {key: value for key, value in params.items() if key not in {"source", "db"}}
    if source == "sejusp":
        return getattr(sejusp_analytics_service, name)(params["db"], **values)
    return getattr(historical_service, name)(**values)


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
def available_filters(
    source: str | None = Query(default="historico"),
    fonte: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    source_key = fonte or source or "historico"
    if source_key not in VALID_SOURCES:
        raise _invalid_source(source_key)
    if source_key == "sejusp":
        values = sejusp_analytics_service.available_filter_values(db)
        return {
            "periods": sejusp_analytics_service.period_options(db),
            "types": values["types"],
            "municipalities": values["municipalities"],
            "units": values["units"],
            "subtypes": values["subtypes"],
            "shifts": values["shifts"],
            "filterable_dimensions": ["period", "type", "municipality", "unit", "subtype", "shift"],
            "limited_dimensions": [],
            "source_scope": "sejusp_importado",
            "sources": SOURCE_OPTIONS,
        }
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
        "sources": SOURCE_OPTIONS,
    }


@router.get("/sla", response_model=SlaResponse)
def sla(db: Session = Depends(get_db)):
    return calculate(db)
