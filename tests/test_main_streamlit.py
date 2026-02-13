from pathlib import Path

import pandas as pd
import pytest


class FakeCarService:
    def __init__(self, db):
        self.calls = []

    def list_brands(self):
        return {"Ford": 2}

    def list_models(self, brand_id: int):
        assert brand_id == 2
        return {"Ka": 11}

    def list_years(self, model_id: int):
        assert model_id == 11
        return [2024]

    def list_regions(self):
        return ["DF", "SP"]

    def get_consolidated_price(self, brand_id: int, model_id: int, year_model: int, region=None):
        self.calls.append(("get_consolidated_price", brand_id, model_id, year_model, region))

        if region is None:
            df = pd.DataFrame(
                [
                    {"Mês": "2026-01", "Preço Médio": 1000.0, "Amostras": 10},
                    {"Mês": "2026-02", "Preço Médio": 1050.0, "Amostras": 12},
                ]
            )
            return {
                "current_price": 1050.0,
                "current_month": "2026-02",
                "samples": 12,
                "history_df": df,
            }

        df = pd.DataFrame(
            [
                {"Mês": "2026-01", "Preço Médio": 1100.0, "Amostras": 3},
                {"Mês": "2026-02", "Preço Médio": 1150.0, "Amostras": 2},
            ]
        )
        return {
            "current_price": 1150.0,
            "current_month": "2026-02",
            "samples": 2,
            "history_df": df,
        }


def _find_streamlit_app_file(project_root: Path) -> Path:
    candidates = []
    for p in project_root.rglob("*.py"):
        if any(x in p.parts for x in (".venv", "venv", "__pycache__", "site-packages", "tests")):
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if ("CarFlow Analytics" in txt) and ("CONSULTAR PREÇO" in txt or "CONSULTAR PRECO" in txt) and (
            "import streamlit as st" in txt
        ):
            candidates.append(p)

    if not candidates:
        raise FileNotFoundError("Não encontrei o arquivo do app Streamlit (CarFlow Analytics / CONSULTAR PREÇO).")

    candidates.sort(key=lambda x: x.stat().st_size)
    return candidates[0]


def _any_rendered_text(at) -> str:
    parts = []
    for coll_name in ("markdown", "text", "title", "header", "subheader", "caption"):
        coll = getattr(at, coll_name, None)
        if not coll:
            continue
        for el in coll:
            v = getattr(el, "value", None) or getattr(el, "body", None) or getattr(el, "text", None)
            if v is not None:
                parts.append(str(v))
    return "\n".join(parts)


def _sidebar_labels(at):
    return [getattr(sb, "label", "") for sb in getattr(at.sidebar, "selectbox", [])]


def _get_history_from_session_state(at):
    stt = getattr(at, "session_state", None)
    if stt and isinstance(stt, dict) and "history" in stt:
        return stt["history"]
    return None


def _assert_no_exception(at, where: str):
    # Nesta versão do Streamlit, exception é ElementList() (vazio quando ok)
    assert len(at.exception) == 0, f"App lançou exceção {where}: {at.exception}"


def test_streamlit_main_flow(monkeypatch):
    pytest.importorskip("streamlit", reason="streamlit não instalado")
    pytest.importorskip("plotly", reason="plotly não instalado")
    pytest.importorskip("streamlit.testing.v1", reason="streamlit.testing.v1 não disponível (atualize streamlit)")

    from streamlit.testing.v1 import AppTest

    import src.services as services_mod
    import src.database as database_mod

    # Não tocar no banco real
    monkeypatch.setattr(database_mod.Base.metadata, "create_all", lambda *a, **k: None, raising=True)
    monkeypatch.setattr(database_mod, "SessionLocal", lambda: object(), raising=True)

    # Service fake
    monkeypatch.setattr(services_mod, "CarService", FakeCarService, raising=True)

    project_root = Path(__file__).resolve().parents[1]
    app_path = _find_streamlit_app_file(project_root)

    at = AppTest.from_file(str(app_path)).run()
    _assert_no_exception(at, "no load")

    labels = _sidebar_labels(at)
    assert "Marca" in labels
    assert "Região" in labels

    at.sidebar.selectbox[0].set_value("Ford")
    at.run()
    _assert_no_exception(at, "após selecionar marca")

    at.sidebar.selectbox[1].set_value("Ka")
    at.run()
    _assert_no_exception(at, "após selecionar modelo")

    at.sidebar.selectbox[2].set_value(2024)
    at.run()
    _assert_no_exception(at, "após selecionar ano")

    at.sidebar.selectbox[3].set_value("DF")
    at.run()
    _assert_no_exception(at, "após selecionar região")

    at.sidebar.button[0].click()
    at.run()
    _assert_no_exception(at, "após clicar consultar")

    rendered = _any_rendered_text(at)
    assert "Análise:" in rendered
    assert "Referência:" in rendered
    # assert len(at.plotly_chart) >= 1 
    assert "Histórico Recente" in rendered

    history = _get_history_from_session_state(at)

    at.sidebar.button[0].click()
    at.run()
    _assert_no_exception(at, "no segundo clique")

    history2 = _get_history_from_session_state(at)

    if history is not None and history2 is not None:
        assert len(history2) == len(history)
        assert history2[0]["Veículo"] == "Ford Ka"
        assert history2[0]["Região"] == "DF"
    else:
        rendered2 = _any_rendered_text(at)
        assert "Análise:" in rendered2
