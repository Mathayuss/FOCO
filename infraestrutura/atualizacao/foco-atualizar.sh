#!/usr/bin/env bash
set -Eeuo pipefail

# FOCO - Atualizador de Releases
# Não depende de git. Usa GitHub Releases via HTTPS ou pacote local/offline.
# Destino padrão: /opt/foco

VERSAO_ATUALIZADOR="0.1.0"

DIRETORIO_FOCO="${FOCO_DIRETORIO:-/opt/foco}"
DIRETORIO_BACKUP="${FOCO_BACKUP_DIR:-/var/backups/foco}"
DIRETORIO_CACHE="${FOCO_CACHE_DIR:-/var/cache/foco-atualizador}"
ARQUIVO_LOG="${FOCO_UPDATE_LOG:-/var/log/foco-atualizador.log}"
ARQUIVO_CONFIG="${FOCO_UPDATE_CONFIG:-/etc/foco-atualizador.conf}"
ARQUIVO_LOCK="${FOCO_UPDATE_LOCK:-/var/lock/foco-atualizador.lock}"

REPOSITORIO="${FOCO_REPOSITORIO:-Mathayuss/FOCO}"
API_RELEASE="${FOCO_RELEASE_API:-https://api.github.com/repos/${REPOSITORIO}/releases/latest}"
BASE_DOWNLOAD="${FOCO_RELEASE_DOWNLOAD_BASE:-https://github.com/${REPOSITORIO}/releases/download}"

URL_HEALTH_API="${FOCO_HEALTH_API:-http://127.0.0.1:8000/api/v1/health}"
URL_HEALTH_INTERFACE="${FOCO_HEALTH_INTERFACE:-http://127.0.0.1:5173/}"
TIMEOUT_HEALTH="${FOCO_HEALTH_TIMEOUT:-120}"

MODO_NAO_INTERATIVO=0
SEM_CONFIRMACAO=0
PERMITIR_DOWNGRADE=0
SEM_VALIDAR_SHA=0

if [[ -f "$ARQUIVO_CONFIG" ]]; then
    # shellcheck disable=SC1090
    source "$ARQUIVO_CONFIG"
fi

if [[ -t 1 ]]; then
    C_RESET=$'\033[0m'
    C_BOLD=$'\033[1m'
    C_RED=$'\033[31m'
    C_GREEN=$'\033[32m'
    C_YELLOW=$'\033[33m'
    C_BLUE=$'\033[34m'
    C_CYAN=$'\033[36m'
    C_GRAY=$'\033[90m'
else
    C_RESET=""
    C_BOLD=""
    C_RED=""
    C_GREEN=""
    C_YELLOW=""
    C_BLUE=""
    C_CYAN=""
    C_GRAY=""
fi

mkdir -p "$(dirname "$ARQUIVO_LOG")" "$DIRETORIO_CACHE" "$DIRETORIO_BACKUP" "$(dirname "$ARQUIVO_LOCK")"
touch "$ARQUIVO_LOG"

exec 9>"$ARQUIVO_LOCK"

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

log() {
    printf '%s %s\n' "$(timestamp)" "$*" >> "$ARQUIVO_LOG"
}

linha() {
    printf '%s\n' "────────────────────────────────────────────────────────────"
}

cabecalho() {
    clear 2>/dev/null || true
    printf '%s\n' "${C_RED}${C_BOLD}███████╗ ██████╗  ██████╗ ██████╗ ${C_RESET}"
    printf '%s\n' "${C_RED}${C_BOLD}██╔════╝██╔═══██╗██╔════╝██╔═══██╗${C_RESET}"
    printf '%s\n' "${C_RED}${C_BOLD}█████╗  ██║   ██║██║     ██║   ██║${C_RESET}"
    printf '%s\n' "${C_YELLOW}${C_BOLD}██╔══╝  ██║   ██║██║     ██║   ██║${C_RESET}"
    printf '%s\n' "${C_YELLOW}${C_BOLD}██║     ╚██████╔╝╚██████╗╚██████╔╝${C_RESET}"
    printf '%s\n' "${C_YELLOW}${C_BOLD}╚═╝      ╚═════╝  ╚═════╝ ╚═════╝ ${C_RESET}"
    printf '\n%s\n' "${C_BOLD}Central de Atualização de Releases${C_RESET}"
    printf '%s\n' "${C_GRAY}Atualizador v${VERSAO_ATUALIZADOR} · ${REPOSITORIO}${C_RESET}"
    linha
}

