#!/usr/bin/env bash
set -Eeuo pipefail

VERSAO="${1:?Informe a versao sem o prefixo v}"
DESTINO="${2:?Informe o diretorio de destino}"
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

[[ "$VERSAO" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$ ]] || {
    printf 'Versao invalida: %s\n' "$VERSAO" >&2
    exit 1
}

for arquivo in compose.producao.yml .env.producao.example frontend/Dockerfile.producao frontend/nginx.conf infraestrutura/scripts/preparar_ambiente.py; do
    [[ -f "$RAIZ/$arquivo" ]] || {
        printf 'Artefato de producao ausente: %s\n' "$arquivo" >&2
        exit 1
    }
done

mkdir -p "$DESTINO"
DESTINO="$(cd "$DESTINO" && pwd)"
STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT

rsync -a \
    --exclude='.git/' \
    --exclude='.env' \
    --exclude='backend/.venv/' \
    --exclude='backend/foco.db' \
    --exclude='frontend/node_modules/' \
    --exclude='frontend/dist/' \
    --exclude='frontend/playwright-report/' \
    --exclude='frontend/test-results/' \
    --exclude='__pycache__/' \
    --exclude='.pytest_cache/' \
    "$RAIZ/" "$STAGING/"

cp "$STAGING/compose.producao.yml" "$STAGING/docker-compose.yml"
cp "$STAGING/frontend/Dockerfile.producao" "$STAGING/frontend/Dockerfile"
cp "$STAGING/.env.producao.example" "$STAGING/.env.example"
sed -i "s/^VERSAO_FOCO=.*/VERSAO_FOCO=$VERSAO/" "$STAGING/.env.example"
printf '%s\n' "$VERSAO" > "$STAGING/VERSAO"

ARQUIVO="FOCO-v${VERSAO}.tar.gz"
tar -C "$STAGING" -czf "$DESTINO/$ARQUIVO" .
(
    cd "$DESTINO"
    sha256sum "$ARQUIVO" > "$ARQUIVO.sha256"
)

printf '%s\n' "$DESTINO/$ARQUIVO"
