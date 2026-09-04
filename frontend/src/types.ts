export type FilterIssue = { field:string; value:string; reason:string }
export type FilterCoverage = { source_scope:string; months:string[]; filterable_dimensions:string[]; limited_dimensions:string[]; types:number; municipalities:number; units:number; hours:number; type_distribution_scope?:string; partial_type_series?:boolean; missing_type_months?:string[] }
export type PeriodOption = { key:string; label:string; months:string[] }
export type FilterMetadata = { available_periods:PeriodOption[]; applied_filters:Record<string,string|null>; unavailable_filters:FilterIssue[]; coverage:FilterCoverage }
export type Overview = FilterMetadata & { total:number; average_per_day:number; delta_pct:number|null; top_type:string; top_municipality:string; source_scope:string }
export type Sla = { sample_size:number; computable:number; compliance_pct:number; median_response_minutes:number; p90_response_minutes:number; target_minutes:number; source_scope:string }
export type NamedMetric = { nome:string; total:number; pct?:number; lat?:number|null; lon?:number|null }
export type MonthlyItem = { mes:string; total:number|null; tip:NamedMetric[] }
export type ApiList<T> = Partial<FilterMetadata> & { items:T[]; source_scope:string }
export type MonthlyComparison = { mes:string; v2025:number; v2026:number; delta:number }
export type MonthlyResponse = FilterMetadata & { items:MonthlyItem[]; comparison:MonthlyComparison[]; source_scope:string }
export type AvailableFilters = { periods:PeriodOption[]; types:string[]; municipalities:string[]; units:string[]; subtypes:string[]; shifts:string[]; filterable_dimensions:string[]; limited_dimensions:string[]; source_scope:string }
export type CsvIssue = { row:number; issues:string[] }
export type CsvPreview = {
  headers:string[]
  recognized_headers:string[]
  missing_required_headers:string[]
  total_rows:number
  valid_rows:number
  invalid_rows:number
  issues:CsvIssue[]
  can_commit:boolean
}
