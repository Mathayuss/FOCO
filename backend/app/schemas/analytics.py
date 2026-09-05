from typing import Any
from pydantic import BaseModel, Field

class FilterIssue(BaseModel):
    field: str
    value: str
    reason: str

class ComparisonSummary(BaseModel):
    available: bool
    current_label: str
    baseline_label: str | None = None
    current_total: int | None = None
    baseline_total: int | None = None
    delta_abs: int | None = None
    delta_pct: float | None = None
    reason: str | None = None
    source_scope: str

class OverviewResponse(BaseModel):
    total: int
    average_per_day: float
    delta_pct: float | None = None
    comparison: ComparisonSummary
    top_type: str
    top_municipality: str
    source_scope: str
    available_periods: list[dict[str, Any]] = Field(default_factory=list)
    applied_filters: dict[str, Any] = Field(default_factory=dict)
    unavailable_filters: list[FilterIssue] = Field(default_factory=list)
    coverage: dict[str, Any] = Field(default_factory=dict)

class SlaResponse(BaseModel):
    sample_size: int
    computable: int
    compliance_pct: float
    median_response_minutes: float
    p90_response_minutes: float
    target_minutes: float
    source_scope: str
