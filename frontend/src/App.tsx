import React, { Suspense, lazy, useEffect, useState } from "react"
import Sidebar from "./components/Sidebar"
import { api } from "./api"
import { activeFilterCount, activeFilterEntries, defaultGlobalFilters, resetFilterPatch, type FilterKey, type GlobalFilters, type SetGlobalFilters } from "./filterState"

const Overview = lazy(() => import("./pages/Overview"))
const Imports = lazy(() => import("./pages/Imports"))
const Placeholder = lazy(() => import("./pages/Placeholder"))
const EvolutionPage = lazy(() => import("./pages/AnalyticsPages").then(module => ({ default: module.EvolutionPage })))
const QualityPage = lazy(() => import("./pages/AnalyticsPages").then(module => ({ default: module.QualityPage })))
const SlaPage = lazy(() => import("./pages/AnalyticsPages").then(module => ({ default: module.SlaPage })))
const TemporalPage = lazy(() => import("./pages/AnalyticsPages").then(module => ({ default: module.TemporalPage })))
const TerritoryPage = lazy(() => import("./pages/AnalyticsPages").then(module => ({ default: module.TerritoryPage })))
const TypificationPage = lazy(() => import("./pages/AnalyticsPages").then(module => ({ default: module.TypificationPage })))
const UnitsPage = lazy(() => import("./pages/AnalyticsPages").then(module => ({ default: module.UnitsPage })))

const FILTER_STORAGE_KEY = "foco.globalFilters.v03"
const PAGE_STORAGE_KEY = "foco.activePage.v03"
const PAGE_NAMES = ["Visão Geral","Evolução","Tipificação","Temporal","Território","SLA","Viaturas","Unidades","Importações","Integrações","Qualidade","Configurações"]

type ApiStatus = "checking" | "online" | "offline"

function loadGlobalFilters(): GlobalFilters {
 try {
  const raw = window.localStorage.getItem(FILTER_STORAGE_KEY)
  if(!raw) return defaultGlobalFilters
  const parsed = JSON.parse(raw) as Partial<GlobalFilters>
  return {...defaultGlobalFilters,...parsed,period:parsed.period || "all"}
 } catch {
  return defaultGlobalFilters
 }
}

function loadActivePage(){
 try {
  const page = window.localStorage.getItem(PAGE_STORAGE_KEY) || ""
  return PAGE_NAMES.includes(page) ? page : "Visão Geral"
 } catch {
  return "Visão Geral"
 }
}

function apiStatusLabel(status:ApiStatus){
 if(status === "online") return "API online"
 if(status === "offline") return "API offline"
 return "Verificando API"
}

export default function App(){
 const [active,setActive]=useState(loadActivePage)
 const [globalFilters,setGlobalFiltersState]=useState<GlobalFilters>(loadGlobalFilters)
 const [apiStatus,setApiStatus]=useState<ApiStatus>("checking")
 const [fullscreen,setFullscreen]=useState(Boolean(document.fullscreenElement))
 const count=activeFilterCount(globalFilters)
 const entries=activeFilterEntries(globalFilters)
 const setGlobalFilters:SetGlobalFilters=(patch)=>setGlobalFiltersState(prev=>({...prev,...patch}))
 const clearGlobalFilters=()=>setGlobalFiltersState(defaultGlobalFilters)
 const removeGlobalFilter=(key:FilterKey)=>setGlobalFiltersState(prev=>({...prev,...resetFilterPatch(key)}))
 useEffect(()=>{window.localStorage.setItem(FILTER_STORAGE_KEY,JSON.stringify(globalFilters))},[globalFilters])
 useEffect(()=>{window.localStorage.setItem(PAGE_STORAGE_KEY,active)},[active])
 useEffect(()=>{document.title=`FOCO - ${active}`},[active])
 useEffect(()=>{
  const syncFullscreen=()=>setFullscreen(Boolean(document.fullscreenElement))
  document.addEventListener("fullscreenchange",syncFullscreen)
  return ()=>document.removeEventListener("fullscreenchange",syncFullscreen)
 },[])
 useEffect(()=>{
  let alive=true
  const checkApi=()=>api.health().then(()=>{ if(alive) setApiStatus("online") }).catch(()=>{ if(alive) setApiStatus("offline") })
  checkApi()
  const timer=window.setInterval(checkApi,30000)
  return ()=>{ alive=false; window.clearInterval(timer) }
 },[])
 const toggleFullscreen=()=>{
  if(document.fullscreenElement){
   document.exitFullscreen().catch(()=>{})
   return
  }
  document.documentElement.requestFullscreen().catch(()=>{})
 }
 const common={globalFilters,setGlobalFilters,clearGlobalFilters}
 const pages:Record<string,React.ReactNode>={
  "Visão Geral":<Overview {...common}/>,
  "Evolução":<EvolutionPage {...common}/>,
  "Tipificação":<TypificationPage {...common}/>,
  "Temporal":<TemporalPage {...common}/>,
  "Território":<TerritoryPage {...common}/>,
  "SLA":<SlaPage/>,
  "Unidades":<UnitsPage {...common}/>,
  "Importações":<Imports setGlobalFilters={setGlobalFilters} onShowDashboard={()=>setActive("Visão Geral")}/>,
  "Qualidade":<QualityPage/>,
 }
 const page = pages[active] || <Placeholder name={active}/>
 return <div className="app"><Sidebar active={active} setActive={setActive}/><main><div className="topbar"><div className="filterSummary"><b>Filtros globais</b><span>{count ? `${count} filtros ativos` : "Sem filtros ativos"}</span></div><div className="topFilterChips">{entries.slice(0,4).map(entry=><button className={`filterChip ${entry.limited?"limited":""}`} key={entry.key} title={`Remover filtro ${entry.label}`} aria-label={`Remover filtro ${entry.label}: ${entry.value}`} onClick={()=>removeGlobalFilter(entry.key)}>{entry.label}: {entry.value}<span aria-hidden="true">x</span></button>)}{entries.length>4&&<i>+{entries.length-4}</i>}</div><div className="topActions"><span className={`apiStatus ${apiStatus}`} role="status">{apiStatusLabel(apiStatus)}</span><button title="Limpar filtros globais" aria-label="Limpar filtros globais" disabled={!count} onClick={clearGlobalFilters}>↺</button><button title={fullscreen?"Sair da tela cheia":"Tela cheia"} aria-label={fullscreen?"Sair da tela cheia":"Tela cheia"} onClick={toggleFullscreen}>⛶</button><div className="user"><div className="avatar">A</div><div><b>Analista</b><small>MVP</small></div></div></div></div><div className="content"><Suspense fallback={<div className="emptyState">Carregando módulo...</div>}>{page}</Suspense></div></main></div>
}
