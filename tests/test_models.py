import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect

from src.database import Base
from src.models import Brand, Model, PriceCollection, MonthlyAverage, QueryLog


@pytest.fixture()
def engine():
    # SQLite em memória + StaticPool (mesma conexão) -> estável para testes
    eng = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Habilita FK no SQLite (por padrão é OFF)
    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture()
def db(engine):
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def test_metadata_has_all_tables(engine):
    insp = inspect(engine)
    tables = set(insp.get_table_names())

    assert "brands" in tables
    assert "models" in tables
    assert "price_collections" in tables
    assert "monthly_averages" in tables
    assert "query_logs" in tables




def test_brand_columns_constraints(engine):
    insp = inspect(engine)
    cols = {c["name"]: c for c in insp.get_columns("brands")}

    assert set(cols.keys()) == {"id", "name"}
    assert bool(cols["id"]["primary_key"]) is True

    # SQLite pode refletir unique como constraint OU como index unique
    uniques = insp.get_unique_constraints("brands")
    indexes = insp.get_indexes("brands")

    has_unique_constraint = any("name" in uc.get("column_names", []) for uc in uniques)
    has_unique_index = any(idx.get("unique") and "name" in idx.get("column_names", []) for idx in indexes)

    assert has_unique_constraint or has_unique_index



def test_brand_name_unique_enforced(db):
    db.add(Brand(name="Ford"))
    db.commit()

    db.add(Brand(name="Ford"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_model_fk_enforced(db):
    # tenta inserir Model com brand_id inexistente -> deve falhar por FK
    db.add(Model(name="Ka", brand_id=999, vehicle_type="Carro"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_can_insert_minimal_rows_and_defaults_work(db):
    # Seed mínimo coerente
    b = Brand(name="Ford")
    db.add(b)
    db.commit()
    db.refresh(b)

    m = Model(name="Ka", brand_id=b.id, vehicle_type="Carro")
    db.add(m)
    db.commit()
    db.refresh(m)

    # PriceCollection: collected_at tem server_default=func.now()
    pc = PriceCollection(model_id=m.id, year_model=2024, price=1000.0, region="DF")
    db.add(pc)
    db.commit()
    db.refresh(pc)
    assert pc.id is not None
    assert pc.collected_at is not None  # default do banco

    # MonthlyAverage: created_at tem server_default=func.now(), region nullable
    ma = MonthlyAverage(
        brand_id=b.id,
        model_id=m.id,
        year_model=2024,
        month_ref="2026-01",
        region=None,  # permitido
        avg_price=1234.5,
        samples_count=7,
    )
    db.add(ma)
    db.commit()
    db.refresh(ma)
    assert ma.id is not None
    assert ma.created_at is not None

    # QueryLog: created_at default, region nullable
    ql = QueryLog(
        brand_id=b.id,
        model_id=m.id,
        year_model=2024,
        region="DF",
        status="SUCCESS",
    )
    db.add(ql)
    db.commit()
    db.refresh(ql)
    assert ql.id is not None
    assert ql.created_at is not None


def test_expected_nullable_flags(engine):
    insp = inspect(engine)

    # monthly_averages.region é nullable=True no model
    cols_ma = {c["name"]: c for c in insp.get_columns("monthly_averages")}
    assert cols_ma["region"]["nullable"] is True

    # query_logs.region é nullable=True no model
    cols_ql = {c["name"]: c for c in insp.get_columns("query_logs")}
    assert cols_ql["region"]["nullable"] is True
