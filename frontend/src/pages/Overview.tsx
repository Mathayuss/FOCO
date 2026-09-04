import React, { useEffect, useMemo, useState } from "react"
import ReactECharts from "echarts-for-react"
import { ApiError, api } from "../api"
import { activeFilterCount, activeFilterEntries, periodLabel, resetFilterPatch, toAnalyticsParams, type FilterKey, type GlobalFilters, type SetGlobalFilters } from "../filterState"
import type { AvailableFilters, MonthlyComparison, MonthlyItem, NamedMetric, Overview as OverviewType, PeriodOption, Sla } from "../types"
import KpiCard from "../components/KpiCard"
import Panel from "../components/Panel"
import MapPanel from "../components/MapPanel"

const fmt=(n:number)=>n.toLocaleString("pt-BR")
const dec=(n:number)=>n.toFixed(1).replace(".",",")
const axis={axisLine:{lineStyle:{color:"#3a4049"}},axisLabel:{color:"#aeb4bd",fontSize:10},splitLine:{lineStyle:{color:"#2b3037"}}}
const fallbackPeriods=[{key:"all",label:"Jan-Jul/2026",months:["Jan","Fev","Mar","Abr","Mai","Jun","Jul"]},{key:"jan",label:"Jan/2026",months:["Jan"]},{key:"fev",label:"Fev/2026",months:["Fev"]},{key:"mar",label:"Mar/2026",months:["Mar"]},{key:"abr",label:"Abr/2026",months:["Abr"]},{key:"mai",label:"Mai/2026",months:["Mai"]},{key:"jun",label:"Jun/2026",months:["Jun"]},{key:"jul",label:"Jul/2026",months:["Jul"]}]
const filterLabels:Record<string,string>={municipality:"Município",unit:"Unidade",subtype:"Subtipo",shift:"Turno",period:"Período",type:"Tipo"}


function periodKeyForMonth(month:string, periods:PeriodOption[]){
 return periods.find(option=>option.months.length===1 && option.months[0]===month)?.key || ""
}

type OverviewProps={globalFilters:GlobalFilters;setGlobalFilters:SetGlobalFilters;clearGlobalFilters:()=>void}

