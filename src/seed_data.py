import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.database import SessionLocal, engine, Base
from src.models import Brand, Model, PriceCollection

# Listas de Dados Fictícios (Inspirados na FIPE)
BRANDS_DATA = [
    {"name": "Toyota"}, 
    {"name": "Honda"}, 
    {"name": "Ford"}, 
    {"name": "Chevrolet"}, 
    {"name": "Volkswagen"}
]

MODELS_DATA = {
    "Toyota": [
        {"name": "Corolla XEi 2.0", "type": "Carro"},
        {"name": "Hilux CD 4x4", "type": "Caminhonete"},
        {"name": "Yaris Hatch", "type": "Carro"}
    ],
    "Honda": [
        {"name": "Civic Touring 1.5 Turbo", "type": "Carro"},
        {"name": "HR-V EXL", "type": "Carro"},
        {"name": "CR-V", "type": "Carro"}
    ],
    "Ford": [
        {"name": "Ranger Limited", "type": "Caminhonete"},
        {"name": "Mustang GT", "type": "Carro"},
        {"name": "Bronco Sport", "type": "Carro"}
    ],
    "Chevrolet": [
        {"name": "Onix Plus", "type": "Carro"},
        {"name": "Tracker RS", "type": "Carro"},
        {"name": "S10 High Country", "type": "Caminhonete"}
    ],
    "Volkswagen": [
        {"name": "Polo Highline", "type": "Carro"},
        {"name": "T-Cross Comfortline", "type": "Carro"},
        {"name": "Nivus", "type": "Carro"}
    ]
}

REGIONS = ["SP", "RJ", "MG", "RS", "PR", "BA", "DF"]

def seed_database():
    # Recria tabelas para garantir schema novo
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 1. Inserir Marcas
        if db.query(Brand).count() == 0:
            print("Inserindo Marcas...")
            brands_db = {}
            for brand_info in BRANDS_DATA:
                brand = Brand(name=brand_info["name"])
                db.add(brand)
                db.commit()
                db.refresh(brand)
                brands_db[brand.name] = brand.id
            
            # 2. Inserir Modelos
            print("Inserindo Modelos...")
            models_ids = []
            for brand_name, models_list in MODELS_DATA.items():
                brand_id = brands_db.get(brand_name)
                for model_info in models_list:
                    model = Model(
                        name=model_info["name"],
                        brand_id=brand_id,
                        vehicle_type=model_info["type"]
                    )
                    db.add(model)
                    db.commit()
                    db.refresh(model)
                    models_ids.append(model.id)

            # 3. Gerar Coletas de Preço (PriceCollection)
            # Simula dados dos últimos 6 meses
            print("Gerando Manteiga (Dados de Coleta)...")
            today = datetime.now()
            collections = []
            
            for _ in range(3000): # 3000 coletas simuladas
                model_id_choice = random.choice(models_ids)
                
                # Preço base aleatório entre 80k e 250k
                base_price = random.uniform(80000, 250000)
                
                # Data aleatória nos últimos 180 dias
                days_ago = random.randint(0, 180)
                collected_date = today - timedelta(days=days_ago)
                
                # Ano do modelo (2020 a 2024)
                year_mod = random.choice([2020, 2021, 2022, 2023, 2024])
                
                # Ajuste de preço por ano (Aproximação)
                price_adjusted = base_price * (1 + (year_mod - 2020) * 0.05)
                # Variação regional/aleatória (+- 5%)
                price_final = price_adjusted * random.uniform(0.95, 1.05)
                
                collection = PriceCollection(
                    model_id=model_id_choice,
                    year_model=year_mod,
                    price=price_final,
                    region=random.choice(REGIONS),
                    collected_at=collected_date
                )
                collections.append(collection)
                
                # Batch insert a cada 500 para performance
                if len(collections) >= 500:
                    db.add_all(collections)
                    db.commit()
                    collections = []

            if collections:
                db.add_all(collections)
                db.commit()
                
            print("Sucesso! Banco populado.")
        else:
            print("O banco já possui dados. Pulei o Seed.")

    except Exception as e:
        print(f"Erro ao popular banco: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()