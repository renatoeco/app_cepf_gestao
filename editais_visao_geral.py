import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import pandas as pd
import time
import datetime

###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()


col_editais = db["editais"]
df_editais = pd.DataFrame(list(col_editais.find()))

col_chamadas = db["chamadas"]
df_chamadas = pd.DataFrame(list(col_chamadas.find()))

col_parceiros = db["parceiros"]
df_parceiros = pd.DataFrame(list(col_parceiros.find()))

col_financiadores = db["financiadores"]
df_financiadores = pd.DataFrame(list(col_financiadores.find()))

# Define as coleções específicas que serão utilizadas a partir do banco
# col_pessoas = db["pessoas"]


###########################################################################################################
# TRATAMENTO DOS DADOS
###########################################################################################################

# Renomear as colunas de df_editais
df_editais = df_editais.rename(columns={
    "codigo_edital": "Código",
    "nome_edital": "Nome",
    "data_lancamento": "Data de Lançamento",
    "parceiros": "Parceiros",
    "financiadores": "Financiadores"
})

# Converte o ObjectId para string (evita erro do PyArrow)
if "_id" in df_editais.columns:
    df_editais["_id"] = df_editais["_id"].astype(str)

if "_id" in df_chamadas.columns:
    df_chamadas["_id"] = df_chamadas["_id"].astype(str)

if "_id" in df_parceiros.columns:
    df_parceiros["_id"] = df_parceiros["_id"].astype(str)

if "_id" in df_financiadores.columns:
    df_financiadores["_id"] = df_financiadores["_id"].astype(str)




###########################################################################################################
# FUNÇÕES
###########################################################################################################




###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################

# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Visão geral")
st.write('')


# EDITAIS ------------------------------------------------------

st.subheader(f"{len(df_editais)} editais")
st.write('')

# Converte listas Parceiros e Financiadores em strings separadas por vírgula e espaço
for col in ["Parceiros", "Financiadores"]:
    if col in df_editais.columns:
        df_editais[col] = df_editais[col].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else (x if pd.notna(x) else "")
        )

# Lista de editais
st.dataframe(df_editais, hide_index=True, column_order=['Código', 'Nome', 'Data de Lançamento', 'Parceiros', 'Financiadores'],)

st.write('')




# CHAMADAS ------------------------------------------------------

st.subheader(f"{len(df_chamadas)} chamadas")
st.write('')

# Lista de chamadas
st.dataframe(df_chamadas, hide_index=True, column_order=['Código', 'Nome', 'Data de Lançamento', 'Parceiros', 'Financiadores'],)




# PARCEIROS ------------------------------------------------------

st.subheader(f"{len(df_parceiros)} parceiros")
st.write('')

# Lista de parceiros
st.dataframe(df_parceiros, hide_index=True, column_order=['Código', 'Nome', 'Data de Lançamento', 'Parceiros', 'Financiadores'],)




# FINANCIADORES ------------------------------------------------------

st.subheader(f"{len(df_financiadores)} financiadores")
st.write('')


# Lista de financiadores
st.dataframe(df_financiadores, hide_index=True, column_order=['Código', 'Nome', 'Data de Lançamento', 'Parceiros', 'Financiadores'],)
