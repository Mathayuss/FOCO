import type { ReactNode } from "react"

export default function Panel({title,sub,children,className=""}:{title:string,sub?:string,children:ReactNode,className?:string}){
 return <section className={`panel ${className}`}><header><div><b>{title}</b>{sub&&<small>{sub}</small>}</div></header><div className="panelBody">{children}</div></section>
}
