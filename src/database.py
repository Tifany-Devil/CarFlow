import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Configuração da URL do banco a partir de variáveis de ambiente
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/carflow_db")

# Ajuste para compatibilidade com SQLAlchemy (Render usa postgres:// mas o correto é postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Render e Neon exigem SSL, vamos garantir que a query string tenha sslmode=require
if "render.com" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

# Criação da Engine
engine = create_engine(DATABASE_URL, echo=False)

# Configuração da Sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos ORM
Base = declarative_base()

def get_db():
    """Dependency injection helper para obter a sessão."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
