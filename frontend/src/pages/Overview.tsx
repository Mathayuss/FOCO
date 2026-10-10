import React, { useMemo } from "react"
import ReactECharts from "echarts-for-react"
import { useDashboardSnapshot } from "../hooks/useDashboardSnapshot"
import DashboardLoadState from "../components/DashboardLoadState"
import { periodKeyForMonth, preserveFilterSelection, preservePeriodSelection, toAnalyticsParams, type GlobalFilters, type SetGlobalFilters } from "../filterState"
import KpiCard from "../components/KpiCard"
import Panel from "../components/Panel"
import MapPanel from "../components/MapPanel"
import FilterField from "../components/FilterField"
import PeriodFilter from "../components/PeriodFilter"

const fmt=(n:number)=>n.toLocaleString("pt-BR")
const dec=(n:number)=>n.toFixed(1).replace(".",",")
const axis={axisLine:{lineStyle:{color:"#3a4049"}},axisLabel:{color:"#c4c9d0",fontSize:11},splitLine:{lineStyle:{color:"#2b3037"}}}
const fallbackPeriods=[{key:"all",label:"Todo período importado",months:[]}]
const filterLabels:Record<string,string>={source:"Fonte",municipality:"Município",unit:"Unidade",subtype:"Subtipo",shift:"Turno",period:"Período",type:"Tipo"}

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

type OverviewProps={globalFilters:GlobalFilters;setGlobalFilters:SetGlobalFilters;clearGlobalFilters:()=>void}