ok()   { printf '%s\n' "${C_GREEN}✔${C_RESET} $*"; log "OK: $*"; }
aviso(){ printf '%s\n' "${C_YELLOW}⚠${C_RESET} $*"; log "AVISO: $*"; }
erro() { printf '%s\n' "${C_RED}✖${C_RESET} $*" >&2; log "ERRO: $*"; }
info() { printf '%s\n' "${C_CYAN}●${C_RESET} $*"; log "INFO: $*"; }

etapa() {
    local atual="$1" total="$2"; shift 2
    printf '\n%s[%s/%s]%s %s\n' "$C_BLUE" "$atual" "$total" "$C_RESET" "$*"
    log "ETAPA ${atual}/${total}: $*"
}

falhar() {
    erro "$*"
    exit 1
}

exigir_root() {
    [[ "${EUID:-$(id -u)}" -eq 0 ]] || falhar "Execute como root: sudo foco-atualizar"
}

adquirir_lock() {
    flock -n 9 || falhar "Já existe outra atualização do FOCO em execução."
}

tem_comando() {
    command -v "$1" >/dev/null 2>&1
}

verificar_dependencias() {
    local faltando=()
    for cmd in curl tar sha256sum rsync docker sort awk sed grep flock; do
        tem_comando "$cmd" || faltando+=("$cmd")
    done
    if ((${#faltando[@]})); then
        falhar "Dependências ausentes: ${faltando[*]}. Em Debian/Ubuntu: apt install curl tar coreutils rsync util-linux"
    fi
    docker compose version >/dev/null 2>&1 || falhar "Docker Compose v2 não está disponível."
}

versao_local() {
    local v=""
    if [[ -f "$DIRETORIO_FOCO/VERSAO" ]]; then
        v="$(tr -d '[:space:]' < "$DIRETORIO_FOCO/VERSAO")"
    elif [[ -f "$DIRETORIO_FOCO/package.json" ]]; then
        v="$(sed -n 's/^[[:space:]]*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$DIRETORIO_FOCO/package.json" | head -n1)"
    elif [[ -f "$DIRETORIO_FOCO/.env" ]]; then
        v="$(sed -n 's/^[[:space:]]*VERSAO_FOCO[[:space:]]*=[[:space:]]*//p' "$DIRETORIO_FOCO/.env" | tail -n1 | tr -d '"'\''[:space:]')"
    fi
    printf '%s' "${v:-desconhecida}"
}

normalizar_versao() {
    printf '%s' "${1#v}"
}

versao_maior() {
    local a b maior
    a="$(normalizar_versao "$1")"
    b="$(normalizar_versao "$2")"
    [[ "$a" != "$b" ]] || return 1
    maior="$(printf '%s\n%s\n' "$a" "$b" | sort -V | tail -n1)"
    [[ "$maior" == "$a" ]]
}

cabecalho_auth_curl() {
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        printf '%s\n' "-H" "Authorization: Bearer ${GITHUB_TOKEN}"
    fi
}

obter_release_mais_recente() {
    local resposta tag
    local -a auth=()
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        auth=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
    fi

    if ! resposta="$(curl -fsSL --connect-timeout 8 --max-time 30 \
        -H "Accept: application/vnd.github+json" \
        -H "User-Agent: foco-atualizador/${VERSAO_ATUALIZADOR}" \
        "${auth[@]}" "$API_RELEASE" 2>/dev/null)"; then
        return 1
    fi

    tag="$(printf '%s\n' "$resposta" | sed -n 's/^[[:space:]]*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)"
    [[ -n "$tag" ]] || return 1
    printf '%s' "$tag"
}

nome_pacote_tag() {
    printf 'FOCO-%s.tar.gz' "$1"
}

nome_sha_tag() {
    printf 'FOCO-%s.tar.gz.sha256' "$1"
}

url_pacote_tag() {
    local tag="$1"
    printf '%s/%s/%s' "$BASE_DOWNLOAD" "$tag" "$(nome_pacote_tag "$tag")"
}

url_sha_tag() {
    local tag="$1"
    printf '%s/%s/%s' "$BASE_DOWNLOAD" "$tag" "$(nome_sha_tag "$tag")"
}

confirmar() {
    local pergunta="${1:-Continuar?}"
    if ((SEM_CONFIRMACAO)); then
        return 0
    fi
    local resposta
    printf '%s [s/N]: ' "$pergunta"
    read -r resposta
    [[ "$resposta" =~ ^[SsYy]$ ]]
}

status_foco() {
    cabecalho
    printf '%-24s %s\n' "Diretório:" "$DIRETORIO_FOCO"
    printf '%-24s %s\n' "Versão instalada:" "$(versao_local)"
    printf '%-24s %s\n' "API de releases:" "$API_RELEASE"
    printf '%-24s %s\n' "Backups:" "$DIRETORIO_BACKUP"
    printf '%-24s %s\n' "Log:" "$ARQUIVO_LOG"
    linha

    if [[ -d "$DIRETORIO_FOCO" && -f "$DIRETORIO_FOCO/docker-compose.yml" ]]; then
        (cd "$DIRETORIO_FOCO" && docker compose ps) || true
    else
        aviso "Instalação do FOCO não encontrada em $DIRETORIO_FOCO."
    fi
}

verificar_atualizacao() {
    cabecalho
    local localv latest latestv
    localv="$(versao_local)"
    info "Versão instalada: ${localv}"
    info "Consultando GitHub Releases via HTTPS..."

    if ! latest="$(obter_release_mais_recente)"; then
        aviso "Nenhuma release publicada foi encontrada ou a página está inacessível."
        printf '\nPágina esperada:\n  https://github.com/%s/releases\n' "$REPOSITORIO"
        printf '\nO modo offline continua disponível com:\n  foco-atualizar --arquivo /caminho/FOCO-vX.Y.Z.tar.gz\n'
        return 2
    fi

    latestv="$(normalizar_versao "$latest")"
    ok "Release mais recente: $latest"

    if [[ "$localv" == "desconhecida" ]]; then
        aviso "Não foi possível determinar a versão instalada."
        return 3
    fi

    if versao_maior "$latestv" "$localv"; then
        printf '\n%sAtualização disponível:%s %s → %s\n' "$C_YELLOW" "$C_RESET" "$localv" "$latestv"
        return 10
    elif [[ "$(normalizar_versao "$localv")" == "$latestv" ]]; then
        ok "O FOCO já está atualizado."
        return 0
    else
        aviso "A versão instalada (${localv}) é superior à release publicada (${latestv})."
        return 0
    fi
}

validar_tar_seguro() {
    local pacote="$1"
    local item
    while IFS= read -r item; do
        case "$item" in
            /*|../*|*/../*|*/..)
                falhar "Pacote rejeitado: caminho inseguro detectado: $item"
                ;;
        esac
    done < <(tar -tzf "$pacote")
}

verificar_sha() {
    local pacote="$1" arquivo_sha="${2:-}"
    if [[ -z "$arquivo_sha" || ! -f "$arquivo_sha" ]]; then
        if ((SEM_VALIDAR_SHA)); then
            aviso "Checksum SHA-256 não informado; validação ignorada por opção explícita."
            return 0
        fi
        falhar "Arquivo SHA-256 não encontrado. Informe --sha256 ARQUIVO ou use --sem-validar-sha conscientemente."
    fi

    local esperado obtido
    esperado="$(awk '{print $1}' "$arquivo_sha" | head -n1)"
    obtido="$(sha256sum "$pacote" | awk '{print $1}')"
    [[ "$esperado" == "$obtido" ]] || falhar "SHA-256 inválido. Esperado: $esperado; obtido: $obtido"
    ok "SHA-256 validado."
}

localizar_raiz_release() {
    local staging="$1"
    if [[ -f "$staging/docker-compose.yml" ]]; then
        printf '%s' "$staging"
        return
    fi

    local encontrado
    encontrado="$(find "$staging" -mindepth 2 -maxdepth 3 -type f -name docker-compose.yml -print -quit 2>/dev/null || true)"
    [[ -n "$encontrado" ]] || falhar "Pacote inválido: docker-compose.yml não encontrado."
    dirname "$encontrado"
}

validar_conteudo_release() {
    local raiz="$1"
    local obrigatorios=(
        "docker-compose.yml"
        "backend"
        "frontend"
    )
    local p
    for p in "${obrigatorios[@]}"; do
        [[ -e "$raiz/$p" ]] || falhar "Pacote inválido: item obrigatório ausente: $p"
    done
}

versao_pacote_extraido() {
    local raiz="$1" v=""
    if [[ -f "$raiz/VERSAO" ]]; then
        v="$(tr -d '[:space:]' < "$raiz/VERSAO")"
    elif [[ -f "$raiz/package.json" ]]; then
        v="$(sed -n 's/^[[:space:]]*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$raiz/package.json" | head -n1)"
    fi
    printf '%s' "${v:-desconhecida}"
}

