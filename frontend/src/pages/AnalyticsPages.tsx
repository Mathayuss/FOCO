import { useMemo, type ReactNode } from "react"
import ReactECharts from "echarts-for-react"
import type { AnalyticsParams } from "../api"
import { useDashboardSnapshot } from "../hooks/useDashboardSnapshot"
import DashboardLoadState from "../components/DashboardLoadState"
import { periodKeyForMonth, preserveFilterSelection, preservePeriodSelection, toAnalyticsParams, type GlobalFilters, type SetGlobalFilters } from "../filterState"
import type { ApiList, AvailableFilters, MonthlyComparison, MonthlyItem, NamedMetric, Overview as OverviewType, Sla } from "../types"
import KpiCard from "../components/KpiCard"
import MapPanel from "../components/MapPanel"
import Panel from "../components/Panel"

const fmt=(n:number)=>n.toLocaleString("pt-BR")
const dec=(n:number)=>n.toFixed(1).replace(".",",")
const axis={axisLine:{lineStyle:{color:"#3a4049"}},axisLabel:{color:"#aeb4bd",fontSize:10},splitLine:{lineStyle:{color:"#2b3037"}}}
const fallbackPeriods=[{key:"all",label:"Todo período importado",months:[]}]
const filterLabels:Record<string,string>={period:"Período",type:"Tipo",municipality:"Município",unit:"Unidade",subtype:"Subtipo",shift:"Turno"}

function shiftForHour(hour:number){
 if(hour >= 0 && hour < 6) return "Madrugada"
 if(hour < 12) return "Manhã"
 if(hour < 18) return "Tarde"
 return "Noite"
}

function toggleText(current:string, next:string){
 return current === next ? "" : next
}

function togglePeriod(current:string, next:string){
 return current === next ? "all" : next
}

type DashboardProps={globalFilters:GlobalFilters;setGlobalFilters:SetGlobalFilters;clearGlobalFilters:()=>void}
type Snapshot={loading:boolean;error:string;retry:()=>void;filters:AvailableFilters|null;overview:OverviewType|null;sla:Sla|null;monthly:MonthlyItem[];comparison:MonthlyComparison[];types:ApiList<NamedMetric>|null;cities:ApiList<NamedMetric>|null;hours:ApiList<number>|null;units:ApiList<NamedMetric>|null;shifts:ApiList<NamedMetric>|null}

function useSnapshot(params:AnalyticsParams={}):Snapshot{
 const {loading,error,filters,data,retry}=useDashboardSnapshot(params)
 return {
  loading,error,filters,retry,overview:data?.overview || null,sla:data?.sla || null,
  monthly:data?.monthly.items || [],comparison:data?.monthly.comparison || [],
  types:data?.types || null,cities:data?.cities || null,hours:data?.hours || null,
  units:data?.units || null,shifts:data?.shifts || null,
 }
}

function PageHead({area,title,caption,badge}:{area:string;title:string;caption:string;badge:string}){
 return <div className="pageHead"><div><div className="eyebrow">{area}</div><h1>{title}</h1><p>{caption}</p></div><span className="badge">{badge}</span></div>
}

function FilterBar({filters,globalFilters,setGlobalFilters,children}:{filters:AvailableFilters|null;globalFilters:GlobalFilters;setGlobalFilters:SetGlobalFilters;children?:ReactNode}){
 const periodOptions=preservePeriodSelection(filters?.periods.length?filters.periods:fallbackPeriods,globalFilters.period)
 const typeOptions=preserveFilterSelection(filters?.types || [],globalFilters.type)
 const sourceOptions=filters?.sources || [{key:"sejusp",label:"SEJUSP importado"}]
 const sourceChange=(value:string)=>setGlobalFilters({source:value,period:"all",type:"",municipality:"",unit:"",subtype:"",shift:""})
 return <div className="filters pageFilterRow"><span>FILTROS</span><select aria-label="Fonte" value={globalFilters.source} onChange={e=>sourceChange(e.target.value)}>{sourceOptions.map(option=><option key={option.key} value={option.key}>{option.label}</option>)}</select><select aria-label="Período" value={globalFilters.period} onChange={e=>setGlobalFilters({period:e.target.value})}>{periodOptions.map(option=><option key={option.key} value={option.key}>{option.label}</option>)}</select><select aria-label="Tipificação" value={globalFilters.type} onChange={e=>setGlobalFilters({type:e.target.value})}><option value="">Todas as tipificações</option>{typeOptions.map(item=><option key={item} value={item}>{item}</option>)}</select>{children}</div>
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
 return <table className="dataTable"><thead><tr><th>{label}</th><th>Total</th><th>%</th></tr></thead><tbody>{items.map(item=><tr key={item.nome} className={onSelect?"selectable":""} onClick={onSelect?()=>onSelect(item):undefined}><td>{onSelect?<button type="button" className="rowAction" aria-label={`Filtrar ${label}: ${item.nome}`} onClick={event=>{event.stopPropagation();onSelect(item)}}>{item.nome}</button>:item.nome}</td><td>{fmt(item.total)}</td><td>{item.pct==null?"-":`${dec(item.pct)}%`}</td></tr>)}</tbody></table>
}

