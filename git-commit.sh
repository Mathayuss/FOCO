#!/bin/bash

set -e

echo "========================================"
echo "   GIT - COMMIT E PUSH AUTOMATICO"
echo "========================================"

# Verifica se está dentro de um repositório Git
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "[ERRO] Este diretório não é um repositório Git."
    exit 1
fi

# Branch atual
BRANCH=$(git branch --show-current)

if [ -z "$BRANCH" ]; then
    echo "[ERRO] Não foi possível identificar a branch atual."
    exit 1
fi

echo "Branch atual: $BRANCH"
echo

# Mensagem do commit
if [ -n "$1" ]; then
    MENSAGEM="$*"
else
    read -p "Digite a mensagem do commit: " MENSAGEM
fi

if [ -z "$MENSAGEM" ]; then
    echo "[ERRO] A mensagem do commit não pode estar vazia."
    exit 1
fi

echo
echo "Arquivos alterados:"
git status --short
echo

# Adiciona todas as alterações
git add -A

# Verifica se existe algo para commitar
if git diff --cached --quiet; then
    echo "[INFO] Não existem alterações para commit."
    exit 0
fi

echo
echo "[1/3] Criando commit..."

git commit -m "$MENSAGEM"

echo
echo "[2/3] Sincronizando com origin/$BRANCH..."

git pull --rebase origin "$BRANCH"

echo
echo "[3/3] Enviando para origin/$BRANCH..."

git push origin "$BRANCH"

echo
echo "========================================"
echo " COMMIT E PUSH REALIZADOS COM SUCESSO"
echo "========================================"
echo
echo "Branch:  $BRANCH"
echo "Commit:  $(git rev-parse --short HEAD)"
echo "Mensagem: $MENSAGEM"
