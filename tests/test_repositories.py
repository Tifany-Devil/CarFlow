import pytest
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.inspection import inspect as sa_inspect

from src.repositories import CarRepository
from src.models import Brand, Model as CarModel, MonthlyAverage, QueryLog


def _autofill_required_fields(cls, **overrides):
    """
    Cria instância ORM preenchendo automaticamente campos NOT NULL
    (sem default) com valores dummy, para evitar quebra caso o model
    tenha mais colunas obrigatórias além das usadas nos testes.
    """
    mapper = sa_inspect(cls)
    data = dict(overrides)

    for col in mapper.columns:
        if col.primary_key:
            continue
        if col.name in data:
            continue

        needs_value = (col.nullable is False) and (col.default is None) and (col.server_default is None)
        if not needs_value:
            continue

        # Tenta inferir por tipo Python
        try:
            py_t = col.type.python_type
        except Exception:
            py_t = str

        if py_t is int:
            data[col.name] = 1
        elif py_t is float:
            data[col.name] = 1.0
        elif py_t is bool:
            data[col.name] = False
        elif py_t is datetime:
            data[col.name] = datetime.now(timezone.utc)
        else:
            data[col.name] = "x"

    return cls(**data)


@pytest.fixture()
def db_session():
    """
    Cria um banco em memória (SQLite), cria as tabelas e fornece uma sessão.
    """
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    # Cria tabelas usando a metadata dos models
    Brand.metadata.create_all(engine)

    sess = Session()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture()
def repo(db_session):
    return CarRepository(db_session)


def seed_basic_data(db):
    """
    Insere marcas, modelos e alguns monthly_averages para os testes.
    """
    b_fiat = _autofill_required_fields(Brand, id=10, name="Fiat")
    b_ford = _autofill_required_fields(Brand, id=20, name="Ford")

    m_argo = _autofill_required_fields(CarModel, id=100, brand_id=10, name="Argo")
    m_ka = _autofill_required_fields(CarModel, id=200, brand_id=20, name="Ka")
    m_fiesta = _autofill_required_fields(CarModel, id=201, brand_id=20, name="Fiesta")

    db.add_all([b_fiat, b_ford, m_argo, m_ka, m_fiesta])

    # MonthlyAverage: insere duplicados p/ distinct e múltiplas regiões/meses
    rows = [
        _autofill_required_fields(
            MonthlyAverage,
            model_id=200,
            year_model=2022,
            region="DF",
            month_ref="2026-01",
            avg_price=1000.0,
            samples_count=3,
        ),
        _autofill_required_fields(
            MonthlyAverage,
            model_id=200,
            year_model=2022,
            region="DF",
            month_ref="2026-02",
            avg_price=1100.0,
            samples_count=2,
        ),
        _autofill_required_fields(
            MonthlyAverage,
            model_id=200,
            year_model=2021,
            region="SP",
            month_ref="2026-01",
            avg_price=900.0,
            samples_count=5,
        ),
        # duplicado de year_model (p/ distinct)
        _autofill_required_fields(
            MonthlyAverage,
            model_id=200,
            year_model=2022,
            region="SP",
            month_ref="2026-03",
            avg_price=1200.0,
            samples_count=1,
        ),
    ]
    db.add_all(rows)
    db.commit()


def test_get_brands_returns_ordered_by_name(db_session, repo):
    seed_basic_data(db_session)

    brands = repo.get_brands()
    assert [b.name for b in brands] == sorted([b.name for b in brands])
    assert [b.name for b in brands] == ["Fiat", "Ford"]


def test_get_models_by_brand_filters_and_orders(db_session, repo):
    seed_basic_data(db_session)

    models_ford = repo.get_models_by_brand(brand_id=20)
    names = [m.name for m in models_ford]

    assert names == ["Fiesta", "Ka"]  # ordem alfabética
    assert all(m.brand_id == 20 for m in models_ford)


def test_get_years_by_model_distinct_desc(db_session, repo):
    seed_basic_data(db_session)

    years = repo.get_years_by_model(model_id=200)
    assert years == sorted(set(years), reverse=True)
    assert years == [2022, 2021]


def test_get_available_regions_distinct_ordered(db_session, repo):
    seed_basic_data(db_session)

    regions = repo.get_available_regions()
    assert regions == sorted(set(regions))
    assert regions == ["DF", "SP"]


def test_get_price_history_orders_by_month_and_filters_region(db_session, repo):
    seed_basic_data(db_session)

    # Sem filtro de região
    hist_all = repo.get_price_history(model_id=200, year_model=2022, region=None)
    assert [h.month_ref for h in hist_all] == ["2026-01", "2026-02", "2026-03"]

    # Com filtro DF
    hist_df = repo.get_price_history(model_id=200, year_model=2022, region="DF")
    assert [h.month_ref for h in hist_df] == ["2026-01", "2026-02"]
    assert all(h.region == "DF" for h in hist_df)


def test_create_log_inserts_row_and_commits(db_session, repo):
    # cria log
    repo.create_log(brand_id=10, model_id=100, year_model=2022, status="FOUND", region="DF")

    # verifica no banco
    logs = db_session.execute(select(QueryLog)).scalars().all()
    assert len(logs) == 1

    log = logs[0]
    assert log.brand_id == 10
    assert log.model_id == 100
    assert log.year_model == 2022
    assert log.status == "FOUND"
    assert log.region == "DF"
