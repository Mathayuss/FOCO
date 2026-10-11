#!/usr/bin/env bash
set -Eeuo pipefail

[[ "${EUID:-$(id -u)}" -eq 0 ]] || {
    echo "Execute como root: sudo ./instalar-atualizador.sh"
    exit 1
}

BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORIGEM="$BASE/foco-atualizar.sh"
DESTINO="/usr/local/sbin/foco-atualizar"
CONFIG="/etc/foco-atualizador.conf"

[[ -f "$ORIGEM" ]] || {
    echo "foco-atualizar.sh não encontrado em $BASE"
    exit 1
}

install -m 0755 "$ORIGEM" "$DESTINO"
mkdir -p /var/backups/foco /var/cache/foco-atualizador /var/log

if [[ ! -f "$CONFIG" ]]; then
    install -m 0600 "$BASE/foco-atualizador.conf.example" "$CONFIG"
    echo "Configuração criada: $CONFIG"
else
    echo "Configuração existente preservada: $CONFIG"
fi
chmod 0600 "$CONFIG"

ln -sf "$DESTINO" /usr/local/bin/foco-atualizar

echo
echo "FOCO Atualizador instalado."
echo
echo "Execute:"
echo "  sudo foco-atualizar"
echo
echo "Verificação rápida:"
echo "  sudo foco-atualizar --verificar"