function LoadState({state,children}:{state:Snapshot;children:ReactNode}){
 return <DashboardLoadState loading={state.loading} error={state.error} onRetry={state.retry}>{children}</DashboardLoadState>
}

function useGlobalParams(globalFilters:GlobalFilters){
 const {source,period,type,municipality,unit,subtype,shift}=globalFilters
 return useMemo(()=>toAnalyticsParams(globalFilters),[source,period,type,municipality,unit,subtype,shift])
}

export function EvolutionPage({globalFilters,setGlobalFilters}:DashboardProps){
 const params=useGlobalParams(globalFilters)
 const state=useSnapshot(params)
 const hasComparison=state.comparison.length>0
 const comparisonSummary=state.overview?.comparison
 const zeroBaseline=Boolean(comparisonSummary?.available && comparisonSummary.baseline_total===0 && comparisonSummary.delta_pct==null)
 const variationValue=state.overview?.delta_pct==null?(zeroBaseline?"indisponível":"sem base"):`${state.overview.delta_pct>0?"+":""}${dec(state.overview.delta_pct)}%`
 const variationMeta=zeroBaseline?"base anterior: 0 ocorrências":comparisonSummary?.baseline_label || comparisonSummary?.reason || "período anterior"
 const monthEvents={click:(p:any)=>{ const key=periodKeyForMonth(String(p?.name || ""),state.filters?.periods); if(key) setGlobalFilters({period:togglePeriod(globalFilters.period,key)}) }}
 const selectedMonths=new Set(((state.filters?.periods || fallbackPeriods).find(option=>option.key===globalFilters.period)?.months || []))
 const highlightPeriod=globalFilters.period!=="all"
 const series:any[]=[{name:comparisonSummary?.current_label || "SEJUSP",type:"line",smooth:true,symbolSize:(_:unknown,p:any)=>highlightPeriod&&selectedMonths.has(state.monthly[p.dataIndex]?.mes)?10:7,data:state.monthly.map(item=>item.total),lineStyle:{width:3,color:"#d83135"},itemStyle:{color:"#ffcc29"}}]
 if(hasComparison) series.unshift({name:comparisonSummary?.baseline_label || "Período anterior",type:"line",smooth:true,symbolSize:5,data:state.comparison.map(item=>item.baseline),lineStyle:{width:2,color:"#58a6ff",type:"dashed"},itemStyle:{color:"#58a6ff"}})
 const option={animation:false,tooltip:{trigger:"axis"},legend:{show:hasComparison,textStyle:{color:"#aeb4bd"}},grid:{left:42,right:18,top:hasComparison?34:18,bottom:34},xAxis:{type:"category",data:state.monthly.map(item=>item.mes),...axis},yAxis:{type:"value",...axis},series}
 return <><PageHead area="ANÁLISE / EVOLUÇÃO" title="Evolução" caption="Volume mensal e comparação disponível." badge="Série temporal"/><FilterBar filters={state.filters} globalFilters={globalFilters} setGlobalFilters={setGlobalFilters}/><Warning items={state.overview?.unavailable_filters}/><LoadState state={state}><div className="kpiGrid compact"><KpiCard label="Total" value={fmt(state.overview?.total || 0)} meta="período selecionado" tone="red"/><KpiCard label="Média diária" value={dec(state.overview?.average_per_day || 0)} meta="dias reais do período"/><KpiCard label="Variação" value={variationValue} meta={variationMeta} tone="gold"/><KpiCard label="Base comparada" value={comparisonSummary?.baseline_total==null?"sem base":fmt(comparisonSummary.baseline_total)} meta={comparisonSummary?.baseline_label || comparisonSummary?.reason || "comparativo histórico"} tone="neutral"/></div><Panel title="Evolução mensal" sub={hasComparison?`${comparisonSummary?.current_label} comparado com ${comparisonSummary?.baseline_label}`:"Série filtrada pela API"}><ReactECharts option={option} onEvents={monthEvents} style={{height:390}}/></Panel></LoadState></>
}

