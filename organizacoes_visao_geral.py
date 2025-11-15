import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao # Funções personalizadas
import pandas as pd
# import locale


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()


col_projetos = db["projetos"]
df_projetos = pd.DataFrame(list(col_projetos.find()))

col_organizacoes = db["organizacoes"]
df_organizacoes = pd.DataFrame(list(col_organizacoes.find()))

# col_chamadas = db["chamadas"]
# df_chamadas = pd.DataFrame(list(col_chamadas.find()))

# col_direcoes = db["direcoes_estrategicas"]
# df_direcoes = pd.DataFrame(list(col_direcoes.find()))

# col_publicos = db["publicos"]
# df_publicos = pd.DataFrame(list(col_publicos.find()))






# ###########################################################################################################
# # CONFIGURAÇÃO DE LOCALE
# ###########################################################################################################


# # CONFIGURAÇÃO DE LOCALIDADE PARA PORTUGUÊS (Ajuste conforme seu SO)
# try:
#     # Tenta a configuração comum em sistemas Linux/macOS
#     locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
# except locale.Error:
#     try:
#         # Tenta a configuração comum em alguns sistemas Windows
#         locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
#     except locale.Error:
#         # Se falhar, usa a configuração padrão (geralmente inglês)
#         print("Aviso: Não foi possível definir a localidade para Português. Usando a localidade padrão.")





###########################################################################################################
# FUNÇÕES
###########################################################################################################






###########################################################################################################
# TRATAMENTO DE DADOS   
###########################################################################################################



# ---- Contagem de projetos por organização ----
contagem_projetos = df_projetos["organizacao"].value_counts()

# ---- Merge para adicionar coluna de contagem ----
df_organizacoes = df_organizacoes.merge(
    contagem_projetos.rename("quantidade_projetos"),
    left_on="sigla_organizacao",
    right_index=True,
    how="left"
)

# ---- Organizações sem projeto ficam com 0 ----
df_organizacoes["quantidade_projetos"] = (
    df_organizacoes["quantidade_projetos"].fillna(0).astype(int)
)


###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################


# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Organizações")

st.write('')
st.write('')

# Contagem de organizações
st.write(f"**{df_organizacoes['sigla_organizacao'].nunique()} organizações cadastradas**")
st.write('')

st.dataframe(df_organizacoes, 
             column_order=["sigla_organizacao", "nome_organizacao", "cnpj", "quantidade_projetos"], 
             hide_index=True,
             column_config={
                 "sigla_organizacao": st.column_config.Column(
                     label="Sigla",
                     width="small" 
                 ),
                 "nome_organizacao": st.column_config.Column(
                     label="Nome",
                     width="large" 
                 ),
                 "cnpj": st.column_config.Column(
                     label="CNPJ", 
                     width="small" 
                 ),
                 "quantidade_projetos": st.column_config.Column(
                     label="Quantidade de Projetos", 
                     width="small" 
                 )
             })

