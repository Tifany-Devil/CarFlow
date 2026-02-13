from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import List, Optional

from src.models import Brand, Model, MonthlyAverage, QueryLog

class CarRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_brands(self) -> List[Brand]:
        statement = select(Brand).order_by(Brand.name)
        return self.db.execute(statement).scalars().all()

    def get_models_by_brand(self, brand_id: int) -> List[Model]:
        statement = select(Model).where(Model.brand_id == brand_id).order_by(Model.name)
        return self.db.execute(statement).scalars().all()

    def get_years_by_model(self, model_id: int) -> List[int]:
        # Busca anos distintos disponíveis na tabela consolidada
        statement = (
            select(MonthlyAverage.year_model)
            .where(MonthlyAverage.model_id == model_id)
            .distinct()
            .order_by(desc(MonthlyAverage.year_model))
        )
        return self.db.execute(statement).scalars().all()

    def get_price_history(self, model_id: int, year_model: int) -> List[MonthlyAverage]:
        statement = (
            select(MonthlyAverage)
            .where(
                MonthlyAverage.model_id == model_id,
                MonthlyAverage.year_model == year_model
            )
            .order_by(MonthlyAverage.month_ref)
        )
        return self.db.execute(statement).scalars().all()

    def create_log(self, brand_id: Optional[int], model_id: Optional[int], year_model: Optional[int], status: str):
        log = QueryLog(
            brand_id=brand_id,
            model_id=model_id,
            year_model=year_model,
            status=status
        )
        self.db.add(log)
        self.db.commit()