import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import plotly.graph_objects as go



st.set_page_config(page_title="Armazenamento no BD")






###########################################################################################################
# CARREGAMENTO DO BANCO DE DADOS
###########################################################################################################


db = conectar_mongo_cepf_gestao()






###########################################################################################################
# CONEXÃO COM GOOGLE DRIVE
###########################################################################################################


# Escopo mínimo necessário para Drive
ESCOPO_DRIVE = ["https://www.googleapis.com/auth/drive"]

@st.cache_resource
def obter_servico_drive():
    """
    Retorna o cliente autenticado do Google Drive,
    usando as credenciais armazenadas em st.secrets.
    """
    credenciais = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=ESCOPO_DRIVE
    )
    return build("drive", "v3", credentials=credenciais)








###########################################################################################################
# INTERFACE
###########################################################################################################





# Logo do sidebar
st.logo("images/ieb_logo.svg", size='large')

st.header('Armazenamento do banco de dados')

st.write('')



col1, col2, col3 = st.columns(3)

# Obtém estatísticas do banco
stats = db.command("dbStats")

# Extrai o tamanho total usado (em MB)
usado_mb = stats.get("storageSize", 0) / (1024 * 1024)
capacidade_total_mb = 500
porcentagem_usada = (usado_mb / capacidade_total_mb) * 100

if porcentagem_usada <= 50:
    cor = "green"
elif porcentagem_usada <= 75:
    cor = "yellow"
else:
    cor = "red"

# Velocímetro
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=round(usado_mb, 1),
    number={'suffix': " MB", "font": {"size": 36}, "valueformat": ".1f"},
    gauge={
        'axis': {'range': [0, capacidade_total_mb]},
        'bar': {'color': cor},
        'steps': [
            {'range': [0, capacidade_total_mb*0.5], 'color': 'rgba(0,255,0,0.2)'},
            {'range': [capacidade_total_mb*0.5, capacidade_total_mb*0.75], 'color': 'rgba(255,255,0,0.2)'},
            {'range': [capacidade_total_mb*0.75, capacidade_total_mb], 'color': 'rgba(255,0,0,0.2)'},
        ],
        'threshold': {'line': {'color': cor, 'width': 6}, 'value': usado_mb}
    }
))


fig_gauge.update_layout(
    height=400,
    margin=dict(l=30, r=30, t=60, b=30),
    title="Limite do plano gratuito da nuvem Mongo Atlas: 500 MB"
)

col1.plotly_chart(fig_gauge)

