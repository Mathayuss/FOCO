import React from 'react'
export default function Placeholder({name}:{name:string}){
 const notes:Record<string,string>={
  'SLA':'Próxima entrega: tempos de despacho, mobilização, deslocamento, atendimento, retorno, P50/P90/P95 e metas configuráveis.',
  'Viaturas':'Próxima entrega: ocorrência × VTR, tipo de VTR, tempo empenhado, utilização e disponibilidade.',
  'Importações':'Backend já possui preview CSV canônico. Próxima entrega: mapeamento visual de colunas, validação e commit.',
  'Território':'A Visão Geral já possui mapa por município. Próxima entrega: malhas PostGIS, heatmap e drill-down região/bairro.',
  'Qualidade':'Próxima entrega: completude, campos faltantes, SLA calculável, coordenadas e erros por fonte.'
 }
 return <div className="placeholder"><span>EM ESTRUTURAÇÃO</span><h1>{name}</h1><p>{notes[name]||'Módulo previsto no escopo do MVP. A navegação já está preparada para receber a implementação.'}</p><div className="placeholderCard"><b>Base arquitetural pronta</b><ul><li>API versionada</li><li>modelos de domínio separados</li><li>componentes React reutilizáveis</li><li>fonte histórica isolada de dados DEMO</li></ul></div></div>
}
