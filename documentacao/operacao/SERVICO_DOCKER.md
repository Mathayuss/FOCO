# Servico Docker do FOCO

O Docker e o servico `foco.service` devem estar habilitados no systemd.
O FOCO inicia depois do Docker e da rede, usando as imagens locais e o
Compose em `/home/administrador/foco` (caminho real, em minusculas).
Se o projeto mudar de pasta, ajuste o arquivo de servico antes de reinstalar.

## Instalacao no host

Execute como root, a partir da raiz do projeto:

```sh
install -m 0644 infraestrutura/systemd/foco.service /etc/systemd/system/foco.service
systemctl daemon-reload
systemctl enable --now docker.service
systemctl enable --now foco.service
```

## Operacao

```sh
systemctl status foco.service --no-pager
systemctl restart foco.service
systemctl stop foco.service
journalctl -u foco.service -b --no-pager
docker compose ps
```

`active (exited)` e o estado esperado: systemd executa o Compose e o Docker
mantem os containers em segundo plano. Os containers usam `unless-stopped`
para recuperar falhas e reinicios do daemon. O servico systemd executa
`compose up` a cada boot, inclusive depois de uma parada manual anterior.
Para impedir o proximo inicio automatico, use `systemctl disable --now foco.service`.

O comando de parada nao exclui containers nem volumes. O banco permanece
no volume `dados_postgis`; nao use `docker compose down -v` para reiniciar.

O boot nao recompila imagens. A atualizacao das imagens e uma operacao
separada: `docker compose build`, seguida de `systemctl restart foco.service`.


## Rede do banco - FOCO-044

O PostgreSQL publica a porta apenas em `127.0.0.1:5432`. API e banco continuam
se comunicando pela rede interna do Compose, usando `bd:5432`. As portas
8000 e 5173 da aplicacao nao foram restringidas por esse ajuste.

`BD_SENHA` e obrigatoria no ambiente. O Compose nao fornece senha padrao.
Nao versionar `.env` nem imprimir a configuracao resolvida: ela pode conter
credenciais. Mudar `BD_SENHA` em um volume ja inicializado nao altera sozinho
a senha armazenada no PostgreSQL; rotacao exige procedimento separado.

Verifique a configuracao e o container ativo:

```sh
python3 infraestrutura/scripts/verificar_banco_docker.py --verificar-execucao
ss -ltn '( sport = :5432 )'
```

Sem `--verificar-execucao`, o script valida somente a configuracao resolvida.
O verificador e somente leitura, retorna JSON com status e erros, e usa codigo
de saida 1 para exposicao externa, ausencia de senha, limites de importacao
divergentes ou acima de 512 MB, falha do Docker ou formato inesperado.
Aceita loopback IPv4/IPv6 ou ausencia de publicacao.
Nao exibe valores de ambiente nem a saida de erro do Compose.

Editar o YAML nao altera automaticamente o container existente. Para aplicar
o bind, planeje uma breve indisponibilidade do banco, gere backup privado
fora do container e confira seu volume antes da recriacao:

```sh
docker inspect --format '{{json .Mounts}}' foco-bd-1
docker compose config --quiet
docker compose up -d --no-deps --wait --wait-timeout 120 bd
python3 infraestrutura/scripts/verificar_banco_docker.py --verificar-execucao
curl --fail http://localhost:8000/api/v1/health
docker compose ps
```

O volume persistente deve continuar sendo o mesmo. Compare as contagens e
a revisao Alembic antes/depois, e confirme a reconexao da API. Nao use
`down -v`, nao reinicialize o volume nem restaure o backup sobre a base ativa
apenas para testar sua integridade. A listagem por `pg_restore --list` valida
o formato do arquivo, mas nao equivale a um ensaio completo de restauracao.

O backup deste incremento foi gerado com `pg_dump --format=custom`, listado
e copiado para diretorio privado no host antes da recriacao. Backups em
`/tmp` sao temporarios: nao substituem uma politica institucional de retencao,
criptografia e ensaios de restauracao.

## Testes da verificacao

A suite usa somente a biblioteca padrao Python, sem Docker ou dados reais:

```sh
python3 -m unittest discover -s infraestrutura/tests -v
```

O CI executa esses testes e valida o Compose versionado, sem iniciar containers,
usando uma copia do ambiente de exemplo. Essa copia e criada somente depois
dos testes/migrations do backend, para nao alterar sua conexao. O runner precisa
do plugin Docker Compose. Nao copie esse ambiente sobre o .env operacional.
A verificacao do container ativo deve ser feita no host de implantacao;
a checagem de CI nao comprova sua configuracao real.
Este script verifica a exposicao das portas e a presenca de senha configurada,
nao a sua complexidade, regras de firewall ou vulnerabilidades do Docker.
