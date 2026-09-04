import { useEffect, useMemo, useState, type ReactNode } from "react"
import ReactECharts from "echarts-for-react"
import { ApiError, api, type AnalyticsParams } from "../api"
import { toAnalyticsParams, type GlobalFilters, type SetGlobalFilters } from "../filterState"
import type { ApiList, AvailableFilters, MonthlyComparison, MonthlyItem, NamedMetric, Overview as OverviewType, Sla } from "../types"
import KpiCard from "../components/KpiCard"
import MapPanel from "../components/MapPanel"
import Panel from "../components/Panel"

const fmt=(n:number)=>n.toLocaleString("pt-BR")
const dec=(n:number)=>n.toFixed(1).replace(".",",")
const axis={axisLine:{lineStyle:{color:"#42364b"}},axisLabel:{color:"#817489",fontSize:10},splitLine:{lineStyle:{color:"#2a2030"}}}
const fallbackPeriods=[{key:"all",label:"Jan-Jul/2026",months:["Jan","Fev","Mar","Abr","Mai","Jun","Jul"]}]
const filterLabels:Record<string,string>={period:"Período",type:"Tipo",municipality:"Município",unit:"Unidade",subtype:"Subtipo",shift:"Turno"}

type DashboardProps={globalFilters:GlobalFilters;setGlobalFilters:SetGlobalFilters;clearGlobalFilters:()=>void}
type Snapshot={loading:boolean;error:string;filters:AvailableFilters|null;overview:OverviewType|null;sla:Sla|null;monthly:MonthlyItem[];comparison:MonthlyComparison[];types:ApiList<NamedMetric>|null;cities:ApiList<NamedMetric>|null;hours:ApiList<number>|null;units:ApiList<NamedMetric>|null;shifts:ApiList<NamedMetric>|null}

function useSnapshot(params:AnalyticsParams={}){
 const [state,setState]=useState<Snapshot>({loading:true,error:"",filters:null,overview:null,sla:null,monthly:[],comparison:[],types:null,cities:null,hours:null,units:null,shifts:null})
 useEffect(()=>{
  let alive=true
  setState(prev=>({...prev,loading:true,error:""}))
  Promise.all([api.filters(),api.overview(params),api.sla(),api.monthly(params),api.types(params),api.cities(params),api.hours(params),api.units(params),api.shifts(params)])
   .then(([filters,overview,sla,monthly,types,cities,hours,units,shifts])=>{if(alive)setState({loading:false,error:"",filters,overview,sla,monthly:monthly.items,comparison:monthly.comparison,types,cities,hours,units,shifts})})
   .catch((err)=>{if(alive)setState(prev=>({...prev,loading:false,error:err instanceof ApiError ? err.message : "Não foi possível acessar a API. Verifique se o backend está ativo."}))})
  return ()=>{alive=false}
 },[params.period,params.type,params.municipality,params.unit,params.subtype,params.shift])
 return state
}

function PageHead({area,title,caption,badge}:{area:string;title:string;caption:string;badge:string}){
 return <div className="pageHead"><div><div className="eyebrow">{area}</div><h1>{title}</h1><p>{caption}</p></div><span className="badge">{badge}</span></div>
}

function FilterBar({filters,globalFilters,setGlobalFilters,children}:{filters:AvailableFilters|null;globalFilters:GlobalFilters;setGlobalFilters:SetGlobalFilters;children?:ReactNode}){
 const periodOptions=filters?.periods.length?filters.periods:fallbackPeriods
 const typeOptions=filters?.types || []
 return <div className="filters pageFilterRow"><span>FILTROS</span><select value={globalFilters.period} onChange={e=>setGlobalFilters({period:e.target.value})}>{periodOptions.map(option=><option key={option.key} value={option.key}>{option.label}</option>)}</select><select value={globalFilters.type} onChange={e=>setGlobalFilters({type:e.target.value})}><option value="">Todas as tipificações</option>{typeOptions.map(item=><option key={item} value={item}>{item}</option>)}</select>{children}</div>
}

