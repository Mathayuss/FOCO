import { useEffect, useMemo } from "react"
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip, useMap } from "react-leaflet"
import type { NamedMetric } from "../types"

type MapPanelProps = {
 cities: NamedMetric[]
 selected?: string
 onSelect?: (city: NamedMetric) => void
 onClear?: () => void
}

function MapViewport({cities,selected}:{cities:NamedMetric[];selected:string}){
 const map=useMap()
 useEffect(()=>{
  const selectedCity=cities.find(city=>city.nome===selected)
  if(selectedCity){
   map.setView([selectedCity.lat!,selectedCity.lon!],9,{animate:false})
  }else if(cities.length===1){
   map.setView([cities[0].lat!,cities[0].lon!],8,{animate:false})
  }else if(cities.length>1){
   map.fitBounds(cities.map(city=>[city.lat!,city.lon!] as [number,number]),{padding:[28,28],maxZoom:8,animate:false})
  }
 },[cities,map,selected])
 return null
}

export default function MapPanel({cities,selected="",onSelect,onClear}:MapPanelProps){
 const mappedCities=useMemo(()=>cities.filter(city=>city.lat!=null&&city.lon!=null),[cities])
 const selectedCity=mappedCities.find(city=>city.nome===selected)
 return <div className="mapShell">
  <div className="mapToolbar"><span><b>{mappedCities.length}</b> municípios no mapa</span>{selectedCity&&onClear&&<button type="button" onClick={onClear} aria-label="Limpar município selecionado">Ver todos</button>}</div>
  <MapContainer center={[-20.5,-54.6]} zoom={6} scrollWheelZoom className="map">
   <MapViewport cities={mappedCities} selected={selected}/>
   <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
   {mappedCities.map(c=>{
   const active = c.nome === selected
   return <CircleMarker key={c.nome} center={[c.lat!,c.lon!]} radius={Math.max(active?9:6,Math.min(active?30:26,Math.sqrt(c.total)/5))} pathOptions={{color:active?"#ffcc29":"#d83135",fillColor:active?"#ffcc29":"#d83135",fillOpacity:active ? .76 : .58,weight:active?3:1}} eventHandlers={onSelect?{click:()=>onSelect(c)}:undefined}>
    <Tooltip sticky><b>{c.nome}</b><span>{c.total.toLocaleString("pt-BR")} ocorrências</span></Tooltip>
    <Popup><b>{c.nome}</b><br/>{c.total.toLocaleString("pt-BR")} ocorrências<br/><small>Clique no marcador para filtrar o dashboard.</small></Popup>
   </CircleMarker>
   })}
  </MapContainer>
 </div>
}
