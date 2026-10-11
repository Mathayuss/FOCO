# FOCO-081 - Credenciais de banco protegidas

## Problema

A instalação ativa ainda utilizava a senha distribuída como exemplo. Embora o PostgreSQL não estivesse publicado, a credencial conhecida ampliava o impacto de uma futura alteração de rede ou configuração.

## Solução

- rotação para segredo aleatório mantido somente no `.env` de produção;
- permissão `0600` preservada no arquivo;
- PostgreSQL e API recriados de forma controlada;
- rollback preparado durante a operação;
- validação preventiva de senhas padrão;
- comparação estrutural entre `DATABASE_URL` e configuração do PostgreSQL.

## Validações

- banco, API e interface saudáveis após a rotação;
- segredo consistente entre `.env` e contêineres, sem exibição do valor;
- nenhum backup temporário preservado;
- acesso web e health check respondendo `200`;
- 27 testes de infraestrutura aprovados;
- testes cobrem URL ausente, inválida, divergente e credenciais padrão.

## Resultado

A instalação não utiliza mais a credencial de exemplo, e futuras implantações são bloqueadas antes da inicialização quando mantiverem valores padrão ou inconsistentes.
