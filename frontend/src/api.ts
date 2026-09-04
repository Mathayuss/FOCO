import type { ApiList, AvailableFilters, CsvPreview, MonthlyResponse, NamedMetric, Overview, Sla } from "./types"

export type HealthStatus = { status:string; service:string }

const configuredBase = import.meta.env.VITE_API_URL as string | undefined
const runtimeBase = `${window.location.protocol}//${window.location.hostname}:8000/api/v1`

export type AnalyticsParams = {
  period?: string
  type?: string
  municipality?: string
  unit?: string
  subtype?: string
  shift?: string
}

type ApiErrorPayload = { code?: string; errors?: { field:string; value:string; allowed?: string[] }[] }

function formatFilterIssue(issue:{ field:string; value:string; allowed?: string[] }){
  const labels:Record<string,string>={period:"período",type:"tipificação",municipality:"município",unit:"unidade",subtype:"subtipo",shift:"turno"}
  const allowed = issue.allowed?.length ? ` Valores aceitos: ${issue.allowed.join(", ")}.` : ""
  return `${labels[issue.field] || issue.field}=\"${issue.value}\".${allowed}`
}

function formatApiError(status:number, detail:unknown){
  if(typeof detail === "string") return detail
  const payload = detail as ApiErrorPayload
  if(payload?.code === "INVALID_FILTER" && Array.isArray(payload.errors)){
    return `Filtro inválido: ${payload.errors.map(formatFilterIssue).join(" ")}`
  }
  return `Erro da API (${status})`
}

export class ApiError extends Error{
  status:number
  detail:unknown
  constructor(status:number, detail:unknown){
    super(formatApiError(status, detail))
    this.name="ApiError"
    this.status=status
    this.detail=detail
  }
}

function apiBase(){
  if(!configuredBase) return runtimeBase
  try{
    const url = new URL(configuredBase, window.location.href)
    const openedByIp = !["localhost","127.0.0.1"].includes(window.location.hostname)
    const configuredLocal = ["localhost","127.0.0.1"].includes(url.hostname)
    if(openedByIp && configuredLocal) return runtimeBase
    return configuredBase.replace(/\/$/, "")
  }catch{
    return configuredBase.replace(/\/$/, "")
  }
}

function withParams(path:string, params?:AnalyticsParams){
  const query = new URLSearchParams()
  Object.entries(params || {}).forEach(([key,value])=>{ if(value) query.set(key,value) })
  const suffix = query.toString()
  return suffix ? `${path}?${suffix}` : path
}

const BASE = apiBase()

async function request<T>(path:string, init?:RequestInit):Promise<T>{
  const r=await fetch(`${BASE}${path}`, init)
  if(!r.ok){
    let detail:unknown = `${r.status}`
    try{
      const body = await r.json() as { detail?:unknown }
      detail = body.detail ?? detail
    }catch{}
    throw new ApiError(r.status, detail)
  }
  return r.json()
}

function get<T>(path:string, params?:AnalyticsParams){ return request<T>(withParams(path, params)) }
function postForm<T>(path:string, body:FormData){ return request<T>(path, {method:"POST", body}) }

export const api={
  health:()=>get<HealthStatus>("/health"),
  overview:(params?:AnalyticsParams)=>get<Overview>("/analytics/overview", params),
  monthly:(params?:AnalyticsParams)=>get<MonthlyResponse>("/analytics/monthly", params),
  types:(params?:AnalyticsParams)=>get<ApiList<NamedMetric>>("/analytics/types", params),
  cities:(params?:AnalyticsParams)=>get<ApiList<NamedMetric>>("/analytics/cities", params),
  hours:(params?:AnalyticsParams)=>get<ApiList<number>>("/analytics/hours", params),
  units:(params?:AnalyticsParams)=>get<ApiList<NamedMetric>>("/analytics/units", params),
  shifts:(params?:AnalyticsParams)=>get<ApiList<NamedMetric>>("/analytics/shifts", params),
  filters:()=>get<AvailableFilters>("/analytics/filters"),
  sla:()=>get<Sla>("/analytics/sla"),
  previewCsv:(file:File)=>{
    const body = new FormData()
    body.append("file", file)
    return postForm<CsvPreview>("/imports/csv/preview", body)
  },
}
