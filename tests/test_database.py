import importlib
import sys

import sqlalchemy
import sqlalchemy.orm


def _import_fresh_database_module(monkeypatch, database_url=None):
    """
    Importa 'src.database' do zero (recarregando o módulo) e intercepta
    create_engine/sessionmaker para não abrir conexão real.
    """
    # Ajusta env antes do import do módulo
    if database_url is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", database_url)

    calls = {}

    class EngineStub:
        pass

    engine_stub = EngineStub()

    def fake_create_engine(
        url,
        *,
        echo=False,
        connect_args=None,
        pool_pre_ping=None,
        pool_recycle=None,
        **kwargs,
    ):
        calls["create_engine"] = {
            "url": url,
            "echo": echo,
            "connect_args": connect_args,
            "pool_pre_ping": pool_pre_ping,
            "pool_recycle": pool_recycle,
            "kwargs": kwargs,
        }
        return engine_stub

    class SessionStub:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    def fake_sessionmaker(*, autocommit=False, autoflush=False, bind=None, **kwargs):
        calls["sessionmaker"] = {
            "autocommit": autocommit,
            "autoflush": autoflush,
            "bind": bind,
            "kwargs": kwargs,
        }

        def factory():
            s = SessionStub()
            calls.setdefault("sessions", []).append(s)
            return s

        return factory

    # Patch ANTES do import do módulo (porque ele cria engine no import)
    monkeypatch.setattr(sqlalchemy, "create_engine", fake_create_engine, raising=True)
    monkeypatch.setattr(sqlalchemy.orm, "sessionmaker", fake_sessionmaker, raising=True)

    # Import limpo (sem cache)
    modname = "src.database"  # se o arquivo não for esse, ajuste aqui
    sys.modules.pop(modname, None)
    module = importlib.import_module(modname)

    return module, calls, engine_stub


def test_uses_default_database_url_and_engine_params(monkeypatch):
    module, calls, engine_stub = _import_fresh_database_module(monkeypatch, None)

    assert module.DATABASE_URL == "postgresql://user:password@localhost:5432/carflow_db"
    assert calls["create_engine"]["url"] == module.DATABASE_URL
    assert calls["create_engine"]["echo"] is False
    assert calls["create_engine"]["connect_args"] == {}  # sem render.com
    assert calls["create_engine"]["pool_pre_ping"] is True
    assert calls["create_engine"]["pool_recycle"] == 1800

    # sessionmaker configurado com o engine retornado
    assert calls["sessionmaker"]["autocommit"] is False
    assert calls["sessionmaker"]["autoflush"] is False
    assert calls["sessionmaker"]["bind"] is engine_stub

    # Base do ORM existe
    assert hasattr(module.Base, "metadata")


def test_normalizes_postgres_scheme_to_postgresql(monkeypatch):
    url = "postgres://user:pass@localhost:5432/carflow_db"
    module, calls, _ = _import_fresh_database_module(monkeypatch, url)

    assert module.DATABASE_URL.startswith("postgresql://")
    assert calls["create_engine"]["url"].startswith("postgresql://")


def test_enables_sslmode_require_for_render(monkeypatch):
    url = "postgres://user:pass@my-host.render.com:5432/carflow_db"
    module, calls, _ = _import_fresh_database_module(monkeypatch, url)

    # Normaliza e aplica SSL
    assert module.DATABASE_URL.startswith("postgresql://")
    assert calls["create_engine"]["connect_args"] == {"sslmode": "require"}


def test_get_db_yields_session_and_closes(monkeypatch):
    module, calls, _ = _import_fresh_database_module(monkeypatch, None)

    gen = module.get_db()
    db = next(gen)

    assert db is calls["sessions"][0]
    assert db.closed is False

    # Ao fechar o generator, executa o finally e fecha a sessão
    gen.close()
    assert db.closed is True
