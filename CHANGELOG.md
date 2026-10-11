# Changelog

## v0.3.1 - 2026-09-17

### Releases reproduzíveis - FOCO-079 - 2026-10-10

- Compose, Dockerfile e Nginx de produção passam a ser versionados separadamente do ambiente de desenvolvimento.
- Pacotes de release usam API no mesmo domínio, banco sem porta pública e limite de importação de 512 MB em todas as camadas.
- Gerador único cria o pacote, grava a versão e produz o SHA-256 sem incluir o arquivo `.env`.
- Teste automatizado abre o pacote e valida configuração, checksum e ausência de segredos locais.
- Workflow de release passa a executar testes de infraestrutura, tipagem e Playwright antes da publicação.
- Atualizador usa `/opt/foco` por padrão e protege sua configuração com permissão `0600`.

### Credenciais de banco protegidas - FOCO-081 - 2026-10-11

- Senha padrão da instalação ativa foi substituída por segredo aleatório sem registro no Git ou nos logs.
- PostgreSQL, API e `.env` foram alinhados e validados após a rotação.
- Validador de infraestrutura passa a rejeitar senhas de exemplo antes da implantação.
- `DATABASE_URL` é analisada estruturalmente e deve corresponder a usuário, senha, host, porta e banco do PostgreSQL.
- Mensagens de validação não incluem a credencial recebida.
- CI utiliza credencial fictícia própria, sem aceitar os placeholders distribuídos nos arquivos de exemplo.

### BI

- Dashboard consolidado em `/api/v1/analytics/dashboard`, preservando os endpoints individuais.
- Mesma leitura de linhas SEJUSP para os paineis de uma requisicao, com validacao unica de filtros.
- Visao Geral e paineis analiticos usam a resposta consolidada.
- Cancelamento de carregamentos substituidos ao trocar filtros ou sair do painel.
- Seletor de tipificacao limitado a area disponivel para evitar overflow em notebook e mobile.

### Importação de planilhas - FOCO-051

- Limite padrão alinhado em 512 MB no backend, frontend, Docker e ambiente de exemplo.
- Backend impede valores acima de 512 MB e a CI valida que API e interface usam o mesmo limite.
- Upload com tamanho conhecido acima do limite é rejeitado antes da leitura em memória.
- Prévia e confirmação rodam no thread pool, com uma importação pesada por worker.
- CSV aceito em UTF-8 e Windows-1252; CSV malformado ou binário é rejeitado.
- XLS e XLSX corrompidos retornam erro de validação sem expor falha interna.
- XLS HTML híbrido com texto intercalado por bytes NUL é normalizado.
- A primeira linha reconhecida define as colunas; datas com hífen são aceitas.
- XLSX protegido por limite descompactado e taxa máxima de compactação.
- Cabeçalhos duplicados ou ambíguos são bloqueados antes da normalização.
- Datas, horários, comprimentos de campos, IBGE e faixas de coordenadas são validados.
- Pares de coordenadas incompletos ou inválidos não são persistidos parcialmente.
- Exportações com conteúdo equivalente também são verificadas por identificador de origem, informando linhas existentes e realmente novas.
- Número físico da planilha é preservado nas rejeições.
- Importação parcial exige ao menos uma linha válida e nenhum erro estrutural.
- Anos do lote consideram somente linhas válidas, priorizando a data de registro.
- Falhas inesperadas na confirmação executam rollback explícito.

### Leitura incremental de CSV - FOCO-052 - 2026-10-07

- Upload validado e resumido com SHA-256 em blocos de 1 MB sobre o arquivo temporário do multipart.
- Limite de 512 MB também é aplicado durante a leitura quando o tamanho não é informado pelo cliente.
- CSV processado por iterador, sem materializar uma segunda cópia integral do arquivo e das linhas de origem.
- Prévia não retém registros normalizados: conserva somente IDs válidos, anos, contadores e até 50 rejeições.
- Detecção incremental de UTF-8 ou Windows-1252 e rejeição de bytes NUL preservadas.
- Prévia e confirmação compartilham o mesmo parser, validações e regras de deduplicação.
- XLS e XLSX mantêm o caminho compatível existente; leitura incremental desses formatos permanece para v0.4.
- Testes garantem equivalência com o parser anterior e impedem leitura ilimitada no caminho CSV.
- Medição sintética com 20 mil linhas reduziu o pico rastreado do parser de 28,34 MiB para 3,67 MiB, cerca de 87%.
- Planilha operacional `relatorio(2).xls` validada somente em prévia: 413 linhas válidas, ano 2026 e nenhuma alteração no banco.