export function TypificationPage({globalFilters,setGlobalFilters}:DashboardProps){
 const params=useGlobalParams(globalFilters)
 const state=useSnapshot(params)
 const items=state.types?.items || []
 const typeEvents={click:(p:any)=>{ if(p?.name) setGlobalFilters({type:toggleText(globalFilters.type,String(p.name))}) }}
 const option={animation:false,tooltip:{trigger:"item"},grid:{left:150,right:24,top:8,bottom:26},xAxis:{type:"value",...axis},yAxis:{type:"category",inverse:true,data:items.slice(0,12).map(item=>item.nome),...axis,axisLabel:{color:"#aeb4bd",fontSize:10,width:132,overflow:"truncate"}},series:[{type:"bar",data:items.slice(0,12).map(item=>item.total),barWidth:12,itemStyle:{borderRadius:6,color:(p:any)=>items[p.dataIndex]?.nome===globalFilters.type?"#ffcc29":"#d83135"}}]}
 return <><PageHead area="ANÁLISE / TIPIFICAÇÃO" title="Tipificação" caption="Distribuição das principais naturezas de ocorrência." badge="Categorias"/><FilterBar filters={state.filters} globalFilters={globalFilters} setGlobalFilters={setGlobalFilters}/><Warning items={state.types?.unavailable_filters}/><LoadState state={state}><div className="grid twoOne"><Panel title="Ranking de tipificações" sub="Totais do recorte disponível"><ReactECharts option={option} onEvents={typeEvents} style={{height:420}}/></Panel><Panel title="Tabela" sub="Clique em uma linha para filtrar"><Table items={items} label="Tipificação" onSelect={item=>setGlobalFilters({type:toggleText(globalFilters.type,item.nome)})}/></Panel></div></LoadState></>
}

export function TemporalPage({globalFilters,setGlobalFilters}:DashboardProps){
 const params=useGlobalParams(globalFilters)
 const state=useSnapshot(params)
 const hours=state.hours?.items || []
 const shifts=state.shifts?.items || []
 const peakHour=hours.reduce<number|null>((best,value,index)=>value>0 && (best===null || value>hours[best])?index:best,null)
 const hourEvents={click:(p:any)=>{ const index=Number(p?.dataIndex); if(globalFilters.source==="sejusp" && Number.isInteger(index)){ const next=shiftForHour(index); setGlobalFilters({shift:toggleText(globalFilters.shift,next)}) } }}
 const hourOption={animation:false,tooltip:{trigger:"axis"},grid:{left:42,right:16,top:18,bottom:34},xAxis:{type:"category",data:hours.map((_,i)=>String(i).padStart(2,"0")),...axis},yAxis:{type:"value",...axis},series:[{type:"bar",data:hours,barWidth:"62%",itemStyle:{color:(p:any)=>globalFilters.shift&&shiftForHour(p.dataIndex)===globalFilters.shift?"#ffcc29":p.dataIndex===peakHour?"#ffcc29":p.dataIndex>=7&&p.dataIndex<=18?"#d83135":"#343a44",borderRadius:[3,3,0,0]}}]}
 const shiftEvents={click:(p:any)=>{ if(p?.name) setGlobalFilters({shift:toggleText(globalFilters.shift,String(p.name))}) }}
 const shiftOption={animation:false,tooltip:{trigger:"item"},grid:{left:92,right:18,top:12,bottom:22},xAxis:{type:"value",...axis},yAxis:{type:"category",inverse:true,data:shifts.map(item=>item.nome),...axis},series:[{type:"bar",data:shifts.map(item=>item.total),barWidth:14,itemStyle:{borderRadius:6,color:(p:any)=>shifts[p.dataIndex]?.nome===globalFilters.shift?"#ffcc29":"#58a6ff"}}]}
 return <><PageHead area="ANÁLISE / TEMPORAL" title="Temporal" caption="Perfil horário e distribuição por turno." badge="Tempo"/><FilterBar filters={state.filters} globalFilters={globalFilters} setGlobalFilters={setGlobalFilters}><select aria-label="Turno" className={globalFilters.shift&&state.filters?.limited_dimensions?.includes("shift")?"filterLimited":""} value={globalFilters.shift} onChange={e=>setGlobalFilters({shift:e.target.value})}><option value="">Todos os turnos</option>{preserveFilterSelection(state.filters?.shifts || [],globalFilters.shift).map(item=><option key={item} value={item}>{item}</option>)}</select></FilterBar><Warning items={[...(state.hours?.unavailable_filters || []),...(state.shifts?.unavailable_filters || [])]}/><LoadState state={state}><div className="kpiGrid compact"><KpiCard label="Pico horário" value={peakHour===null?"sem dados":`${String(peakHour).padStart(2,"0")}h`} meta={peakHour===null?"sem horário registrado":`${fmt(hours[peakHour])} ocorrências`} tone="gold"/><KpiCard label="Turnos" value={String(shifts.length)} meta={globalFilters.source==="sejusp"?"recorte importado":"consolidado histórico"}/><KpiCard label="Fonte" value={globalFilters.source==="sejusp"?"SEJUSP":"Histórico"} meta={globalFilters.source==="sejusp"?"com filtros cruzados":"sem cruzamento por período/tipo"} tone="neutral"/></div><div className="grid twoOne"><Panel title="Ocorrências por hora" sub="Perfil consolidado"><ReactECharts option={hourOption} onEvents={hourEvents} style={{height:380}}/></Panel><Panel title="Turnos" sub={globalFilters.shift?"Turno selecionado":"Distribuição consolidada"}><ReactECharts option={shiftOption} onEvents={shiftEvents} style={{height:380}}/></Panel></div></LoadState></>
}

