# FOCO — Infraestrutura de Atualização por Releases

Este pacote adiciona um mecanismo de atualização do FOCO em `/opt/foco` sem depender do Git na VM.

## Conteúdo

```text
infraestrutura/atualizacao/
├── foco-atualizar.sh
├── instalar-atualizador.sh
├── foco-atualizador.conf.example
└── testar-atualizador.sh

infraestrutura/scripts/
└── preparar_release.sh

compose.producao.yml
.env.producao.example
frontend/Dockerfile.producao
frontend/nginx.conf

.github/workflows/
└── publicar_release.yml

documentacao/operacao/
└── ATUALIZACAO_RELEASES.md

VERSAO
```

## Instalar na VM

```bash
sudo cp -a infraestrutura/atualizacao /opt/foco/infraestrutura/
cd /opt/foco/infraestrutura/atualizacao
sudo ./instalar-atualizador.sh
```

Depois:

```bash
sudo foco-atualizar
```

## Importante

O repositório `Mathayuss/FOCO` ainda não possuía GitHub Releases publicadas quando este pacote foi criado.

Para o fluxo online funcionar, inclua o workflow `publicar_release.yml` no repositório e publique a próxima tag, por exemplo `v0.3.2`.

O pacote publicado é gerado com a configuração de produção, sem substituir o `docker-compose.yml` usado no desenvolvimento e sem incluir o `.env` local.
