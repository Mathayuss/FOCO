import { useEffect, useRef } from "react"
import type { CsvPreview, ImportCommit } from "../types"

export type ImportProgressState = {
  operation:"preview"|"commit"
  phase:"upload"|"process"|"history"
  percent:number
}

export type ImportDialogError = {
  operation:"preview"|"commit"
  message:string
}

type StepState = "waiting"|"active"|"done"
type DialogTone = "processing"|"ready"|"success"|"duplicate"|"error"

type ImportProgressDialogProps = {
  file:File
  progress:ImportProgressState|null
  preview:CsvPreview|null
  result:ImportCommit|null
  error:ImportDialogError|null
  dashboardReady:boolean
  onCommit:()=>void
  onClose:()=>void
  onOpenDashboard:()=>void
}

function fileSize(bytes:number){
  if(bytes >= 1024*1024) return `${(bytes/(1024*1024)).toFixed(1).replace(".",",")} MB`
  return `${Math.max(0.1,bytes/1024).toFixed(1).replace(".",",")} KB`
}

function stepState(current:number,index:number):StepState{
  if(index < current) return "done"
  if(index === current) return "active"
  return "waiting"
}

function quantity(value:number,singular:string,plural:string){
  return `${value} ${value === 1 ? singular : plural}`
}

function ProcessingContent({state}:{state:ImportProgressState}){
  const isPreview=state.operation === "preview"
  const currentStep=state.phase === "upload" ? 0 : state.phase === "process" ? 1 : 2
  const title=state.phase === "upload" ? "Enviando arquivo" : state.phase === "history" ? "Finalizando importação" : isPreview ? "Analisando arquivo" : "Importando dados"
  const description=state.phase === "upload"
    ? "Transferindo o arquivo para o servidor com segurança."
    : state.phase === "history"
      ? "Atualizando o resultado e o histórico de lotes."
      : isPreview
        ? "Verificando colunas, linhas, datas, coordenadas e duplicidades."
        : "Validando novamente e consolidando as linhas aceitas no banco de dados."
  const steps=isPreview
    ? ["Envio seguro","Análise e validação"]
    : ["Envio seguro","Validação e consolidação","Atualização do histórico"]

  return <>
    <div className="importProgressSignal" aria-hidden="true"><span/></div>
    <div className="importProgressCopy" aria-live="polite">
      <h2 id="import-progress-title">{title}</h2>
      <p id="import-progress-description">{description}</p>
    </div>
    <div className={`importProgressTrack ${state.phase === "upload" ? "determinate" : "indeterminate"}`} role="progressbar" aria-label={state.phase === "upload" ? "Progresso do envio" : "Processamento no servidor"} aria-valuemin={state.phase === "upload" ? 0 : undefined} aria-valuemax={state.phase === "upload" ? 100 : undefined} aria-valuenow={state.phase === "upload" ? state.percent : undefined}>
      <span style={state.phase === "upload" ? {width:`${state.percent}%`} : undefined}/>
    </div>
    <div className={`importProgressSteps ${isPreview ? "two" : "three"}`}>
      {steps.map((step,index)=><div className={stepState(currentStep,index)} key={step}><i aria-hidden="true">{index < currentStep ? "✓" : index+1}</i><span>{step}</span></div>)}
    </div>
    <small>{isPreview ? "O arquivo ainda não está sendo gravado no banco de dados." : "Nenhuma linha será exibida no dashboard antes da conclusão."}</small>
  </>
}

