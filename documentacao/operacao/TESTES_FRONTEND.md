# Testes de navegador do frontend

## Preparacao

Na raiz do projeto, usando Node 22 e pnpm 9.15.5:

```sh
COREPACK_ENABLE_PROJECT_SPEC=0 pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend exec playwright install --with-deps chromium
```

O segundo comando instala o navegador e, em Linux, suas bibliotecas de sistema.
Use `pnpm --dir frontend run test:install` quando as bibliotecas ja estiverem
disponiveis e precisar baixar apenas o Chromium.

## Execucao

```sh
pnpm run test:frontend
```

Esse comando valida os tipos dos testes e executa o Playwright. Nao e preciso
subir o backend, importar dados ou iniciar o Compose. Um Vite exclusivo e
iniciado em `http://127.0.0.1:4174` e encerrado ao terminar a suite.
O servidor operacional em 5173 nao e reiniciado nem reutilizado.

Se 4174 estiver ocupada, escolha outra porta:

```sh
FOCO_PORTA_TESTES=4175 pnpm run test:frontend
```

O teste recusa reutilizar um servidor ja aberto nessa porta, evitando validar
acidentalmente outra aplicacao. As resolucoes sao 1920x1080, 1366x768 e 390x844.

## Isolamento e dados

`frontend/tests/fixtures/dashboard.ts` contem somente respostas ficticias de
teste, identificadas como nao operacionais. Elas nao sao inseridas em banco,
disponibilizadas pelo backend nem importadas pelo codigo da aplicacao.

Todas as chamadas `/api/v1/` sao interceptadas no contexto do navegador.
A suite permite apenas health e dashboard GET simulados. Chamadas nao previstas
ou para outra origem sao bloqueadas; uma tentativa de acessar outra API faz o
teste falhar. Service workers ficam bloqueados e requisicoes externas do mapa
nao saem do contexto. Nao sao usados arquivos institucionais ou credenciais.

Estes testes verificam comportamento da interface contra respostas controladas,
nao a integracao real com FastAPI/PostGIS nem o carregamento de tiles externos.
A integracao dos indicadores continua coberta pela suite backend isolada.

## Cobertura funcional

- Carga consolidada e canvas com pixels renderizados.
- Seis filtros globais enviados, persistidos na navegacao e no reload.
- Limpeza global e remocao individual sem apagar outros filtros.
- Base comparada e variacao exibidas.
- Base vazia, falha de rede e recuperacao de filtro invalido persistido.
- Cancelamento de requisicao substituida e protecao contra resposta atrasada.
- Resposta antiga ignorada mesmo quando o transporte nao respeita o cancelamento.
- Clique real na barra para aplicar/remover a tipificacao como filtro cruzado.
- Tipificacoes extensas sem overflow horizontal.
- Carga inicial e troca de periodo sem indicadores, tabelas, mapas ou graficos antigos.
- Cabecalho e filtros visiveis durante carga, erro de rede e erro HTTP.
- Seis selecoes persistidas visiveis antes da chegada das opcoes da API.
- Cobertura zero preservada mesmo com serie contendo 24 posicoes vazias.
- Nova tentativa apos falha inicial ou filtrada, conservando o recorte solicitado.
- Clique mensal em base esparsa seleciona a chave do mes, nao `all`/ano/trimestre,
  persiste na navegacao e pode ser removido sem apagar a tipificacao.
- Recorte sem contagens horarias positivas nao mostra pico `00h`;
  recorte com dados mantem o horario e total observados.
- Tabelas de Tipificacao e Unidades aceitam Enter/Espaco para filtrar;
  clique na linha permanece e nome longo nao causa overflow.
- Comparacao com base anterior zero nao apresenta percentual valido nem
  confunde base zerada com base ausente nos paineis Visao Geral e Evolucao.
- Maior demanda fica vazia em recorte zero sem esconder tipo e municipio
  selecionados; recortes preenchidos mantem os lideres observados.
- Importacao exibe progresso modal durante previa e confirmacao, bloqueia a
  rolagem e permanece dentro da viewport em desktop, notebook e celular.
- Apos a previa, o dialogo permite confirmar a importacao e informa sucesso,
  duplicidade ou erro sem perder o contexto do arquivo analisado.
- O seletor de arquivo aceita teclado; o dialogo contem o foco, bloqueia `Esc`
  durante o processamento e permite fechamento seguro nos estados finais.
- Comparacao anual identifica o recorte de meses equivalentes quando os anos
  possuem coberturas diferentes, sem substituir o total anual completo.
- Mes, trimestre, ano e intervalo personalizado usam o mesmo periodo do ano
  anterior, com os dois recortes apresentados na interface.
- Mapa permite inspecionar, selecionar e limpar municipio; tooltip, ajuste de
  enquadramento e legibilidade sao verificados nos tres viewports.
- Area superior compacta nao repete fonte, filtros, versao ou contexto; os
  filtros ativos continuam acessiveis na barra fixa e removiveis individualmente.
