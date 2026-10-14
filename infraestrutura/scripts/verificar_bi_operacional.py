#!/usr/bin/env python3
"""Verifica a API analitica ativa usando somente requisicoes HTTP GET."""

from __future__ import annotations

import argparse
from ipaddress import ip_address
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


DIMENSOES = {"period", "type", "municipality", "unit", "subtype", "shift"}
PAINEIS = ("monthly", "types", "cities", "hours", "units", "shifts")
LIMITE_RESPOSTA = 16 * 1024 * 1024


class ErroSmoke(RuntimeError):
    pass


def _url_base(valor: str) -> str:
    try:
        partes = urlsplit(valor)
        hostname = partes.hostname
        partes.port
    except ValueError:
        raise ErroSmoke("URL da API invalida; informe somente origem e prefixo /api/v1.") from None
    if (
        partes.scheme not in {"http", "https"}
        or not hostname
        or partes.username
        or partes.password
        or partes.query
        or partes.fragment
    ):
        raise ErroSmoke("URL da API invalida; informe somente origem e prefixo /api/v1.")
    loopback = hostname.casefold() == "localhost"
    if not loopback:
        try:
            loopback = ip_address(hostname).is_loopback
        except ValueError:
            loopback = False
    if partes.scheme == "http" and not loopback:
        raise ErroSmoke("Hosts remotos exigem HTTPS.")
    return urlunsplit((partes.scheme, partes.netloc, partes.path.rstrip("/"), "", ""))


def _get(base: str, caminho: str, parametros: dict[str, str] | None, timeout: float) -> dict[str, Any]:
    query = urlencode(parametros or {})
    url = f"{base}{caminho}" + (f"?{query}" if query else "")
    requisicao = Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urlopen(requisicao, timeout=timeout) as resposta:
            conteudo = resposta.read(LIMITE_RESPOSTA + 1)
            if len(conteudo) > LIMITE_RESPOSTA:
                raise ErroSmoke("Resposta da API excede o limite de verificacao.")
            if resposta.status != 200:
                raise ErroSmoke(f"API retornou HTTP {resposta.status} em {caminho}.")
    except HTTPError as erro:
        raise ErroSmoke(f"API retornou HTTP {erro.code} em {caminho}.") from None
    except (URLError, TimeoutError, OSError):
        raise ErroSmoke(f"Falha de conexao com a API em {caminho}.") from None
    try:
        dados = json.loads(conteudo)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ErroSmoke(f"Resposta JSON invalida em {caminho}.") from None
    if not isinstance(dados, dict):
        raise ErroSmoke(f"Formato de resposta invalido em {caminho}.")
    return dados


def _exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise ErroSmoke(mensagem)


def _periodo_recente(filtros: dict[str, Any]) -> str:
    opcoes = filtros.get("periods")
    _exigir(isinstance(opcoes, list), "API nao retornou periodos selecionaveis.")
    meses = {
        opcao["key"]
        for opcao in opcoes
        if isinstance(opcao, dict)
        and isinstance(opcao.get("key"), str)
        and re.fullmatch(r"\d{4}-\d{2}", opcao["key"])
    }
    _exigir(bool(meses), "Base SEJUSP nao possui periodo mensal para validar.")
    comparaveis = []
    for mes_atual in meses:
        ano, mes = map(int, mes_atual.split("-"))
        if ano > 1 and f"{ano - 1:04d}-{mes:02d}" in meses:
            comparaveis.append(mes_atual)
    _exigir(bool(comparaveis), "Base SEJUSP nao possui mes com cobertura no ano anterior.")
    return max(comparaveis)


def _periodo_anual(filtros: dict[str, Any]) -> str:
    opcoes = filtros.get("periods")
    _exigir(isinstance(opcoes, list), "API nao retornou periodos selecionaveis.")
    periodos = {
        opcao["key"]
        for opcao in opcoes
        if isinstance(opcao, dict)
        and isinstance(opcao.get("key"), str)
        and re.fullmatch(r"\d{4}-\d{2}|ano-\d{4}", opcao["key"])
    }
    anos = sorted(
        (int(periodo[4:]) for periodo in periodos if periodo.startswith("ano-")),
        reverse=True,
    )
    for ano in anos:
        if any(f"{ano:04d}-{mes:02d}" in periodos and f"{ano - 1:04d}-{mes:02d}" in periodos
               for mes in range(1, 13)):
            return f"ano-{ano:04d}"
    raise ErroSmoke("Base SEJUSP nao possui periodo anual com meses comparaveis.")