export function TerritoryPage({globalFilters,setGlobalFilters}:DashboardProps){
 const params=useGlobalParams(globalFilters)
 const state=useSnapshot(params)
 const cities=state.cities?.items || []
 const total=cities.reduce((sum,item)=>sum+item.total,0)
 const cityEvents={click:(p:any)=>{ if(p?.name) setGlobalFilters({municipality:toggleText(globalFilters.municipality,String(p.name))}) }}
 const option={animation:false,tooltip:{trigger:"item"},grid:{left:128,right:18,top:8,bottom:20},xAxis:{type:"value",...axis},yAxis:{type:"category",inverse:true,data:cities.slice(0,12).map(item=>item.nome),...axis,axisLabel:{color:"#aeb4bd",fontSize:10,width:112,overflow:"truncate"}},series:[{type:"bar",data:cities.slice(0,12).map(item=>item.total),barWidth:12,itemStyle:{borderRadius:6,color:(p:any)=>cities[p.dataIndex]?.nome===globalFilters.municipality?"#ffcc29":"#d83135"}}]}
 return <><PageHead area="ANÁLISE / TERRITÓRIO" title="Território" caption="Concentração municipal consolidada." badge="Municípios"/><FilterBar filters={state.filters} globalFilters={globalFilters} setGlobalFilters={setGlobalFilters}><select aria-label="Município" className={globalFilters.municipality&&state.filters?.limited_dimensions?.includes("municipality")?"filterLimited":""} value={globalFilters.municipality} onChange={e=>setGlobalFilters({municipality:e.target.value})}><option value="">Todos os municípios</option>{preserveFilterSelection(state.filters?.municipalities || [],globalFilters.municipality).map(item=><option key={item} value={item}>{item}</option>)}</select></FilterBar><Warning items={state.cities?.unavailable_filters}/><LoadState state={state}><div className="kpiGrid compact"><KpiCard label={globalFilters.municipality?"Município":"Municípios"} value={globalFilters.municipality || String(cities.length)} meta={globalFilters.municipality?`${fmt(total)} ocorrências consolidadas`:"com coordenadas disponíveis"} tone="red"/><KpiCard label="Total exibido" value={fmt(total)} meta="consolidado territorial"/><KpiCard label="Escopo" value="Municipal" meta={globalFilters.source==="sejusp"?"recorte filtrado":"sem recorte período/tipo"} tone="gold"/></div><div className="grid twoOne"><Panel title="Mapa territorial" sub={globalFilters.municipality?"Município selecionado":"Top municípios consolidados"}><MapPanel cities={cities} selected={globalFilters.municipality} onSelect={city=>setGlobalFilters({municipality:toggleText(globalFilters.municipality,city.nome)})}/></Panel><Panel title="Ranking municipal" sub="Ocorrências consolidadas"><ReactECharts option={option} onEvents={cityEvents} style={{height:380}}/></Panel></div></LoadState></>
}