esperar_health() {
    local url="$1" nome="$2" limite="${3:-$TIMEOUT_HEALTH}"
    local inicio agora
    inicio="$(date +%s)"
    while true; do
        if curl -fsS --max-time 5 "$url" >/dev/null 2>&1; then
            ok "$nome respondeu em $url"
            return 0
        fi
        agora="$(date +%s)"
        if (( agora - inicio >= limite )); then
            erro "$nome não respondeu após ${limite}s: $url"
            return 1
        fi
        printf '\r%sAguardando %-20s%s' "$C_GRAY" "$nome..." "$C_RESET"
        sleep 2
    done
}

criar_backup() {
    local identificador="$1"
    local destino="$DIRETORIO_BACKUP/$identificador"
    mkdir -p "$destino"

    etapa 1 8 "Criando backup do código e configuração"
    tar \
        --exclude='./.git' \
        --exclude='./frontend/node_modules' \
        --exclude='./backend/.venv' \
        --exclude='./__pycache__' \
        -czf "$destino/codigo.tar.gz" \
        -C "$DIRETORIO_FOCO" .

    if [[ -f "$DIRETORIO_FOCO/.env" ]]; then
        cp -a "$DIRETORIO_FOCO/.env" "$destino/.env"
        chmod 600 "$destino/.env" || true
    fi

    etapa 2 8 "Criando backup lógico do PostgreSQL"
    (
        cd "$DIRETORIO_FOCO"
        docker compose up -d bd >/dev/null
        local tentativas=0
        until docker compose exec -T bd sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; do
            sleep 2
            tentativas=$((tentativas + 1))
            ((tentativas < 30)) || exit 1
        done
        docker compose exec -T bd sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$destino/banco.dump"
    ) || falhar "Falha ao criar backup do PostgreSQL. Atualização cancelada."

    printf '%s\n' "$(versao_local)" > "$destino/VERSAO_ORIGEM"
    printf '%s' "$destino"
}