def _verificar_comparacao_anual(base: str, filtros: dict[str, Any], timeout: float) -> str:
    periodo = _periodo_anual(filtros)
    ano = int(periodo[4:])
    painel = _get(base, "/analytics/dashboard", {"source": "sejusp", "period": periodo}, timeout)
    overview = painel.get("overview")
    mensal = painel.get("monthly")
    _exigir(isinstance(overview, dict) and isinstance(mensal, dict),
            "Dashboard anual nao retornou visao geral e evolucao.")
    comparacao = overview.get("comparison")
    _exigir(isinstance(comparacao, dict) and comparacao.get("available") is True,
            "Comparacao anual indisponivel apesar de haver meses equivalentes.")

    rotulo_atual = comparacao.get("current_label")
    rotulo_base = comparacao.get("baseline_label")
    padrao_rotulo = re.compile(r"^(?P<meses>.+)/(\d{4})$")
    atual = padrao_rotulo.fullmatch(rotulo_atual) if isinstance(rotulo_atual, str) else None
    anterior = padrao_rotulo.fullmatch(rotulo_base) if isinstance(rotulo_base, str) else None
    _exigir(atual is not None and anterior is not None
            and int(atual.group(2)) == ano
            and int(anterior.group(2)) == ano - 1
            and atual.group("meses") == anterior.group("meses"),
            "Rotulos anuais nao representam os mesmos meses de anos consecutivos.")

    serie = mensal.get("items")
    _exigir(isinstance(serie, list) and bool(serie), "Serie mensal anual invalida.")
    meses_atuais = {
        item.get("mes")
        for item in serie
        if isinstance(item, dict) and isinstance(item.get("mes"), str)
    }
    _exigir(len(meses_atuais) == len(serie), "Serie anual contem meses sem rotulo valido.")

    pontos = mensal.get("comparison")
    _exigir(isinstance(pontos, list) and bool(pontos), "Serie anual nao retornou meses comparativos.")
    meses_comparados: set[str] = set()
    soma_atual = 0
    soma_base = 0
    padrao_mes = re.compile(r"^(?P<mes>[^/]+)/(?P<ano>\d{4})$")
    for ponto in pontos:
        _exigir(isinstance(ponto, dict), "Ponto da comparacao anual invalido.")
        rotulo_mes = ponto.get("current_month")
        rotulo_base_mes = ponto.get("baseline_month")
        mes_atual = padrao_mes.fullmatch(rotulo_mes) if isinstance(rotulo_mes, str) else None
        mes_base = padrao_mes.fullmatch(rotulo_base_mes) if isinstance(rotulo_base_mes, str) else None
        _exigir(mes_atual is not None and mes_base is not None
                and mes_atual.group("ano") == str(ano)
                and mes_base.group("ano") == str(ano - 1)
                and mes_atual.group("mes") == mes_base.group("mes")
                and rotulo_mes in meses_atuais,
                "Comparacao anual inclui meses que nao sao equivalentes.")
        _exigir(rotulo_mes not in meses_comparados, "Comparacao anual repete um mes.")
        atual_mes = ponto.get("current")
        base_mes = ponto.get("baseline")
        _exigir(isinstance(atual_mes, int) and atual_mes >= 0
                and isinstance(base_mes, int) and base_mes >= 0,
                "Comparacao anual contem totais mensais invalidos.")
        meses_comparados.add(rotulo_mes)
        soma_atual += atual_mes
        soma_base += base_mes

    _exigir(soma_atual == comparacao.get("current_total")
            and soma_base == comparacao.get("baseline_total"),
            "Totais anuais comparados divergem da soma dos meses equivalentes.")
    if len(meses_comparados) < len(meses_atuais):
        motivo = comparacao.get("reason")
        _exigir(isinstance(motivo, str) and "limitad" in motivo.casefold()
                and "equivalentes" in motivo.casefold(),
                "Cobertura parcial anual nao foi explicada na resposta.")
    return f"{rotulo_atual} vs {rotulo_base}"


