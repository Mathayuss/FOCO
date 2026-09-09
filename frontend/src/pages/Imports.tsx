import React, { useEffect, useState } from "react"
import { api } from "../api"
import type { SetGlobalFilters } from "../filterState"
import type { CsvPreview, ImportBatch, ImportCommit } from "../types"

const pct=(part:number,total:number)=>total?`${Math.round(part/total*100)}%`:"0%"
const dateTime=(value:string|null)=>value?new Date(value).toLocaleString("pt-BR",{dateStyle:"short",timeStyle:"short"}):"-"
const MAX_IMPORT_UPLOAD_MB=512
const MAX_IMPORT_UPLOAD_BYTES=MAX_IMPORT_UPLOAD_MB*1024*1024
const SEJUSP_DASHBOARD_FILTERS = {source:"sejusp",period:"all",type:"",municipality:"",unit:"",subtype:"",shift:""}
const yearList=(years?:number[])=>years?.length?years.join(", "):"-"
const dashboardPeriod=(years?:number[])=>years?.length===1?`ano-${years[0]}`:"all"
const dashboardFilters=(years?:number[])=>({...SEJUSP_DASHBOARD_FILTERS,period:dashboardPeriod(years)})
const dashboardScope=(years?:number[])=>years?.length===1?`no ano ${years[0]}`:"no período importado"

type ImportsProps = {
 setGlobalFilters: SetGlobalFilters
 onShowDashboard: () => void
}

