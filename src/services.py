from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd

from src.repositories import CarRepository

class CarService:
    def __init__(self, db: Session):
        self.repository = CarRepository(db)

    def list_brands(self) -> Dict[str, int]:
        """Retorna um dicionário {Nome: ID} das marcas."""
        brands = self.repository.get_brands()
        return {b.name: b.id for b in brands}

    def list_models(self, brand_id: int) -> Dict[str, int]:
        """Retorna modelos de uma marca específica."""
        models = self.repository.get_models_by_brand(brand_id)
        return {m.name: m.id for m in models}

    def list_years(self, model_id: int) -> List[int]:
        """Retorna anos disponíveis para um modelo."""
        return self.repository.get_years_by_model(model_id)

    def get_consolidated_price(self, brand_id: int, model_id: int, year_model: int) -> Dict[str, Any]:
        """
        Retorna o KPI principal (último preço) e o histórico para gráficos.
        Registra log automaticamente.
        """
        history = self.repository.get_price_history(model_id, year_model)
        
        if not history:
            self.repository.create_log(brand_id, model_id, year_model, "NO_RESULT")
            return None

        # Preparar dados para o Front
        df = pd.DataFrame([
            {"Mês": h.month_ref, "Preço Médio": h.avg_price, "Amostras": h.samples_count}
            for h in history
        ])
        
        latest = history[-1]
        
        self.repository.create_log(brand_id, model_id, year_model, "SUCCESS")
        
        return {
            "current_price": latest.avg_price,
            "current_month": latest.month_ref,
            "samples": latest.samples_count,
            "history_df": df
        }