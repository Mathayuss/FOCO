import React, { useEffect, useState } from "react"
import { api } from "../api"
import ImportProgressDialog, { type ImportDialogError, type ImportProgressState } from "../components/ImportProgressDialog"
import type { SetGlobalFilters } from "../filterState"
import type { CsvPreview, ImportBatch, ImportCommit } from "../types"

const pct=(part:number,total:number)=>total?`${Math.round(part/total*100)}%`:"0%"
const dateTime=(value:string|null)=>value?new Date(value).toLocaleString("pt-BR",{dateStyle:"short",timeStyle:"short"}):"-"
const limiteImportacaoConfigurado=Number(import.meta.env.VITE_LIMITE_IMPORTACAO_MB)
const limiteImportacaoMb=Number.isInteger(limiteImportacaoConfigurado) && limiteImportacaoConfigurado>0 ? limiteImportacaoConfigurado : 512
const limiteImportacaoBytes=limiteImportacaoMb*1024*1024
const SEJUSP_DASHBOARD_FILTERS = {source:"sejusp",period:"all",type:"",municipality:"",unit:"",subtype:"",shift:""}
const yearList=(years?:number[])=>years?.length?years.join(", "):"-"
const monthList=(periods?:string[]|null)=>periods===undefined?"-":periods===null?"Desconhecida":periods.length?periods.map(period=>{const [year,month]=period.split("-");return `${month}/${year}`}).join(", "):"Sem data de registro"
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
 const [progress,setProgress]=useState<ImportProgressState|null>(null)
 const [dialogError,setDialogError]=useState<ImportDialogError|null>(null)
 const [dialogOpen,setDialogOpen]=useState(false)

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
  setDialogError(null); setProgress(null); setDialogOpen(Boolean(next))
  if(!next) return
  if(next.size>limiteImportacaoBytes){
   const message=`Arquivo excede o limite de ${limiteImportacaoMb} MB`
   setError(message)
   setDialogError({operation:"preview",message})
   return
  }
  setLoading(true)
  setProgress({operation:"preview",phase:"upload",percent:0})
  try{
   setPreview(await api.previewCsv(next,percent=>setProgress({operation:"preview",phase:percent<100?"upload":"process",percent})))
  }
  catch(e){
   const message=e instanceof Error ? e.message : "Falha ao analisar arquivo"
   setError(message)
   setDialogError({operation:"preview",message})
  }
  finally{ setLoading(false); setProgress(null) }
 }

 async function commitFile(){
  if(!file || !preview?.can_commit) return
  setCommitting(true); setError(""); setCommit(null); setDialogError(null); setDialogOpen(true)
  setProgress({operation:"commit",phase:"upload",percent:0})
  try{
   const result = await api.commitImport(file,percent=>setProgress({operation:"commit",phase:percent<100?"upload":"process",percent}))
   setCommit(result)
   setProgress({operation:"commit",phase:"history",percent:100})
   await loadBatches()
   if(result.source_scope==="RELATORIO_SEJUSP" && (result.inserted_rows>0 || result.skipped_duplicate_rows>0)){
    setGlobalFilters(dashboardFilters(result.registration_years))
    setDashboardReady(true)
   }
  }
  catch(e){
   const message=e instanceof Error ? e.message : "Falha ao importar arquivo"
   setError(message)
   setDialogError({operation:"commit",message})
  }
  finally{ setCommitting(false); setProgress(null) }
 }

 function openSejuspDashboard(){
  setDialogOpen(false)
  setGlobalFilters(dashboardFilters(commit?.registration_years))
  onShowDashboard()
 }

 const status = preview?.can_commit ? (preview.already_imported ? "Arquivo já processado" : preview.new_rows===0 ? "Ocorrências já existentes" : preview.invalid_rows ? "Pronto com ressalvas" : "Pronto para importar") : preview ? "Importação bloqueada" : loading ? "Analisando arquivo" : "Aguardando arquivo"
 return <>
  {file && dialogOpen && <ImportProgressDialog file={file} progress={progress} preview={preview} result={commit} error={dialogError} dashboardReady={dashboardReady} onCommit={commitFile} onClose={()=>setDialogOpen(false)} onOpenDashboard={openSejuspDashboard}/>}
  <div className="pageHead"><div><div className="eyebrow">DADOS / IMPORTAÇÕES</div><h1>Importações</h1><p>Pré-validação de arquivos CSV/XLS/XLSX antes de consolidar ocorrências operacionais.</p></div><span className={`badge ${preview?.can_commit && !preview.already_imported && preview.new_rows>0?"ok":"warn"}`}>{status}</span></div>
  <div className="importGrid">
   <section className="uploadPanel">
    <label className={`dropZone ${loading?"loading":""}`} role="button" tabIndex={0} aria-label="Selecionar arquivo de ocorrências" onKeyDown={event=>{
     if(event.key!=="Enter" && event.key!==" ") return
     event.preventDefault()
     event.currentTarget.querySelector<HTMLInputElement>('input[type="file"]')?.click()
    }}>
     <input type="file" accept=".csv,.xls,.xlsx,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={e=>handleFile(e.target.files?.[0]||null)}/>
     <span className="dropIcon">ARQ</span>
     <b>{file?.name || "Selecionar CSV/XLS/XLSX de ocorrências"}</b>
    <small>{file ? `${(file.size/1024).toFixed(1).replace(".",",")} KB` : `FOCO ou relatório SEJUSP · limite ${limiteImportacaoMb} MB`}</small>
    </label>
    {error && <div className="errorBox">{error}</div>}
    <div className="importNote"><b>Escopo atual</b><span>Preview, equivalência de colunas, regras mínimas, duplicidade e insert das linhas válidas.</span></div>
    <button className="importAction" disabled={!file || !preview?.can_commit || loading || committing} onClick={commitFile}>{committing?"Importando":preview?.new_rows===0?"Registrar reprocessamento":"Importar linhas válidas"}</button>
    {commit && <div className="importResult"><b>Importação concluída</b><span>Lote #{commit.id_lote_importacao} · {commit.inserted_rows} inseridas · {commit.skipped_duplicate_rows} duplicadas · {commit.invalid_rows} inválidas</span><small>Cobertura por data de registro: {monthList(commit.registration_periods)}{commit.valid_rows_without_registration_date ? ` · ${commit.valid_rows_without_registration_date} linha(s) válida(s) sem data` : ""}.</small>{dashboardReady && <><small>Fonte SEJUSP ativada {dashboardScope(commit.registration_years)}.</small><button type="button" onClick={openSejuspDashboard}>Abrir dashboard SEJUSP</button></>}</div>}
   </section>
   <section className="panel importPanel"><header><div><b>Resumo do arquivo</b><small>Retorno da API de importação</small></div></header><div className="panelBody importSummary">
    <div className="metricRow"><span>Linhas</span><b>{preview?.total_rows ?? "-"}</b></div>
    <div className="metricRow good"><span>Válidas</span><b>{preview ? `${preview.valid_rows} · ${pct(preview.valid_rows, preview.total_rows)}` : "-"}</b></div>
    <div className="metricRow bad"><span>Inválidas</span><b>{preview ? `${preview.invalid_rows} · ${pct(preview.invalid_rows, preview.total_rows)}` : "-"}</b></div>
    <div className="metricRow good"><span>Novas</span><b>{preview?.new_rows ?? "-"}</b></div>
    <div className="metricRow"><span>Já existentes</span><b>{preview?.existing_rows ?? "-"}</b></div>
    <div className="metricRow"><span>Colunas reconhecidas</span><b>{preview?.recognized_headers.length ?? "-"}</b></div>
    <div className="metricRow"><span>Importação anterior</span><b>{preview?.already_imported ? `Lote #${preview.previous_import_batch_id}` : preview ? "Não encontrada" : "-"}</b></div>
    <div className="metricRow"><span>Perfil</span><b>{preview?.source_profile?.replace("RELATORIO_","") ?? "-"}</b></div>
    <div className="metricRow"><span>Ano do registro</span><b>{yearList(preview?.registration_years)}</b></div>
    <div className="metricRow"><span>Meses cobertos</span><b>{monthList(preview?.registration_periods)}</b></div>
    <div className="metricRow"><span>Válidas sem data de registro</span><b>{preview?.valid_rows_without_registration_date ?? "-"}</b></div>
    <div className="metricRow"><span>Sigilo</span><b>{preview?.sensitive_rows ?? "-"}</b></div>
    <div className="metricRow"><span>Sem coordenada</span><b>{preview?.missing_coordinate_rows ?? "-"}</b></div>
   </div></section>
  </div>
  <section className="panel importHistory"><header><div><b>Lotes recentes</b><small>{batchTotal} importações registradas</small></div></header><div className="panelBody">
   {batchError ? <div className="errorBox">{batchError}</div> : <table className="dataTable"><thead><tr><th>Lote</th><th>Arquivo</th><th>Situação</th><th>Cobertura</th><th>Linhas</th><th>Início</th></tr></thead><tbody>{batches.length ? batches.map(item=><tr key={item.id_lote_importacao}><td>#{item.id_lote_importacao}</td><td title={item.nome_arquivo}>{item.nome_arquivo}</td><td>{item.situacao}</td><td>{monthList(item.periodos_registro)}</td><td>{item.linhas_inseridas}/{item.total_linhas}</td><td>{dateTime(item.iniciado_em)}</td></tr>) : <tr><td colSpan={6}>Nenhum lote registrado.</td></tr>}</tbody></table>}
  </div></section>
  <div className="grid twoOne">
   <section className="panel"><header><div><b>Colunas</b><small>Reconhecimento canônico</small></div></header><div className="panelBody columnAudit">
    <div><span>Reconhecidas</span><div className="chipList">{preview?.recognized_headers.length ? preview.recognized_headers.map(h=><i key={h}>{h}</i>) : <small>Nenhum arquivo analisado.</small>}</div></div>
    {preview?.validation_errors?.length ? <div><span>Bloqueios da importação</span><div className="chipList missing">{preview.validation_errors.map(item=><i key={item}>{item}</i>)}</div></div> : null}
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
