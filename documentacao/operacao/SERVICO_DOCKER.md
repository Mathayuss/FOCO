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
