from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.occurrence import Occurrence
from app.models.unit import Unit

SOURCE_SCOPE = "RELATORIO_SEJUSP"
SOURCE_LABEL = "sejusp_importado"
FILTER_DIMENSIONS = ["period", "type", "municipality", "unit", "subtype", "shift"]
MONTH_NAMES = {
    1: "Jan",
    2: "Fev",
    3: "Mar",
    4: "Abr",
    5: "Mai",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Set",
    10: "Out",
    11: "Nov",
    12: "Dez",
}
MONTH_KEYS = {
    1: "jan",
    2: "fev",
    3: "mar",
    4: "abr",
    5: "mai",
    6: "jun",
    7: "jul",
    8: "ago",
    9: "set",
    10: "out",
    11: "nov",
    12: "dez",
}
QUARTERS = {
    "q1": [1, 2, 3],
    "q2": [4, 5, 6],
    "q3": [7, 8, 9],
    "q4": [10, 11, 12],
}
SHIFT_RANGES = {
    "Madrugada": range(0, 6),
    "Manhã": range(6, 12),
    "Tarde": range(12, 18),
    "Noite": range(18, 24),
}


def _rows(db: Session) -> list[dict[str, Any]]:
    stmt = (
        select(
            Occurrence.opened_at,
            Occurrence.type_name,
            Occurrence.group_name,
            Occurrence.subtype_name,
            Occurrence.municipality,
            Occurrence.neighborhood,
            Occurrence.latitude,
            Occurrence.longitude,
            Occurrence.judicial_secret,
            Occurrence.ibge_code,
            Unit.name,
        )
        .outerjoin(Unit, Occurrence.unit_id == Unit.id)
        .where(Occurrence.source == SOURCE_SCOPE)
    )
    return [
        {
            "opened_at": opened_at,
            "type": type_name,
            "group": group_name,
            "subtype": subtype_name,
            "municipality": municipality,
            "neighborhood": neighborhood,
            "lat": latitude,
            "lon": longitude,
            "judicial_secret": judicial_secret,
            "ibge_code": ibge_code,
            "unit": unit_name,
            "shift": _shift_for(opened_at),
        }
        for (
            opened_at,
            type_name,
            group_name,
            subtype_name,
            municipality,
            neighborhood,
            latitude,
            longitude,
            judicial_secret,
            ibge_code,
            unit_name,
        ) in db.execute(stmt)
    ]


def _shift_for(opened_at: datetime | None) -> str | None:
    if not opened_at:
        return None
    hour = opened_at.hour
    for name, hours in SHIFT_RANGES.items():
        if hour in hours:
            return name
    return None


def _year_label(years: set[int]) -> str:
    if not years:
        return "sem dados"
    ordered = sorted(years)
    return str(ordered[0]) if len(ordered) == 1 else f"{ordered[0]}-{ordered[-1]}"


