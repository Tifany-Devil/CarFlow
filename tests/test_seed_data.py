import importlib.util
from pathlib import Path

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base
from src.models import Brand, Model as CarModel, PriceCollection


def _make_sqlite_engine():
    # StaticPool mantém a mesma conexão, então o :memory: não “some”
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _deterministic_randint(a, b):
    # num_coletas: randint(15, 40) -> 15
    if (a, b) == (15, 40):
        return 15
    # day_jitter: randint(-10, 10) -> 0
    if (a, b) == (-10, 10):
        return 0
    return a


def _find_seed_file(project_root: Path) -> Path:
    """
    Encontra o arquivo do seed procurando por 'def seed_database'
    em arquivos .py do projeto.
    """
    # procura primeiro por nomes prováveis
    likely = []
    for pat in ("seed*.py", "*seed*.py"):
        likely.extend(project_root.rglob(pat))

    # elimina venv/cache
    likely = [
        p for p in likely
        if ".venv" not in p.parts and "venv" not in p.parts and "__pycache__" not in p.parts
        and "site-packages" not in p.parts
    ]

    # procura pelo conteúdo
    for p in likely:
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "def seed_database" in txt and "MODELS_DATA" in txt and "REGIONS" in txt:
            return p

    # fallback: busca geral (mais ampla)
    for p in project_root.rglob("*.py"):
        if ".venv" in p.parts or "venv" in p.parts or "__pycache__" in p.parts or "site-packages" in p.parts:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "def seed_database" in txt and "PriceCollection" in txt:
            return p

    raise FileNotFoundError("Não encontrei o arquivo do seed (função seed_database).")


def _import_seed_module_from_path(seed_path: Path):
    """
    Importa um módulo Python a partir do caminho do arquivo (sem depender do nome no PYTHONPATH).
    """
    spec = importlib.util.spec_from_file_location("seed_module", str(seed_path))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_seed_database_populates_tables(monkeypatch, capsys):
    project_root = Path(__file__).resolve().parents[1]
    seed_path = _find_seed_file(project_root)
    seed_mod = _import_seed_module_from_path(seed_path)

    # Banco isolado (SQLite em memória persistente)
    engine = _make_sqlite_engine()
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

    # Patcha engine/session/base no módulo do seed (é isso que ele usa)
    monkeypatch.setattr(seed_mod, "engine", engine, raising=True)
    monkeypatch.setattr(seed_mod, "SessionLocal", SessionLocal, raising=True)
    monkeypatch.setattr(seed_mod, "Base", Base, raising=True)

    # Reduz volume: 1 marca, 1 modelo, 1 região
    monkeypatch.setattr(seed_mod, "MODELS_DATA", {"Ford": [("Ka", 100000)]}, raising=True)
    monkeypatch.setattr(seed_mod, "REGIONS", ["DF"], raising=True)

    # Random determinístico
    monkeypatch.setattr(seed_mod.random, "randint", _deterministic_randint, raising=True)
    monkeypatch.setattr(seed_mod.random, "uniform", lambda a, b: 1.0, raising=True)

    # Executa seed
    seed_mod.seed_database()

    # Verifica inserts
    db = SessionLocal()
    try:
        brands = db.execute(select(func.count(Brand.id))).scalar_one()
        models = db.execute(select(func.count(CarModel.id))).scalar_one()
        cols = db.execute(select(func.count(PriceCollection.id))).scalar_one()

        assert brands == 1
        assert models == 1

        # Esperado: 13 meses * 15 coletas por mês * 1 região * 1 modelo
        assert cols == 13 * 15

        bad = db.execute(
            select(func.count(PriceCollection.id)).where(
                (PriceCollection.region != "DF") | (PriceCollection.year_model != 2024)
            )
        ).scalar_one()
        assert bad == 0
    finally:
        db.close()

    out = capsys.readouterr().out
    assert "Banco populado com sucesso" in out
