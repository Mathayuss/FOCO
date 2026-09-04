import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "historical_metrics.json"
DAYS_BY_MONTH = {"Jan": 31, "Fev": 28, "Mar": 31, "Abr": 30, "Mai": 31, "Jun": 30, "Jul": 31}
PERIODS = {
    "all": {"label": "Jan-Jul/2026", "months": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul"]},
    "q1": {"label": "Jan-Mar/2026", "months": ["Jan", "Fev", "Mar"]},
    "q2": {"label": "Abr-Jun/2026", "months": ["Abr", "Mai", "Jun"]},
    "last3": {"label": "Mai-Jul/2026", "months": ["Mai", "Jun", "Jul"]},
}
FILTER_DIMENSIONS = ["period", "type", "municipality", "unit", "subtype", "shift"]
UNSUPPORTED_FILTER_REASONS = {
    "period": "Este endpoint retorna consolidado geral e ainda não possui recorte por período.",
    "type": "Este endpoint retorna consolidado geral e ainda não possui recorte por tipificação.",
    "municipality": "A fonte histórica atual não possui cruzamento mês × município × tipo.",
    "unit": "A fonte histórica atual não possui cruzamento mês × unidade × tipo.",
    "subtype": "A fonte histórica atual não possui subtipo agregado por período.",
    "shift": "A fonte histórica atual possui turno consolidado, sem cruzamento por período/tipo.",
}

@lru_cache
def historical_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))

def period_options() -> list[dict[str, Any]]:
    return [{"key": key, **value} for key, value in PERIODS.items()]

def available_filter_values() -> dict[str, list[str]]:
    data = historical_data()
    return {
        "periods": list(PERIODS),
        "types": [item["nome"] for item in data.get("tip", [])],
        "municipalities": [item["nome"] for item in data.get("mun", [])],
        "units": [item["nome"] for item in data.get("uni", [])],
        "subtypes": [],
        "shifts": list(data.get("turno", {}).keys()),
    }

def validate_filter_params(period: str | None = None, type_name: str | None = None, municipality: str | None = None, unit: str | None = None, subtype: str | None = None, shift: str | None = None) -> list[dict[str, Any]]:
    values = available_filter_values()
    checks = {
        "period": (period, values["periods"]),
        "type": (type_name, values["types"]),
        "municipality": (municipality, values["municipalities"]),
        "unit": (unit, values["units"]),
        "subtype": (subtype, values["subtypes"]),
        "shift": (shift, values["shifts"]),
    }
    return [
        {"field": field, "value": value, "allowed": allowed}
        for field, (value, allowed) in checks.items()
        if value and value not in allowed
    ]

def _period(period: str | None) -> dict[str, Any]:
    return PERIODS.get(period or "all", PERIODS["all"])

def _filtered_months(data: dict, period: str | None) -> list[dict]:
    selected = set(_period(period)["months"])
    return [month for month in data["monthly"] if month["mes"] in selected]

def _month_type_total(month: dict, type_name: str | None) -> int | None:
    if not type_name:
        return int(month["total"])
    item = next((item for item in month.get("tip", []) if item["nome"] == type_name), None)
    return int(item["total"]) if item else None

def _aggregate_type_total(data: dict, type_name: str) -> int | None:
    item = next((item for item in data.get("tip", []) if item["nome"] == type_name), None)
    return int(item["total"]) if item else None

def _sum_types(data: dict, months: list[dict], period: str | None) -> list[dict]:
    if (period or "all") == "all":
        return data.get("tip", [])
    totals: dict[str, int] = {}
    for month in months:
        for item in month.get("tip", []):
            totals[item["nome"]] = totals.get(item["nome"], 0) + int(item["total"])
    total = sum(month["total"] for month in months)
    return sorted(
        [
            {"nome": name, "total": value, "pct": round((value / total * 100) if total else 0, 1)}
            for name, value in totals.items()
        ],
        key=lambda item: item["total"],
        reverse=True,
    )

def _delta_pct(data: dict, months: list[dict], period: str | None, type_name: str | None) -> float | None:
    key = period or "all"
    if type_name:
        if key != "all":
            return None
        item = next((row for row in data["comparativo"].get("tip", []) if row["nome"] == type_name), None)
        return float(item["delta"]) if item else None
    current = sum(month["total"] for month in months)
    selected = {month["mes"] for month in months}
    previous = sum(row["v2025"] for row in data["comparativo"]["mensal"] if row["mes"] in selected)
    return round(((current - previous) / previous * 100), 1) if previous else None

def _type_series_quality(months: list[dict], type_name: str | None) -> dict[str, Any]:
    if not type_name:
        return {"partial_type_series": False, "missing_type_months": []}
    missing = [month["mes"] for month in months if _month_type_total(month, type_name) is None]
    return {"partial_type_series": bool(missing), "missing_type_months": missing}

def _requested_filters(period: str | None = None, type_name: str | None = None, municipality: str | None = None, unit: str | None = None, subtype: str | None = None, shift: str | None = None) -> dict[str, str | None]:
    return {
        "period": period if period and period != "all" else None,
        "type": type_name,
        "municipality": municipality,
        "unit": unit,
        "subtype": subtype,
        "shift": shift,
    }

def _apply_name_filter(items: list[dict], selected: str | None) -> list[dict]:
    if not selected:
        return items
    return [item for item in items if item.get("nome") == selected]

