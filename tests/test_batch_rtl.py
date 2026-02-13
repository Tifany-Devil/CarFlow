import importlib
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest


from src.batch_etl import run_monthly_batch

BATCH_MODULE_PATH = "src.batch_etl"  


@dataclass
class DummyMonthlyAverage:
    brand_id: int
    model_id: int
    year_model: int
    month_ref: str
    region: str
    avg_price: float
    samples_count: int


def _make_db_mock(results_rows, existing_first_return=None, execute_raises=None):
    """
    Cria um mock de sessão do SQLAlchemy com o comportamento esperado pelo seu batch:
      - db.execute(stmt).all() -> results_rows
      - db.query(...).filter_by(...).first() -> existing_first_return
    """
    db = MagicMock(name="db_session_mock")

    if execute_raises is not None:
        db.execute.side_effect = execute_raises
    else:
        result_proxy = MagicMock(name="result_proxy")
        result_proxy.all.return_value = results_rows
        db.execute.return_value = result_proxy

    q = db.query.return_value
    f = q.filter_by.return_value
    f.first.return_value = existing_first_return

    return db


def _patch_module(monkeypatch, db_mock):
    batch_mod = importlib.import_module(BATCH_MODULE_PATH)

    monkeypatch.setattr(batch_mod, "SessionLocal", lambda: db_mock)

    monkeypatch.setattr(batch_mod, "MonthlyAverage", DummyMonthlyAverage)

    return batch_mod


def test_run_monthly_batch_inserts_new_rows(monkeypatch, capsys):
    results = [
        (10, 20, 2022, "DF", "2026-01", 12345.67, 3),
    ]

    db = _make_db_mock(results_rows=results, existing_first_return=None)
    batch_mod = _patch_module(monkeypatch, db)

    batch_mod.run_monthly_batch()

    assert db.add.call_count == 1
    added_obj = db.add.call_args[0][0]
    assert isinstance(added_obj, DummyMonthlyAverage)

    assert added_obj.brand_id == 10
    assert added_obj.model_id == 20
    assert added_obj.year_model == 2022
    assert added_obj.region == "DF"
    assert added_obj.month_ref == "2026-01"
    assert added_obj.avg_price == 12345.67
    assert added_obj.samples_count == 3

    db.commit.assert_called_once()
    db.close.assert_called_once()
    db.rollback.assert_not_called()

    out = capsys.readouterr().out
    assert "Batch Mensal finalizado com sucesso" in out


def test_run_monthly_batch_updates_existing_row(monkeypatch):
    results = [
        (10, 20, 2022, "DF", "2026-01", 999.0, 7),
    ]

    existing = DummyMonthlyAverage(
        brand_id=10,
        model_id=20,
        year_model=2022,
        month_ref="2026-01",
        region="DF",
        avg_price=111.0,
        samples_count=1,
    )

    db = _make_db_mock(results_rows=results, existing_first_return=existing)
    batch_mod = _patch_module(monkeypatch, db)

    batch_mod.run_monthly_batch()

    db.add.assert_not_called()

    assert existing.avg_price == 999.0
    assert existing.samples_count == 7

    db.commit.assert_called_once()
    db.close.assert_called_once()
    db.rollback.assert_not_called()


def test_run_monthly_batch_on_error_rollbacks_and_closes(monkeypatch, capsys):
    db = _make_db_mock(
        results_rows=[],
        execute_raises=RuntimeError("db explode"),
    )
    batch_mod = _patch_module(monkeypatch, db)

    batch_mod.run_monthly_batch()

    db.rollback.assert_called_once()
    db.commit.assert_not_called()

    db.close.assert_called_once()

    out = capsys.readouterr().out
    assert "Erro no Batch" in out