restaurar_backup() {
    local backup="$1"
    [[ -d "$backup" ]] || falhar "Backup inexistente: $backup"
    [[ -f "$backup/codigo.tar.gz" ]] || falhar "Backup de código ausente."

    aviso "Iniciando restauração de: $backup"
    (
        cd "$DIRETORIO_FOCO"
        docker compose stop servidor interface >/dev/null 2>&1 || true
    )

    local tmp
    tmp="$(mktemp -d /var/tmp/foco-restore.XXXXXX)"
    trap 'rm -rf "$tmp"' RETURN
    tar -xzf "$backup/codigo.tar.gz" -C "$tmp"

    rsync -a --delete \
        --exclude='.git/' \
        --exclude='.env' \
        --exclude='frontend/node_modules/' \
        --exclude='backend/.venv/' \
        "$tmp/" "$DIRETORIO_FOCO/"

    if [[ -f "$backup/.env" ]]; then
        cp -a "$backup/.env" "$DIRETORIO_FOCO/.env"
        chmod 600 "$DIRETORIO_FOCO/.env" || true
    fi

    if [[ -s "$backup/banco.dump" ]]; then
        (
            cd "$DIRETORIO_FOCO"
            docker compose up -d bd >/dev/null
            docker compose exec -T bd sh -c '
                dropdb -U "$POSTGRES_USER" --force --if-exists "$POSTGRES_DB"
                createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
            '
            docker compose exec -T bd sh -c \
                'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges' \
                < "$backup/banco.dump"
        ) || falhar "Falha ao restaurar o banco a partir do backup."
    fi

    (
        cd "$DIRETORIO_FOCO"
        docker compose build servidor interface
        docker compose up -d --wait --wait-timeout "$TIMEOUT_HEALTH"
    ) || falhar "Código restaurado, mas os serviços não subiram corretamente."

    esperar_health "$URL_HEALTH_API" "API FOCO" "$TIMEOUT_HEALTH" || true
    ok "Restauração concluída."
}

