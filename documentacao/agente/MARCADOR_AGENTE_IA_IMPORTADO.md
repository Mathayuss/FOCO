# FOCO — Marcador para Agentes de IA

## Marcador oficial

```text
[FOCO-PADRAO:v2]
```

## Regra

Ao encontrar esse marcador, o agente deve:

1. Ler `AGENTES.md`.
2. Ler os documentos aplicáveis em `documentacao/`.
3. Usar português em todos os nomes criados pela equipe.
4. Respeitar a identidade visual institucional.
5. Respeitar o roteiro de versões.
6. Não inventar áreas operacionais.
7. Usar áreas territoriais versionadas no banco.
8. Diferenciar dados reais, históricos agregados e demonstrativos.
9. Registrar decisões estruturais em `documentacao/adr/`.
10. Marcar dúvidas como `DECISAO_PENDENTE_HOMOLOGACAO`.

## Bloco curto

```text
[FOCO-PADRAO:v2]

Use português em toda nomenclatura criada pela equipe:
arquivos, pastas, tabelas, colunas, schemas, classes, funções,
serviços, rotas, documentação e mensagens.

Exceções somente para nomes exigidos por ferramentas, linguagens,
bibliotecas ou padrões externos.

Respeite ARQUITETURA.md, ROTEIRO_DE_VERSOES.md,
MODELO_DE_DADOS.md, SEGURANCA.md, EXPERIENCIA_INTERFACE.md,
IDENTIDADE_VISUAL.md, AREAS_OPERACIONAIS.md e as decisões arquiteturais.
```

## Regra MD33-M-02

Ao encontrar `[FOCO-PADRAO:v2]`, o agente também deve:

- consultar `PADRAO_DE_ABREVIACOES.md`;
- usar o `DICIONARIO_ABREVIACOES_FOCO.json`;
- não inventar abreviações;
- aplicar o padrão MD33-M-02 antes das convenções internas;
- adaptar abreviações ao `snake_case` somente no código/banco.
