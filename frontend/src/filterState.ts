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

export const defaultGlobalFilters: GlobalFilters = {
  period: "all",
  type: "",
  municipality: "",
  unit: "",
  subtype: "",
  shift: "",
}

const periodLabels: Record<string, string> = {
  all: "Jan-Jul/2026",
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

export function activeFilterEntries(filters: GlobalFilters) {
  return [
    ["Período", filters.period !== "all" ? periodLabels[filters.period] || filters.period : ""],
    ["Tipo", filters.type],
    ["Município", filters.municipality],
    ["Unidade", filters.unit],
    ["Subtipo", filters.subtype],
    ["Turno", filters.shift],
  ].filter((entry): entry is [string, string] => Boolean(entry[1]))
}
