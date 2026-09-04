import React from 'react'
export default function KpiCard({label,value,meta,tone='cyan'}:{label:string,value:string,meta:string,tone?:string}){
 return <div className={`kpi ${tone}`}><div className="kpiGlow"/><div className="kpiLabel">{label}</div><div className="kpiValue">{value}</div><div className="kpiMeta">{meta}</div></div>
}
