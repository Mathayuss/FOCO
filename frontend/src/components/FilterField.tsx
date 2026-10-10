import type { ReactNode } from "react"

export default function FilterField({label,children,className=""}:{label:string;children:ReactNode;className?:string}){
  return <label className={`filterField ${className}`.trim()}>
    <span>{label}</span>
    {children}
  </label>
}
