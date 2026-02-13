import importlib
from types import SimpleNamespace

import pytest
from sqlalchemy import text


def _reload_database_with_url(monkeypatch, url: str):
    """
    Recarrega src.database depois de setar DATABASE_URL,
    porque engine/SessionLocal são criados no import.
    """
    monkeypatch.setenv("DATABASE_URL", url)

    # Importa e recarrega para pegar o novo env
    import src.database as dbmod
    importlib.reload(dbmod)
    return dbmod


def test_engine_uses_env_database_url_and_connects(monkeypatch):
    dbmod = _reload_database_with_url(monkeypatch, "sqlite+pysqlite:///:memory:")

    # Testa que a engine conecta e executa SQL básico
    with dbmod.engine.connect() as conn:
        value = conn.execute(text("SELECT 1")).scalar_one()

    assert value == 1


def test_sessionlocal_creates_working_session(monkeypatch):
    dbmod = _reload_database_with_url(monkeypatch, "sqlite+pysqlite:///:memory:")

    session = dbmod.SessionLocal()
    try:
        value = session.execute(text("SELECT 1")).scalar_one()
        assert value == 1
    finally:
        session.close()


def test_get_db_yields_session_and_closes(monkeypatch):
    """
    Testa a lógica do generator get_db() garantindo que close() é chamado.
    Aqui a gente não depende da engine real; apenas valida o fluxo.
    """
    import src.database as dbmod

    closed = {"called": False}

    class DummySession:
        def close(self):
            closed["called"] = True

    # Força SessionLocal a retornar DummySession
    monkeypatch.setattr(dbmod, "SessionLocal", lambda: DummySession(), raising=True)

    gen = dbmod.get_db()
    db = next(gen)
    assert isinstance(db, DummySession)

    # Finaliza o generator para cair no finally e chamar close()
    gen.close()
    assert closed["called"] is True