### Confirmação concorrente segura - FOCO-054 - 2026-10-07

- Confirmações usam advisory lock transacional e não bloqueante no PostgreSQL.
- Uma confirmação concorrente recebe `503` e `Retry-After: 2`, sem lote parcial ou erro interno.
- A constraint única de `sistema_origem + id_origem` permanece como proteção definitiva da integridade.
- SQLite mantém o fluxo existente, sem executar função específica do PostgreSQL.
- Teste operacional com duas sessões confirmou aquisição, rejeição imediata e liberação do lock.
- Suítes ampliadas para 90 testes aprovados no ambiente operacional e no PostGIS descartável.

### Reprocessamento sem unidades órfãs - FOCO-056 - 2026-10-07

- Unidades operacionais passam a ser criadas somente para ocorrências realmente novas.
- Reprocessamento com `id_origem` existente e unidade divergente não altera o cadastro de unidades.
- Lote de reprocessamento e contagem de linhas duplicadas permanecem preservados.
- Regressão reproduzida antes da correção e coberta pelo fluxo HTTP completo.
- Suítes ampliadas para 91 testes aprovados no ambiente operacional e no PostGIS descartável.

### Rastreabilidade dos valores importados - FOCO-058 - 2026-10-07

- Campos consolidados continuam normalizados para validação, deduplicação e análise.
- `dados_origem` passa a preservar espaços e valores textuais recebidos nas células CSV/XLSX.
- Cabeçalhos permanecem normalizados para manter equivalências e contratos existentes.
- Linhas vazias, separadores Markdown e colunas excedentes continuam avaliados sem considerar espaços decorativos.
- Regressão reproduzida antes da correção e coberta por confirmação, persistência e leitura do payload.
- Suítes ampliadas para 92 testes aprovados no ambiente operacional e no PostGIS descartável.

### Diagnóstico consistente de codificação - FOCO-060 - 2026-10-07

- CSV passa a ser validado integralmente como UTF-8 e Windows-1252 durante a leitura incremental.
- Bytes inválidos nas duas codificações são rejeitados antes da normalização ou persistência.
- Prévia e confirmação compartilham a mensagem `CSV deve estar em UTF-8 ou Windows-1252`.
- CSV válido em UTF-8 ou Windows-1252 continua aceito sem alteração no contrato de importação.
- Regressão reproduzida antes da correção e coberta nos dois endpoints de importação.
- Suítes ampliadas para 93 testes aprovados no ambiente operacional e no PostGIS descartável.

### Progresso visual da importação - FOCO-062 - 2026-10-07

- Prévia e confirmação exibem um diálogo modal durante todo o processamento.
- O envio apresenta percentual real calculado pelos eventos de upload do navegador.
- Após o envio, a interface diferencia análise, consolidação e atualização do histórico.
- Nome e tamanho do arquivo permanecem visíveis, sem expor o conteúdo importado.
- Fundo e rolagem ficam bloqueados para impedir ações concorrentes enquanto a operação está ativa.
- Diálogo acessível com estado anunciado, barra de progresso e foco inicial.
- Layout validado em 1920x1080, 1366x768 e 390x844, sem corte ou overflow.
- Suíte frontend ampliada para 108 testes aprovados, com build e tipagem aprovados.

### Comparação anual por meses equivalentes - FOCO-064 - 2026-10-07

