from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.occurrence import Occurrence
from app.models.unit import Unit

SOURCE_SCOPE = "RELATORIO_SEJUSP"
SOURCE_LABEL = "sejusp_importado"
FILTER_DIMENSIONS = ["period", "type", "municipality", "unit", "subtype", "shift"]
LOCAL_TZ = ZoneInfo("America/Campo_Grande")
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


@dataclass(frozen=True)
class _DatasetSignature:
    database_url: str
    total: int
    ultimo_id: int | None
    ultima_importacao: datetime | None


_CACHE_LOCK = Lock()
_CACHE_SIGNATURE: _DatasetSignature | None = None
_CACHE_ROWS: list[dict[str, Any]] | None = None


def clear_cache() -> None:
    global _CACHE_SIGNATURE, _CACHE_ROWS
    with _CACHE_LOCK:
        _CACHE_SIGNATURE = None
        _CACHE_ROWS = None


def _database_key(db: Session) -> str:
    bind = db.get_bind()
    return bind.url.render_as_string(hide_password=True) if bind is not None else "desconhecido"


def _dataset_signature(db: Session) -> _DatasetSignature:
    total, ultimo_id, ultima_importacao = db.execute(
        select(
            func.count(Occurrence.id),
            func.max(Occurrence.id),
            func.max(Occurrence.imported_at),
        ).where(Occurrence.source == SOURCE_SCOPE)
    ).one()
    return _DatasetSignature(
        database_url=_database_key(db),
        total=int(total or 0),
        ultimo_id=ultimo_id,
        ultima_importacao=ultima_importacao,
    )


def _local_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=LOCAL_TZ)
    return value.astimezone(LOCAL_TZ)