aplicar_release() {
    local pacote="$1"
    local arquivo_sha="${2:-}"
    local origem="${3:-local}"

    exigir_root
    adquirir_lock
    verificar_dependencias

    [[ -d "$DIRETORIO_FOCO" ]] || falhar "Diretório do FOCO não encontrado: $DIRETORIO_FOCO"
    [[ -f "$DIRETORIO_FOCO/docker-compose.yml" ]] || falhar "docker-compose.yml não encontrado em $DIRETORIO_FOCO"
    [[ -f "$pacote" ]] || falhar "Pacote não encontrado: $pacote"

    verificar_sha "$pacote" "$arquivo_sha"
    validar_tar_seguro "$pacote"

    local staging raiz_release v_local v_nova agora backup
    staging="$(mktemp -d /var/tmp/foco-release.XXXXXX)"
    trap 'rm -rf "$staging"' RETURN
    tar -xzf "$pacote" -C "$staging"
    raiz_release="$(localizar_raiz_release "$staging")"
    validar_conteudo_release "$raiz_release"

    v_local="$(versao_local)"
    v_nova="$(versao_pacote_extraido "$raiz_release")"

    cabecalho
    info "Origem: $origem"
    info "Versão atual: $v_local"
    info "Versão do pacote: $v_nova"
    info "Destino: $DIRETORIO_FOCO"

    if [[ "$v_nova" == "desconhecida" ]]; then
        falhar "O pacote não possui VERSAO nem versão identificável em package.json."
    fi

    if [[ "$v_local" != "desconhecida" ]]; then
        if [[ "$(normalizar_versao "$v_local")" == "$(normalizar_versao "$v_nova")" ]]; then
            aviso "A versão $v_nova já está instalada."
            confirmar "Deseja reinstalar mesmo assim?" || return 0
        elif versao_maior "$v_local" "$v_nova" && (( ! PERMITIR_DOWNGRADE )); then
            falhar "Downgrade bloqueado: instalado=$v_local pacote=$v_nova. Use --permitir-downgrade se for intencional."
        fi
    fi

    confirmar "Aplicar FOCO $v_nova em $DIRETORIO_FOCO?" || {
        aviso "Atualização cancelada pelo operador."
        return 0
    }

    agora="$(date '+%Y%m%d-%H%M%S')"
    backup="$(criar_backup "${agora}-v${v_local//[^0-9A-Za-z._-]/_}")"
    ok "Backup salvo em $backup"

    local falhou=0
    set +e

    etapa 3 8 "Parando API e interface"
    (cd "$DIRETORIO_FOCO" && docker compose stop servidor interface)
    [[ $? -eq 0 ]] || falhou=1

    if (( ! falhou )); then
        etapa 4 8 "Aplicando arquivos da release"
        rsync -a --delete \
            --exclude='.git/' \
            --exclude='.env' \
            --exclude='frontend/node_modules/' \
            --exclude='backend/.venv/' \
            --exclude='backend/foco.db' \
            "$raiz_release/" "$DIRETORIO_FOCO/"
        [[ $? -eq 0 ]] || falhou=1
    fi

    if (( ! falhou )); then
        etapa 5 8 "Validando configuração Docker"
        (cd "$DIRETORIO_FOCO" && docker compose config -q)
        [[ $? -eq 0 ]] || falhou=1
    fi

    if (( ! falhou )); then
        etapa 6 8 "Construindo imagens da nova versão"
        (cd "$DIRETORIO_FOCO" && docker compose build servidor interface)
        [[ $? -eq 0 ]] || falhou=1
    fi

    if (( ! falhou )); then
        etapa 7 8 "Aplicando migrações Alembic"
        (cd "$DIRETORIO_FOCO" && docker compose run --rm servidor python -m alembic upgrade head)
        [[ $? -eq 0 ]] || falhou=1
    fi

    if (( ! falhou )); then
        etapa 8 8 "Subindo serviços e validando saúde"
        (cd "$DIRETORIO_FOCO" && docker compose up -d --wait --wait-timeout "$TIMEOUT_HEALTH")
        [[ $? -eq 0 ]] || falhou=1
    fi

    if (( ! falhou )); then
        esperar_health "$URL_HEALTH_API" "API FOCO" "$TIMEOUT_HEALTH" || falhou=1
        esperar_health "$URL_HEALTH_INTERFACE" "Interface FOCO" "$TIMEOUT_HEALTH" || falhou=1
    fi

    set -e

    if (( falhou )); then
        erro "A atualização falhou. O backup anterior será restaurado."
        restaurar_backup "$backup"
        falhar "Release $v_nova não foi aplicada. O FOCO foi restaurado para o estado anterior."
    fi

    ok "FOCO atualizado com sucesso para v$v_nova."
    info "Backup de segurança preservado em: $backup"
}

baixar_e_atualizar() {
    exigir_root
    adquirir_lock
    verificar_dependencias

    local localv tag nova pacote sha urlp urls
    localv="$(versao_local)"

    cabecalho
    info "Versão instalada: $localv"
    info "Consultando release mais recente..."

    tag="$(obter_release_mais_recente)" || falhar "Nenhuma release disponível ou GitHub Releases inacessível."
    nova="$(normalizar_versao "$tag")"

    if [[ "$localv" != "desconhecida" ]] && [[ "$(normalizar_versao "$localv")" == "$nova" ]]; then
        ok "FOCO já está na release mais recente: $tag"
        return 0
    fi

    if [[ "$localv" != "desconhecida" ]] && ! versao_maior "$nova" "$localv"; then
        if (( ! PERMITIR_DOWNGRADE )); then
            aviso "Release disponível ($nova) não é superior à instalada ($localv). Nada a fazer."
            return 0
        fi
    fi

    pacote="$DIRETORIO_CACHE/$(nome_pacote_tag "$tag")"
    sha="$DIRETORIO_CACHE/$(nome_sha_tag "$tag")"
    urlp="$(url_pacote_tag "$tag")"
    urls="$(url_sha_tag "$tag")"

    info "Baixando: $urlp"
    curl -fL --retry 3 --connect-timeout 10 --max-time 900 \
        -H "User-Agent: foco-atualizador/${VERSAO_ATUALIZADOR}" \
        -o "$pacote.part" "$urlp"
    mv "$pacote.part" "$pacote"

    info "Baixando SHA-256"
    curl -fL --retry 3 --connect-timeout 10 --max-time 60 \
        -H "User-Agent: foco-atualizador/${VERSAO_ATUALIZADOR}" \
        -o "$sha.part" "$urls"
    mv "$sha.part" "$sha"

    # liberar lock desta função para aplicar_release adquiri-lo novamente
    flock -u 9
    aplicar_release "$pacote" "$sha" "GitHub Release $tag"
}

ultimo_backup() {
    find "$DIRETORIO_BACKUP" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' 2>/dev/null \
        | sort -nr | head -n1 | cut -d' ' -f2-
}

menu() {
    exigir_root
    verificar_dependencias

    while true; do
        cabecalho
        printf '%sVersão instalada:%s %s\n\n' "$C_BOLD" "$C_RESET" "$(versao_local)"
        printf '  %s1%s  Status da instalação\n' "$C_YELLOW" "$C_RESET"
        printf '  %s2%s  Verificar atualização online\n' "$C_YELLOW" "$C_RESET"
        printf '  %s3%s  Atualizar pela última release\n' "$C_YELLOW" "$C_RESET"
        printf '  %s4%s  Instalar pacote local / offline\n' "$C_YELLOW" "$C_RESET"
        printf '  %s5%s  Restaurar último backup\n' "$C_YELLOW" "$C_RESET"
        printf '  %s6%s  Exibir log do atualizador\n' "$C_YELLOW" "$C_RESET"
        printf '  %s0%s  Sair\n\n' "$C_YELLOW" "$C_RESET"
        read -r -p "Selecione uma opção: " opcao

        case "$opcao" in
            1)
                status_foco
                read -r -p "Pressione ENTER para continuar..." _
                ;;
            2)
                verificar_atualizacao || true
                read -r -p "Pressione ENTER para continuar..." _
                ;;
            3)
                baixar_e_atualizar || true
                read -r -p "Pressione ENTER para continuar..." _
                ;;
            4)
                local arq arqsha
                read -r -e -p "Caminho do pacote .tar.gz: " arq
                [[ -f "$arq" ]] || { aviso "Arquivo não encontrado."; sleep 2; continue; }
                if [[ -f "${arq}.sha256" ]]; then
                    arqsha="${arq}.sha256"
                    info "SHA-256 detectado automaticamente: $arqsha"
                else
                    read -r -e -p "Caminho do .sha256: " arqsha
                fi
                aplicar_release "$arq" "$arqsha" "pacote local/offline" || true
                read -r -p "Pressione ENTER para continuar..." _
                ;;
            5)
                local b
                b="$(ultimo_backup)"
                if [[ -z "$b" ]]; then
                    aviso "Nenhum backup encontrado."
                elif confirmar "Restaurar o backup $b?"; then
                    adquirir_lock
                    restaurar_backup "$b"
                fi
                read -r -p "Pressione ENTER para continuar..." _
                ;;
            6)
                ${PAGER:-less} +G "$ARQUIVO_LOG" 2>/dev/null || tail -n 100 "$ARQUIVO_LOG"
                ;;
            0) exit 0 ;;
            *) aviso "Opção inválida."; sleep 1 ;;
        esac
    done
}

