from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal, engine
from app.models.import_batch import ImportBatch
from app.models.occurrence import Occurrence


def test_banco_comeca_sem_dados_operacionais():
    assert get_settings().ambiente == "teste"
    assert engine.url.database != "foco_ocorrencias"
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Occurrence)) == 0
        assert db.scalar(select(func.count()).select_from(ImportBatch)) == 0


def test_banco_rejeita_ocorrencia_com_lote_inexistente():
    with SessionLocal() as db:
        db.add(Occurrence(
            source="RELATORIO_SEJUSP",
            source_id="TESTE-LOTE-INEXISTENTE",
            opened_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            type_name="TIPO TESTE",
            municipality="MUNICIPIO TESTE",
            import_batch_id=999999,
        ))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_limite_de_importacao_deve_ser_positivo():
    with pytest.raises(ValueError):
        Settings(limite_importacao_mb=0)

    with pytest.raises(ValueError):
        Settings(limite_importacao_mb=-1)