- Visao Geral aparece na mesma barra do status da API e do usuario, sem manter
  um segundo cabecalho no conteudo.

Para repetir os casos de temporizacao:

```sh
pnpm --dir frontend run test --grep 'clique na barra|requisicao substituida|resposta antiga' --repeat-each 5
```

## Relatorios e CI

O relatorio HTML fica em `frontend/playwright-report/`. Falhas preservam traces
e screenshots em `frontend/test-results/`. Esses diretorios sao ignorados pelo
Git e ficam fora do contexto Docker. Para abrir o relatorio local:

```sh
pnpm --dir frontend exec playwright show-report
```

O workflow existente `.github/workflows/integracao_continua.yml` compila a
aplicacao, valida os tipos, instala Chromium e executa os testes. Relatorios
ficam no artefato `testes-interface`, com retencao de sete dias e permissoes
de repositorio apenas para leitura. A execucao remota depende da publicacao
dessas alteracoes; nao confundir os resultados locais com uma execucao de CI.

## Validacao local - 2026-09-17

FOCO v0.3 (pacote v0.3.1): 33 testes frontend aprovados, 0 falhos,
mais 45 execucoes aprovadas dos tres casos de temporizacao repetidos.
Tipos TypeScript e build com lockfile congelado aprovados. Nao foi medida
cobertura percentual e nao foi executado o workflow remoto. Isso nao
constitui homologacao completa da v0.3.

## Validacao local - FOCO-045 - 2026-09-18

Suite ampliada para 24 casos em tres resolucoes: 72 aprovados, 0 falhos.
Clique cruzado na barra repetido cinco vezes por resolucao: 15 aprovados
adicionais. Tipos e build TypeScript/Vite com lockfile congelado aprovados.
Esses resultados atualizam a suite; os numeros de 2026-09-17 acima sao historicos.

Smoke adicional somente leitura na aplicacao ativa: tres resolucoes aprovadas,
38.520 ocorrencias no total e 5.796 em fevereiro/2025, recorte mantido na
navegacao, carregamento sem resultados antigos, canvas nao vazio, sem overflow
horizontal e sem erros JavaScript observados. Nao substitui homologacao.
Capturas com dados reais nao foram examinadas; inspecao visual pendente de
autorizacao. Workflow remoto e cobertura percentual nao verificados.

O host desta verificacao usou Node 20.19.2 e pnpm 9.15.5; a preparacao
padrao e o workflow usam Node 22. Bibliotecas Chromium indisponiveis no host
foram extraidas apenas em `/tmp/foco-browser`, sem alterar o sistema. O comando
local incluiu o caminho dessas bibliotecas:

```sh
LD_LIBRARY_PATH=/tmp/foco-browser/bibliotecas/usr/lib/x86_64-linux-gnu COREPACK_ENABLE_PROJECT_SPEC=0 pnpm run test:frontend
```

Esse caminho e temporario e nao faz parte da instalacao padrao.
Consulte [Validacao FOCO-045](VALIDACAO_FOCO_045.md) para limites e backlog.

## Validacao local - FOCO-046 - 2026-09-18

Regressao de periodo esparso reproduzida antes da correcao no desktop:
clique em fevereiro deixou o periodo em `all` quando deveria selecionar
`2025-02`. A nova suite passou com 75 testes em tres resolucoes, 0 falhos.
O clique mensal foi repetido cinco vezes por resolucao: 15 aprovacoes
adicionais. Tipos e build TypeScript/Vite aprovados; backend, banco e
infraestrutura nao alterados nem reexecutados neste incremento. Nenhuma
execucao remota do CI ou medicao de cobertura percentual foi feita aqui.
Consulte [Validacao FOCO-046](VALIDACAO_FOCO_046.md).

## Validacao local - FOCO-047 - 2026-09-18

O teste de recorte sem horarios reproduziu a apresentacao incorreta de
`00h` antes da correcao. Um segundo teste preservou o pico real de `14h`
com 12 ocorrencias. Suite final: 81 testes aprovados, 0 falhos, em tres
resolucoes. Tipos e build TypeScript/Vite aprovados. Backend, banco e
infraestrutura nao foram alterados nem reexecutados neste incremento.
Consulte [Validacao FOCO-047](VALIDACAO_FOCO_047.md).

## Validacao local - FOCO-048 - 2026-09-19

Dois testes de filtro de tabela por teclado reproduziram a falha antes da
correcao. O clique na linha seguiu funcional e sem dupla ativacao. Suite
final: 93 aprovados, 0 falhos, nas tres resolucoes, com tipagem de testes.
Build TypeScript/Vite aprovado. Nome longo ficticio ficou dentro do viewport
em desktop, notebook e celular. Backend e infraestrutura nao reexecutados;
CI remoto e cobertura percentual nao verificados neste incremento.
Consulte [Validacao FOCO-048](VALIDACAO_FOCO_048.md).

## Validacao local - FOCO-049 - 2026-09-19

