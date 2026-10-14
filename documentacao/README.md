# Documentação do FOCO

Esta pasta `documentacao/` concentra a documentação técnica, normativa e operacional do FOCO. A raiz do projeto deve ficar reservada para arquivos de execução, configuração e orientação principal.

## Estrutura

- `adr/`: decisões arquiteturais e registros de decisão.
- `agente/`: instruções para agentes de IA e padrões de revisão.
- `arquitetura/`: arquitetura do sistema, API e contratos técnicos.
- `dados/`: modelo de dados, dicionários e referências de nomenclatura de dados.
- `operacao/`: inicializacao, migrations, testes isolados e registros de validacao.
- `produto/`: roadmap, áreas operacionais, nomenclatura e escopo funcional.
- `referencias/`: PDFs, manuais, portarias e materiais normativos de apoio.
- `seguranca/`: diretrizes de segurança e riscos técnicos.
- `ux-ui/`: identidade visual, experiência, interface e tokens de design.
- `importados/`: área reservada para materiais brutos ainda não classificados.

## Documentos Canônicos

- Arquitetura: `arquitetura/ARQUITETURA.md`
- API: `arquitetura/INTERFACE_API.md`
- Modelo de dados: `dados/MODELO_DE_DADOS.md`
- Roadmap: `produto/ROTEIRO_DE_VERSOES.md`
- Segurança: `seguranca/SEGURANCA.md`
- UX/UI: `ux-ui/EXPERIENCIA_INTERFACE.md`
- Identidade visual: `ux-ui/IDENTIDADE_VISUAL.md`
- Áreas operacionais: `produto/AREAS_OPERACIONAIS.md`
- Decisões arquiteturais: `adr/`

## Operacao

- [Servico Docker](operacao/SERVICO_DOCKER.md)
- [Inicializacao com migrations](operacao/INICIALIZACAO_MIGRACOES.md)
- [Testes isolados](operacao/TESTES_ISOLADOS.md)
- [Testes frontend](operacao/TESTES_FRONTEND.md)
- [Desempenho do dashboard](operacao/DESEMPENHO_DASHBOARD.md)
- [Validacao incremental v0.3.1](operacao/VALIDACAO_V0_3_1.md)
- [Carregamento confiavel dos dashboards - FOCO-045](operacao/VALIDACAO_FOCO_045.md)
- [Filtro mensal em bases esparsas - FOCO-046](operacao/VALIDACAO_FOCO_046.md)
- [Pico horario em recortes vazios - FOCO-047](operacao/VALIDACAO_FOCO_047.md)
- [Filtros de tabela por teclado - FOCO-048](operacao/VALIDACAO_FOCO_048.md)
- [Comparacao com base zero - FOCO-049](operacao/VALIDACAO_FOCO_049.md)
- [Maior demanda em recortes vazios - FOCO-050](operacao/VALIDACAO_FOCO_050.md)
- [Importacao confiavel de planilhas - FOCO-051](operacao/VALIDACAO_FOCO_051.md)
- [Leitura incremental de CSV - FOCO-052](operacao/VALIDACAO_FOCO_052.md)
- [Confirmacao concorrente segura - FOCO-054](operacao/VALIDACAO_FOCO_054.md)
- [Reprocessamento sem unidades orfas - FOCO-056](operacao/VALIDACAO_FOCO_056.md)
- [Rastreabilidade dos valores importados - FOCO-058](operacao/VALIDACAO_FOCO_058.md)
- [Diagnostico consistente de codificacao - FOCO-060](operacao/VALIDACAO_FOCO_060.md)
- [Progresso visual da importacao - FOCO-062](operacao/VALIDACAO_FOCO_062.md)
- [Comparacao anual por meses equivalentes - FOCO-064](operacao/VALIDACAO_FOCO_064.md)
- [Confirmacao e resultado no dialogo de importacao - FOCO-066](operacao/VALIDACAO_FOCO_066.md)
- [Acessibilidade do fluxo de importacao - FOCO-068](operacao/VALIDACAO_FOCO_068.md)
- [Filtros comparativos e mapa interativo - FOCO-070](operacao/VALIDACAO_FOCO_070.md)
- [Interface operacional compacta - FOCO-072](operacao/VALIDACAO_FOCO_072.md)
- [Ciclo de vida confiavel do mapa - FOCO-074](operacao/VALIDACAO_FOCO_074.md)
- [Releases reproduziveis - FOCO-079](operacao/VALIDACAO_FOCO_079.md)
- [Credenciais de banco protegidas - FOCO-081](operacao/VALIDACAO_FOCO_081.md)
- [Credencial exclusiva por instalacao - FOCO-082](operacao/VALIDACAO_FOCO_082.md)
- [Atualizacao por releases](operacao/ATUALIZACAO_RELEASES.md)

## Observação Sobre Arquivos Importados

Arquivos com sufixo `IMPORTADO` foram preservados porque vieram da raiz com nomes duplicados ou desalinhados em relação ao conteúdo. Eles devem ser revisados e consolidados antes de serem tratados como fonte normativa.
