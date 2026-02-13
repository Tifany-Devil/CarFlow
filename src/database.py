import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Configuração da URL do banco a partir de variáveis de ambiente
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/carflow_db")

# Ajuste para compatibilidade com SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Config SSL para Render/Neon via connect_args (mais seguro que manipular string)
connect_args = {}
if "render.com" in DATABASE_URL:
    connect_args = {"sslmode": "require"}

# Criação da Engine
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

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
