#!/usr/bin/env bash
set -Eeuo pipefail

BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ATUALIZADOR="$BASE/foco-atualizar.sh"
INSTALADOR="$BASE/instalar-atualizador.sh"

falhar() {
    printf 'FALHA: %s\n' "$*" >&2
    exit 1
}

bash -n "$ATUALIZADOR"
bash -n "$INSTALADOR"

grep -Fq 'DIRETORIO_FOCO="${FOCO_DIRETORIO:-/opt/foco}"' "$ATUALIZADOR" \
    || falhar "diretorio padrao deve ser /opt/foco"

bloco_restauracao="$(sed -n '/^[[:space:]]*5)/,/^[[:space:]]*;;/p' "$ATUALIZADOR")"
quantidade_restauracoes="$(grep -Fc 'restaurar_backup "$b"' <<< "$bloco_restauracao")"
[[ "$quantidade_restauracoes" -eq 1 ]] \
    || falhar "menu deve restaurar o backup exatamente uma vez"

grep -Eq 'install -m 0?600 .*foco-atualizador\.conf' "$INSTALADOR" \
    || falhar "configuracao deve ser instalada com permissao 0600"

printf 'Atualizador validado.\n'
