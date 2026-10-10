import { useEffect, useMemo, useState } from "react"
import { customPeriodKey, parseCustomPeriod } from "../filterState"
import type { PeriodOption } from "../types"
import FilterField from "./FilterField"

type PeriodFilterProps = {
  options:PeriodOption[]
  value:string
  onChange:(value:string)=>void
}

function latestYear(options:PeriodOption[]){
  const years=options.flatMap(option=>Array.from(option.key.matchAll(/\d{4}/g),match=>Number(match[0])))
  return years.length ? Math.max(...years) : new Date().getFullYear()
}

export default function PeriodFilter({options,value,onChange}:PeriodFilterProps){
  const selectedCustom=parseCustomPeriod(value)
  const suggestedYear=useMemo(()=>latestYear(options),[options])
  const [open,setOpen]=useState(Boolean(selectedCustom))
  const [start,setStart]=useState(selectedCustom?.start || `${suggestedYear}-01-01`)
  const [end,setEnd]=useState(selectedCustom?.end || `${suggestedYear}-12-31`)
  const valid=Boolean(start && end && start<=end)

  useEffect(()=>{
    const custom=parseCustomPeriod(value)
    if(!custom) return
    setStart(custom.start)
    setEnd(custom.end)
    setOpen(true)
  },[value])

  return <div className="periodControl">
    <FilterField label="Período rápido" className="periodQuick">
      <select aria-label="Período" value={value} onChange={event=>onChange(event.target.value)}>
        {options.map(option=><option key={option.key} value={option.key}>{option.label}</option>)}
      </select>
    </FilterField>
    <button type="button" className="periodToggle" aria-expanded={open} onClick={()=>setOpen(current=>!current)}>
      {open ? "Ocultar intervalo" : "Definir intervalo personalizado"}
    </button>
    {open&&<div className="periodRange" role="group" aria-label="Intervalo personalizado">
      <FilterField label="De"><input type="date" aria-label="Data inicial" value={start} onChange={event=>setStart(event.target.value)}/></FilterField>
      <FilterField label="Até"><input type="date" aria-label="Data final" value={end} onChange={event=>setEnd(event.target.value)}/></FilterField>
      <button type="button" className="applyPeriod" disabled={!valid} onClick={()=>valid&&onChange(customPeriodKey(start,end))}>Aplicar período</button>
      {!valid&&<small>Informe uma data final igual ou posterior à inicial.</small>}
    </div>}
  </div>
}
