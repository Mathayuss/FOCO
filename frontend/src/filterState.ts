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
  all: "Todo período importado",
}

const importedMonthLabels: Record<string, string> = {
  "01": "Jan",
  "02": "Fev",
  "03": "Mar",
  "04": "Abr",
  "05": "Mai",
  "06": "Jun",
  "07": "Jul",
  "08": "Ago",
  "09": "Set",
  "10": "Out",
  "11": "Nov",
  "12": "Dez",
}

const importedQuarterLabels: Record<string, string> = {
  q1: "Jan-Mar",
  q2: "Abr-Jun",
  q3: "Jul-Set",
  q4: "Out-Dez",
}

function importedDynamicPeriodLabel(period: string) {
  const yearOnly = period.match(/^ano-(\d{4})$/)
  if (yearOnly) return yearOnly[1]
  const month = period.match(/^(\d{4})-(0[1-9]|1[0-2])$/)
  if (month) return `${importedMonthLabels[month[2]]}/${month[1]}`
  const quarter = period.match(/^(\d{4})-(q[1-4])$/)
  if (quarter) return `${importedQuarterLabels[quarter[2]]}/${quarter[1]}`
  return ""
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
  if (source === "sejusp") return importedPeriodLabels[period] || importedDynamicPeriodLabel(period) || period
  return historicalPeriodLabels[period] || period
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