def verificar(url_api: str, timeout: float = 12) -> dict[str, Any]:
    base = _url_base(url_api)
    verificacoes: list[str] = []

    saude = _get(base, "/health", None, timeout)
    _exigir(saude.get("status") == "ok" and saude.get("database") == "ok", "API ou banco nao esta saudavel.")
    verificacoes.append("saude_api_banco")

    filtros = _get(base, "/analytics/filters", {"source": "sejusp"}, timeout)
    _exigir(filtros.get("source_scope") == "sejusp_importado", "Escopo de dados nao e SEJUSP importado.")
    dimensoes = filtros.get("filterable_dimensions")
    _exigir(isinstance(dimensoes, list) and set(dimensoes) == DIMENSOES,
            "API nao disponibiliza as seis dimensoes globais.")
    for chave in ("types", "municipalities", "units", "subtypes", "shifts"):
        _exigir(isinstance(filtros.get(chave), list), f"API nao retornou opcoes validas para {chave}.")
    verificacoes.append("filtros_globais")

    periodo = _periodo_recente(filtros)
    rotulos = {
        opcao["key"]: opcao["label"]
        for opcao in filtros["periods"]
        if isinstance(opcao, dict) and isinstance(opcao.get("key"), str)
        and isinstance(opcao.get("label"), str)
    }
    rotulo_periodo = rotulos.get(periodo)
    _exigir(rotulo_periodo is not None, "Periodo recente sem rotulo na API.")
    parametros = {"source": "sejusp", "period": periodo}
    painel = _get(base, "/analytics/dashboard", parametros, timeout)
    overview = painel.get("overview")
    mensal = painel.get("monthly")
    _exigir(isinstance(overview, dict) and isinstance(mensal, dict), "Dashboard nao retornou visao geral e evolucao.")
    _exigir(overview.get("source_scope") == "sejusp_importado", "Visao geral usa fonte inesperada.")
    aplicados = overview.get("applied_filters")
    _exigir(isinstance(aplicados, dict), "Dashboard nao informou os filtros aplicados.")
    _exigir(aplicados.get("period") == rotulo_periodo, "Periodo solicitado nao aparece como filtro aplicado.")
    total = overview.get("total")
    _exigir(isinstance(total, int) and total >= 0, "Total de ocorrencias invalido.")
    itens_mensais = mensal.get("items")
    _exigir(isinstance(itens_mensais, list), "Serie mensal invalida.")
    totais_mensais = [item.get("total") for item in itens_mensais if isinstance(item, dict)]
    _exigir(len(totais_mensais) == len(itens_mensais)
            and all(isinstance(valor, int) and valor >= 0 for valor in totais_mensais),
            "Serie mensal contem totais invalidos.")
    _exigir(sum(totais_mensais) == total,
            "Total da serie mensal diverge da visao geral.")
    verificacoes.append("total_evolucao")

    for nome in PAINEIS:
        resposta = painel.get(nome)
        _exigir(isinstance(resposta, dict), f"Painel {nome} ausente no dashboard.")
        _exigir(resposta.get("source_scope") == "sejusp_importado", f"Painel {nome} usa fonte inesperada.")
        _exigir(resposta.get("applied_filters") == aplicados, f"Filtros divergem no painel {nome}.")
    comparacao = overview.get("comparison")
    _exigir(isinstance(comparacao, dict), "Comparacao de periodo ausente.")
    if comparacao.get("available") is True:
        _exigir(comparacao.get("current_label") == rotulo_periodo, "Comparacao usa periodo atual inesperado.")
        rotulo_anterior = re.sub(r"(\d{4})$", lambda ano: str(int(ano.group(1)) - 1), rotulo_periodo)
        _exigir(comparacao.get("baseline_label") == rotulo_anterior,
                "Comparacao nao usa o mesmo periodo do ano anterior.")
        _exigir(isinstance(comparacao.get("baseline_total"), int), "Total da base comparativa invalido.")
        verificacoes.append("comparacao_anual_disponivel")
    else:
        raise ErroSmoke("Comparacao com o mesmo periodo do ano anterior indisponivel na base ativa.")

    comparacao_anual = _verificar_comparacao_anual(base, filtros, timeout)
    verificacoes.append("comparacao_anual_meses_equivalentes")

    overview_individual = _get(base, "/analytics/overview", parametros, timeout)
    mensal_individual = _get(base, "/analytics/monthly", parametros, timeout)
    _exigir(overview_individual == overview, "Endpoint individual overview diverge do dashboard consolidado.")
    _exigir(mensal_individual == mensal, "Endpoint individual monthly diverge do dashboard consolidado.")
    verificacoes.append("consistencia_endpoints")

    return {
        "status": "ok",
        "periodo_verificado": periodo,
        "comparacao_anual": comparacao_anual,
        "verificacoes": verificacoes,
    }


def main(argumentos: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/v1", help="Prefixo da API (padrao: loopback local).")
    parser.add_argument("--timeout", type=float, default=12, help="Tempo limite por requisicao, em segundos.")
    opcoes = parser.parse_args(argumentos)
    if opcoes.timeout <= 0:
        parser.error("--timeout deve ser maior que zero")
    try:
        resultado = verificar(opcoes.url, opcoes.timeout)
    except ErroSmoke as erro:
        resultado = {"status": "falha", "erros": [str(erro)]}
    print(json.dumps(resultado, ensure_ascii=True, indent=2))
    return 0 if resultado["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