export default function Overview({globalFilters,setGlobalFilters}:OverviewProps){
 const {source,period,type:typeFilter,municipality,unit,subtype,shift}=globalFilters
 const params=useMemo(()=>toAnalyticsParams(globalFilters),[source,period,typeFilter,municipality,unit,subtype,shift])
 const {filters,loading,error,data,retry}=useDashboardSnapshot(params)
 const ov=data?.overview || null
 const months=data?.monthly.items || [], comparison=data?.monthly.comparison || []
 const types=data?.types.items || [], cities=data?.cities.items || []
 const hours=data?.hours.items || [], units=data?.units.items || []
 const periodOptions=preservePeriodSelection(filters?.periods.length?filters.periods:fallbackPeriods,period)
 const typeOptions=preserveFilterSelection(filters?.types.length?filters.types:types.map(item=>item.nome),typeFilter)
 const municipalityOptions=preserveFilterSelection(filters?.municipalities || [],municipality)
 const unitOptions=preserveFilterSelection(filters?.units || [],unit)
 const shiftOptions=preserveFilterSelection(filters?.shifts || [],shift)
 const subtypeOptions=preserveFilterSelection(filters?.subtypes || [],subtype)
 const unavailable=ov?.unavailable_filters || []
 const isLimited=(key:string)=>Boolean((globalFilters as Record<string,string>)[key]) && Boolean(filters?.limited_dimensions?.includes(key))
 const hasRequestedLimited=unavailable.length>0
 const hasComparison=comparison.length>0
 const comparisonSummary=ov?.comparison
 const hasComparisonSummary=Boolean(comparisonSummary?.available)
 const isComparableSlice=Boolean(comparisonSummary?.available && comparisonSummary.current_total!==ov?.total)
 const comparisonDeltaTone=hasComparisonSummary && comparisonSummary?.delta_pct!=null ? ((comparisonSummary.delta_abs || 0)>=0?"up":"down") : "muted"
 const partialTypeSeries=Boolean(ov?.coverage?.partial_type_series)
 const missingTypeMonths=ov?.coverage?.missing_type_months || []
 const typeEvents={click:(p:any)=>{ if(p?.name) setGlobalFilters({type:toggleText(typeFilter,String(p.name))}) }}
 const monthEvents={click:(p:any)=>{ const key=periodKeyForMonth(String(p?.name || ""),periodOptions); if(key) setGlobalFilters({period:togglePeriod(period,key)}) }}
 const monthlyOption=useMemo(()=>{
  const selectedMonths=new Set((periodOptions.find(option=>option.key===period)?.months || []))
  const highlightPeriod=period!=="all"
  const series:any[]=[{name:comparisonSummary?.current_label || "SEJUSP",type:"line",data:months.map(x=>x.total),smooth:true,symbolSize:(_:unknown,p:any)=>highlightPeriod&&selectedMonths.has(months[p.dataIndex]?.mes)?10:7,lineStyle:{width:3,color:"#d83135"},itemStyle:{color:"#ffcc29"},areaStyle:{color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:"rgba(216,49,53,.32)"},{offset:1,color:"rgba(216,49,53,.02)"}]}}}]
  if(hasComparison) series.unshift({name:comparisonSummary?.baseline_label || "Período anterior",type:"line",data:comparison.map(x=>x.baseline),smooth:true,symbolSize:5,lineStyle:{width:2,color:"#58a6ff",type:"dashed"},itemStyle:{color:"#58a6ff"}})
  return {animation:false,tooltip:{trigger:"axis"},legend:{show:hasComparison,top:0,right:12,textStyle:{color:"#c4c9d0",fontSize:11}},grid:{left:42,right:14,top:hasComparison?38:22,bottom:32},xAxis:{type:"category",data:months.map(x=>x.mes),...axis},yAxis:{type:"value",...axis},series}
 },[months,comparison,hasComparison,period,periodOptions,comparisonSummary?.current_label,comparisonSummary?.baseline_label])
 const typeOption=useMemo(()=>({animation:false,tooltip:{trigger:"item"},grid:{left:145,right:20,top:8,bottom:24},xAxis:{type:"value",...axis},yAxis:{type:"category",inverse:true,data:types.slice(0,7).map(x=>x.nome),...axis,axisLabel:{color:"#c4c9d0",fontSize:11,width:128,overflow:"truncate"}},series:[{type:"bar",data:types.slice(0,7).map(x=>x.total),barWidth:12,itemStyle:{borderRadius:6,color:(p:any)=>types[p.dataIndex]?.nome===typeFilter?"#ffcc29":"#d83135"}}]}),[types,typeFilter])
 const hourEvents={click:(p:any)=>{ const index=Number(p?.dataIndex); if(source==="sejusp" && Number.isInteger(index)){ const next=shiftForHour(index); setGlobalFilters({shift:toggleText(shift,next)}) } }}
 const hourOption=useMemo(()=>({animation:false,tooltip:{trigger:"axis"},grid:{left:35,right:12,top:16,bottom:28},xAxis:{type:"category",data:hours.map((_,i)=>String(i).padStart(2,"0")), ...axis},yAxis:{type:"value",...axis},series:[{type:"bar",data:hours,barWidth:"62%",itemStyle:{color:(p:any)=>shift&&shiftForHour(p.dataIndex)===shift?"#ffcc29":p.dataIndex>=7&&p.dataIndex<=18?"#d83135":"#343a44",borderRadius:[3,3,0,0]}}]}),[hours,shift])
 return <>
  <div className="filters">
   <div className="filterHeading"><span>Filtros de análise</span><small><b>SEJUSP importado</b> · comparação com o mesmo período do ano anterior</small></div>
   <div className="filterFields">
    <PeriodFilter options={periodOptions} value={period} onChange={value=>setGlobalFilters({period:value})}/>
    <FilterField label="Tipificação"><select aria-label="Tipificação" value={typeFilter} onChange={e=>setGlobalFilters({type:e.target.value})}><option value="">Todas as tipificações</option>{typeOptions.map(item=><option key={item} value={item}>{item}</option>)}</select></FilterField>
    <FilterField label="Município"><select aria-label="Município" className={isLimited("municipality")?"filterLimited":""} value={municipality} onChange={e=>setGlobalFilters({municipality:e.target.value})}><option value="">Todos os municípios</option>{municipalityOptions.map(item=><option key={item} value={item}>{item}</option>)}</select></FilterField>
    <FilterField label="Unidade"><select aria-label="Unidade" className={isLimited("unit")?"filterLimited":""} value={unit} onChange={e=>setGlobalFilters({unit:e.target.value})}><option value="">Todas as unidades</option>{unitOptions.map(item=><option key={item} value={item}>{item}</option>)}</select></FilterField>
    <FilterField label="Subtipo"><select aria-label="Subtipo" className={isLimited("subtype")?"filterLimited":""} disabled={!subtypeOptions.length} value={subtype} onChange={e=>setGlobalFilters({subtype:e.target.value})}><option value="">Todos os subtipos</option>{subtypeOptions.map(item=><option key={item} value={item}>{item}</option>)}</select></FilterField>
    <FilterField label="Turno"><select aria-label="Turno" className={isLimited("shift")?"filterLimited":""} value={shift} onChange={e=>setGlobalFilters({shift:e.target.value})}><option value="">Todos os turnos</option>{shiftOptions.map(item=><option key={item} value={item}>{item}</option>)}</select></FilterField>
   </div>
  </div>
  {hasRequestedLimited&&<div className="filterWarning"><b>Filtros não aplicados</b><span>{unavailable.map(item=>`${filterLabels[item.field] || item.field}: ${item.value}`).join(" · ")}</span></div>}
  <DashboardLoadState loading={loading} error={error} onRetry={retry}>
  {comparisonSummary&&<div className="comparisonStrip"><div><span>{isComparableSlice?"Recorte comparável":"Recorte atual"}</span><b>{comparisonSummary.current_label}</b><strong>{fmt(comparisonSummary.current_total ?? ov?.total ?? 0)}</strong></div><div><span>Base comparada</span><b>{comparisonSummary.baseline_label || "sem base"}</b><strong>{comparisonSummary.baseline_total==null?"-":fmt(comparisonSummary.baseline_total)}</strong></div><div className={hasComparisonSummary?comparisonDeltaTone:"muted"}><span>Diferença</span><b>{comparisonSummary.delta_abs==null?"sem base":`${comparisonSummary.delta_abs>0?"+":""}${fmt(comparisonSummary.delta_abs)}`}</b><strong>{comparisonSummary.delta_pct==null?"-":`${comparisonSummary.delta_pct>0?"+":""}${dec(comparisonSummary.delta_pct)}%`}</strong></div>{(!comparisonSummary.available||Boolean(comparisonSummary.reason))&&<div className="reason"><span>Comparação</span><b>{comparisonSummary.reason || "sem base detalhada"}</b><strong>-</strong></div>}</div>}
  <div className="kpiGrid overviewKpis">
   <KpiCard label="Ocorrências" value={loading?"-":`${partialTypeSeries?">= ":""}${fmt(ov?.total||0)}`} meta={partialTypeSeries?"mínimo conhecido; série mensal parcial":typeFilter?"total do tipo no período":"total do período selecionado"} tone="red"/>
   <KpiCard label="Média diária" value={loading?"-":dec(ov?.average_per_day||0)} meta={partialTypeSeries?"calculada sobre mínimo conhecido":"calculada pela API com dias reais"}/>
   <KpiCard label="Maior demanda" value={ov?.total?ov.top_type||"-":"-"} meta={ov?.total?ov.top_municipality||"sem dados":"sem dados"} tone="neutral"/>
  </div>
  <div className="grid twoOne"><Panel title="Evolução das ocorrências" sub={partialTypeSeries?"Série parcial: meses ausentes sem valor conhecido":hasComparison?`${comparisonSummary?.current_label} comparado com ${comparisonSummary?.baseline_label}`:typeFilter?`Filtro API: ${typeFilter}`:"Filtro API: período"}><ReactECharts option={monthlyOption} onEvents={monthEvents} style={{height:285}}/></Panel><Panel title="Principais tipificações" sub="Clique em uma barra para filtrar"><ReactECharts option={typeOption} onEvents={typeEvents} style={{height:285}}/></Panel></div>
  <div className="grid twoOne"><Panel title="Concentração territorial" sub={source==="sejusp"?"Clique em um município para aplicar o filtro global":hasRequestedLimited?"Seleção contextual; consolidado geral sem cruzamento":"Mapa consolidado por município"}><MapPanel cities={cities.slice(0,20)} selected={municipality} onSelect={city=>setGlobalFilters({municipality:toggleText(municipality,city.nome)})} onClear={()=>setGlobalFilters({municipality:""})}/></Panel><Panel title="Ocorrências por hora" sub={source==="sejusp"?"Perfil horário do recorte filtrado":hasRequestedLimited?"Consolidado geral: sem cruzamento disponível":"Perfil horário consolidado"}><ReactECharts option={hourOption} onEvents={hourEvents} style={{height:330}}/></Panel></div>
  <div className="coveragePanel"><b>Cobertura v0.3</b><span>{ov?.coverage?.types ?? types.length} tipificações retornadas, {ov?.coverage?.municipalities ?? cities.length} municípios, {ov?.coverage?.units ?? units.length} unidades e {ov?.coverage?.hours ?? hours.filter(total=>total>0).length} faixas horárias disponíveis na API atual.{partialTypeSeries && ` Tipificação sem valor mensal disponível em: ${missingTypeMonths.join(", ")}.`}</span></div>
  </DashboardLoadState>
 </>
}
