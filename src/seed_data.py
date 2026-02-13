import sys
import os

# Adiciona a raiz do projeto ao PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import random  # noqa: E402
from datetime import datetime, timedelta  # noqa: E402
from sqlalchemy import text  # noqa: E402
from src.database import SessionLocal, engine, Base  # noqa: E402
from src.models import Brand, Model, PriceCollection  # noqa: E402

# Catálogo Expandido
MODELS_DATA = {
    "Chevrolet": [("Onix Plus", 95000), ("Tracker RS", 145000), ("S10 High Country", 290000)],
    "Toyota": [("Corolla XEi", 148000), ("Hilux CD", 280000), ("Yaris Hatch", 98000)],
    "Honda": [("Civic Touring", 185000), ("HR-V EXL", 160000), ("City Sedan", 115000)],
    "Volkswagen": [("Polo Highline", 110000), ("Nivus", 135000), ("T-Cross", 140000)],
    "BYD": [("Dolphin", 149800), ("Song Plus", 229800), ("Seal", 296000)],
    "Ford": [("Ranger Limited", 320000), ("Territory", 210000)]
}

REGIONS = ["SP", "RJ", "MG", "RS", "PR", "BA", "DF", "SC", "PE"]
YEARS = [2022, 2023, 2024, 2025] # Anos disponíveis para gerar

def seed_database():
    print("🚀 Iniciando Seed Otimizado (Volume Alto & Anos Variados)...")
    
    # Tenta limpar conexões
    try:
        with engine.connect() as connection:
            connection.execution_options(isolation_level="AUTOCOMMIT")
            connection.execute(text("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = current_database()
                AND pid <> pg_backend_pid();
            """))
    except Exception as e:
        print(f"⚠️ Aviso ao limpar conexões: {e}")

    # Limpeza
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Marcas e Modelos
        models_list = []
        for brand_name, models in MODELS_DATA.items():
            brand = Brand(name=brand_name)
            db.add(brand)
            db.commit()
            db.refresh(brand)
            
            for m_name, base_price in models:
                model = Model(name=m_name, brand_id=brand.id, vehicle_type="Carro")
                db.add(model)
                db.commit()
                db.refresh(model)
                models_list.append((model.id, base_price))

        # 2. Geração Massiva
        print("Gerando histórico...")
        collections = []
        today = datetime.now()
        
        for model_id, base_price in models_list:
            for region in REGIONS:
                for month_offset in range(13): 
                    ref_date = today - timedelta(days=30 * month_offset)
                    
                    # Gera dados para CADA ano disponível
                    for year_model in YEARS:
                        # Menos coletas para anos mais velhos ou muito novos (opcional)
                        num_coletas = random.randint(10, 25)
                        
                        for _ in range(num_coletas):
                            day_jitter = random.randint(-10, 10)
                            final_date = ref_date + timedelta(days=day_jitter)
                            
                            # Fatores de Preço
                            # 1. Região
                            regional_factor = 1.03 if region == "SP" else (0.96 if region == "BA" else 1.0)
                            
                            # 2. Depreciação do Tempo (Mês da coleta)
                            time_factor = 1.0 - (month_offset * 0.005)
                            
                            # 3. Fator do Ano do Modelo (Carro 2025 é mais caro que 2022)
                            # Ex: Se base é 2024, 2025 vale +10%, 2023 vale -10%
                            year_factor = 1.0 + ((year_model - 2024) * 0.10)
                            
                            volatility = random.uniform(0.95, 1.05)
                            
                            final_price = base_price * regional_factor * time_factor * year_factor * volatility
                            
                            c = PriceCollection(
                                model_id=model_id,
                                year_model=year_model, # <--- AGORA É DINÂMICO
                                price=final_price,
                                region=region,
                                collected_at=final_date
                            )
                            collections.append(c)
        
        # Salva em lotes
        print(f"Salvando {len(collections)} registros...")
        for i in range(0, len(collections), 2000):
            db.add_all(collections[i:i+2000])
            db.commit()
            print(f"Lote {i} salvo...")
            
        print("✅ Banco populado com sucesso!")

    except Exception as e:
        print(e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()