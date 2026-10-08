import type { ReactNode } from "react"

export default function DashboardLoadState({loading,error,onRetry,children}:{loading:boolean;error:string;onRetry:()=>void;children:ReactNode}){
  return <div className="dashboardResults" aria-busy={loading}>
    {loading ? <div className="emptyState" role="status">Carregando dados...</div>
      : error ? <div className="errorBox" role="alert"><span>{error}</span><button className="dashboardRetry" type="button" onClick={onRetry}>Tentar novamente</button></div>
      : children}
  </div>
}
