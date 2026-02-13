from dataclasses import dataclass
from typing import Optional

import pandas as pd
import pytest

from src.services import CarService  # ajuste aqui se o módulo for outro


@dataclass
class DummyObj:
    id: int
    name: str


@dataclass
class DummyMonthlyAverage:
    month_ref: str
    avg_price: float
    samples_count: int


class FakeRepo:
    def __init__(self):
        self._brands = [DummyObj(1, "Fiat"), DummyObj(2, "Ford")]
        self._models = {2: [DummyObj(10, "Fiesta"), DummyObj(11, "Ka")]}
        self._years = {11: [2024, 2023, 2022]}
        self._regions = ["DF", None, "SP"]
        self._history_map = {}  # (model_id, year_model, region) -> list[DummyMonthlyAverage]
        self.logs = []          # (brand_id, model_id, year_model, status, region)

    def get_brands(self):
        return self._brands

    def get_models_by_brand(self, brand_id: int):
        return self._models.get(brand_id, [])

    def get_years_by_model(self, model_id: int):
        return self._years.get(model_id, [])

    def get_available_regions(self):
        return self._regions

    def get_price_history(self, model_id: int, year_model: int, region: Optional[str] = None):
        return self._history_map.get((model_id, year_model, region), [])

    def create_log(
        self,
        brand_id: Optional[int],
        model_id: Optional[int],
        year_model: Optional[int],
        status: str,
        region: Optional[str] = None,
    ):
        self.logs.append((brand_id, model_id, year_model, status, region))


@pytest.fixture()
def fake_repo():
    return FakeRepo()


@pytest.fixture()
def service(fake_repo):
    # Cria CarService sem chamar __init__ (evita CarRepository(db))
    svc = CarService.__new__(CarService)
    svc.repository = fake_repo
    return svc


def test_list_brands_returns_name_id_dict(service):
    assert service.list_brands() == {"Fiat": 1, "Ford": 2}


def test_list_models_returns_models_for_brand(service):
    assert service.list_models(2) == {"Fiesta": 10, "Ka": 11}


def test_list_years_returns_years(service):
    assert service.list_years(11) == [2024, 2023, 2022]


def test_list_regions_filters_none(service):
    assert service.list_regions() == ["DF", "SP"]


def test_get_consolidated_price_no_result_logs_and_returns_none(service, fake_repo):
    out = service.get_consolidated_price(brand_id=2, model_id=11, year_model=2024, region="DF")
    assert out is None

    # 1 log esperado (NO_RESULT com região)
    assert fake_repo.logs == [(2, 11, 2024, "NO_RESULT", "DF")]


def test_get_consolidated_price_success_returns_kpi_and_history_df(service, fake_repo):
    fake_repo._history_map[(11, 2024, "DF")] = [
        DummyMonthlyAverage(month_ref="2026-01", avg_price=1000.0, samples_count=3),
        DummyMonthlyAverage(month_ref="2026-02", avg_price=1100.0, samples_count=2),
    ]

    out = service.get_consolidated_price(brand_id=2, model_id=11, year_model=2024, region="DF")
    assert out is not None

    assert out["current_price"] == 1100.0
    assert out["current_month"] == "2026-02"
    assert out["samples"] == 2

    df = out["history_df"]
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["Mês", "Preço Médio", "Amostras"]
    assert df.to_dict(orient="records") == [
        {"Mês": "2026-01", "Preço Médio": 1000.0, "Amostras": 3},
        {"Mês": "2026-02", "Preço Médio": 1100.0, "Amostras": 2},
    ]

    # Esperado: 1 log por consulta (SUCCESS com região)
    assert fake_repo.logs == [(2, 11, 2024, "SUCCESS", "DF")]
