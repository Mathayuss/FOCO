import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet"
import type { NamedMetric } from "../types"

type MapPanelProps = {
 cities: NamedMetric[]
 selected?: string
 onSelect?: (city: NamedMetric) => void
}

export default function MapPanel({cities,selected="",onSelect}:MapPanelProps){
 const selectedCity = cities.find(c=>c.nome===selected && c.lat!=null && c.lon!=null)
 const center:[number,number] = selectedCity ? [selectedCity.lat!, selectedCity.lon!] : [-20.5, -54.6]
 return <MapContainer key={selected || "all"} center={center} zoom={selectedCity?8:6} scrollWheelZoom={false} className="map">
  <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
  {cities.filter(c=>c.lat!=null&&c.lon!=null).map(c=>{
   const active = c.nome === selected
   return <CircleMarker key={c.nome} center={[c.lat!,c.lon!]} radius={Math.max(active?9:6,Math.min(active?30:26,Math.sqrt(c.total)/5))} pathOptions={{color:active?"#ffcc29":"#d83135",fillColor:active?"#ffcc29":"#d83135",fillOpacity:active ? .72 : .55,weight:active?3:1}} eventHandlers={onSelect?{click:()=>onSelect(c)}:undefined}><Popup><b>{c.nome}</b><br/>{c.total.toLocaleString("pt-BR")} ocorrências</Popup></CircleMarker>
  })}
 </MapContainer>
}