function uniqueIssues(items:{field:string;value:string;reason?:string}[]){
 const seen=new Set<string>()
 return items.filter(item=>{const key=`${item.field}:${item.value}`; if(seen.has(key)) return false; seen.add(key); return true})
}

function Warning({items}:{items?:{field:string;value:string;reason?:string}[]}){
 const list=uniqueIssues(items || [])
 if(!list.length) return null
 return <div className="filterWarning"><b>Filtros não aplicados</b><span>{list.map(item=>`${filterLabels[item.field] || item.field}: ${item.value}`).join(" · ")}</span></div>
}

function Table({items,label="Nome",onSelect}:{items:NamedMetric[];label?:string;onSelect?:(item:NamedMetric)=>void}){
 return <table className="dataTable"><thead><tr><th>{label}</th><th>Total</th><th>%</th></tr></thead><tbody>{items.map(item=><tr key={item.nome} className={onSelect?"selectable":""} onClick={onSelect?()=>onSelect(item):undefined}><td>{item.nome}</td><td>{fmt(item.total)}</td><td>{item.pct==null?"-":`${dec(item.pct)}%`}</td></tr>)}</tbody></table>
}

function LoadState({state,children}:{state:Snapshot;children:ReactNode}){
 if(state.error) return <div className="errorBox">{state.error}</div>
 if(state.loading) return <div className="emptyState">Carregando dados...</div>
 return <>{children}</>
}

function useGlobalParams(globalFilters:GlobalFilters){
 const {period,type,municipality,unit,subtype,shift}=globalFilters
 return useMemo(()=>toAnalyticsParams(globalFilters),[period,type,municipality,unit,subtype,shift])
}

export function EvolutionPage({globalFilters,setGlobalFilters}:DashboardProps){
 const params=useGlobalParams(globalFilters)
 const state=useSnapshot(params)
 const hasComparison=state.comparison.length>0 && !globalFilters.type
 const series:any[]=[{name:"2026",type:"line",smooth:true,symbolSize:7,data:state.monthly.map(item=>item.total),lineStyle:{width:3,color:"#e85057"},itemStyle:{color:"#ffcc29"}}]
 if(hasComparison) series.unshift({name:"2025",type:"line",smooth:true,symbolSize:5,data:state.comparison.map(item=>item.v2025),lineStyle:{width:2,color:"#35d0d8",type:"dashed"},itemStyle:{color:"#35d0d8"}})
 const option={tooltip:{trigger:"axis"},legend:{show:hasComparison,textStyle:{color:"#91849a"}},grid:{left:42,right:18,top:hasComparison?34:18,bottom:34},xAxis:{type:"category",data:state.monthly.map(item=>item.mes),...axis},yAxis:{type:"value",...axis},series}
 return <><PageHead area="ANÁLISE / EVOLUÇÃO" title="Evolução" caption="Volume mensal e comparação histórica." badge="Série temporal"/><FilterBar filters={state.filters} globalFilters={globalFilters} setGlobalFilters={setGlobalFilters}/><Warning items={state.overview?.unavailable_filters}/><LoadState state={state}><div className="kpiGrid compact"><KpiCard label="Total" value={fmt(state.overview?.total || 0)} meta="período selecionado" tone="red"/><KpiCard label="Média diária" value={dec(state.overview?.average_per_day || 0)} meta="dias reais do período"/><KpiCard label="Variação" value={state.overview?.delta_pct==null?"sem base":`${state.overview.delta_pct>0?"+":""}${dec(state.overview.delta_pct)}%`} meta="base 2025" tone="gold"/></div><Panel title="Evolução mensal" sub={hasComparison?"Comparativo 2025 x 2026":"Série filtrada pela API"}><ReactECharts option={option} style={{height:390}}/></Panel></LoadState></>
}

