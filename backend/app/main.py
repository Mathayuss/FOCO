from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.db.schema import garantir_colunas_incrementais
from app.services import import_audit_service
from app.services.demo_seed import seed_demo
import app.models  # noqa: F401


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TRANSIÇÃO v0.3.1:
    # create_all/garantir_colunas_incrementais permanecem temporariamente
    # para não quebrar bancos de desenvolvimento existentes.
    # Após gerar e homologar a primeira migration Alembic, remover ambos.
    Base.metadata.create_all(bind=engine)
    garantir_colunas_incrementais(engine)

    db = SessionLocal()
    try:
        seed_demo(db)
        import_audit_service.ensure_legacy_import_batches(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.versao_foco,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "version": settings.versao_foco,
        "ambiente": settings.ambiente,
    }