export default function Imports({setGlobalFilters,onShowDashboard}:ImportsProps){
 const [file,setFile]=useState<File|null>(null)
 const [preview,setPreview]=useState<CsvPreview|null>(null)
 const [loading,setLoading]=useState(false)
 const [committing,setCommitting]=useState(false)
 const [commit,setCommit]=useState<ImportCommit|null>(null)
 const [dashboardReady,setDashboardReady]=useState(false)
 const [batches,setBatches]=useState<ImportBatch[]>([])
 const [batchTotal,setBatchTotal]=useState(0)
 const [batchError,setBatchError]=useState("")
 const [error,setError]=useState("")

 async function loadBatches(){
  try{
   const result=await api.importBatches({limite:8})
   setBatches(result.items)
   setBatchTotal(result.total)
   setBatchError("")
  }catch(e){
   setBatchError(e instanceof Error ? e.message : "Falha ao carregar lotes")
  }
 }

 useEffect(()=>{loadBatches()},[])

 async function handleFile(next:File|null){
  setFile(next); setPreview(null); setCommit(null); setDashboardReady(false); setError("")
  if(!next) return
  if(next.size>MAX_IMPORT_UPLOAD_BYTES){
   setError(`Arquivo excede o limite de ${MAX_IMPORT_UPLOAD_MB} MB`)
   return
  }
  setLoading(true)
  try{ setPreview(await api.previewCsv(next)) }
  catch(e){ setError(e instanceof Error ? e.message : "Falha ao analisar arquivo") }
  finally{ setLoading(false) }
 }

 async function commitFile(){
  if(!file || !preview?.valid_rows) return
  setCommitting(true); setError("")
  try{
   const result = await api.commitImport(file)
   setCommit(result)
   await loadBatches()
   if(result.source_scope==="RELATORIO_SEJUSP" && (result.inserted_rows>0 || result.skipped_duplicate_rows>0)){
    setGlobalFilters(dashboardFilters(result.registration_years))
    setDashboardReady(true)
   }
  }
  catch(e){ setError(e instanceof Error ? e.message : "Falha ao importar arquivo") }
  finally{ setCommitting(false) }
 }

 function openSejuspDashboard(){
  setGlobalFilters(dashboardFilters(commit?.registration_years))
  onShowDashboard()
 }

 const status = preview?.can_commit ? "Pronto para validação final" : preview ? "Pendências encontradas" : loading ? "Analisando arquivo" : "Aguardando arquivo"
 return <>
  <div className="pageHead"><div><div className="eyebrow">DADOS / IMPORTAÇÕES</div><h1>Importações</h1><p>Pré-validação de arquivos CSV/XLS/XLSX antes de consolidar ocorrências operacionais.</p></div><span className={`badge ${preview?.can_commit?"ok":"warn"}`}>{status}</span></div>
  <div className="importGrid">
   <section className="uploadPanel">
    <label className={`dropZone ${loading?"loading":""}`}>
     <input type="file" accept=".csv,.xls,.xlsx,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={e=>handleFile(e.target.files?.[0]||null)}/>
     <span className="dropIcon">ARQ</span>
     <b>{file?.name || "Selecionar CSV/XLS/XLSX de ocorrências"}</b>
     <small>{file ? `${(file.size/1024).toFixed(1).replace(".",",")} KB` : `FOCO ou relatório SEJUSP · limite ${MAX_IMPORT_UPLOAD_MB} MB`}</small>
    </label>
    {error && <div className="errorBox">{error}</div>}
    <div className="importNote"><b>Escopo atual</b><span>Preview, equivalência de colunas, regras mínimas, duplicidade e insert das linhas válidas.</span></div>
    <button className="importAction" disabled={!file || !preview?.valid_rows || loading || committing} onClick={commitFile}>{committing?"Importando":"Importar linhas válidas"}</button>
    {commit && <div className="importResult"><b>Importação concluída</b><span>Lote #{commit.id_lote_importacao} · {commit.inserted_rows} inseridas · {commit.skipped_duplicate_rows} duplicadas · {commit.invalid_rows} inválidas</span>{dashboardReady && <><small>Fonte SEJUSP ativada {dashboardScope(commit.registration_years)}.</small><button type="button" onClick={openSejuspDashboard}>Abrir dashboard SEJUSP</button></>}</div>}
   </section>
   <section className="panel importPanel"><header><div><b>Resumo do arquivo</b><small>Retorno da API de importação</small></div></header><div className="panelBody importSummary">
    <div className="metricRow"><span>Linhas</span><b>{preview?.total_rows ?? "-"}</b></div>
    <div className="metricRow good"><span>Válidas</span><b>{preview ? `${preview.valid_rows} · ${pct(preview.valid_rows, preview.total_rows)}` : "-"}</b></div>
    <div className="metricRow bad"><span>Inválidas</span><b>{preview ? `${preview.invalid_rows} · ${pct(preview.invalid_rows, preview.total_rows)}` : "-"}</b></div>
    <div className="metricRow"><span>Colunas reconhecidas</span><b>{preview?.recognized_headers.length ?? "-"}</b></div>
    <div className="metricRow"><span>Perfil</span><b>{preview?.source_profile?.replace("RELATORIO_","") ?? "-"}</b></div>
    <div className="metricRow"><span>Ano do registro</span><b>{yearList(preview?.registration_years)}</b></div>
    <div className="metricRow"><span>Sigilo</span><b>{preview?.sensitive_rows ?? "-"}</b></div>
    <div className="metricRow"><span>Sem coordenada</span><b>{preview?.missing_coordinate_rows ?? "-"}</b></div>
   </div></section>
  </div>
  <section className="panel importHistory"><header><div><b>Lotes recentes</b><small>{batchTotal} importações registradas</small></div></header><div className="panelBody">
   {batchError ? <div className="errorBox">{batchError}</div> : <table className="dataTable"><thead><tr><th>Lote</th><th>Arquivo</th><th>Situação</th><th>Linhas</th><th>Início</th></tr></thead><tbody>{batches.length ? batches.map(item=><tr key={item.id_lote_importacao}><td>#{item.id_lote_importacao}</td><td title={item.nome_arquivo}>{item.nome_arquivo}</td><td>{item.situacao}</td><td>{item.linhas_inseridas}/{item.total_linhas}</td><td>{dateTime(item.iniciado_em)}</td></tr>) : <tr><td colSpan={5}>Nenhum lote registrado.</td></tr>}</tbody></table>}
  </div></section>
  <div className="grid twoOne">
   <section className="panel"><header><div><b>Colunas</b><small>Reconhecimento canônico</small></div></header><div className="panelBody columnAudit">
    <div><span>Reconhecidas</span><div className="chipList">{preview?.recognized_headers.length ? preview.recognized_headers.map(h=><i key={h}>{h}</i>) : <small>Nenhum arquivo analisado.</small>}</div></div>
    <div><span>Obrigatórias ausentes</span><div className="chipList missing">{preview?.missing_required_headers.length ? preview.missing_required_headers.map(h=><i key={h}>{h}</i>) : <small>Sem pendências de cabeçalho.</small>}</div></div>
    <div><span>Equivalências detectadas</span><div className="mappingList">{preview?.column_mappings?.length ? preview.column_mappings.filter(item=>item.target_field).map(item=><i key={`${item.source_header}-${item.target_field}`}><b>{item.source_header}</b><span>{item.target_field}</span></i>) : <small>Nenhum arquivo analisado.</small>}</div></div>
    {preview?.warnings?.length ? <div><span>Avisos</span><div className="chipList missing">{preview.warnings.map(item=><i key={item}>{item}</i>)}</div></div> : null}
   </div></section>
   <section className="panel"><header><div><b>Problemas por linha</b><small>Até 50 ocorrências retornadas</small></div></header><div className="panelBody issueList">
    {preview?.issues.length ? preview.issues.map(item=><div className="issueItem" key={item.row}><b>Linha {item.row}</b><span>{item.issues.join(", ")}</span></div>) : <div className="emptyState">{preview ? "Nenhum problema encontrado." : "Aguardando análise."}</div>}
   </div></section>
  </div>
 </>
}
