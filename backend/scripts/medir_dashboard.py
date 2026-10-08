"""Mede o dashboard sem alterar dados e sem incluir rede ou serializacao HTTP."""

import argparse
import cProfile
import json
from hashlib import sha256
from statistics import median
from time import perf_counter

from sqlalchemy import event, text

from app.db.session import SessionLocal, engine
from app.services import dashboard_service
from app.services import sejusp_analytics_service as analytics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeticoes", type=int, default=7)
    parser.add_argument("--periodo", default="all")
    parser.add_argument("--tipo")
    parser.add_argument("--municipio")
    parser.add_argument("--unidade")
    parser.add_argument("--subtipo")
    parser.add_argument("--turno")
    args = parser.parse_args()
    if not 1 <= args.repeticoes <= 50:
        parser.error("--repeticoes deve estar entre 1 e 50")
    params = dict(period=args.periodo, type_name=args.tipo, municipality=args.municipio,
                  unit=args.unidade, subtype=args.subtipo, shift=args.turno)
    queries = []

    def count_query(_conn, _cursor, _statement, _params, _context, _many):
        queries.append(1)

    def load(db):
        with analytics.dataset_snapshot(db):
            errors = analytics.validate_filter_params(db, **params)
            if errors:
                raise ValueError(f"Filtros invalidos: {errors}")
            return dashboard_service.snapshot(db, **params)

    try:
        with SessionLocal() as db:
            if engine.dialect.name == "postgresql":
                db.execute(text("SET TRANSACTION READ ONLY"))
            elif engine.dialect.name == "sqlite":
                db.execute(text("PRAGMA query_only=ON"))
            analytics.clear_cache()
            load(db)
            event.listen(engine, "before_cursor_execute", count_query)
            try:
                samples = []
                query_counts = []
                for _ in range(args.repeticoes):
                    queries.clear()
                    start = perf_counter()
                    result = load(db)
                    samples.append((perf_counter() - start) * 1000)
                    query_counts.append(len(queries))
            finally:
                event.remove(engine, "before_cursor_execute", count_query)
            profiler = cProfile.Profile()
            with profiler:
                load(db)
            watched = {"_period_defs", "_filtered_rows", "_build_filter_metadata"}
            calls = {entry.code.co_name:entry.callcount for entry in profiler.getstats()
                     if hasattr(entry.code, "co_name") and entry.code.co_name in watched}
            serialized = json.dumps(result, ensure_ascii=True, sort_keys=True, allow_nan=False)
            print(json.dumps({
                "repeticoes": args.repeticoes,
                "total_recorte": result["overview"]["total"],
                "hash_sha256_resposta": sha256(serialized.encode("utf-8")).hexdigest(),
                "parametros": {key:value for key,value in params.items() if value is not None},
                "cache_linhas": "aquecido",
                "mediana_ms": round(median(samples), 2),
                "minimo_ms": round(min(samples), 2),
                "maximo_ms": round(max(samples), 2),
                "consultas_sql_por_execucao": query_counts,
                "chamadas_em_execucao_perfilada": calls,
            }, ensure_ascii=True, indent=2))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