def _period_defs(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    dates = [row["opened_at"] for row in rows if row["opened_at"]]
    years = {date.year for date in dates}
    months = sorted({date.month for date in dates})
    year = _year_label(years)
    if not months:
        return {"all": {"label": "Sem dados", "months": [], "month_numbers": []}}

    first, last = months[0], months[-1]
    periods: dict[str, dict[str, Any]] = {
        "all": {
            "label": f"{MONTH_NAMES[first]}-{MONTH_NAMES[last]}/{year}",
            "months": [MONTH_NAMES[month] for month in months],
            "month_numbers": months,
        }
    }
    for month in months:
        periods[MONTH_KEYS[month]] = {
            "label": f"{MONTH_NAMES[month]}/{year}",
            "months": [MONTH_NAMES[month]],
            "month_numbers": [month],
        }
    for key, quarter_months in QUARTERS.items():
        present = [month for month in quarter_months if month in months]
        if present:
            periods[key] = {
                "label": f"{MONTH_NAMES[present[0]]}-{MONTH_NAMES[present[-1]]}/{year}",
                "months": [MONTH_NAMES[month] for month in present],
                "month_numbers": present,
            }
    return periods


def period_options(db: Session) -> list[dict[str, Any]]:
    return [
        {"key": key, "label": value["label"], "months": value["months"]}
        for key, value in _period_defs(_rows(db)).items()
    ]


def available_filter_values(db: Session) -> dict[str, list[str]]:
    rows = _rows(db)
    periods = _period_defs(rows)
    return {
        "periods": list(periods),
        "types": _sorted_unique(row["type"] for row in rows),
        "municipalities": _sorted_unique(row["municipality"] for row in rows),
        "units": _sorted_unique(row["unit"] for row in rows),
        "subtypes": _sorted_unique(row["subtype"] for row in rows),
        "shifts": list(SHIFT_RANGES),
    }


def validate_filter_params(
    db: Session,
    period: str | None = None,
    type_name: str | None = None,
    municipality: str | None = None,
    unit: str | None = None,
    subtype: str | None = None,
    shift: str | None = None,
) -> list[dict[str, Any]]:
    values = available_filter_values(db)
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


def _sorted_unique(values: Any) -> list[str]:
    return sorted({str(value).strip() for value in values if value and str(value).strip()})


def _period(rows: list[dict[str, Any]], period: str | None) -> dict[str, Any]:
    periods = _period_defs(rows)
    return periods.get(period or "all", periods["all"])


def _filtered_rows(
    rows: list[dict[str, Any]],
    period: str | None = None,
    type_name: str | None = None,
    municipality: str | None = None,
    unit: str | None = None,
    subtype: str | None = None,
    shift: str | None = None,
) -> list[dict[str, Any]]:
    selected_months = set(_period(rows, period)["month_numbers"])
    filtered = []
    for row in rows:
        opened_at = row["opened_at"]
        if selected_months and opened_at and opened_at.month not in selected_months:
            continue
        if type_name and row["type"] != type_name:
            continue
        if municipality and row["municipality"] != municipality:
            continue
        if unit and row["unit"] != unit:
            continue
        if subtype and row["subtype"] != subtype:
            continue
        if shift and row["shift"] != shift:
            continue
        filtered.append(row)
    return filtered


def _metric_items(rows: list[dict[str, Any]], field: str, total: int | None = None) -> list[dict[str, Any]]:
    counter = Counter(row[field] for row in rows if row.get(field))
    base = total if total is not None else sum(counter.values())
    return [
        {"nome": name, "total": count, "pct": round((count / base * 100) if base else 0, 1)}
        for name, count in counter.most_common()
    ]


def _date_count(rows: list[dict[str, Any]]) -> int:
    dates = {row["opened_at"].date() for row in rows if row.get("opened_at")}
    return len(dates)


def _requested_filters(
    period: str | None = None,
    type_name: str | None = None,
    municipality: str | None = None,
    unit: str | None = None,
    subtype: str | None = None,
    shift: str | None = None,
) -> dict[str, str | None]:
    return {
        "period": period if period and period != "all" else None,
        "type": type_name,
        "municipality": municipality,
        "unit": unit,
        "subtype": subtype,
        "shift": shift,
    }


def filter_metadata(
    db: Session,
    period: str | None = None,
    type_name: str | None = None,
    municipality: str | None = None,
    unit: str | None = None,
    subtype: str | None = None,
    shift: str | None = None,
) -> dict[str, Any]:
    rows = _rows(db)
    selected_period = _period(rows, period)
    filtered = _filtered_rows(rows, period, type_name, municipality, unit, subtype, shift)
    return {
        "available_periods": period_options(db),
        "applied_filters": {
            "period": selected_period["label"],
            "type": type_name,
            "municipality": municipality,
            "unit": unit,
            "subtype": subtype,
            "shift": shift,
        },
        "unavailable_filters": [],
        "coverage": {
            "source_scope": SOURCE_LABEL,
            "months": selected_period["months"],
            "filterable_dimensions": FILTER_DIMENSIONS,
            "limited_dimensions": [],
            "types": len(_sorted_unique(row["type"] for row in rows)),
            "municipalities": len(_sorted_unique(row["municipality"] for row in rows)),
            "units": len(_sorted_unique(row["unit"] for row in rows)),
            "hours": len({row["opened_at"].hour for row in filtered if row.get("opened_at")}),
            "type_distribution_scope": "linhas_importadas",
            "partial_type_series": False,
            "missing_type_months": [],
        },
    }


def _comparison(period_label: str, total: int) -> dict[str, Any]:
    return {
        "available": False,
        "current_label": period_label,
        "baseline_label": None,
        "current_total": total,
        "baseline_total": None,
        "delta_abs": None,
        "delta_pct": None,
        "reason": "A fonte importada ainda não possui base comparativa cadastrada.",
        "source_scope": SOURCE_LABEL,
    }


def overview(
    db: Session,
    period: str | None = None,
    type_name: str | None = None,
    municipality: str | None = None,
    unit: str | None = None,
    subtype: str | None = None,
    shift: str | None = None,
) -> dict[str, Any]:
    rows = _rows(db)
    filtered = _filtered_rows(rows, period, type_name, municipality, unit, subtype, shift)
    total = len(filtered)
    days = _date_count(filtered)
    type_items = _metric_items(filtered, "type", total)
    city_items = _metric_items(filtered, "municipality", total)
    selected_period = _period(rows, period)
    comparison = _comparison(selected_period["label"], total)
    return {
        "total": total,
        "average_per_day": round((total / days) if days else 0, 1),
        "delta_pct": None,
        "comparison": comparison,
        "top_type": type_name or (type_items[0]["nome"] if type_items else ""),
        "top_municipality": municipality or (city_items[0]["nome"] if city_items else ""),
        "source_scope": SOURCE_LABEL,
        **filter_metadata(db, period, type_name, municipality, unit, subtype, shift),
    }


def monthly(
    db: Session,
    period: str | None = None,
    type_name: str | None = None,
    municipality: str | None = None,
    unit: str | None = None,
    subtype: str | None = None,
    shift: str | None = None,
) -> dict[str, Any]:
    rows = _rows(db)
    filtered = _filtered_rows(rows, period, type_name, municipality, unit, subtype, shift)
    selected_months = _period(rows, period)["month_numbers"]
    months = selected_months or sorted({row["opened_at"].month for row in rows if row.get("opened_at")})
    items = []
    for month in months:
        month_rows = [row for row in filtered if row.get("opened_at") and row["opened_at"].month == month]
        total = len(month_rows)
        items.append({"mes": MONTH_NAMES[month], "total": total, "tip": _metric_items(month_rows, "type", total)[:8]})
    return {
        "items": items,
        "comparison": [],
        "source_scope": SOURCE_LABEL,
        **filter_metadata(db, period, type_name, municipality, unit, subtype, shift),
    }


def types(db: Session, type_name: str | None = None, **filters: str | None) -> dict[str, Any]:
    filtered = _filtered_rows(_rows(db), type_name=type_name, **filters)
    return {"items": _metric_items(filtered, "type", len(filtered)), "source_scope": SOURCE_LABEL, **filter_metadata(db, type_name=type_name, **filters)}


def cities(db: Session, municipality: str | None = None, **filters: str | None) -> dict[str, Any]:
    filtered = _filtered_rows(_rows(db), municipality=municipality, **filters)
    totals = Counter(row["municipality"] for row in filtered if row.get("municipality"))
    coords: dict[str, dict[str, float]] = defaultdict(lambda: {"lat_sum": 0.0, "lon_sum": 0.0, "count": 0.0})
    for row in filtered:
        city = row.get("municipality")
        if not city or row.get("lat") is None or row.get("lon") is None:
            continue
        coords[city]["lat_sum"] += float(row["lat"])
        coords[city]["lon_sum"] += float(row["lon"])
        coords[city]["count"] += 1
    total = len(filtered)
    items = []
    for name, count in totals.most_common():
        coord = coords.get(name)
        coord_count = coord["count"] if coord else 0
        items.append(
            {
                "nome": name,
                "total": count,
                "pct": round((count / total * 100) if total else 0, 1),
                "lat": round(coord["lat_sum"] / coord_count, 6) if coord_count else None,
                "lon": round(coord["lon_sum"] / coord_count, 6) if coord_count else None,
            }
        )
    return {"items": items, "source_scope": SOURCE_LABEL, **filter_metadata(db, municipality=municipality, **filters)}


def hours(db: Session, **filters: str | None) -> dict[str, Any]:
    filtered = _filtered_rows(_rows(db), **filters)
    counts = [0] * 24
    for row in filtered:
        opened_at = row.get("opened_at")
        if opened_at:
            counts[opened_at.hour] += 1
    return {"items": counts, "source_scope": SOURCE_LABEL, **filter_metadata(db, **filters)}


def units(db: Session, unit: str | None = None, **filters: str | None) -> dict[str, Any]:
    filtered = _filtered_rows(_rows(db), unit=unit, **filters)
    return {"items": _metric_items(filtered, "unit", len(filtered)), "source_scope": SOURCE_LABEL, **filter_metadata(db, unit=unit, **filters)}


def shifts(db: Session, shift: str | None = None, **filters: str | None) -> dict[str, Any]:
    filtered = _filtered_rows(_rows(db), shift=shift, **filters)
    return {"items": _metric_items(filtered, "shift", len(filtered)), "source_scope": SOURCE_LABEL, **filter_metadata(db, shift=shift, **filters)}
