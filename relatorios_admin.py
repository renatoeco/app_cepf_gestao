import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import pandas as pd
from bson import ObjectId
import time
import streamlit_shadcn_ui as ui
from streamlit_sortables import sort_items
import uuid



###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Importa coleções e cria dataframes

# Beneficiários
col_publicos = db["publicos"]

# Benefícios
col_beneficios = db["beneficios"]

# Direções Estratégicas
# col_direcoes = db["direcoes_estrategicas"]

# Indicadores
# col_indicadores = db["indicadores"]

# Categorias de despesa
col_categorias_despesa = db["categorias_despesa"]

# Corredores
col_corredores = db["corredores"]

# KBAs
col_kbas = db["kbas"]

# Editais
col_editais = db["editais"]



###########################################################################################################
# INTERFACE
###########################################################################################################


# Logo do sidebar
st.logo("images/ieb_logo.svg", size='large')

st.header('Relatórios')

st.write('')