A regressao de base anterior zero falhou antes da correcao e passou depois.
Suite frontend final com tipos: 96 aprovados, 0 falhos, em tres resolucoes;
build TypeScript/Vite aprovado. O mesmo caso foi exercitado na API em bancos
isolados: 69 testes SQLite e 69 PostGIS aprovados. CI remoto e cobertura
percentual nao verificados. Consulte [Validacao FOCO-049](VALIDACAO_FOCO_049.md).

## Validacao local - FOCO-050 - 2026-09-19

Regressoes de maior demanda vazia falharam antes da correcao na API e no
navegador e passaram depois, preservando o recorte preenchido. Suite
frontend final com tipos: 102 aprovados, 0 falhos, em tres resolucoes;
build TypeScript/Vite aprovado. Backend isolado: 70 testes SQLite e
70 PostGIS aprovados. CI remoto e cobertura percentual nao verificados.
Consulte [Validacao FOCO-050](VALIDACAO_FOCO_050.md).

## Validacao local - FOCO-062 - 2026-10-07

O fluxo de importacao passou a usar eventos reais de upload e um dialogo modal
para envio, analise e consolidacao. Suite frontend final com tipos: 108
aprovados, 0 falhos, em 1920x1080, 1366x768 e 390x844. Build TypeScript/Vite
aprovado. Capturas temporarias foram inspecionadas em desktop e celular, sem
corte, overflow ou sobreposicao incoerente. Backend e banco nao foram alterados;
CI remoto e cobertura percentual nao verificados neste incremento.
Consulte [Validacao FOCO-062](VALIDACAO_FOCO_062.md).

## Validacao local - FOCO-064 - 2026-10-07

Comparacao anual com oito meses no ano atual e seis no anterior foi reproduzida
como indisponivel antes da correcao. Depois, a suite backend aprovou 94 testes
em SQLite e 94 no PostgreSQL/PostGIS descartavel. A suite frontend aprovou 111
testes nos tres viewports e o build TypeScript/Vite foi concluido. A base
operacional foi conferida no fuso `America/Campo_Grande`; CI remoto e cobertura
percentual nao foram verificados neste incremento.
Consulte [Validacao FOCO-064](VALIDACAO_FOCO_064.md).

## Validacao local - FOCO-066 - 2026-10-07

O dialogo de importacao passou a permanecer aberto entre a analise, a decisao
do usuario e o resultado final. Os casos de arquivo pronto, sucesso,
duplicidade total e erro da API foram cobertos em 1920x1080, 1366x768 e
390x844. Suite frontend final: 117 testes aprovados, 0 falhos; tipagem e build
TypeScript/Vite aprovados. Backend e banco nao foram alterados nem reexecutados
neste incremento. CI remoto e cobertura percentual nao foram verificados.
Consulte [Validacao FOCO-066](VALIDACAO_FOCO_066.md).

## Validacao local - FOCO-068 - 2026-10-09

O fluxo de importacao foi exercitado somente por teclado desde a selecao do
arquivo ate o dialogo de confirmacao. O foco permaneceu contido no modal, `Esc`
nao interrompeu a analise e fechou o estado pronto. Suite frontend final: 120
testes aprovados, 0 falhos, nos tres viewports; tipagem e build TypeScript/Vite
aprovados. Backend e banco nao foram alterados nem reexecutados. CI remoto e
cobertura percentual nao foram verificados.
Consulte [Validacao FOCO-068](VALIDACAO_FOCO_068.md).

## Validacao local - FOCO-070 - 2026-10-09

Regressoes demonstraram que mes e trimestre ainda usavam o periodo imediatamente
anterior e que intervalos de datas nao eram aceitos. A regra foi unificada para
o mesmo recorte do ano anterior. Suite final: 132 testes frontend aprovados,
0 falhos, em 1920x1080, 1366x768 e 390x844; tipagem e build TypeScript/Vite
aprovados. O backend aprovou 97 testes em SQLite e 97 em PostgreSQL/PostGIS.
A aplicacao operacional foi conferida em `2026 x 2025` e por intervalo exato.
CI remoto e cobertura percentual nao foram verificados.
Consulte [Validacao FOCO-070](VALIDACAO_FOCO_070.md).

## Validacao local - FOCO-072 - 2026-10-10

As capturas de apoio demonstraram excesso de altura e repeticao antes dos dados.
Testes reproduziram a presenca do resumo duplicado, chips locais, faixa da fonte,
breadcrumb e selo de versao. A versao final reduziu a barra fixa para 54 px e
antecipa o primeiro comparativo em cerca de 130 px no desktop de referencia.
Suite final: 135 testes aprovados, 0 falhos, em 1920x1080, 1366x768 e 390x844;
tipagem e build TypeScript/Vite aprovados. Backend e banco nao foram alterados.
Consulte [Validacao FOCO-072](VALIDACAO_FOCO_072.md).

## Referencias

- [Servidor de testes](https://playwright.dev/docs/test-webserver)
- [Mock de APIs](https://playwright.dev/docs/mock)
- [Integracao continua](https://playwright.dev/docs/ci-intro)
