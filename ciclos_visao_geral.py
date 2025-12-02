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


col_ciclos = db["ciclos_investimento"]
df_ciclos = pd.DataFrame(list(col_ciclos.find()))

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

# Renomear as colunas de df_ciclos
df_ciclos = df_ciclos.rename(columns={
    "codigo_ciclo": "Código",
    "nome_ciclo": "Nome",
    "data_lancamento": "Data de Lançamento",
    "parceiros": "Parceiros",
    "financiadores": "Financiadores"
})

# Renomear as colunas de df_chamadas
df_chamadas = df_chamadas.rename(columns={
    "codigo_chamada": "Código",
    "nome_chamada": "Nome",
    "data_lancamento": "Data de Lançamento",
    "ciclo_investimento": "Ciclo de investimento",
})

# Renomear as colunas de df_parceiros
df_parceiros = df_parceiros.rename(columns={
    "sigla_parceiro": "Sigla",
    "nome_parceiro": "Nome",
})

# Renomear as colunas de df_financiadores
df_financiadores = df_financiadores.rename(columns={
    "sigla_financiador": "Sigla",
    "nome_financiador": "Nome",
})

# Converte o ObjectId para string (evita erro do PyArrow)
if "_id" in df_ciclos.columns:
    df_ciclos["_id"] = df_ciclos["_id"].astype(str)

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




# --- Função auxiliar para pluralização ---
def pluralizar(qtd, singular, plural):
    return f"{qtd} {singular if qtd == 1 else plural}"


# --- FILTROS ---
with st.expander("**Filtros**"):

    col_filtros = st.columns(4)

    with col_filtros[0]:
        filtro_ciclo = st.selectbox(
            "Ciclo de investimento:",
            options=["Todos"] + sorted(df_ciclos["Código"].unique().tolist()),
            index=0
        )

    with col_filtros[1]:
        filtro_chamada = st.selectbox(
            "Chamada:",
            options=["Todas"] + sorted(df_chamadas["Código"].unique().tolist()),
            index=0
        )

    with col_filtros[2]:
        filtro_parceiro = st.selectbox(
            "Parceiro:",
            options=["Todos"] + sorted(df_parceiros["Sigla"].unique().tolist()),
            index=0
        )

    with col_filtros[3]:
        filtro_financiador = st.selectbox(
            "Financiador:",
            options=["Todos"] + sorted(df_financiadores["Sigla"].unique().tolist()),
            index=0
        )


# --- Inicializa dataframes filtrados ---
df_ciclos_filtrado = df_ciclos.copy()
df_chamadas_filtrado = df_chamadas.copy()
df_parceiros_filtrado = df_parceiros.copy()
df_financiadores_filtrado = df_financiadores.copy()


# --- FILTRO POR CICLO DE INVESTIMENTO ---
if filtro_ciclo != "Todos":
    # Ciclo de investimento selecionado
    df_ciclos_filtrado = df_ciclos[df_ciclos["Código"] == filtro_ciclo]

    # Chamadas relacionadas
    df_chamadas_filtrado = df_chamadas[df_chamadas["Ciclo de investimento"] == filtro_ciclo]

    # Parceiros e financiadores relacionados
    parceiros_rel = df_ciclos_filtrado["Parceiros"].explode().dropna().unique().tolist()
    financiadores_rel = df_ciclos_filtrado["Financiadores"].explode().dropna().unique().tolist()

    df_parceiros_filtrado = df_parceiros[df_parceiros["Sigla"].isin(parceiros_rel)]
    df_financiadores_filtrado = df_financiadores[df_financiadores["Sigla"].isin(financiadores_rel)]


# --- FILTRO POR CHAMADA ---
elif filtro_chamada != "Todas":
    df_chamadas_filtrado = df_chamadas[df_chamadas["Código"] == filtro_chamada]

    ciclo_rel = df_chamadas_filtrado["Ciclo de investimento"].iloc[0]
    df_ciclos_filtrado = df_ciclos[df_ciclos["Código"] == ciclo_rel]

    parceiros_rel = df_ciclos_filtrado["Parceiros"].explode().dropna().unique().tolist()
    financiadores_rel = df_ciclos_filtrado["Financiadores"].explode().dropna().unique().tolist()

    df_parceiros_filtrado = df_parceiros[df_parceiros["Sigla"].isin(parceiros_rel)]
    df_financiadores_filtrado = df_financiadores[df_financiadores["Sigla"].isin(financiadores_rel)]


# --- FILTRO POR PARCEIRO ---
elif filtro_parceiro != "Todos":
    df_ciclos_filtrado = df_ciclos[
        df_ciclos["Parceiros"].apply(lambda x: filtro_parceiro in x if isinstance(x, list) else False)
    ]

    codigos_ciclos_rel = df_ciclos_filtrado["Código"].unique().tolist()
    df_chamadas_filtrado = df_chamadas[df_chamadas["Ciclo de investimento"].isin(codigos_ciclos_rel)]

    df_parceiros_filtrado = df_parceiros[df_parceiros["Sigla"] == filtro_parceiro]

    financiadores_rel = df_ciclos_filtrado["Financiadores"].explode().dropna().unique().tolist()
    df_financiadores_filtrado = df_financiadores[df_financiadores["Sigla"].isin(financiadores_rel)]


# --- FILTRO POR FINANCIADOR ---
elif filtro_financiador != "Todos":
    df_ciclos_filtrado = df_ciclos[
        df_ciclos["Financiadores"].apply(lambda x: filtro_financiador in x if isinstance(x, list) else False)
    ]

    codigos_ciclos_rel = df_ciclos_filtrado["Código"].unique().tolist()
    df_chamadas_filtrado = df_chamadas[df_chamadas["Ciclo de investimento"].isin(codigos_ciclos_rel)]

    parceiros_rel = df_ciclos_filtrado["Parceiros"].explode().dropna().unique().tolist()
    df_parceiros_filtrado = df_parceiros[df_parceiros["Sigla"].isin(parceiros_rel)]

    df_financiadores_filtrado = df_financiadores[df_financiadores["Sigla"] == filtro_financiador]


# --- EXIBIÇÃO DOS DATAFRAMES ---

st.write('')

# CICLOS DE INVESTIMENTO ------------------------------------------------------
st.subheader(pluralizar(len(df_ciclos_filtrado), "ciclo de investimento", "ciclos de investimento"))
st.dataframe(
    df_ciclos_filtrado,
    hide_index=True,
    column_order=['Código', 'Nome', 'Data de Lançamento', 'Parceiros', 'Financiadores']
)
st.write('')

# CHAMADAS ------------------------------------------------------
st.subheader(pluralizar(len(df_chamadas_filtrado), "chamada", "chamadas"))
st.dataframe(
    df_chamadas_filtrado,
    hide_index=True,
    column_order=['Código', 'Nome', 'Data de Lançamento', 'Ciclo de investimento']
)
st.write('')

# PARCEIROS ------------------------------------------------------
st.subheader(pluralizar(len(df_parceiros_filtrado), "parceiro", "parceiros"))
st.dataframe(
    df_parceiros_filtrado,
    hide_index=True,
    column_order=['Sigla', 'Nome']
)
st.write('')

# FINANCIADORES ------------------------------------------------------
st.subheader(pluralizar(len(df_financiadores_filtrado), "financiador", "financiadores"))
st.dataframe(
    df_financiadores_filtrado,
    hide_index=True,
    column_order=['Sigla', 'Nome']
)









