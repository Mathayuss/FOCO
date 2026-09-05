import type { AnalyticsParams } from "./api"

export type GlobalFilters = {
  source: string
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
  source: "historico",
  period: "all",
  type: "",
  municipality: "",
  unit: "",
  subtype: "",
  shift: "",
}

export const filterLabels: Record<FilterKey, string> = {
  source: "Fonte",
  period: "Período",
  type: "Tipo",
  municipality: "Município",
  unit: "Unidade",
  subtype: "Subtipo",
  shift: "Turno",
}

const sourceLabels: Record<string, string> = {
  historico: "Histórico consolidado",
  sejusp: "SEJUSP importado",
}

const historicalPeriodLabels: Record<string, string> = {
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

const importedPeriodLabels: Record<string, string> = {
  all: "Jan-Jun/2025",
  jan: "Jan/2025",
  fev: "Fev/2025",
  mar: "Mar/2025",
  abr: "Abr/2025",
  mai: "Mai/2025",
  jun: "Jun/2025",
  q1: "Jan-Mar/2025",
  q2: "Abr-Jun/2025",
}

export function toAnalyticsParams(filters: GlobalFilters): AnalyticsParams {
  return {
    source: filters.source,
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
    filters.source !== "historico",
    filters.period !== "all",
    Boolean(filters.type),
    Boolean(filters.municipality),
    Boolean(filters.unit),
    Boolean(filters.subtype),
    Boolean(filters.shift),
  ].filter(Boolean).length
}

export function sourceLabel(source: string) {
  return sourceLabels[source] || source
}

export function periodLabel(period: string, source = "historico") {
  const labels = source === "sejusp" ? importedPeriodLabels : historicalPeriodLabels
  return labels[period] || period
}

export function resetFilterPatch(key: FilterKey): Partial<GlobalFilters> {
  if (key === "source") return { source: "historico", period: "all", type: "", municipality: "", unit: "", subtype: "", shift: "" }
  return { [key]: key === "period" ? "all" : "" }
}

export function activeFilterEntries(filters: GlobalFilters): ActiveFilterEntry[] {
  const detailedSource = filters.source === "sejusp"
  const entries: ActiveFilterEntry[] = [
    { key: "source", label: filterLabels.source, value: filters.source !== "historico" ? sourceLabel(filters.source) : "", limited: false },
    { key: "period", label: filterLabels.period, value: filters.period !== "all" ? periodLabel(filters.period, filters.source) : "", limited: false },
    { key: "type", label: filterLabels.type, value: filters.type, limited: false },
    { key: "municipality", label: filterLabels.municipality, value: filters.municipality, limited: !detailedSource },
    { key: "unit", label: filterLabels.unit, value: filters.unit, limited: !detailedSource },
    { key: "subtype", label: filterLabels.subtype, value: filters.subtype, limited: !detailedSource },
    { key: "shift", label: filterLabels.shift, value: filters.shift, limited: !detailedSource },
  ]
  return entries.filter(entry => Boolean(entry.value))
}
