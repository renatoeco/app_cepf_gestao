import streamlit as st
import time
import pandas as pd
import io
import folium
from streamlit_folium import st_folium

from funcoes_auxiliares import (
    conectar_mongo_cepf_gestao,
    sidebar_projeto,
    # ajustar_altura_data_editor,

    # Google Drive
    obter_servico_drive,
    obter_ou_criar_pasta,
    obter_pasta_locais,
    obter_pasta_projeto,
    enviar_arquivo_drive,
    gerar_link_drive
)








###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Coleção de projetos
col_projetos = db["projetos"]






###########################################################################################################
# CARREGAMENTO DE DADOS
###########################################################################################################


# Capturando o código do projeto e os dados do projeto
codigo_projeto_atual = st.session_state.get("projeto_atual")

if not codigo_projeto_atual:
    st.error("Nenhum projeto selecionado.")
    st.stop()


df_projeto = pd.DataFrame(
    list(
        col_projetos.find(
            {"codigo": codigo_projeto_atual}
        )
    )
)




###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################



# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página e identificação
col_titulo, col_identificacao = st.columns([3, 2])

with col_titulo:
    st.header("Fotos")

with col_identificacao:
    st.markdown(
        f"<div style='text-align: right; margin-top: 30px;'>{df_projeto['codigo'].values[0]} - {df_projeto['sigla'].values[0]}</div>",
        unsafe_allow_html=True
    )


st.write('')


# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()