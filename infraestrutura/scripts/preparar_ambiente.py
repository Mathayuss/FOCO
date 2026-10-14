#!/usr/bin/env python3
"""Prepara o .env inicial do FOCO sem expor ou sobrescrever credenciais."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import secrets
import stat
import sys
import tempfile
from urllib.parse import quote, unquote, urlsplit


SENHAS_PADRAO = frozenset({
    "altere_esta_senha",
    "troque-esta-senha-antes-de-iniciar",
})
CHAVES_OBRIGATORIAS = ("BD_USUARIO", "BD_SENHA", "BD_NOME", "DATABASE_URL")


class ErroPreparacao(RuntimeError):
    pass


def _valor_sem_aspas(valor: str) -> str:
    valor = valor.strip()
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in {'"', "'"}:
        return valor[1:-1]
    return valor


def _ler_variaveis(conteudo: str) -> dict[str, str]:
    variaveis: dict[str, str] = {}
    duplicadas: set[str] = set()
    for linha in conteudo.splitlines():
        limpa = linha.strip()
        if not limpa or limpa.startswith("#") or "=" not in limpa:
            continue
        chave, valor = limpa.split("=", 1)
        chave = chave.strip()
        if chave in variaveis:
            duplicadas.add(chave)
        variaveis[chave] = _valor_sem_aspas(valor)
    if duplicadas.intersection(CHAVES_OBRIGATORIAS):
        raise ErroPreparacao("Arquivo de ambiente possui chaves obrigatorias duplicadas.")
    return variaveis


def _exigir_chaves(variaveis: dict[str, str], origem: str) -> None:
    ausentes = [chave for chave in CHAVES_OBRIGATORIAS if not variaveis.get(chave)]
    if ausentes:
        raise ErroPreparacao(f"Arquivo {origem} incompleto; faltam variaveis obrigatorias.")


def _url_coerente(variaveis: dict[str, str]) -> bool:
    try:
        partes = urlsplit(variaveis["DATABASE_URL"])
        return (
            partes.scheme == "postgresql+psycopg"
            and unquote(partes.username or "") == variaveis["BD_USUARIO"]
            and unquote(partes.password or "") == variaveis["BD_SENHA"]
            and partes.hostname == "bd"
            and partes.port == 5432
            and unquote(partes.path.lstrip("/")) == variaveis["BD_NOME"]
        )
    except (KeyError, ValueError):
        return False


def _validar_existente(destino: Path) -> None:
    if destino.is_symlink():
        raise ErroPreparacao("O arquivo de ambiente nao pode ser um link simbolico.")
    if not destino.is_file():
        raise ErroPreparacao("O destino existente nao e um arquivo regular.")
    variaveis = _ler_variaveis(destino.read_text(encoding="utf-8"))
    _exigir_chaves(variaveis, "existente")
    if variaveis["BD_SENHA"].strip().casefold() in SENHAS_PADRAO:
        raise ErroPreparacao(
            "Arquivo existente usa senha padrao; realize a rotacao controlada antes de iniciar."
        )
    if not _url_coerente(variaveis):
        raise ErroPreparacao("DATABASE_URL do arquivo existente diverge da configuracao do banco.")
    os.chmod(destino, stat.S_IRUSR | stat.S_IWUSR)


def _substituir(conteudo: str, valores: dict[str, str]) -> str:
    resultado: list[str] = []
    substituidas: set[str] = set()
    for linha in conteudo.splitlines(keepends=True):
        chave = linha.split("=", 1)[0].strip() if "=" in linha else ""
        if chave in valores:
            final = "\n" if linha.endswith("\n") else ""
            resultado.append(f"{chave}={valores[chave]}{final}")
            substituidas.add(chave)
        else:
            resultado.append(linha)
    if substituidas != set(valores):
        raise ErroPreparacao("Arquivo modelo incompleto; faltam variaveis obrigatorias.")
    return "".join(resultado)


def _gravar_sem_sobrescrever(destino: Path, conteudo: str) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destino.parent,
            prefix=f"{destino.name}.",
            suffix=".tmp",
            delete=False,
        ) as arquivo:
            temporario = Path(arquivo.name)
            os.chmod(temporario, stat.S_IRUSR | stat.S_IWUSR)
            arquivo.write(conteudo)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        try:
            os.link(temporario, destino)
        except FileExistsError as erro:
            raise ErroPreparacao("O arquivo de ambiente foi criado por outro processo.") from erro
        os.chmod(destino, stat.S_IRUSR | stat.S_IWUSR)
        descritor = os.open(destino.parent, os.O_RDONLY)
        try:
            os.fsync(descritor)
        finally:
            os.close(descritor)
    finally:
        if temporario is not None:
            temporario.unlink(missing_ok=True)


def preparar(modelo: Path, destino: Path) -> str:
    if destino.is_symlink():
        raise ErroPreparacao("O arquivo de ambiente nao pode ser um link simbolico.")
    if destino.exists():
        _validar_existente(destino)
        return "preservado"
    if not modelo.is_file() or modelo.is_symlink():
        raise ErroPreparacao("Arquivo modelo ausente ou invalido.")

    conteudo_modelo = modelo.read_text(encoding="utf-8")
    variaveis = _ler_variaveis(conteudo_modelo)
    _exigir_chaves(variaveis, "modelo")
    segredo = secrets.token_hex(32)
    usuario = variaveis["BD_USUARIO"]
    banco = variaveis["BD_NOME"]
    url = (
        "postgresql+psycopg://"
        f"{quote(usuario, safe='')}:{quote(segredo, safe='')}@bd:5432/{quote(banco, safe='')}"
    )
    conteudo = _substituir(conteudo_modelo, {"BD_SENHA": segredo, "DATABASE_URL": url})
    _gravar_sem_sobrescrever(destino, conteudo)
    return "criado"


def main(argumentos: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepara o ambiente inicial do FOCO.")
    parser.add_argument("--modelo", type=Path, default=Path(".env.example"))
    parser.add_argument("--arquivo", type=Path, default=Path(".env"))
    opcoes = parser.parse_args(argumentos)
    try:
        resultado = preparar(opcoes.modelo, opcoes.arquivo)
    except (ErroPreparacao, OSError, UnicodeError) as erro:
        mensagem = str(erro) if isinstance(erro, ErroPreparacao) else "Falha ao preparar o ambiente."
        print(f"Erro: {mensagem}", file=sys.stderr)
        return 1
    if resultado == "criado":
        print("Ambiente criado com credencial exclusiva e permissao 0600.")
    else:
        print("Ambiente existente validado e preservado com permissao 0600.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
