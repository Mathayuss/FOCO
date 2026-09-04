import type { AnalyticsParams } from "./api"

export type GlobalFilters = {
  period: string
  type: string
  municipality: string
  unit: string
  subtype: string
  shift: string
}

export type SetGlobalFilters = (patch: Partial<GlobalFilters>) => void
export type FilterKey = keyof GlobalFilters
export type ActiveFilterEntry = { key: FilterKey; label: string; value: string; limited: boolean }

export const defaultGlobalFilters: GlobalFilters = {
  period: "all",
  type: "",
  municipality: "",
  unit: "",
  subtype: "",
  shift: "",
}

export const filterLabels: Record<FilterKey, string> = {
  period: "Período",
  type: "Tipo",
  municipality: "Município",
  unit: "Unidade",
  subtype: "Subtipo",
  shift: "Turno",
}

const periodLabels: Record<string, string> = {
  all: "Jan-Jul/2026",
  jan: "Jan/2026",
  fev: "Fev/2026",
  mar: "Mar/2026",
  abr: "Abr/2026",
  mai: "Mai/2026",
  jun: "Jun/2026",
  jul: "Jul/2026",
  q1: "Jan-Mar/2026",
  q2: "Abr-Jun/2026",
  last3: "Mai-Jul/2026",
}

export function toAnalyticsParams(filters: GlobalFilters): AnalyticsParams {
  return {
    period: filters.period,
    type: filters.type || undefined,
    municipality: filters.municipality || undefined,
    unit: filters.unit || undefined,
    subtype: filters.subtype || undefined,
    shift: filters.shift || undefined,
  }
}

export function activeFilterCount(filters: GlobalFilters) {
  return [
    filters.period !== "all",
    Boolean(filters.type),
    Boolean(filters.municipality),
    Boolean(filters.unit),
    Boolean(filters.subtype),
    Boolean(filters.shift),
  ].filter(Boolean).length
}

export function periodLabel(period: string) {
  return periodLabels[period] || period
}

export function resetFilterPatch(key: FilterKey): Partial<GlobalFilters> {
  return { [key]: key === "period" ? "all" : "" }
}

export function activeFilterEntries(filters: GlobalFilters): ActiveFilterEntry[] {
  const entries: ActiveFilterEntry[] = [
    { key: "period", label: filterLabels.period, value: filters.period !== "all" ? periodLabel(filters.period) : "", limited: false },
    { key: "type", label: filterLabels.type, value: filters.type, limited: false },
    { key: "municipality", label: filterLabels.municipality, value: filters.municipality, limited: true },
    { key: "unit", label: filterLabels.unit, value: filters.unit, limited: true },
    { key: "subtype", label: filterLabels.subtype, value: filters.subtype, limited: true },
    { key: "shift", label: filterLabels.shift, value: filters.shift, limited: true },
  ]
  return entries.filter(entry => Boolean(entry.value))
}