ajuda() {
cat <<EOF
FOCO - Atualizador de Releases v${VERSAO_ATUALIZADOR}

Uso:
  foco-atualizar
  foco-atualizar --status
  foco-atualizar --verificar
  foco-atualizar --atualizar
  foco-atualizar --arquivo PACOTE.tar.gz --sha256 PACOTE.tar.gz.sha256
  foco-atualizar --restaurar-ultimo

Opções:
  --sem-confirmacao       modo não interativo
  --permitir-downgrade    autoriza instalação de versão inferior
  --sem-validar-sha       instala pacote local sem SHA-256 (não recomendado)
  --diretorio CAMINHO     substitui /opt/foco
  --ajuda

O atualizador NÃO usa git.

Online:
  consulta GitHub Releases e baixa o pacote por HTTPS.

Offline:
  copie o .tar.gz e o .sha256 para a VM via SCP, pendrive,
  compartilhamento SMB/NFS etc. e use --arquivo.

Configuração:
  ${ARQUIVO_CONFIG}

Log:
  ${ARQUIVO_LOG}
EOF
}

ACAO="menu"
PACOTE_LOCAL=""
SHA_LOCAL=""

while (($#)); do
    case "$1" in
        --status) ACAO="status"; MODO_NAO_INTERATIVO=1 ;;
        --verificar) ACAO="verificar"; MODO_NAO_INTERATIVO=1 ;;
        --atualizar) ACAO="atualizar"; MODO_NAO_INTERATIVO=1 ;;
        --arquivo)
            [[ $# -ge 2 ]] || falhar "--arquivo exige um caminho"
            ACAO="arquivo"; PACOTE_LOCAL="$2"; MODO_NAO_INTERATIVO=1; shift
            ;;
        --sha256)
            [[ $# -ge 2 ]] || falhar "--sha256 exige um caminho"
            SHA_LOCAL="$2"; shift
            ;;
        --restaurar-ultimo) ACAO="restaurar"; MODO_NAO_INTERATIVO=1 ;;
        --sem-confirmacao) SEM_CONFIRMACAO=1 ;;
        --permitir-downgrade) PERMITIR_DOWNGRADE=1 ;;
        --sem-validar-sha) SEM_VALIDAR_SHA=1 ;;
        --diretorio)
            [[ $# -ge 2 ]] || falhar "--diretorio exige um caminho"
            DIRETORIO_FOCO="$2"; shift
            ;;
        --ajuda|-h|--help) ajuda; exit 0 ;;
        *) falhar "Opção desconhecida: $1" ;;
    esac
    shift
done

case "$ACAO" in
    menu) menu ;;
    status)
        exigir_root
        adquirir_lock
        verificar_dependencias
        status_foco
        ;;
    verificar)
        exigir_root
        adquirir_lock
        verificar_dependencias
        verificar_atualizacao
        ;;
    atualizar)
        baixar_e_atualizar
        ;;
    arquivo)
        aplicar_release "$PACOTE_LOCAL" "$SHA_LOCAL" "pacote local/offline"
        ;;
    restaurar)
        exigir_root
        adquirir_lock
        verificar_dependencias
        b="$(ultimo_backup)"
        [[ -n "$b" ]] || falhar "Nenhum backup disponível."
        confirmar "Restaurar $b?" || exit 0
        restaurar_backup "$b"
        ;;
esac