def _load_rows(db: Session) -> list[dict[str, Any]]:
    stmt = (
        select(
            Occurrence.opened_at,
            Occurrence.registered_at,
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
    rows = []
    for (
        opened_at,
        registered_at,
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
    ) in db.execute(stmt):
        opened_at = _local_datetime(opened_at)
        registered_at = _local_datetime(registered_at)
        reference_at = registered_at or opened_at
        rows.append(
            {
                "opened_at": opened_at,
                "registered_at": registered_at,
                "reference_at": reference_at,
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
                "shift": _shift_for(reference_at),
            }
        )
    return rows


def _rows(db: Session) -> list[dict[str, Any]]:
    global _CACHE_SIGNATURE, _CACHE_ROWS

    signature = _dataset_signature(db)
    with _CACHE_LOCK:
        if _CACHE_SIGNATURE == signature and _CACHE_ROWS is not None:
            return list(_CACHE_ROWS)

    rows = _load_rows(db)
    with _CACHE_LOCK:
        _CACHE_SIGNATURE = signature
        _CACHE_ROWS = rows
    return list(rows)


def _shift_for(opened_at: datetime | None) -> str | None:
    if not opened_at:
        return None
    hour = opened_at.hour
    for name, hours in SHIFT_RANGES.items():
        if hour in hours:
            return name
    return None


def _month_label(year: int, month: int) -> str:
    return f"{MONTH_NAMES[month]}/{year}"


def _range_label(pairs: list[tuple[int, int]]) -> str:
    if not pairs:
        return "Sem dados"
    if len(pairs) == 1:
        year, month = pairs[0]
        return _month_label(year, month)
    first_year, first_month = pairs[0]
    last_year, last_month = pairs[-1]
    if first_year == last_year:
        return f"{MONTH_NAMES[first_month]}-{MONTH_NAMES[last_month]}/{first_year}"
    return f"{_month_label(first_year, first_month)}-{_month_label(last_year, last_month)}"


def _period_defs(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    dates = [row["reference_at"] for row in rows if row.get("reference_at")]
    pairs = sorted({(date.year, date.month) for date in dates})
    if not pairs:
        return {"all": {"label": "Sem dados", "months": [], "period_keys": []}}

    periods: dict[str, dict[str, Any]] = {
        "all": {
            "label": _range_label(pairs),
            "months": [_month_label(year, month) for year, month in pairs],
            "period_keys": pairs,
        }
    }
    years = sorted({year for year, _month in pairs})
    for year in years:
        year_pairs = [pair for pair in pairs if pair[0] == year]
        year_months = [month for _year, month in year_pairs]
        periods[f"ano-{year}"] = {
            "label": str(year),
            "months": [_month_label(year, month) for month in year_months],
            "period_keys": year_pairs,
        }
        for key, quarter_months in QUARTERS.items():
            present = [month for month in quarter_months if (year, month) in pairs]
            if present:
                quarter_pairs = [(year, month) for month in present]
                periods[f"{year}-{key}"] = {
                    "label": _range_label(quarter_pairs),
                    "months": [_month_label(year, month) for month in present],
                    "period_keys": quarter_pairs,
                }
        for month in year_months:
            periods[f"{year}-{month:02d}"] = {
                "label": _month_label(year, month),
                "months": [_month_label(year, month)],
                "period_keys": [(year, month)],
            }
    return periods


def period_options(
    db: Session,
    period: str | None = None,
    type_name: str | None = None,
    municipality: str | None = None,
    unit: str | None = None,
    subtype: str | None = None,
    shift: str | None = None,
) -> list[dict[str, Any]]:
    rows = _rows(db)
    if any([period, type_name, municipality, unit, subtype, shift]):
        rows = _filtered_rows(rows, **_filter_args_without("period", period, type_name, municipality, unit, subtype, shift))
    return [
        {"key": key, "label": value["label"], "months": value["months"]}
        for key, value in _period_defs(rows).items()
    ]


def _filter_args_without(excluded: str, period: str | None, type_name: str | None, municipality: str | None, unit: str | None, subtype: str | None, shift: str | None) -> dict[str, str | None]:
    return {
        "period": None if excluded == "period" else period,
        "type_name": None if excluded == "type" else type_name,
        "municipality": None if excluded == "municipality" else municipality,
        "unit": None if excluded == "unit" else unit,
        "subtype": None if excluded == "subtype" else subtype,
        "shift": None if excluded == "shift" else shift,
    }


def _shift_options(rows: list[dict[str, Any]]) -> list[str]:
    present = {row["shift"] for row in rows if row.get("shift")}
    return [name for name in SHIFT_RANGES if name in present]


def available_filter_values(
    db: Session,
    period: str | None = None,
    type_name: str | None = None,
    municipality: str | None = None,
    unit: str | None = None,
    subtype: str | None = None,
    shift: str | None = None,
) -> dict[str, list[str]]:
    rows = _rows(db)
    period_rows = _filtered_rows(rows, **_filter_args_without("period", period, type_name, municipality, unit, subtype, shift))
    type_rows = _filtered_rows(rows, **_filter_args_without("type", period, type_name, municipality, unit, subtype, shift))
    municipality_rows = _filtered_rows(rows, **_filter_args_without("municipality", period, type_name, municipality, unit, subtype, shift))
    unit_rows = _filtered_rows(rows, **_filter_args_without("unit", period, type_name, municipality, unit, subtype, shift))
    subtype_rows = _filtered_rows(rows, **_filter_args_without("subtype", period, type_name, municipality, unit, subtype, shift))
    shift_rows = _filtered_rows(rows, **_filter_args_without("shift", period, type_name, municipality, unit, subtype, shift))
    periods = _period_defs(period_rows)
    return {
        "periods": list(periods),
        "types": _sorted_unique(row["type"] for row in type_rows),
        "municipalities": _sorted_unique(row["municipality"] for row in municipality_rows),
        "units": _sorted_unique(row["unit"] for row in unit_rows),
        "subtypes": _sorted_unique(row["subtype"] for row in subtype_rows),
        "shifts": _shift_options(shift_rows),
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
    rows = _rows(db)
    periods = _period_defs(rows)
    checks = {
        "period": (period, list(periods)),
        "type": (type_name, _sorted_unique(row["type"] for row in rows)),
        "municipality": (municipality, _sorted_unique(row["municipality"] for row in rows)),
        "unit": (unit, _sorted_unique(row["unit"] for row in rows)),
        "subtype": (subtype, _sorted_unique(row["subtype"] for row in rows)),
        "shift": (shift, list(SHIFT_RANGES)),
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


def _row_period_pair(row: dict[str, Any]) -> tuple[int, int] | None:
    reference_at = row.get("reference_at")
    if not reference_at:
        return None
    return reference_at.year, reference_at.month


def _filtered_rows(
    rows: list[dict[str, Any]],
    period: str | None = None,
    type_name: str | None = None,
    municipality: str | None = None,
    unit: str | None = None,
    subtype: str | None = None,
    shift: str | None = None,
) -> list[dict[str, Any]]:
    selected_pairs = set(_period(rows, period)["period_keys"])
    filtered = []
    for row in rows:
        if selected_pairs and _row_period_pair(row) not in selected_pairs:
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
    dates = {row["reference_at"].date() for row in rows if row.get("reference_at")}
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
            "hours": len({row["reference_at"].hour for row in filtered if row.get("reference_at")}),
            "type_distribution_scope": "linhas_importadas",
            "partial_type_series": False,
            "missing_type_months": [],
        },
    }


def _previous_month(pair: tuple[int, int]) -> tuple[int, int]:
    year, month = pair
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _is_contiguous(pairs: list[tuple[int, int]]) -> bool:
    return all(_previous_month(current) == previous for previous, current in zip(pairs, pairs[1:]))


def _previous_period(pairs: list[tuple[int, int]]) -> list[tuple[int, int]]:
    previous = []
    cursor = pairs[0]
    for _ in pairs:
        cursor = _previous_month(cursor)
        previous.append(cursor)
    return list(reversed(previous))


def _comparison(
    rows: list[dict[str, Any]],
    selected_period: dict[str, Any],
    total: int,
    type_name: str | None = None,
    municipality: str | None = None,
    unit: str | None = None,
    subtype: str | None = None,
    shift: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    summary = {
        "available": False,
        "current_label": selected_period["label"],
        "baseline_label": None,
        "current_total": total,
        "baseline_total": None,
        "delta_abs": None,
        "delta_pct": None,
        "reason": None,
        "source_scope": SOURCE_LABEL,
    }
    current_pairs = list(selected_period["period_keys"])
    if not current_pairs:
        summary["reason"] = "O recorte atual não possui meses válidos para comparação."
        return summary, []
    if not _is_contiguous(current_pairs):
        summary["reason"] = "O recorte atual possui meses descontínuos e não pode ser comparado."
        return summary, []

    baseline_pairs = _previous_period(current_pairs)
    available_pairs = {_row_period_pair(row) for row in rows if row.get("reference_at")}
    if not set(baseline_pairs).issubset(available_pairs):
        summary["reason"] = "Não há cobertura completa para o período imediatamente anterior."
        return summary, []

    comparable_rows = _filtered_rows(
        rows,
        type_name=type_name,
        municipality=municipality,
        unit=unit,
        subtype=subtype,
        shift=shift,
    )
    totals = Counter(_row_period_pair(row) for row in comparable_rows)
    baseline_total = sum(totals[pair] for pair in baseline_pairs)
    delta_abs = total - baseline_total
    delta_pct = round(delta_abs / baseline_total * 100, 1) if baseline_total else (0.0 if total == 0 else None)
    summary.update(
        {
            "available": True,
            "baseline_label": _range_label(baseline_pairs),
            "baseline_total": baseline_total,
            "delta_abs": delta_abs,
            "delta_pct": delta_pct,
            "reason": None if baseline_total else "A base anterior não possui ocorrências para calcular a variação percentual.",
        }
    )
    points = [
        {
            "current_month": _month_label(*current_pair),
            "baseline_month": _month_label(*baseline_pair),
            "current": totals[current_pair],
            "baseline": totals[baseline_pair],
            "delta": totals[current_pair] - totals[baseline_pair],
        }
        for current_pair, baseline_pair in zip(current_pairs, baseline_pairs)
    ]
    return summary, points


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
    comparison, _points = _comparison(
        rows,
        selected_period,
        total,
        type_name,
        municipality,
        unit,
        subtype,
        shift,
    )
    return {
        "total": total,
        "average_per_day": round((total / days) if days else 0, 1),
        "delta_pct": comparison["delta_pct"],
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
    selected_period = _period(rows, period)
    pairs = selected_period["period_keys"]
    items = []
    for year, month in pairs:
        month_rows = [row for row in filtered if _row_period_pair(row) == (year, month)]
        total = len(month_rows)
        items.append({"mes": _month_label(year, month), "total": total, "tip": _metric_items(month_rows, "type", total)[:8]})
    _summary, comparison = _comparison(
        rows,
        selected_period,
        len(filtered),
        type_name,
        municipality,
        unit,
        subtype,
        shift,
    )
    return {
        "items": items,
        "comparison": comparison,
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
        reference_at = row.get("reference_at")
        if reference_at:
            counts[reference_at.hour] += 1
    return {"items": counts, "source_scope": SOURCE_LABEL, **filter_metadata(db, **filters)}


def units(db: Session, unit: str | None = None, **filters: str | None) -> dict[str, Any]:
    filtered = _filtered_rows(_rows(db), unit=unit, **filters)
    return {"items": _metric_items(filtered, "unit", len(filtered)), "source_scope": SOURCE_LABEL, **filter_metadata(db, unit=unit, **filters)}


def shifts(db: Session, shift: str | None = None, **filters: str | None) -> dict[str, Any]:
    filtered = _filtered_rows(_rows(db), shift=shift, **filters)
    return {"items": _metric_items(filtered, "shift", len(filtered)), "source_scope": SOURCE_LABEL, **filter_metadata(db, shift=shift, **filters)}