export default function ImportProgressDialog({file,progress,preview,result,error,dashboardReady,onCommit,onClose,onOpenDashboard}:ImportProgressDialogProps){
  const dialogRef=useRef<HTMLElement>(null)
  const previewDuplicate=Boolean(preview?.can_commit && preview.new_rows === 0 && preview.existing_rows > 0)
  const resultDuplicate=Boolean(result && result.inserted_rows === 0 && result.skipped_duplicate_rows > 0)
  let tone:DialogTone="processing"
  let title="Processando arquivo"
  let description="Aguarde a conclusão da operação."
  let headerStatus=progress?.phase === "upload" ? `${progress.percent}% enviado` : "Em processamento"

  if(!progress && error){
    tone="error"
    title=error.operation === "preview" ? "Falha na análise" : "Falha na importação"
    description=error.message
    headerStatus="Erro"
  }else if(!progress && result){
    tone=resultDuplicate ? "duplicate" : "success"
    title=resultDuplicate ? "Nenhum dado novo" : result.invalid_rows || result.skipped_duplicate_rows ? "Importação concluída com ressalvas" : "Importação concluída"
    description=resultDuplicate
      ? `O lote #${result.id_lote_importacao} foi registrado com ${quantity(result.skipped_duplicate_rows,"duplicada","duplicadas")}; nenhuma ocorrência foi inserida novamente.`
      : `Lote #${result.id_lote_importacao}: ${quantity(result.inserted_rows,"inserida","inseridas")}, ${quantity(result.skipped_duplicate_rows,"duplicada","duplicadas")} e ${quantity(result.invalid_rows,"inválida","inválidas")}.`
    headerStatus=resultDuplicate ? "Duplicidade" : "Concluído"
  }else if(!progress && preview){
    tone=!preview.can_commit ? "error" : previewDuplicate ? "duplicate" : "ready"
    title=!preview.can_commit ? "Arquivo não pode ser importado" : previewDuplicate ? "Dados já importados" : "Arquivo pronto para importar"
    description=!preview.can_commit
      ? preview.validation_errors[0] || "A análise encontrou bloqueios que impedem a importação."
      : previewDuplicate
        ? `${quantity(preview.existing_rows,"ocorrência já existe","ocorrências já existem")} na base. A confirmação registrará somente o reprocessamento.`
        : `${quantity(preview.new_rows,"linha nova","linhas novas")} pronta para importação${preview.invalid_rows ? `; ${quantity(preview.invalid_rows,"linha inválida será ignorada","linhas inválidas serão ignoradas")}` : ""}.`
    headerStatus=!preview.can_commit ? "Bloqueado" : previewDuplicate ? "Duplicidade" : "Pronto"
  }

  useEffect(()=>{
    const previousOverflow=document.body.style.overflow
    document.body.style.overflow="hidden"
    dialogRef.current?.focus()
    return ()=>{ document.body.style.overflow=previousOverflow }
  },[])

  return <div className="importProgressOverlay">
    <section ref={dialogRef} className={`importProgressDialog ${tone}`} role="dialog" aria-modal="true" aria-labelledby="import-progress-title" aria-describedby="import-progress-description" tabIndex={-1}>
      <header>
        <span>IMPORTAÇÃO DE DADOS</span>
        <b><i aria-hidden="true"/> {headerStatus}</b>
      </header>
      <div className="importProgressBody">
        {progress ? <ProcessingContent state={progress}/> : <>
          <div className={`importOutcomeSignal ${tone}`} aria-hidden="true">{tone === "success" ? "OK" : tone === "duplicate" ? "=" : tone === "ready" ? "✓" : "!"}</div>
          <div className="importProgressCopy" aria-live="polite">
            <h2 id="import-progress-title">{title}</h2>
            <p id="import-progress-description">{description}</p>
          </div>
          {preview && !result && !error && <div className="importOutcomeStats">
            <div><span>Linhas</span><b>{preview.total_rows}</b></div>
            <div><span>Válidas</span><b>{preview.valid_rows}</b></div>
            <div><span>Novas</span><b>{preview.new_rows}</b></div>
            <div><span>Existentes</span><b>{preview.existing_rows}</b></div>
          </div>}
          {result && <div className="importOutcomeStats">
            <div><span>Linhas</span><b>{result.total_rows}</b></div>
            <div><span>Inseridas</span><b>{result.inserted_rows}</b></div>
            <div><span>Duplicadas</span><b>{result.skipped_duplicate_rows}</b></div>
            <div><span>Inválidas</span><b>{result.invalid_rows}</b></div>
          </div>}
        </>}
        <div className="importProgressFile">
          <div><span>Arquivo</span><b title={file.name}>{file.name}</b></div>
          <strong>{fileSize(file.size)}</strong>
        </div>
        {!progress && <div className="importDialogActions">
          <button type="button" className="secondary" onClick={onClose}>Fechar</button>
          {error?.operation === "commit" && preview?.can_commit && <button type="button" className="primary" onClick={onCommit}>Tentar novamente</button>}
          {!error && !result && preview?.can_commit && <button type="button" className="primary" onClick={onCommit}>{previewDuplicate?"Registrar reprocessamento":"Importar agora"}</button>}
          {result && dashboardReady && <button type="button" className="primary success" onClick={onOpenDashboard}>Abrir dashboard</button>}
        </div>}
      </div>
    </section>
  </div>
}