- Períodos anuais passam a comparar os mesmos meses disponíveis no ano anterior.
- Meses sem base equivalente são excluídos somente do cálculo comparativo, não do total anual.
- Rótulos informam os intervalos efetivamente comparados e a limitação de cobertura.
- Visão Geral identifica o total reduzido como `Recorte comparável`.
- Meses, trimestres e períodos genéricos preservam a regra anterior.
- Base operacional validada em `Jan-Jun/2026 x Jan-Jun/2025`: 39.563 contra 38.520, variação de +2,7%.
- Suítes ampliadas para 94 testes backend em SQLite e PostGIS e 111 testes frontend.

### Confirmação e resultado no diálogo de importação - FOCO-066 - 2026-10-07

- O diálogo permanece aberto após a análise e oferece a ação explícita `Importar agora`.
- Arquivos já existentes oferecem `Registrar reprocessamento` sem sugerir nova inserção.
- A confirmação exibe no próprio diálogo os resultados de linhas inseridas, duplicadas e inválidas.
- Falhas de análise ou confirmação permanecem visíveis, com a mensagem retornada pela API.
- Importações SEJUSP concluídas oferecem acesso direto ao dashboard com o período importado.
- Estados de processamento não permitem fechar ou repetir a ação enquanto a requisição está ativa.
- Fluxo validado em desktop, notebook e celular; suíte frontend ampliada para 117 testes aprovados.

### Acessibilidade do fluxo de importação - FOCO-068 - 2026-10-09

- A área de seleção de planilha pode ser acionada por teclado com Enter ou Espaço.
- O seletor exibe foco visível e possui nome acessível específico.
- O foco permanece contido no diálogo enquanto ele está aberto.
- `Esc` fecha estados concluídos ou de erro, mas não interrompe processamento ativo.
- Ao fechar, o foco retorna ao elemento que iniciou o fluxo.
- Suíte frontend ampliada para 120 testes aprovados em desktop, notebook e celular.

### Filtros comparativos e mapa interativo - FOCO-070 - 2026-10-09

- Meses, trimestres, anos e intervalos personalizados são comparados com o mesmo recorte do ano anterior.
- O filtro aceita datas inicial e final e mantém o intervalo ativo ao navegar entre os painéis analíticos.
- Comparações anuais continuam limitadas aos meses com cobertura equivalente, sem alterar o total completo do ano selecionado.
- Rótulos de comparação exibem explicitamente os dois períodos utilizados no cálculo.
- Mapa territorial ajusta o enquadramento aos municípios disponíveis, exibe tooltip e permite aplicar ou limpar o filtro pelo marcador.
- Tipografia de filtros, indicadores, tabelas, navegação e painéis foi ampliada sem reduzir a densidade operacional.
- Base operacional validada em `2026 x 2025` e em `15/01/2026-10/02/2026 x 15/01/2025-10/02/2025`.
- Suítes finais: 97 testes backend em SQLite, 97 em PostgreSQL/PostGIS e 132 testes frontend nos três viewports.

### Interface operacional compacta - FOCO-072 - 2026-10-10

- Área superior da Visão Geral reorganizada a partir das capturas em `documentacao/imagens de apoio`.
- Barra fixa reduzida para 54 px e mantida somente para filtros ativos, saúde da API e ações globais.
- Título e descrição da Visão Geral movidos para a barra superior, eliminando o cabeçalho separado.
- Removidos resumo duplicado de filtros, breadcrumb decorativo, selo de versão, chips repetidos e faixa explicativa da fonte.
- Seletor de fonte de opção única removido; `SEJUSP importado` permanece identificado uma vez no painel de filtros.
- Filtros secundários usam duas colunas no celular, reduzindo a rolagem antes dos resultados.
- No celular, a barra mostra o título e oculta chips comprimidos; os valores ativos permanecem nos próprios controles.
- Cartões de variação e cobertura SLA removidos da Visão Geral: a variação já existe no comparativo e SLA pertence ao módulo próprio da v0.7.
- Ocorrências, média diária e maior demanda permanecem como indicadores principais da v0.3.
- Primeiro bloco de resultados antecipado em cerca de 130 px no desktop de referência.
- Suíte frontend ampliada para 135 testes aprovados em desktop, notebook e celular; build e tipagem aprovados.

### Ciclo de vida confiável do mapa - FOCO-074 - 2026-10-10