export function TypificationPage({globalFilters,setGlobalFilters}:DashboardProps){
 const params=useGlobalParams(globalFilters)
 const state=useSnapshot(params)
 const items=state.types?.items || []
 const typeEvents={click:(p:any)=>{ if(p?.name) setGlobalFilters({type:String(p.name)}) }}
 const option={tooltip:{trigger:"item"},grid:{left:150,right:24,top:8,bottom:26},xAxis:{type:"value",...axis},yAxis:{type:"category",inverse:true,data:items.slice(0,12).map(item=>item.nome),...axis,axisLabel:{color:"#9c8fa4",fontSize:10,width:132,overflow:"truncate"}},series:[{type:"bar",data:items.slice(0,12).map(item=>item.total),barWidth:12,itemStyle:{borderRadius:6,color:(p:any)=>items[p.dataIndex]?.nome===globalFilters.type?"#ffcc29":"#d83135"}}]}
 return <><PageHead area="ANÁLISE / TIPIFICAÇÃO" title="Tipificação" caption="Distribuição das principais naturezas de ocorrência." badge="Categorias"/><FilterBar filters={state.filters} globalFilters={globalFilters} setGlobalFilters={setGlobalFilters}/><Warning items={state.types?.unavailable_filters}/><LoadState state={state}><div className="grid twoOne"><Panel title="Ranking de tipificações" sub="Totais do recorte disponível"><ReactECharts option={option} onEvents={typeEvents} style={{height:420}}/></Panel><Panel title="Tabela" sub="Clique em uma linha para filtrar"><Table items={items} onSelect={item=>setGlobalFilters({type:item.nome})}/></Panel></div></LoadState></>
}

export function TemporalPage({globalFilters,setGlobalFilters}:DashboardProps){
 const params=useGlobalParams(globalFilters)
 const state=useSnapshot(params)
 const hours=state.hours?.items || []
 const shifts=state.shifts?.items || []
 const peakHour=hours.reduce((best,value,index)=>value>(hours[best]||0)?index:best,0)
 const hourOption={tooltip:{trigger:"axis"},grid:{left:42,right:16,top:18,bottom:34},xAxis:{type:"category",data:hours.map((_,i)=>String(i).padStart(2,"0")),...axis},yAxis:{type:"value",...axis},series:[{type:"bar",data:hours,barWidth:"62%",itemStyle:{color:(p:any)=>p.dataIndex===peakHour?"#ffcc29":p.dataIndex>=7&&p.dataIndex<=18?"#d83135":"#44324d",borderRadius:[3,3,0,0]}}]}
 const shiftEvents={click:(p:any)=>{ if(p?.name) setGlobalFilters({shift:String(p.name)}) }}
 const shiftOption={tooltip:{trigger:"item"},grid:{left:92,right:18,top:12,bottom:22},xAxis:{type:"value",...axis},yAxis:{type:"category",inverse:true,data:shifts.map(item=>item.nome),...axis},series:[{type:"bar",data:shifts.map(item=>item.total),barWidth:14,itemStyle:{borderRadius:6,color:(p:any)=>shifts[p.dataIndex]?.nome===globalFilters.shift?"#ffcc29":"#35d0d8"}}]}
 return <><PageHead area="ANÁLISE / TEMPORAL" title="Temporal" caption="Perfil horário e distribuição por turno." badge="Tempo"/><FilterBar filters={state.filters} globalFilters={globalFilters} setGlobalFilters={setGlobalFilters}><select className={globalFilters.shift?"filterLimited":""} value={globalFilters.shift} onChange={e=>setGlobalFilters({shift:e.target.value})}><option value="">Todos os turnos</option>{(state.filters?.shifts || []).map(item=><option key={item} value={item}>{item}</option>)}</select></FilterBar><Warning items={[...(state.hours?.unavailable_filters || []),...(state.shifts?.unavailable_filters || [])]}/><LoadState state={state}><div className="kpiGrid compact"><KpiCard label="Pico horário" value={`${String(peakHour).padStart(2,"0")}h`} meta={`${fmt(hours[peakHour] || 0)} ocorrências`} tone="gold"/><KpiCard label="Turnos" value={String(shifts.length)} meta="consolidado histórico"/><KpiCard label="Fonte" value="Histórico" meta="sem cruzamento por período/tipo" tone="purple"/></div><div className="grid twoOne"><Panel title="Ocorrências por hora" sub="Perfil consolidado"><ReactECharts option={hourOption} style={{height:380}}/></Panel><Panel title="Turnos" sub={globalFilters.shift?"Turno selecionado":"Distribuição consolidada"}><ReactECharts option={shiftOption} onEvents={shiftEvents} style={{height:380}}/></Panel></div></LoadState></>
}