export default function Overview({globalFilters,setGlobalFilters,clearGlobalFilters}:OverviewProps){
 const [filters,setFilters]=useState<AvailableFilters|null>(null)
 const [ov,setOv]=useState<OverviewType|null>(null),[sla,setSla]=useState<Sla|null>(null),[months,setMonths]=useState<MonthlyItem[]>([]),[comparison,setComparison]=useState<MonthlyComparison[]>([]),[types,setTypes]=useState<NamedMetric[]>([]),[cities,setCities]=useState<NamedMetric[]>([]),[hours,setHours]=useState<number[]>([]),[units,setUnits]=useState<NamedMetric[]>([])
 const [loading,setLoading]=useState(true)
 const [error,setError]=useState("")
 const {period,type:typeFilter,municipality,unit,shift}=globalFilters
 const params=useMemo(()=>toAnalyticsParams(globalFilters),[period,typeFilter,municipality,unit,shift,globalFilters.subtype])
 useEffect(()=>{api.filters().then(setFilters).catch(()=>{})},[])
 useEffect(()=>{
  setLoading(true); setError("")
  Promise.all([api.overview(params),api.sla(),api.monthly(params),api.types(params),api.cities(params),api.hours(params),api.units(params)])
   .then(([a,b,c,d,e,f,g])=>{setOv(a);setSla(b);setMonths(c.items);setComparison(c.comparison);setTypes(d.items);setCities(e.items);setHours(f.items);setUnits(g.items)})
   .catch((err)=>setError(err instanceof ApiError ? err.message : "Não foi possível acessar a API. Verifique se o backend está ativo."))
   .finally(()=>setLoading(false))
 },[params])
 const periodOptions=filters?.periods.length?filters.periods:fallbackPeriods
 const typeOptions=filters?.types.length?filters.types:types.map(item=>item.nome)
 const municipalityOptions=filters?.municipalities || []
 const unitOptions=filters?.units || []
 const shiftOptions=filters?.shifts || []
 const unavailable=ov?.unavailable_filters || []
 const activeEntries=activeFilterEntries(globalFilters)
 const currentPeriod=ov?.applied_filters?.period || periodOptions.find(option=>option.key===period)?.label || periodLabel(period)
 const removeFilter=(key:FilterKey)=>setGlobalFilters(resetFilterPatch(key))
 const hasRequestedLimited=unavailable.length>0
 const hasFilter=activeFilterCount(globalFilters)>0
 const hasComparison=comparison.length>0 && !typeFilter
 const limited=ov?.coverage?.limited_dimensions || []
 const partialTypeSeries=Boolean(ov?.coverage?.partial_type_series)
 const missingTypeMonths=ov?.coverage?.missing_type_months || []
 const typeEvents={click:(p:any)=>{ if(p?.name) setGlobalFilters({type:String(p.name)}) }}
 const monthEvents={click:(p:any)=>{ const key=periodKeyForMonth(String(p?.name || ""),periodOptions); if(key) setGlobalFilters({period:key}) }}
 const monthlyOption=useMemo(()=>{
  const selectedMonths=new Set((periodOptions.find(option=>option.key===period)?.months || []))
  const highlightPeriod=period!=="all"
  const series:any[]=[{name:"2026",type:"line",data:months.map(x=>x.total),smooth:true,symbolSize:(_:unknown,p:any)=>highlightPeriod&&selectedMonths.has(months[p.dataIndex]?.mes)?10:7,lineStyle:{width:3,color:"#d83135"},itemStyle:{color:"#ffcc29"},areaStyle:{color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:"rgba(216,49,53,.32)"},{offset:1,color:"rgba(216,49,53,.02)"}]}}}]
  if(hasComparison) series.unshift({name:"2025",type:"line",data:comparison.map(x=>x.v2025),smooth:true,symbolSize:5,lineStyle:{width:2,color:"#58a6ff",type:"dashed"},itemStyle:{color:"#58a6ff"}})
  return {tooltip:{trigger:"axis"},legend:{show:hasComparison,top:0,right:12,textStyle:{color:"#aeb4bd",fontSize:10}},grid:{left:38,right:14,top:hasComparison?34:20,bottom:30},xAxis:{type:"category",data:months.map(x=>x.mes),...axis},yAxis:{type:"value",...axis},series}
 },[months,comparison,hasComparison,period,periodOptions])
 const typeOption=useMemo(()=>({tooltip:{trigger:"item"},grid:{left:135,right:20,top:8,bottom:20},xAxis:{type:"value",...axis},yAxis:{type:"category",inverse:true,data:types.slice(0,7).map(x=>x.nome),...axis,axisLabel:{color:"#aeb4bd",fontSize:9,width:120,overflow:"truncate"}},series:[{type:"bar",data:types.slice(0,7).map(x=>x.total),barWidth:10,itemStyle:{borderRadius:6,color:(p:any)=>types[p.dataIndex]?.nome===typeFilter?"#ffcc29":"#d83135"}}]}),[types,typeFilter])
 const hourOption=useMemo(()=>({tooltip:{trigger:"axis"},grid:{left:35,right:12,top:16,bottom:28},xAxis:{type:"category",data:hours.map((_,i)=>String(i).padStart(2,"0")), ...axis},yAxis:{type:"value",...axis},series:[{type:"bar",data:hours,barWidth:"62%",itemStyle:{color:(p:any)=>p.dataIndex>=7&&p.dataIndex<=18?"#d83135":"#343a44",borderRadius:[3,3,0,0]}}]}),[hours])
 if(error)return <div className="errorBox">{error}</div>
 return <>
  <div className="pageHead"><div><div className="eyebrow">DASHBOARD / HOME</div><h1>Visão Geral</h1><p>Panorama consolidado de ocorrências e indicadores operacionais do MVP.</p></div><span className="badge">v0.3 · BI FUNCIONAL</span></div>
  <div className="filters"><span>FILTROS</span><select value={period} onChange={e=>setGlobalFilters({period:e.target.value})}>{periodOptions.map(option=><option key={option.key} value={option.key}>{option.label}</option>)}</select><select value={typeFilter} onChange={e=>setGlobalFilters({type:e.target.value})}><option value="">Todas as tipificações</option>{typeOptions.map(item=><option key={item} value={item}>{item}</option>)}</select><select className={municipality?"filterLimited":""} value={municipality} onChange={e=>setGlobalFilters({municipality:e.target.value})} title="Filtro aceito, mas ainda sem cruzamento na fonte histórica"><option value="">Todos os municípios</option>{municipalityOptions.map(item=><option key={item} value={item}>{item}</option>)}</select><select className={unit?"filterLimited":""} value={unit} onChange={e=>setGlobalFilters({unit:e.target.value})} title="Filtro aceito, mas ainda sem cruzamento na fonte histórica"><option value="">Todas as unidades</option>{unitOptions.map(item=><option key={item} value={item}>{item}</option>)}</select><select disabled title="A fonte atual não possui subtipo agregado"><option>Todos os subtipos</option></select><select className={shift?"filterLimited":""} value={shift} onChange={e=>setGlobalFilters({shift:e.target.value})} title="Filtro aceito, mas ainda sem cruzamento na fonte histórica"><option value="">Todos os turnos</option>{shiftOptions.map(item=><option key={item} value={item}>{item}</option>)}</select>{hasFilter&&<button className="clearFilters" onClick={clearGlobalFilters}>Limpar filtros</button>}</div>
  <div className="activeFilters">{!activeEntries.some(entry=>entry.key==="period")&&<i>Período: {currentPeriod}</i>}{activeEntries.map(entry=><button key={entry.key} className={entry.limited?"limited":""} title={`Remover filtro ${entry.label}`} aria-label={`Remover filtro ${entry.label}: ${entry.value}`} onClick={()=>removeFilter(entry.key)}>{entry.label}: {entry.value}<span aria-hidden="true">x</span></button>)}<i>Fonte: histórico consolidado</i>{hasComparison&&<i>Comparativo: 2025 x 2026</i>}{limited.length>0&&<i className="limited">Limitados: {limited.join(", ")}</i>}</div>
  {hasRequestedLimited&&<div className="filterWarning"><b>Filtros não aplicados</b><span>{unavailable.map(item=>`${filterLabels[item.field] || item.field}: ${item.value}`).join(" · ")}</span></div>}
  <div className="scopeNote"><b>Histórico consolidado</b> alimenta volume, evolução e tipificação filtráveis por período/tipo. <b>Território, hora e unidade</b> aguardam agregações cruzadas para refletir todos os filtros.</div>
  <div className="kpiGrid">
   <KpiCard label="Ocorrências" value={loading?"-":`${partialTypeSeries?">= ":""}${fmt(ov?.total||0)}`} meta={partialTypeSeries?"mínimo conhecido; série mensal parcial":typeFilter?"total do tipo no período":"total do período selecionado"} tone="red"/>
   <KpiCard label="Média diária" value={loading?"-":dec(ov?.average_per_day||0)} meta={partialTypeSeries?"calculada sobre mínimo conhecido":"calculada pela API com dias reais"}/>
   <KpiCard label="Variação" value={ov?.delta_pct==null?"sem base":`${ov.delta_pct>0?"+":""}${dec(ov.delta_pct)}%`} meta={hasComparison?"comparação com 2025 no período":"comparação indisponível para este recorte"} tone="gold"/>
   <KpiCard label="SLA demonstrativo" value={sla?`${dec(sla.compliance_pct)}%`:"-"} meta={sla?`${sla.computable}/${sla.sample_size} registros calculáveis`:"carregando"} tone="green"/>
   <KpiCard label="Maior demanda" value={ov?.top_type||"-"} meta={ov?.top_municipality||"carregando"} tone="neutral"/>
  </div>
  <div className="grid twoOne"><Panel title="Evolução das ocorrências" sub={partialTypeSeries?"Série parcial: meses ausentes sem valor conhecido":hasComparison?"Comparativo mensal 2025 x 2026":typeFilter?`Filtro API: ${typeFilter}`:"Filtro API: período"}><ReactECharts option={monthlyOption} onEvents={monthEvents} style={{height:285}}/></Panel><Panel title="Principais tipificações" sub="Clique em uma barra para filtrar"><ReactECharts option={typeOption} onEvents={typeEvents} style={{height:285}}/></Panel></div>
  <div className="grid twoOne"><Panel title="Concentração territorial" sub={hasRequestedLimited?"Seleção contextual; consolidado geral sem cruzamento":"Mapa consolidado por município"}><MapPanel cities={cities.slice(0,20)} selected={municipality} onSelect={city=>setGlobalFilters({municipality:city.nome})}/></Panel><Panel title="Ocorrências por hora" sub={hasRequestedLimited?"Consolidado geral: sem cruzamento disponível":"Perfil horário consolidado"}><ReactECharts option={hourOption} style={{height:330}}/></Panel></div>
  <div className="coveragePanel"><b>Cobertura v0.3</b><span>{ov?.coverage?.types || types.length} tipificações retornadas, {ov?.coverage?.municipalities || cities.length} municípios, {ov?.coverage?.units || units.length} unidades e {ov?.coverage?.hours || hours.length} faixas horárias disponíveis na API atual.{partialTypeSeries && ` Tipificação sem valor mensal disponível em: ${missingTypeMonths.join(", ")}.`}</span></div>
 </>
}