export function UnitsPage({globalFilters,setGlobalFilters}:DashboardProps){
 const params=useGlobalParams(globalFilters)
 const state=useSnapshot(params)
 const items=state.units?.items || []
 const total=items.reduce((sum,item)=>sum+item.total,0)
 const unitEvents={click:(p:any)=>{ if(p?.name) setGlobalFilters({unit:toggleText(globalFilters.unit,String(p.name))}) }}
 const option={animation:false,tooltip:{trigger:"item"},grid:{left:135,right:18,top:8,bottom:20},xAxis:{type:"value",...axis},yAxis:{type:"category",inverse:true,data:items.map(item=>item.nome),...axis,axisLabel:{color:"#aeb4bd",fontSize:10,width:118,overflow:"truncate"}},series:[{type:"bar",data:items.map(item=>item.total),barWidth:12,itemStyle:{borderRadius:6,color:(p:any)=>items[p.dataIndex]?.nome===globalFilters.unit?"#ffcc29":"#58a6ff"}}]}
 return <><PageHead area="OPERAÇÃO / UNIDADES" title="Unidades" caption="Distribuição consolidada por unidade operacional." badge="Consolidado"/><FilterBar filters={state.filters} globalFilters={globalFilters} setGlobalFilters={setGlobalFilters}><select aria-label="Unidade" className={globalFilters.unit&&state.filters?.limited_dimensions?.includes("unit")?"filterLimited":""} value={globalFilters.unit} onChange={e=>setGlobalFilters({unit:e.target.value})}><option value="">Todas as unidades</option>{preserveFilterSelection(state.filters?.units || [],globalFilters.unit).map(item=><option key={item} value={item}>{item}</option>)}</select></FilterBar><Warning items={state.units?.unavailable_filters}/><LoadState state={state}><div className="grid twoOne"><Panel title="Ranking de unidades" sub={globalFilters.unit?"Unidade selecionada":"Ocorrências consolidadas"}><ReactECharts option={option} onEvents={unitEvents} style={{height:420}}/></Panel><Panel title="Tabela" sub={`${fmt(total)} ocorrências exibidas`}><Table items={items} label="Unidade" onSelect={item=>setGlobalFilters({unit:toggleText(globalFilters.unit,item.nome)})}/></Panel></div></LoadState></>
}

export function SlaPage(){
 const state=useSnapshot({})
 const sla=state.sla
 const coveragePct=sla?.sample_size?Math.round(sla.computable/sla.sample_size*1000)/10:0
 const hasCoverage=Boolean(sla?.computable)
 const items=sla?[{nome:"Calculáveis",total:sla.computable,pct:coveragePct},{nome:"Sem cobertura",total:sla.sample_size-sla.computable,pct:Math.round((100-coveragePct)*10)/10}]:[]
 return <><PageHead area="OPERAÇÃO / SLA" title="SLA" caption="Cobertura calculada apenas com timestamps operacionais disponíveis." badge={hasCoverage?"Calculável":"Sem cobertura"}/><LoadState state={state}><div className="kpiGrid compact"><KpiCard label="Conformidade" value={hasCoverage?`${dec(sla?.compliance_pct || 0)}%`:"sem dados"} meta="meta de 15 minutos" tone="green"/><KpiCard label="Mediana" value={hasCoverage?`${dec(sla?.median_response_minutes || 0)} min`:"sem dados"} meta="tempo-resposta"/><KpiCard label="P90" value={hasCoverage?`${dec(sla?.p90_response_minutes || 0)} min`:"sem dados"} meta="tempo-resposta" tone="gold"/><KpiCard label="Cobertura" value={`${sla?.computable || 0}/${sla?.sample_size || 0}`} meta={`${dec(coveragePct)}% calculável`} tone="neutral"/></div><div className="grid twoOne"><Panel title="Cobertura do indicador" sub="Base SEJUSP importada"><Table items={items}/></Panel><section className="statusPanel"><b>Escopo atual</b><span>O SLA somente será calculado quando existirem timestamps suficientes. Registros sem chegada não entram no indicador e permanecem contabilizados na cobertura.</span></section></div></LoadState></>
}

export function QualityPage(){
 const state=useSnapshot({})
 const coverage=state.overview?.coverage
 const rows=[
  {label:"Fonte operacional",value:state.overview?.source_scope || "-",tone:"cyan"},
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
