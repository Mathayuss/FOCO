# FOCO — Correção proposta v0.3.1

Base analisada: branch `main` do repositório público Mathayuss/FOCO em 05/09/2026.

## Alterações incluídas

1. PostgreSQL comum substituído por PostgreSQL + PostGIS.
2. Banco padrão alterado para `foco_ocorrencias`.
3. Serviços Docker nomeados em português: `bd`, `servidor`, `interface`.
4. Credenciais do banco retiradas do `docker-compose.yml` e parametrizadas.
5. Versão FOCO centralizada em `VERSAO_FOCO`.
6. API deixa de possuir `0.2.0` fixo em dois pontos.
7. Limite de importação passa de 512 MB para 50 MB por padrão e fica configurável.
8. Frontend passa a usar pnpm de forma consistente no Docker.
9. Pacote frontend renomeado para `foco-interface` e versão alinhada.
10. Backend deixa de executar como root no container.
11. Alembic adicionado e estrutura inicial de migrations preparada.
12. GitHub Actions adicionado para testes do backend e build do frontend.

## Alterações deliberadamente NÃO incluídas

Para reduzir risco, esta correção não executa ainda:

- renomeação completa de `backend/`, `frontend/`, `models/`, `services/` etc.;
- migração das classes Python para nomes em português;
- mudança das rotas `/imports` para `/importacoes`;
- bloqueio da criação automática de unidades;
- refatoração das agregações SEJUSP para SQL;
- alteração do filtro mensal para intervalo completo de datas;
- remoção imediata de `create_all` e `garantir_colunas_incrementais`.

Esses pontos exigem uma segunda correção com execução integral da suíte de testes.

## Como aplicar

Faça uma branch:

```bash
git checkout -b correcao/v0.3.1-base
```

Copie os arquivos deste pacote sobre a raiz do repositório.

Depois aplique:

```bash
git apply ATUALIZAR_TESTE_VERSAO.patch
cp .env.example .env
```

Revise `BD_SENHA` no `.env`.

Valide:

```bash
docker compose config
docker compose up --build
```

Backend:

```bash
cd backend
pytest -q
```

Frontend:

```bash
cd frontend
corepack enable
pnpm install --frozen-lockfile
pnpm run build
```

## Observação

Como a revisão foi feita sobre os arquivos publicados no GitHub e o ambiente de execução
não conseguiu clonar o repositório completo, esta correção deve ser aplicada em uma branch
e validada pela suíte do projeto antes do merge.