- Removida a animação de reenquadramento que podia continuar após a saída da tela de Território.
- Seleção municipal e ajuste aos limites passam a usar posicionamento imediato e determinístico.
- Navegação rápida do mapa para outro módulo não gera mais erro interno `_leaflet_pos`.
- Regressão cobre seleção, reenquadramento e desmontagem em desktop, notebook e celular.
- Suíte frontend ampliada para 138 testes aprovados; build e tipagem aprovados.

### Testes frontend - FOCO-041

- Suite Playwright integrada ao repositorio e ao workflow de CI existente.
- Comando `pnpm run test:frontend` valida os tipos e executa os testes.
- Dados ficticios restritos aos testes, chamadas API simuladas e servidor separado.
- Nomes acessiveis nos filtros, preservando a identidade visual.
- 33 testes aprovados em desktop, notebook e mobile, com checagem de pixels dos graficos.
- Clique na barra, cancelamento e resposta antiga sem cancelamento repetidos cinco vezes por resolucao: 45 aprovados adicionais.
- Relatorios, traces e screenshots de falha fora do Git e do contexto Docker; CI preserva os artefatos.
- Execucao remota do workflow nao verificada neste incremento.

### Desempenho do dashboard - FOCO-042

- Periodos, recortes e metadados reutilizados apenas durante cada requisicao.
- Serie mensal agrupada em uma passagem, preservando contratos e regras.
- Metadados independentes entre paineis e limpeza do contexto apos erros.
- Medidor somente leitura: `python -m scripts.medir_dashboard`.
- Base de 38.520 ocorrencias: mediana local do servico de 500,90 para 138,68 ms.
- Recorte de fevereiro/2025: 415,74 para 118,24 ms; hashes completos iguais nos dois recortes.
- Medicoes excluem rede, serializacao HTTP e renderizacao; nao substituem testes de carga.
- Quinze novos casos de dashboard e dois adicionais de chaves combinadas/vazias.

### Rede do banco - FOCO-044

- Ativado o bind do PostgreSQL em `127.0.0.1:5432`, antes apenas configurado.
- Recriado somente o container do banco, mantendo o volume e as credenciais existentes.
- Backup temporario privado gerado antes da alteracao; formato listado, sem restauracao sobre a base ativa.
- Preservadas 38.520 ocorrencias, 13 lotes, 50 unidades e revisao 20260914_0005.
- Verificador somente leitura para configuracao e portas do container, sem expor secrets.
- 18 testes de infraestrutura aprovados e integrados ao CI.
- CI tambem verifica o Compose versionado com ambiente de exemplo, sem iniciar containers; execucao remota nao verificada.
- API reconectada e saudavel; portas da interface e API mantidas.

### Carregamento confiavel - FOCO-045 - 2026-09-18

- Resultados antigos retirados imediatamente ao alterar filtros, antes da nova requisicao.
- Controle compartilhado de carregamento, cancelamento e rejeicao de respostas atrasadas.
- Cabecalho, filtros ativos e selecoes persistidas visiveis durante carga e falhas.
- Comando de nova tentativa conserva o recorte e recupera inclusive a primeira carga.
- Cobertura zero preservada; series horarias vazias nao sao contadas como 24 horas cobertas.
- Animacoes de entrada desativadas e teste de clique aguarda a pintura da barra selecionada.
- Suite ampliada: 72 testes frontend aprovados e 15 repeticoes adicionais do clique cruzado.
- Smoke somente leitura na aplicacao ativa aprovado em tres viewports; base preservada.
- Build e tipos aprovados; inspecao visual de capturas reais pendente de autorizacao.
- Registro completo em `documentacao/operacao/VALIDACAO_FOCO_045.md`; v0.3 ainda sem homologacao completa.

### Filtro mensal em bases esparsas - FOCO-046 - 2026-09-18

