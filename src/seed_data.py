import random
from datetime import datetime, timedelta
from sqlalchemy import text
from src.database import SessionLocal, engine, Base
from src.models import Brand, Model, PriceCollection

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

def seed_database():
    print("🚀 Iniciando Seed Otimizado (Volume Alto)...")
    
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
        print("Gerando histórico de 13 meses com alta densidade...")
        collections = []
        today = datetime.now()
        
        for model_id, base_price in models_list:
            for region in REGIONS:
                # Últimos 13 meses para garantir gráficos cheios
                for month_offset in range(13): 
                    ref_date = today - timedelta(days=30 * month_offset)
                    
                    # Aumentei para 15 a 40 coletas por região/mês
                    num_coletas = random.randint(15, 40)
                    
                    for _ in range(num_coletas):
                        day_jitter = random.randint(-10, 10)
                        final_date = ref_date + timedelta(days=day_jitter)
                        
                        # Fatores de Variação de Preço
                        regional_factor = 1.0
                        if region == "SP": regional_factor = 1.03
                        if region == "BA": regional_factor = 0.96
                        
                        # Volatilidade de mercado (depreciação leve no passado)
                        time_factor = 1.0 - (month_offset * 0.005) 
                        
                        volatility = random.uniform(0.95, 1.05)
                        final_price = base_price * regional_factor * time_factor * volatility
                        
                        c = PriceCollection(
                            model_id=model_id,
                            year_model=2024,
                            price=final_price,
                            region=region,
                            collected_at=final_date
                        )
                        collections.append(c)
        
        # Salva em lotes maiores
        print(f"Salvando {len(collections)} registros...")
        for i in range(0, len(collections), 2000):
            db.add_all(collections[i:i+2000])
            db.commit()
            print(f"Lote {i} processado...")
            
        print("✅ Banco populado com sucesso!")

    except Exception as e:
        print(e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()