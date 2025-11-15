import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import pandas as pd
from bson import ObjectId
import time

###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Importa coleções e cria dataframes

# Pessoas
col_pessoas = db["pessoas"]



###########################################################################################################
# TRATAMENTO DOS DADOS
###########################################################################################################

# Busca todos os documentos, mas exclui o campo "senha"
df_pessoas = pd.DataFrame(list(col_pessoas.find({}, {"senha": 0})))

# Converte ObjectId para string
df_pessoas["_id"] = df_pessoas["_id"].astype(str)

# Renomeia as colunas
df_pessoas = df_pessoas.rename(columns={
    "nome_completo": "Nome",
    "tipo_usuario": "Tipo de usuário",
    "tipo_beneficiario": "Tipo de beneficiário",
    "e_mail": "E-mail",
    "telefone": "Telefone",
    "status": "Status",
    "projetos": "Projetos"
})

# Ordena por Nome
df_pessoas = df_pessoas.sort_values(by="Nome")

# Projetos
col_projetos = db["projetos"]
df_projetos = pd.DataFrame(list(col_projetos.find()))
# Converte objectId para string
df_projetos['_id'] = df_projetos['_id'].astype(str)





###########################################################################################################
# Funções
###########################################################################################################





###########################################################################################################
# INTERFACE
###########################################################################################################


# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

st.header('Cadastros auxiliares')

st.write('')



abas = st.tabs(['Públicos', 'Direções Estratégicas'])

with abas[0]:
    st.write('Públicos')

with abas[1]:
    st.write('Direções Estratégicas')