def filter_metadata(period: str | None = None, type_name: str | None = None, municipality: str | None = None, unit: str | None = None, subtype: str | None = None, shift: str | None = None, filterable_dimensions: list[str] | None = None) -> dict:
    data = historical_data()
    selected_period = _period(period)
    months = _filtered_months(data, period)
    filterable = ["period", "type"] if filterable_dimensions is None else filterable_dimensions
    requested = _requested_filters(period, type_name, municipality, unit, subtype, shift)
    unavailable = [
        {"field": field, "value": value, "reason": UNSUPPORTED_FILTER_REASONS[field]}
        for field, value in requested.items()
        if value and field not in filterable
    ]
    type_quality = _type_series_quality(months, type_name) if "period" in filterable and "type" in filterable else {"partial_type_series": False, "missing_type_months": []}
    applied_filters = {
        "period": selected_period["label"] if "period" in filterable else None,
        "type": type_name if "type" in filterable else None,
        "municipality": municipality if "municipality" in filterable else None,
        "unit": unit if "unit" in filterable else None,
        "subtype": subtype if "subtype" in filterable else None,
        "shift": shift if "shift" in filterable else None,
    }
    return {
        "available_periods": period_options(),
        "applied_filters": applied_filters,
        "unavailable_filters": unavailable,
        "coverage": {
            "source_scope": "historical_consolidated",
            "months": selected_period["months"],
            "filterable_dimensions": filterable,
            "limited_dimensions": [field for field in FILTER_DIMENSIONS if field not in filterable],
            "types": len(data.get("tip", [])),
            "municipalities": len(data.get("mun", [])),
            "units": len(data.get("uni", [])),
            "hours": len(data.get("hora", [])),
            "type_distribution_scope": "complete_aggregate" if (period or "all") == "all" else "monthly_top_categories",
            **type_quality,
        },
    }

def overview(period: str | None = None, type_name: str | None = None, **filters: str | None) -> dict:
    data = historical_data()
    months = _filtered_months(data, period)
    days = sum(DAYS_BY_MONTH.get(month["mes"], 0) for month in months)
    if type_name and (period or "all") == "all":
        total = _aggregate_type_total(data, type_name) or 0
    else:
        total = sum(value for month in months if (value := _month_type_total(month, type_name)) is not None)
    types = _sum_types(data, months, period)
    return {
        "total": total,
        "average_per_day": round((total / days) if days else 0, 1),
        "delta_pct": _delta_pct(data, months, period, type_name),
        "top_type": type_name or (types[0]["nome"] if types else ""),
        "top_municipality": data["mun"][0]["nome"] if data.get("mun") else "",
        "source_scope": "historical_consolidated",
        **filter_metadata(period, type_name, **filters, filterable_dimensions=["period", "type"]),
    }

def monthly(period: str | None = None, type_name: str | None = None, **filters: str | None) -> dict:
    data = historical_data()
    months = _filtered_months(data, period)
    selected = {month["mes"] for month in months}
    items = [{"mes": month["mes"], "total": _month_type_total(month, type_name), "tip": month.get("tip", [])} for month in months]
    comparison = [] if type_name else [row for row in data["comparativo"]["mensal"] if row["mes"] in selected]
    return {"items": items, "comparison": comparison, "source_scope": "historical_consolidated", **filter_metadata(period, type_name, **filters, filterable_dimensions=["period", "type"])}

def types(period: str | None = None, type_name: str | None = None, **filters: str | None) -> dict:
    data = historical_data()
    items = _sum_types(data, _filtered_months(data, period), period)
    if type_name:
        items = _apply_name_filter(items, type_name)
    return {"items": items, "source_scope": "historical_consolidated", **filter_metadata(period, type_name, **filters, filterable_dimensions=["period", "type"])}

def cities(municipality: str | None = None, **filters: str | None) -> dict:
    data = historical_data()
    coords = data.get("coords", {})
    items = [{**item, "lat": coords.get(item["nome"], [None, None])[0], "lon": coords.get(item["nome"], [None, None])[1]} for item in data["mun"]]
    items = _apply_name_filter(items, municipality)
    return {"items": items, "source_scope": "historical_consolidated", **filter_metadata(municipality=municipality, **filters, filterable_dimensions=["municipality"])}

def hours(**filters: str | None) -> dict:
    data = historical_data()
    return {"items": data["hora"], "source_scope": "historical_consolidated", **filter_metadata(**filters, filterable_dimensions=[])}

def units(unit: str | None = None, **filters: str | None) -> dict:
    data = historical_data()
    items = _apply_name_filter(data["uni"], unit)
    return {"items": items, "source_scope": "historical_consolidated", **filter_metadata(unit=unit, **filters, filterable_dimensions=["unit"])}

def shifts(shift: str | None = None, **filters: str | None) -> dict:
    data = historical_data()
    total = sum(data.get("turno", {}).values())
    items = [
        {"nome": name, "total": value, "pct": round((value / total * 100) if total else 0, 1)}
        for name, value in data.get("turno", {}).items()
    ]
    items = _apply_name_filter(items, shift)
    return {"items": items, "source_scope": "historical_consolidated", **filter_metadata(shift=shift, **filters, filterable_dimensions=["shift"])}
