import sys
import os

# Adiciona a raiz do projeto ao PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import func, select  # noqa: E402
from src.database import SessionLocal  # noqa: E402
from src.models import PriceCollection, MonthlyAverage, Model  # noqa: E402

def run_monthly_batch():
    """
    Processo Batch que:
    1. Lê a tabela raw (price_collections)
    2. Agrupa por Marca, Modelo, Ano e Mês de Referência
    3. Calcula a Média e Count
    4. Salva/Atualiza na tabela 'monthly_averages'
    """
    db = SessionLocal()
    print("Iniciando processamento mensal Batch...")

    try:
        # Query de Agregação
        # Extrai YYYY-MM do collected_at no Postgres: to_char(collected_at, 'YYYY-MM')
        # Em SQLite seria diferente, mas estamos usando Postgres.
        
        stmt = (
            select(
                # Model needs to be joined to get brand_id? 
                # Actually PriceCollection -> Model -> Brand.
                Model.brand_id,
                PriceCollection.model_id,
                PriceCollection.year_model,
                PriceCollection.region,
                func.to_char(PriceCollection.collected_at, 'YYYY-MM').label("month_ref"),
                func.avg(PriceCollection.price).label("avg_price"),
                func.count(PriceCollection.id).label("samples_count")
            )
            .join(Model, Model.id == PriceCollection.model_id)
            .group_by(
                Model.brand_id,
                PriceCollection.model_id,
                PriceCollection.year_model,
                PriceCollection.region,
                func.to_char(PriceCollection.collected_at, 'YYYY-MM')
            )
        )
        
        results = db.execute(stmt).all()
        
        print(f"Calculadas {len(results)} métricas consolidadas.")

        # OTIMIZAÇÃO: Carregar dados existentes em memória para evitar N+1 queries via rede
        # Isso reduz drasticamente o tempo quando o banco está remoto (Render)
        print("Carregando médias existentes para comparação...")
        existing_records = db.query(MonthlyAverage).all()
        existing_map = {
            (r.model_id, r.year_model, r.region, r.month_ref): r 
            for r in existing_records
        }

        print("Atualizando registros...")
        for row in results:
            # row: (brand_id, model_id, year_model, region, month_ref, avg_price, samples_count)
            brand_id, model_id, year_model, region, month_ref, avg_price, samples_count = row
            
            key = (model_id, year_model, region, month_ref)
            
            if key in existing_map:
                # Atualiza existente (SQLAlchemy detecta a mudança automaticamente)
                record = existing_map[key]
                record.avg_price = avg_price
                record.samples_count = samples_count
            else:
                # Cria novo
                new_avg = MonthlyAverage(
                    brand_id=brand_id,
                    model_id=model_id,
                    year_model=year_model,
                    month_ref=month_ref,
                    region=region,
                    avg_price=avg_price,
                    samples_count=samples_count
                )
                db.add(new_avg)
        
        print("Commitando alterações...")
        db.commit()
        print("Batch Mensal finalizado com sucesso!")
        
    except Exception as e:
        print(f"Erro no Batch: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_monthly_batch()