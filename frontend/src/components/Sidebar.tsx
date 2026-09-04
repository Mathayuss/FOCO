import React from 'react'
const sections=[
 ['PRINCIPAL',['Visão Geral']],['ANÁLISE',['Evolução','Tipificação','Temporal','Território']],
 ['OPERAÇÃO',['SLA','Viaturas','Unidades']],['DADOS',['Importações','Integrações','Qualidade']],['SISTEMA',['Configurações']]
]
export default function Sidebar({active,setActive}:{active:string,setActive:(s:string)=>void}){
 return <aside className="sidebar"><div className="brand"><div className="brandIcon">F</div><div><strong>FOCO</strong><span>Inteligência Operacional</span></div></div><nav>{sections.map(([label,items])=><React.Fragment key={label as string}><div className="navLabel">{label}</div>{(items as string[]).map(item=><button key={item} className={active===item?'active':''} onClick={()=>setActive(item)}><i>◆</i>{item}</button>)}</React.Fragment>)}</nav><div className="sideFoot"><span className="liveDot"/> API preparada para integração</div></aside>
}
