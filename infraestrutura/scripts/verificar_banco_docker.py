"""Verifica seguranca do banco e consistencia da importacao no Docker Compose."""

import argparse
from ipaddress import ip_address
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

RAIZ = Path(__file__).resolve().parents[2]
LIMITE_MAXIMO_IMPORTACAO_MB = 512


class ErroVerificacao(RuntimeError):
    pass


def _loopback(valor: Any) -> bool:
    if not isinstance(valor, str):
        return False
    try:
        return ip_address(valor).is_loopback
    except ValueError:
        return False


def validar_configuracao(configuracao: dict[str, Any]) -> list[str]:
    servicos = configuracao.get("services")
    banco = servicos.get("bd") if isinstance(servicos, dict) else None
    if not isinstance(banco, dict):
        return ["Servico bd ausente na configuracao resolvida."]
    erros = []
    ambiente = banco.get("environment")
    senha = ambiente.get("POSTGRES_PASSWORD") if isinstance(ambiente, dict) else None
    if not isinstance(senha, str) or not senha.strip():
        erros.append("Senha do banco ausente na configuracao resolvida.")
    portas = banco.get("ports", [])
    if not isinstance(portas, list):
        erros.append("Formato das portas configuradas nao reconhecido.")
    elif any(not isinstance(porta, dict) or not _loopback(porta.get("host_ip")) for porta in portas):
        erros.append("Compose publica uma porta do banco fora de loopback.")
    return erros


def _inteiro_positivo(valor: Any) -> int | None:
    try:
        convertido = int(str(valor))
    except (TypeError, ValueError):
        return None
    return convertido if convertido > 0 else None


def validar_limite_importacao(configuracao: dict[str, Any]) -> list[str]:
    servicos = configuracao.get("services")
    if not isinstance(servicos, dict):
        return ["Servicos ausentes na configuracao resolvida."]

    limites = {}
    for servico, variavel in (
        ("servidor", "LIMITE_IMPORTACAO_MB"),
        ("interface", "VITE_LIMITE_IMPORTACAO_MB"),
    ):
        definicao = servicos.get(servico)
        ambiente = definicao.get("environment") if isinstance(definicao, dict) else None
        limite = _inteiro_positivo(
            ambiente.get(variavel) if isinstance(ambiente, dict) else None
        )
        if limite is None:
            return [f"{variavel} ausente ou invalido no servico {servico}."]
        limites[servico] = limite

    if limites["servidor"] != limites["interface"]:
        return ["Limites de importacao divergem entre servidor e interface."]
    if limites["servidor"] > LIMITE_MAXIMO_IMPORTACAO_MB:
        return [f"Limite de importacao excede {LIMITE_MAXIMO_IMPORTACAO_MB} MB."]
    return []


def validar_portas_ativas(portas: dict[str, Any]) -> list[str]:
    for vinculos in portas.values():
        if vinculos is None:
            continue
        if not isinstance(vinculos, list):
            return ["Formato das portas ativas nao reconhecido."]
        if any(not isinstance(vinculo, dict) or not _loopback(vinculo.get("HostIp")) for vinculo in vinculos):
            return ["Container do banco publica uma porta fora de loopback."]
    return []


def _executar(argumentos: list[str]) -> str:
    try:
        resultado = subprocess.run(
            argumentos, cwd=RAIZ, check=True, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        # A saida do Compose pode conter secrets; nao a repasse ao relatorio.
        raise ErroVerificacao("Falha ao consultar Docker/Compose; confira o daemon e o arquivo .env.") from None
    return resultado.stdout


def _objeto_json(saida: str) -> dict[str, Any]:
    try:
        objeto = json.loads(saida)
    except json.JSONDecodeError:
        raise ErroVerificacao("Docker/Compose retornou JSON invalido.") from None
    if not isinstance(objeto, dict):
        raise ErroVerificacao("Docker/Compose retornou uma estrutura nao reconhecida.")
    return objeto


def verificar(execucao: bool = False) -> list[str]:
    configuracao = _objeto_json(_executar(["docker", "compose", "config", "--format", "json"]))
    erros = validar_configuracao(configuracao)
    erros.extend(validar_limite_importacao(configuracao))
    if execucao:
        identificador = _executar(["docker", "compose", "ps", "-q", "bd"]).strip()
        if not identificador or len(identificador.splitlines()) != 1:
            raise ErroVerificacao("Esperado exatamente um container bd em execucao.")
        portas = _objeto_json(_executar([
            "docker", "inspect", "--format", "{{json .NetworkSettings.Ports}}", identificador,
        ]))
        erros.extend(validar_portas_ativas(portas))
    return erros


def main(argumentos: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar-execucao", action="store_true")
    opcoes = parser.parse_args(argumentos)
    try:
        erros = verificar(opcoes.verificar_execucao)
    except ErroVerificacao as erro:
        erros = [str(erro)]
    print(json.dumps({
        "status": "falha" if erros else "ok",
        "escopo": "configuracao_e_execucao" if opcoes.verificar_execucao else "configuracao",
        "erros": erros,
    }, ensure_ascii=True, indent=2))
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
