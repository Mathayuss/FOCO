from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from app.schemas.analytics import FilterIssue, OverviewResponse, SlaResponse


class PeriodOption(BaseModel):
    key: str
    label: str
    months: list[str]


class SourceOption(BaseModel):
    key: str
    label: str


class AvailableFiltersResponse(BaseModel):
    periods: list[PeriodOption]
    types: list[str]
    municipalities: list[str]
    units: list[str]
    subtypes: list[str]
    shifts: list[str]
    filterable_dimensions: list[str]
    limited_dimensions: list[str]
    source_scope: str
    sources: list[SourceOption]


class NamedMetric(BaseModel):
    nome: str
    total: int
    pct: float | None = None
    lat: float | None = None
    lon: float | None = None


class SeriesMetadata(BaseModel):
    source_scope: str
    available_periods: list[PeriodOption]
    applied_filters: dict[str, str | None]
    unavailable_filters: list[FilterIssue]
    coverage: dict[str, Any]


Item = TypeVar("Item")


class SeriesResponse(SeriesMetadata, Generic[Item]):
    items: list[Item]


class MonthlyItem(BaseModel):
    mes: str
    total: int | None
    tip: list[NamedMetric]


class MonthlyComparison(BaseModel):
    current_month: str
    baseline_month: str
    current: int
    baseline: int
    delta: int


class MonthlyResponse(SeriesResponse[MonthlyItem]):
    comparison: list[MonthlyComparison] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    filters: AvailableFiltersResponse
    overview: OverviewResponse
    sla: SlaResponse
    monthly: MonthlyResponse
    types: SeriesResponse[NamedMetric]
    cities: SeriesResponse[NamedMetric]
    hours: SeriesResponse[int]
    units: SeriesResponse[NamedMetric]
    shifts: SeriesResponse[NamedMetric]
