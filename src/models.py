from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.sql import func
from src.database import Base

class Brand(Base):
    __tablename__ = "brands"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Model(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"))
    name = Column(String, index=True)
    vehicle_type = Column(String) # Carro, Moto, Caminhão

class PriceCollection(Base):
    """Coletas de preços brutas (antes da consolidação)"""
    __tablename__ = "price_collections"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    year_model = Column(Integer)
    price = Column(Float)
    region = Column(String) # Estado ou Região
    collected_at = Column(DateTime(timezone=True), server_default=func.now())

class MonthlyAverage(Base):
    """Tabela consolidada (Otimizada para leitura na consulta pública)"""
    __tablename__ = "monthly_averages"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"))
    model_id = Column(Integer, ForeignKey("models.id"))
    year_model = Column(Integer, index=True)
    month_ref = Column(String, index=True) # Formato YYYY-MM
    region = Column(String, index=True, nullable=True) # Região consolidada
    
    avg_price = Column(Float)
    samples_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class QueryLog(Base):
    """Log de auditoria para consultas realizadas"""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=True)
    model_id = Column(Integer, nullable=True)
    year_model = Column(Integer, nullable=True)
    region = Column(String, nullable=True) # Adicionado para análises regionais
    status = Column(String) # SUCCESS, NO_RESULT, ERROR
    created_at = Column(DateTime(timezone=True), server_default=func.now())