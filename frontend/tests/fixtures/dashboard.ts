import type { DashboardResponse, FilterMetadata, NamedMetric } from "../../src/types"

// Dados ficticios exclusivos dos testes; nao sao inseridos ou servidos pela API real.
export const tipoTeste = "INCENDIO TESTE"
export const tipoLongoTeste = "TIPIFICACAO TESTE " + "DESCRICAO EXTENSA PARA VALIDAR O SELETOR ".repeat(8)
export const municipioTeste = "MUNICIPIO TESTE"
export const unidadeTeste = "UNIDADE TESTE"
export const subtipoTeste = "SUBTIPO TESTE"
export const periodoTeste = "2025-02"
export const turnoTeste = "Tarde"

const periods = [
  {key:"all", label:"Jan-Fev/2025", months:["Jan/2025","Fev/2025"]},
  {key:"ano-2025", label:"2025", months:["Jan/2025","Fev/2025"]},
  {key:"2025-01", label:"Jan/2025", months:["Jan/2025"]},
  {key:periodoTeste, label:"Fev/2025", months:["Fev/2025"]},
]
const dimensions = ["period","type","municipality","unit","subtype","shift"]

export function dashboardFixture(params = new URLSearchParams(), total?:number): DashboardResponse {
  const period = periods.find(option => option.key === params.get("period")) || periods[0]
  const filtered = dimensions.some(key => params.get(key) && params.get(key) !== "all")
  const count = total ?? (filtered ? 4 : 12)
  const metadata:FilterMetadata = {
    available_periods: periods,
    applied_filters: {
      period:period.label,
      type:params.get("type"), municipality:params.get("municipality"),
      unit:params.get("unit"), subtype:params.get("subtype"), shift:params.get("shift"),
    },
    unavailable_filters: [],
    coverage: {
      source_scope:"sejusp_importado", months:period.months,
      filterable_dimensions:dimensions, limited_dimensions:[],
      types:2, municipalities:1, units:1, hours:1,
    },
  }
  const metrics = (items:NamedMetric[]) => ({...metadata,source_scope:"sejusp_importado",items})
  const type = params.get("type") || tipoTeste
  const hours = Array.from({length:24},(_,hour) => hour === 14 ? count : 0)
  const comparison = period.key === periodoTeste
  return {
    filters: {
      periods, types:[tipoTeste,tipoLongoTeste], municipalities:[municipioTeste],
      units:[unidadeTeste], subtypes:[subtipoTeste], shifts:[turnoTeste],
      filterable_dimensions:dimensions, limited_dimensions:[], source_scope:"sejusp_importado",
      sources:[{key:"sejusp",label:"SEJUSP - fixture de teste, nao operacional"}],
    },
    overview: {
      ...metadata, total:count, average_per_day:2, delta_pct:comparison ? 100 : null,
      comparison: {
        available:comparison, current_label:period.label,
        baseline_label:comparison ? "Jan/2025" : null, current_total:count,
        baseline_total:comparison ? count / 2 : null,
        delta_abs:comparison ? count / 2 : null, delta_pct:comparison ? 100 : null,
        reason:comparison ? null : "Fixture de teste sem base anterior.",source_scope:"sejusp_importado",
      },
      top_type:type, top_municipality:municipioTeste,source_scope:"sejusp_importado",
    },
    sla: {
      sample_size:12,computable:0,compliance_pct:0,median_response_minutes:0,
      p90_response_minutes:0,target_minutes:15,source_scope:"sejusp_importado",
    },
    monthly: {
      ...metadata, source_scope:"sejusp_importado",
      items:period.months.map(mes => ({mes,total:count / period.months.length,tip:[]})),
      comparison:comparison ? [{current_month:"Fev/2025",baseline_month:"Jan/2025",
        current:count,baseline:count / 2,delta:count / 2}] : [],
    },
    types:metrics([{nome:type,total:count,pct:100}]),
    cities:metrics([{nome:municipioTeste,total:count,pct:100,lat:-20.45,lon:-54.61}]),
    units:metrics([{nome:unidadeTeste,total:count,pct:100}]),
    shifts:metrics([{nome:turnoTeste,total:count,pct:100}]),
    hours:{...metadata,source_scope:"sejusp_importado",items:hours},
  }
}
