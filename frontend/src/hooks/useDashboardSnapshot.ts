import { useEffect, useState } from "react"
import { ApiError, api, type AnalyticsParams } from "../api"
import type { AvailableFilters, DashboardResponse } from "../types"

type SnapshotState = {
  requestKey:string
  loading:boolean
  error:string
  data:DashboardResponse|null
}

export function useDashboardSnapshot(params:AnalyticsParams={}){
  const [attempt,setAttempt] = useState(0)
  const requestKey = JSON.stringify([
    params.source || "", params.period || "", params.type || "",
    params.municipality || "", params.unit || "", params.subtype || "", params.shift || "", attempt,
  ])
  const [state,setState] = useState<SnapshotState>({requestKey:"",loading:true,error:"",data:null})
  const [filters,setFilters] = useState<AvailableFilters|null>(null)
  useEffect(() => {
    let alive = true
    const controller = new AbortController()
    setState({requestKey,loading:true,error:"",data:null})
    api.dashboard(params,controller.signal)
      .then(data => {
        if(!alive) return
        setFilters(data.filters)
        setState({requestKey,loading:false,error:"",data})
      })
      .catch(error => {
        if(!alive) return
        setState({requestKey,loading:false,data:null,
          error:error instanceof ApiError ? error.message : "Não foi possível acessar a API. Verifique se o backend está ativo."})
      })
    return () => { alive = false; controller.abort() }
  },[requestKey])
  // O render ja invalida o recorte anterior antes de iniciar o proximo efeito.
  const current = state.requestKey === requestKey
  return {
    filters,
    retry:() => setAttempt(value => value + 1),
    loading:!current || state.loading,
    error:current ? state.error : "",
    data:current && !state.loading && !state.error ? state.data : null,
  }
}
