import streamlit as st
import plotly.express as px
from src.database import SessionLocal, engine, Base
from src.services import CarService

# --- SETUP INICIAL ---
# Cria as tabelas se não existirem (apenas para dev/inicialização)
Base.metadata.create_all(bind=engine)

st.set_page_config(
    page_title="CarFlow - Consulta FIPE",
    page_icon="🟣", # Roxo para seguir identidade visual
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INJEÇÃO DE DEPENDÊNCIA ---
def get_service():
    db = SessionLocal()
    return CarService(db)

service = get_service()

# --- CSS CUSTOMIZADO ---
st.markdown("""
<style>
    .stAppHeader {background-color: #5b2c6f;} 
    h1, h2, h3 { color: #5b2c6f; }
    .metric-value { font-weight: bold; color: #5b2c6f; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (FILTROS) ---
with st.sidebar:
    # Logo do Projeto
    st.image("docs/assets/images/logo.png", use_container_width=True)
    st.header("Filtros de Pesquisa")

    # 1. Marca
    brands_map = service.list_brands()
    selected_brand_name = st.selectbox("Selecione a Marca", options=list(brands_map.keys()) if brands_map else [])
    
    selected_model_name = None
    selected_year = None

    # 2. Modelo (Cascata)
    if selected_brand_name:
        brand_id = brands_map[selected_brand_name]
        models_map = service.list_models(brand_id)
        selected_model_name = st.selectbox("Selecione o Modelo", options=list(models_map.keys()))

        # 3. Ano (Cascata)
        if selected_model_name:
            model_id = models_map[selected_model_name]
            years_list = service.list_years(model_id)
            selected_year = st.selectbox("Selecione o Ano", options=years_list)

# --- CORPO PRINCIPAL (RESULTADOS) ---
st.title("🚗 Consulta de Preços Consolidados")
st.markdown("---")

if selected_year and selected_model_name:
    # Busca dados via serviço
    result = service.get_consolidated_price(
        brand_id=brands_map[selected_brand_name], 
        model_id=models_map[selected_model_name], 
        year_model=selected_year
    )

    if result:
        # Layout de Colunas para KPIs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label=f"Preço Médio ({result['current_month']})", 
                value=f"R$ {result['current_price']:,.2f}",
                delta="Baseado em coletas reais"
            )
        with col2:
            st.metric(label="Amostras Consideradas", value=result['samples'])
        with col3:
            st.metric(label="Ano Modelo", value=selected_year)

        # Gráfico de Histórico
        st.subheader("📈 Evolução de Preço (Últimos 12 meses)")
        df_history = result['history_df']
        
        fig = px.line(
            df_history, 
            x="Mês", 
            y="Preço Médio", 
            markers=True,
            title=f"Histórico: {selected_brand_name} {selected_model_name}",
            color_discrete_sequence=["#5b2c6f"] # Roxo
        )
        fig.update_layout(yaxis_tickprefix="R$ ")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nenhum dado consolidado encontrado para os filtros selecionados.")

else:
    st.info("👈 Utilize a barra lateral para selecionar Marca, Modelo e Ano.")