export function TerritoryPage({globalFilters,setGlobalFilters}:DashboardProps){
 const params=useGlobalParams(globalFilters)
 const state=useSnapshot(params)
 const cities=state.cities?.items || []
 const total=cities.reduce((sum,item)=>sum+item.total,0)
 const cityEvents={click:(p:any)=>{ if(p?.name) setGlobalFilters({municipality:String(p.name)}) }}
 const option={tooltip:{trigger:"item"},grid:{left:128,right:18,top:8,bottom:20},xAxis:{type:"value",...axis},yAxis:{type:"category",inverse:true,data:cities.slice(0,12).map(item=>item.nome),...axis,axisLabel:{color:"#9c8fa4",fontSize:10,width:112,overflow:"truncate"}},series:[{type:"bar",data:cities.slice(0,12).map(item=>item.total),barWidth:12,itemStyle:{borderRadius:6,color:(p:any)=>cities[p.dataIndex]?.nome===globalFilters.municipality?"#ffcc29":"#d83135"}}]}
 return <><PageHead area="ANÁLISE / TERRITÓRIO" title="Território" caption="Concentração municipal consolidada." badge="Municípios"/><FilterBar filters={state.filters} globalFilters={globalFilters} setGlobalFilters={setGlobalFilters}><select className={globalFilters.municipality?"filterLimited":""} value={globalFilters.municipality} onChange={e=>setGlobalFilters({municipality:e.target.value})}><option value="">Todos os municípios</option>{(state.filters?.municipalities || []).map(item=><option key={item} value={item}>{item}</option>)}</select></FilterBar><Warning items={state.cities?.unavailable_filters}/><LoadState state={state}><div className="kpiGrid compact"><KpiCard label={globalFilters.municipality?"Município":"Municípios"} value={globalFilters.municipality || String(cities.length)} meta={globalFilters.municipality?`${fmt(total)} ocorrências consolidadas`:"com coordenadas disponíveis"} tone="red"/><KpiCard label="Total exibido" value={fmt(total)} meta="consolidado territorial"/><KpiCard label="Escopo" value="Municipal" meta="sem recorte período/tipo" tone="gold"/></div><div className="grid twoOne"><Panel title="Mapa territorial" sub={globalFilters.municipality?"Município selecionado":"Top municípios consolidados"}><MapPanel cities={cities} selected={globalFilters.municipality}/></Panel><Panel title="Ranking municipal" sub="Ocorrências consolidadas"><ReactECharts option={option} onEvents={cityEvents} style={{height:380}}/></Panel></div></LoadState></>
}

export function UnitsPage({globalFilters,setGlobalFilters}:DashboardProps){
 const params=useGlobalParams(globalFilters)
 const state=useSnapshot(params)
 const items=state.units?.items || []
 const total=items.reduce((sum,item)=>sum+item.total,0)
 const unitEvents={click:(p:any)=>{ if(p?.name) setGlobalFilters({unit:String(p.name)}) }}
 const option={tooltip:{trigger:"item"},grid:{left:135,right:18,top:8,bottom:20},xAxis:{type:"value",...axis},yAxis:{type:"category",inverse:true,data:items.map(item=>item.nome),...axis,axisLabel:{color:"#9c8fa4",fontSize:10,width:118,overflow:"truncate"}},series:[{type:"bar",data:items.map(item=>item.total),barWidth:12,itemStyle:{borderRadius:6,color:(p:any)=>items[p.dataIndex]?.nome===globalFilters.unit?"#ffcc29":"#35d0d8"}}]}
 return <><PageHead area="OPERAÇÃO / UNIDADES" title="Unidades" caption="Distribuição consolidada por unidade operacional." badge="Consolidado"/><FilterBar filters={state.filters} globalFilters={globalFilters} setGlobalFilters={setGlobalFilters}><select className={globalFilters.unit?"filterLimited":""} value={globalFilters.unit} onChange={e=>setGlobalFilters({unit:e.target.value})}><option value="">Todas as unidades</option>{(state.filters?.units || []).map(item=><option key={item} value={item}>{item}</option>)}</select></FilterBar><Warning items={state.units?.unavailable_filters}/><LoadState state={state}><div className="grid twoOne"><Panel title="Ranking de unidades" sub={globalFilters.unit?"Unidade selecionada":"Ocorrências consolidadas"}><ReactECharts option={option} onEvents={unitEvents} style={{height:420}}/></Panel><Panel title="Tabela" sub={`${fmt(total)} ocorrências exibidas`}><Table items={items} label="Unidade" onSelect={item=>setGlobalFilters({unit:item.nome})}/></Panel></div></LoadState></>
}

