import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from src.database import SessionLocal, engine, Base
from src.services import CarService

# --- SETUP INICIAL ---
Base.metadata.create_all(bind=engine)

st.set_page_config(
    page_title="CarFlow Analytics",
    page_icon="docs/assets/images/logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INICIALIZAÇÃO DE HISTÓRICO E ESTADO ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_search' not in st.session_state:
    st.session_state.last_search = None

def add_to_history(brand, model, year, region, price):
    # Evita duplicatas consecutivas
    if st.session_state.history and st.session_state.history[0]["Veículo"] == f"{brand} {model}" and st.session_state.history[0]["Região"] == region:
        return

    st.session_state.history.insert(0, {
        "Horário": datetime.now().strftime("%H:%M"),
        "Veículo": f"{brand} {model}",
        "Ano": year,
        "Região": region,
        "Valor": f"R$ {price:,.2f}"
    })
    if len(st.session_state.history) > 5:
        st.session_state.history.pop()

# --- SERVICES ---
def get_service():
    db = SessionLocal()
    return CarService(db)

service = get_service()

# --- CSS NUCLEAR ---
st.markdown("""
<style>
    /* 1. FORÇA FUNDO BRANCO E FONTES ESCURAS */
    .stApp {
        background-color: #ffffff !important;
        font-family: 'Segoe UI', sans-serif !important;
    }
    
    /* 2. HEADER ROXO ESCURO */
    header[data-testid="stHeader"] {
        background-color: #5b2c6f !important;
    }

    /* 3. BOTÃO CONSULTAR (TEXTO BRANCO OBRIGATÓRIO) */
    div.stButton > button {
        background-color: #5b2c6f !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        height: 50px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
    }
    div.stButton > button p {
        color: #ffffff !important;
    }
    div.stButton > button:hover {
        background-color: #4a235a !important;
        box-shadow: 0 4px 10px rgba(91, 44, 111, 0.3);
    }

    /* 4. CAIXAS KPI (ROXO CLARINHO) */
    .kpi-card {
        background-color: #f4eefc;
        border: 1px solid #e0d4fc;
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 4px 12px rgba(91, 44, 111, 0.05);
        height: 100%;
    }
    
    .kpi-title {
        color: #7f8c8d;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    
    .kpi-value {
        color: #5b2c6f;
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.2;
    }

    /* 5. TABELA DE HISTÓRICO PERSONALIZADA */
    .history-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #eee;
    }
    .history-table th {
        background-color: #f4eefc !important;
        color: #5b2c6f !important;
        font-weight: 700;
        padding: 12px 15px;
        text-align: left;
        font-size: 14px;
        border-bottom: 2px solid #e0d4fc;
    }
    .history-table td {
        padding: 12px 15px;
        border-bottom: 1px solid #f0f0f0;
        color: #333;
        background-color: #ffffff;
        font-size: 14px;
    }

    /* 7. SIDEBAR FORÇADA CLARA (LIGHT MODE) */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        border-right: 1px solid #e0e0e0 !important;
    }
    
    /* Força textos escuros na sidebar, ignorando tema do navegador */
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] li, 
    section[data-testid="stSidebar"] .stMarkdown {
        color: #2c3e50 !important;
    }

    /* Textos Gerais */
    h1, h2, h3, label, p { color: #2c3e50 !important; }

    /* 6. CAIXAS SELETORAS (ROXO CLARO) */
    div[data-baseweb="select"] > div {
        background-color: #f4eefc !important;
        border: 1px solid #e0d4fc !important;
        border-radius: 8px !important;
        color: #5b2c6f !important;
    }
    
    /* Garante que o texto interno fique roxo escuro */
    div[data-baseweb="select"] * {
        color: #5b2c6f !important;
    }
    
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("docs/assets/images/logo.png", width=300)
    except Exception:
        st.title("CarFlow")
        
    st.write("")
    st.markdown("### 🔍 Filtros de Busca")
    
    brands_map = service.list_brands()
    selected_brand_name = st.selectbox("Marca", options=list(brands_map.keys()) if brands_map else [], key="brand_key", placeholder="Selecione...")
    
    selected_model_name = None
    selected_year = None
    
    if selected_brand_name:
        brand_id = brands_map[selected_brand_name]
        models_map = service.list_models(brand_id)
        selected_model_name = st.selectbox("Modelo", options=list(models_map.keys()), key="model_key", placeholder="Selecione...")

    if selected_model_name:
        model_id = models_map[selected_model_name]
        years_list = service.list_years(model_id)
        selected_year = st.selectbox("Ano Modelo", options=years_list, key="year_key")
        
    regions_list = service.list_regions()
    selected_region = st.selectbox("Região", options=["Nacional"] + regions_list, key="region_key")
    
    st.write("")
    st.write("")
    btn_consultar = st.button("CONSULTAR PREÇO", type="primary")

    if btn_consultar and selected_year and selected_model_name:
        st.session_state.last_search = {
            'brand_id': brands_map[selected_brand_name],
            'model_id': models_map[selected_model_name],
            'year_model': selected_year,
            'region': selected_region,
            'brand_name': selected_brand_name,
            'model_name': selected_model_name
        }

# --- LÓGICA PRINCIPAL ---
if st.session_state.last_search:
    
    # Recupera os dados DA ÚLTIMA BUSCA CONFIRMADA (não dos seletores atuais)
    search_data = st.session_state.last_search
    
    # Lógica para Região
    main_region_param = None if search_data['region'] == "Nacional" else search_data['region']
    
    # Busca Principal com os dados CONGELADOS
    main_result = service.get_consolidated_price(
        brand_id=search_data['brand_id'], 
        model_id=search_data['model_id'], 
        year_model=search_data['year_model'],
        region=main_region_param
    )

    # Busca Nacional (se necessário)
    national_result = None
    if search_data['region'] != "Nacional":
        national_result = service.get_consolidated_price(
            brand_id=search_data['brand_id'], 
            model_id=search_data['model_id'], 
            year_model=search_data['year_model'],
            region=None # Vai buscar onde region IS NULL (Média Nacional consolidada)
        )
    
    # Se ainda assim não achar, tenta buscar explicitamente "Nacional" caso o banco salve assim
    if search_data['region'] != "Nacional" and not national_result:
         national_result = service.get_consolidated_price(
            brand_id=search_data['brand_id'], 
            model_id=search_data['model_id'], 
            year_model=search_data['year_model'],
            region="Nacional"
        )

    if main_result:
        label_hist = search_data['region'] if search_data['region'] != "Nacional" else "Nacional"
        # Só adiciona ao histórico se houve clique novo (opcional, ou add sempre que mostrar)
        if btn_consultar:
            add_to_history(search_data['brand_name'], search_data['model_name'], search_data['year_model'], label_hist, main_result['current_price'])

        st.markdown(f"## 📊 Análise: {search_data['brand_name']} {search_data['model_name']}")
        st.markdown(f"Referência: **{main_result['current_month']}**")
        st.write("")

        col1, col2 = st.columns([1, 2])
        
        with col1:
            region_display = search_data['region']
            samples = main_result['samples']
            
            # KPI Card Principal (Roxo Claro)
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Média de Mercado ({region_display})</div>
                <div class="kpi-value">R$ {main_result['current_price']:,.2f}</div>
                <div style="margin-top: 10px; color: #27ae60; font-weight: bold; font-size: 14px;">
                    ✅ Baseado em {samples} coletas reais
                </div>
                <div style="margin-top: 15px; font-size: 13px; color: #666; line-height: 1.5;">
                    Média ponderada para a região <strong>{region_display}</strong>.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Comparativo Nacional
            if national_result:
                diff = main_result['current_price'] - national_result['current_price']
                pct = (diff / national_result['current_price']) * 100
                color_diff = "#e74c3c" if diff > 0 else "#27ae60"
                
                st.markdown(f"""
                <div style="margin-top: 15px; background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 8px;">
                    <div style="font-size: 11px; color: #999; letter-spacing: 1px; font-weight: bold;">COMPARATIVO NACIONAL</div>
                    <div style="font-weight: 800; color: #333; font-size: 20px;">R$ {national_result['current_price']:,.2f}</div>
                    <div style="font-size: 13px; color: {color_diff}; font-weight: bold;">
                        {pct:+.2f}% em relação ao BR
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            # --- GRÁFICO ---
            df_chart = main_result['history_df'].copy()
            # Usa a região DA BUSCA (search_data) e não a selecionada no momento
            df_chart['Local'] = search_data['region']
            
            if national_result:
                df_nat = national_result['history_df'].copy()
                df_nat['Local'] = 'Nacional (BR)'
                df_chart = pd.concat([df_chart, df_nat])

            fig = px.area(
                df_chart, 
                x="Mês", y="Preço Médio", color="Local", markers=True, symbol="Local",
                color_discrete_map={
                    search_data['region']: "#5b2c6f", 
                    "Nacional (BR)": "#95a5a6",
                    "Nacional": "#5b2c6f"
                }
            )

            fig.update_layout(
                title=dict(text="Evolução de Preço (12 Meses)", font=dict(size=18, color="#2c3e50")),
                paper_bgcolor="white", plot_bgcolor="white",
                legend=dict(orientation="h", y=1.1, x=1),
                hovermode="x unified",
                font=dict(color="black"),
                xaxis=dict(title="Mês", tickfont=dict(color="black"), showgrid=False, linecolor="#ddd"),
                yaxis=dict(title="Preço (R$)", tickfont=dict(color="black"), tickprefix="R$ ", gridcolor="#f0f0f0", zeroline=False)
            )
            
            fig.update_traces(stackgroup=None, fill='tozeroy')
            if national_result: 
                fig.update_traces(opacity=0.6)

            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning(f"Sem dados para {search_data['model_name']} em {search_data['region']}.")
        
else:
    # Landing Page
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px; background-color: #f4eefc; border-radius: 20px; margin-top: 20px; border: 1px solid #e0d4fc;">
        <h1 style="color: #5b2c6f !important; font-size: 3rem;">Bem-vindo ao CarFlow</h1>
        <p style="font-size: 1.2rem; color: #5b2c6f;">
            Selecione os filtros ao lado para iniciar.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- HISTÓRICO COM TABELA ROXA (SEM INDENTAÇÃO NO HTML) ---
if st.session_state.history:
    st.write("")
    st.markdown("### 🕒 Histórico Recente")
    
    # IMPORTANTE: HTML colado à esquerda para evitar que vire bloco de código
    html_table = """
<table class="history-table">
    <thead>
        <tr>
            <th>Horário</th>
            <th>Veículo</th>
            <th>Ano</th>
            <th>Região</th>
            <th>Valor</th>
        </tr>
    </thead>
    <tbody>
"""
    
    for row in st.session_state.history:
        # F-string sem indentação para evitar bloco de código markdown
        html_table += f"""
<tr>
    <td>{row['Horário']}</td>
    <td><strong>{row['Veículo']}</strong></td>
    <td>{row['Ano']}</td>
    <td><span style='background:#f4eefc; color:#5b2c6f; padding:3px 8px; border-radius:4px; font-size:12px; font-weight:bold'>{row['Região']}</span></td>
    <td style='color:#5b2c6f; font-weight:bold'>{row['Valor']}</td>
</tr>
"""
    
    html_table += "</tbody></table>"
    st.markdown(html_table, unsafe_allow_html=True)