- Corrigido clique na serie mensal quando `all`, ano e trimestre contêm somente um mes.
- Chaves mensais `AAAA-MM` identificadas por regra compartilhada na Visao Geral e Evolucao.
- Clique novamente no mes restaura `all` sem apagar tipificacao ou outros filtros.
- Regressao reproduzida antes da correcao; 75 testes frontend e 15 repeticoes adicionais aprovados.
- Build TypeScript/Vite aprovado; sem alteracoes de API, banco ou indicadores.
- Relatorio em `documentacao/operacao/VALIDACAO_FOCO_046.md`; homologacao v0.3 ainda pendente.

### Analise temporal sem pico inventado - FOCO-047 - 2026-09-18

- Recortes com 24 contagens horarias zero mostram `sem dados`, nao pico `00h`.
- Horario de pico so recebe destaque quando ha contagem positiva.
- Regressao reproduzida antes da correcao; pico com dados preservado.
- Suite ampliada: 81 testes frontend aprovados nos tres viewports e build TypeScript/Vite aprovado.
- Sem alteracao de API, banco ou regras estatisticas; v0.3 segue sem homologacao completa.
- Detalhes em `documentacao/operacao/VALIDACAO_FOCO_047.md`.

### Filtros de tabela por teclado - FOCO-048 - 2026-09-19

- Tabelas de Tipificacao e Unidades ganharam acao nativa acessivel por teclado.
- Enter e Espaco aplicam o filtro; clique na linha continua funcionando sem dupla ativacao.
- Foco visivel, rotulo de Tipificacao especifico e nome longo sem overflow nos tres viewports.
- Regressao reproduzida antes da correcao; 93 testes frontend e build TypeScript/Vite aprovados.
- Sem alteracao de API, banco ou regra estatistica; v0.3 ainda nao homologada.
- Registro em `documentacao/operacao/VALIDACAO_FOCO_048.md`.

### Comparacao com base zero - FOCO-049 - 2026-09-19

- `0/0` deixou de ser apresentado como variacao percentual de `0,0%`.
- Base anterior existente com total zero agora retorna `delta_pct: null`, sem alterar diferenca absoluta ou serie mensal.
- Visao Geral e Evolucao mostram percentual indisponivel e identificam a base zerada; motivo completo na faixa comparativa.
- Regressao reproduzida antes da correcao na API e no frontend.
- 69 testes SQLite, 69 PostGIS, 96 frontend e build TypeScript/Vite aprovados.
- API operacional reiniciada isoladamente e saudavel; contagens e revisao Alembic preservadas.
- Relatorio em `documentacao/operacao/VALIDACAO_FOCO_049.md`; v0.3 ainda nao homologada.

### Maior demanda em recortes vazios - FOCO-050 - 2026-09-19

- Lideres de tipo e municipio derivados somente das metricas observadas, nao dos filtros selecionados.
- Visao Geral mostra ausencia de demanda quando o total do recorte e zero; filtros continuam visiveis.
- Regressao reproduzida antes da correcao na API e no navegador; controle com dados preservado.
- 70 testes SQLite, 70 PostGIS, 102 frontend e build TypeScript/Vite aprovados.
- Reiniciado somente o servidor da API; banco e contagens preservados.
- Registro em `documentacao/operacao/VALIDACAO_FOCO_050.md`; v0.3 ainda nao homologada.

### Confiabilidade e operacao

- Alembic como unico responsavel por criar e alterar o schema.
- Migrations antes do Uvicorn no container e validacao da revisao no startup da API.
- Reparacao idempotente da migration 0005 sem perda de colunas ou registros.
- Testes isolados em SQLite temporario e PostgreSQL/PostGIS descartavel, usando migrations reais.
- Healthcheck verifica a disponibilidade do banco.
- Politica de reinicio dos containers e unidade systemd para inicializacao automatica.
- Bancos locais, backups e arquivos de ambiente excluidos da imagem do backend.
- Limite de importacao configuravel e validado no backend e frontend.

### Validacao

- 68 testes aprovados em SQLite e 68 em PostgreSQL/PostGIS.
- Build TypeScript/Vite aprovado.
- Testes de equivalencia entre dashboard consolidado e endpoints individuais,
  base vazia, filtros invalidos e liberacao do snapshot apos erros.

Esta entrega nao declara a v0.3 homologada nem antecipa novos indicadores de SLA.