export function SlaPage(){
 const state=useSnapshot({})
 const sla=state.sla
 const items=sla?[{nome:"Calculáveis",total:sla.computable,pct:Math.round(sla.computable/sla.sample_size*1000)/10},{nome:"Sem cobertura",total:sla.sample_size-sla.computable,pct:Math.round((sla.sample_size-sla.computable)/sla.sample_size*1000)/10}]:[]
 return <><PageHead area="OPERAÇÃO / SLA" title="SLA" caption="Indicadores demonstrativos separados do histórico consolidado." badge="Demo"/><LoadState state={state}><div className="kpiGrid compact"><KpiCard label="Conformidade" value={`${dec(sla?.compliance_pct || 0)}%`} meta="base demonstrativa" tone="green"/><KpiCard label="Mediana" value={`${dec(sla?.median_response_minutes || 0)} min`} meta="tempo-resposta"/><KpiCard label="P90" value={`${dec(sla?.p90_response_minutes || 0)} min`} meta="tempo-resposta" tone="gold"/><KpiCard label="Cobertura" value={`${sla?.computable || 0}/${sla?.sample_size || 0}`} meta="registros calculáveis" tone="purple"/></div><div className="grid twoOne"><Panel title="Cobertura do indicador" sub="Dado demonstrativo"><Table items={items}/></Panel><section className="statusPanel"><b>Escopo atual</b><span>O SLA permanece demonstrativo até existirem timestamps operacionais suficientes na base real ou histórica detalhada.</span></section></div></LoadState></>
}

export function QualityPage(){
 const state=useSnapshot({})
 const coverage=state.overview?.coverage
 const rows=[
  {label:"Fonte histórica",value:state.overview?.source_scope || "-",tone:"cyan"},
  {label:"SLA",value:state.sla?.source_scope || "-",tone:"gold"},
  {label:"Períodos",value:String(state.filters?.periods.length || 0),tone:"cyan"},
  {label:"Tipificações",value:String(state.filters?.types.length || 0),tone:"cyan"},
  {label:"Municípios",value:String(coverage?.municipalities || 0),tone:"cyan"},
  {label:"Unidades",value:String(coverage?.units || 0),tone:"cyan"},
  {label:"Subtipos",value:String(state.filters?.subtypes.length || 0),tone:"gold"},
  {label:"Faixas horárias",value:String(coverage?.hours || 0),tone:"cyan"},
 ]
 return <><PageHead area="DADOS / QUALIDADE" title="Qualidade" caption="Cobertura e limitações da fonte atual." badge="Auditoria"/><LoadState state={state}><div className="statusGrid">{rows.map(row=><div className={`statusItem ${row.tone}`} key={row.label}><span>{row.label}</span><b>{row.value}</b></div>)}</div><div className="grid twoOne"><Panel title="Dimensões aplicáveis" sub="Contrato v0.3"><div className="panelPad"><div className="chipList">{(coverage?.filterable_dimensions || []).map(item=><i key={item}>{filterLabels[item] || item}</i>)}</div></div></Panel><Panel title="Dimensões limitadas" sub="Dependem de agregação cruzada"><div className="panelPad"><div className="chipList missing">{(coverage?.limited_dimensions || []).map(item=><i key={item}>{filterLabels[item] || item}</i>)}</div></div></Panel></div></LoadState></>
}
