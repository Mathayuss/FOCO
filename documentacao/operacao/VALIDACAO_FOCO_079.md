# FOCO-079 - Releases reproduzíveis

## Problema

O ambiente de desenvolvimento usava Vite e portas publicadas diretamente. Empacotar esses arquivos para produção retiraria o Nginx, voltaria a expor serviços e poderia reduzir o limite de importação.

## Solução

- configuração de produção mantida em arquivos próprios;
- pacote montado por um único script;
- `.env` local excluído;
- SHA-256 gerado junto ao artefato;
- atualização validada antes da publicação;
- suíte Playwright obrigatória no workflow de release.

## Validações

- 23 testes de infraestrutura aprovados;
- sintaxe dos scripts Bash aprovada;
- Compose de produção resolvido com limites de 512 MB;
- PostgreSQL sem porta publicada no host;
- imagem Nginx/React de produção construída com sucesso;
- pacote de teste aberto e inspecionado automaticamente;
- checksum recalculado e comparado;
- ausência de `.env` confirmada no pacote.

## Resultado

O desenvolvimento permanece inalterado e as futuras releases passam a transportar uma configuração de produção reproduzível e verificável.
