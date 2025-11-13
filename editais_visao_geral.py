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

# Renomear as colunas de df_chamadas
df_chamadas = df_chamadas.rename(columns={
    "codigo_chamada": "Código",
    "nome_chamada": "Nome",
    "data_lancamento": "Data de Lançamento",
    "edital": "Edital",
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




# --- Função auxiliar para pluralização ---
def pluralizar(qtd, singular, plural):
    return f"{qtd} {singular if qtd == 1 else plural}"


# --- FILTROS ---
with st.expander("**Filtros**"):

    col_filtros = st.columns(4)

    with col_filtros[0]:
        filtro_edital = st.selectbox(
            "Edital:",
            options=["Todos"] + sorted(df_editais["Código"].unique().tolist()),
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
df_editais_filtrado = df_editais.copy()
df_chamadas_filtrado = df_chamadas.copy()
df_parceiros_filtrado = df_parceiros.copy()
df_financiadores_filtrado = df_financiadores.copy()


# --- FILTRO POR EDITAL ---
if filtro_edital != "Todos":
    # Edital selecionado
    df_editais_filtrado = df_editais[df_editais["Código"] == filtro_edital]

    # Chamadas relacionadas
    df_chamadas_filtrado = df_chamadas[df_chamadas["Edital"] == filtro_edital]

    # Parceiros e financiadores relacionados
    parceiros_rel = df_editais_filtrado["Parceiros"].explode().dropna().unique().tolist()
    financiadores_rel = df_editais_filtrado["Financiadores"].explode().dropna().unique().tolist()

    df_parceiros_filtrado = df_parceiros[df_parceiros["Sigla"].isin(parceiros_rel)]
    df_financiadores_filtrado = df_financiadores[df_financiadores["Sigla"].isin(financiadores_rel)]


# --- FILTRO POR CHAMADA ---
elif filtro_chamada != "Todas":
    df_chamadas_filtrado = df_chamadas[df_chamadas["Código"] == filtro_chamada]

    edital_rel = df_chamadas_filtrado["Edital"].iloc[0]
    df_editais_filtrado = df_editais[df_editais["Código"] == edital_rel]

    parceiros_rel = df_editais_filtrado["Parceiros"].explode().dropna().unique().tolist()
    financiadores_rel = df_editais_filtrado["Financiadores"].explode().dropna().unique().tolist()

    df_parceiros_filtrado = df_parceiros[df_parceiros["Sigla"].isin(parceiros_rel)]
    df_financiadores_filtrado = df_financiadores[df_financiadores["Sigla"].isin(financiadores_rel)]


# --- FILTRO POR PARCEIRO ---
elif filtro_parceiro != "Todos":
    df_editais_filtrado = df_editais[
        df_editais["Parceiros"].apply(lambda x: filtro_parceiro in x if isinstance(x, list) else False)
    ]

    codigos_editais_rel = df_editais_filtrado["Código"].unique().tolist()
    df_chamadas_filtrado = df_chamadas[df_chamadas["Edital"].isin(codigos_editais_rel)]

    df_parceiros_filtrado = df_parceiros[df_parceiros["Sigla"] == filtro_parceiro]

    financiadores_rel = df_editais_filtrado["Financiadores"].explode().dropna().unique().tolist()
    df_financiadores_filtrado = df_financiadores[df_financiadores["Sigla"].isin(financiadores_rel)]


# --- FILTRO POR FINANCIADOR ---
elif filtro_financiador != "Todos":
    df_editais_filtrado = df_editais[
        df_editais["Financiadores"].apply(lambda x: filtro_financiador in x if isinstance(x, list) else False)
    ]

    codigos_editais_rel = df_editais_filtrado["Código"].unique().tolist()
    df_chamadas_filtrado = df_chamadas[df_chamadas["Edital"].isin(codigos_editais_rel)]

    parceiros_rel = df_editais_filtrado["Parceiros"].explode().dropna().unique().tolist()
    df_parceiros_filtrado = df_parceiros[df_parceiros["Sigla"].isin(parceiros_rel)]

    df_financiadores_filtrado = df_financiadores[df_financiadores["Sigla"] == filtro_financiador]


# --- EXIBIÇÃO DOS DATAFRAMES ---

st.write('')

# EDITAIS ------------------------------------------------------
st.subheader(pluralizar(len(df_editais_filtrado), "edital", "editais"))
st.dataframe(
    df_editais_filtrado,
    hide_index=True,
    column_order=['Código', 'Nome', 'Data de Lançamento', 'Parceiros', 'Financiadores']
)
st.write('')

# CHAMADAS ------------------------------------------------------
st.subheader(pluralizar(len(df_chamadas_filtrado), "chamada", "chamadas"))
st.dataframe(
    df_chamadas_filtrado,
    hide_index=True,
    column_order=['Código', 'Nome', 'Data de Lançamento', 'Edital']
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




















# # --- Função auxiliar para pluralização ---
# def pluralizar(qtd, singular, plural):
#     return f"{qtd} {singular if qtd == 1 else plural}"





# # --- FILTROS ---

# with st.expander("**Filtros**"):


#     col_filtros = st.columns(4)

#     with col_filtros[0]:
#         filtro_edital = st.selectbox(
#             "Edital:",
#             options=[""] + sorted(df_editais["Código"].unique().tolist()),
#             index=0
#         )

#     with col_filtros[1]:
#         filtro_chamada = st.selectbox(
#             "Chamada:",
#             options=[""] + sorted(df_chamadas["Código"].unique().tolist()),
#             index=0
#         )

#     with col_filtros[2]:
#         filtro_parceiro = st.selectbox(
#             "Parceiro:",
#             options=[""] + sorted(df_parceiros["Sigla"].unique().tolist()),
#             index=0
#         )

#     with col_filtros[3]:
#         filtro_financiador = st.selectbox(
#             "Financiador:",
#             options=[""] + sorted(df_financiadores["Sigla"].unique().tolist()),
#             index=0
#         )


# # --- Inicializa dataframes filtrados ---
# df_editais_filtrado = df_editais.copy()
# df_chamadas_filtrado = df_chamadas.copy()
# df_parceiros_filtrado = df_parceiros.copy()
# df_financiadores_filtrado = df_financiadores.copy()


# # --- FILTRO POR EDITAL ---
# if filtro_edital:
#     # Edital selecionado
#     df_editais_filtrado = df_editais[df_editais["Código"] == filtro_edital]

#     # Chamadas relacionadas
#     df_chamadas_filtrado = df_chamadas[df_chamadas["Edital"] == filtro_edital]

#     # Parceiros e financiadores relacionados
#     parceiros_rel = df_editais_filtrado["Parceiros"].explode().dropna().unique().tolist()
#     financiadores_rel = df_editais_filtrado["Financiadores"].explode().dropna().unique().tolist()

#     df_parceiros_filtrado = df_parceiros[df_parceiros["Sigla"].isin(parceiros_rel)]
#     df_financiadores_filtrado = df_financiadores[df_financiadores["Sigla"].isin(financiadores_rel)]


# # --- FILTRO POR CHAMADA ---
# elif filtro_chamada:
#     # Chamada selecionada
#     df_chamadas_filtrado = df_chamadas[df_chamadas["Código"] == filtro_chamada]

#     # Edital relacionado à chamada
#     edital_rel = df_chamadas_filtrado["Edital"].iloc[0]
#     df_editais_filtrado = df_editais[df_editais["Código"] == edital_rel]

#     # Parceiros e financiadores relacionados ao edital dessa chamada
#     parceiros_rel = df_editais_filtrado["Parceiros"].explode().dropna().unique().tolist()
#     financiadores_rel = df_editais_filtrado["Financiadores"].explode().dropna().unique().tolist()

#     df_parceiros_filtrado = df_parceiros[df_parceiros["Sigla"].isin(parceiros_rel)]
#     df_financiadores_filtrado = df_financiadores[df_financiadores["Sigla"].isin(financiadores_rel)]


# # --- FILTRO POR PARCEIRO ---
# elif filtro_parceiro:
#     # Editais que têm o parceiro
#     df_editais_filtrado = df_editais[
#         df_editais["Parceiros"].apply(lambda x: filtro_parceiro in x if isinstance(x, list) else False)
#     ]

#     # Chamadas relacionadas a esses editais
#     codigos_editais_rel = df_editais_filtrado["Código"].unique().tolist()
#     df_chamadas_filtrado = df_chamadas[df_chamadas["Edital"].isin(codigos_editais_rel)]

#     # Apenas o parceiro selecionado
#     df_parceiros_filtrado = df_parceiros[df_parceiros["Sigla"] == filtro_parceiro]

#     # Financiadores relacionados a esses editais
#     financiadores_rel = df_editais_filtrado["Financiadores"].explode().dropna().unique().tolist()
#     df_financiadores_filtrado = df_financiadores[df_financiadores["Sigla"].isin(financiadores_rel)]


# # --- FILTRO POR FINANCIADOR ---
# elif filtro_financiador:
#     # Editais que têm o financiador
#     df_editais_filtrado = df_editais[
#         df_editais["Financiadores"].apply(lambda x: filtro_financiador in x if isinstance(x, list) else False)
#     ]

#     # Chamadas relacionadas a esses editais
#     codigos_editais_rel = df_editais_filtrado["Código"].unique().tolist()
#     df_chamadas_filtrado = df_chamadas[df_chamadas["Edital"].isin(codigos_editais_rel)]

#     # Parceiros relacionados a esses editais
#     parceiros_rel = df_editais_filtrado["Parceiros"].explode().dropna().unique().tolist()
#     df_parceiros_filtrado = df_parceiros[df_parceiros["Sigla"].isin(parceiros_rel)]

#     # Apenas o financiador selecionado
#     df_financiadores_filtrado = df_financiadores[df_financiadores["Sigla"] == filtro_financiador]


# # --- EXIBIÇÃO DOS DATAFRAMES ---

# st.write('')

# # EDITAIS ------------------------------------------------------
# st.subheader(pluralizar(len(df_editais_filtrado), "edital", "editais"))
# st.dataframe(
#     df_editais_filtrado,
#     hide_index=True,
#     column_order=['Código', 'Nome', 'Data de Lançamento', 'Parceiros', 'Financiadores']
# )
# st.write('')

# # CHAMADAS ------------------------------------------------------
# st.subheader(pluralizar(len(df_chamadas_filtrado), "chamada", "chamadas"))
# st.dataframe(
#     df_chamadas_filtrado,
#     hide_index=True,
#     column_order=['Código', 'Nome', 'Data de Lançamento', 'Edital']
# )
# st.write('')

# # PARCEIROS ------------------------------------------------------
# st.subheader(pluralizar(len(df_parceiros_filtrado), "parceiro", "parceiros"))
# st.dataframe(
#     df_parceiros_filtrado,
#     hide_index=True,
#     column_order=['Sigla', 'Nome']
# )
# st.write('')

# # FINANCIADORES ------------------------------------------------------
# st.subheader(pluralizar(len(df_financiadores_filtrado), "financiador", "financiadores"))
# st.dataframe(
#     df_financiadores_filtrado,
#     hide_index=True,
#     column_order=['Sigla', 'Nome']
# )
















# # ==========================================
# # FILTROS GERAIS
# # ==========================================

# st.subheader("Filtros")
# st.write("")

# # Opções com uma opção vazia no início
# lista_editais = [""] + sorted(df_editais["Código"].dropna().unique().tolist())
# lista_chamadas = [""] + sorted(df_chamadas["Código"].dropna().unique().tolist())
# lista_parceiros = [""] + sorted(df_parceiros["Sigla"].dropna().unique().tolist())
# lista_financiadores = [""] + sorted(df_financiadores["Sigla"].dropna().unique().tolist())

# # Layout de filtros em linha
# col1, col2, col3, col4 = st.columns(4)

# with col1:
#     filtro_edital = st.selectbox("Edital:", options=lista_editais, index=0)
# with col2:
#     filtro_chamada = st.selectbox("Chamada:", options=lista_chamadas, index=0)
# with col3:
#     filtro_parceiro = st.selectbox("Parceiro:", options=lista_parceiros, index=0)
# with col4:
#     filtro_financiador = st.selectbox("Financiador (Doador):", options=lista_financiadores, index=0)

# st.divider()

# # ==========================================
# # APLICAÇÃO DOS FILTROS
# # ==========================================

# df_editais_filtrado = df_editais.copy()
# df_chamadas_filtrado = df_chamadas.copy()

# # Filtro por Edital (Código)
# if filtro_edital:
#     df_editais_filtrado = df_editais_filtrado[df_editais_filtrado["Código"] == filtro_edital]
#     df_chamadas_filtrado = df_chamadas_filtrado[df_chamadas_filtrado["Edital"] == filtro_edital]

# # Filtro por Chamada (Código)
# if filtro_chamada:
#     df_chamadas_filtrado = df_chamadas_filtrado[df_chamadas_filtrado["Código"] == filtro_chamada]

# # Filtro por Parceiro
# if filtro_parceiro:
#     df_editais_filtrado = df_editais_filtrado[
#         df_editais_filtrado["Parceiros"].apply(lambda x: filtro_parceiro in (x if isinstance(x, list) else [x]))
#     ]

# # Filtro por Financiador
# if filtro_financiador:
#     df_editais_filtrado = df_editais_filtrado[
#         df_editais_filtrado["Financiadores"].apply(lambda x: filtro_financiador in (x if isinstance(x, list) else [x]))
#     ]

# # ==========================================
# # TABELAS
# # ==========================================

# # Função para pluralizar dinamicamente
# def pluralizar(qtd, singular, plural):
#     return f"{qtd} {singular if qtd == 1 else plural}"

# # --- EDITAIS ---
# qtd_editais = len(df_editais_filtrado)
# st.subheader(pluralizar(qtd_editais, "edital", "editais"))
# st.write('')

# # Converte listas Parceiros e Financiadores em strings separadas por vírgula e espaço
# for col in ["Parceiros", "Financiadores"]:
#     if col in df_editais_filtrado.columns:
#         df_editais_filtrado[col] = df_editais_filtrado[col].apply(
#             lambda x: ", ".join(x) if isinstance(x, list) else (x if pd.notna(x) else "")
#         )

# st.dataframe(
#     df_editais_filtrado,
#     hide_index=True,
#     column_order=['Código', 'Nome', 'Data de Lançamento', 'Parceiros', 'Financiadores']
# )

# st.write('')

# # --- CHAMADAS ---
# qtd_chamadas = len(df_chamadas_filtrado)
# st.subheader(pluralizar(qtd_chamadas, "chamada", "chamadas"))
# st.write('')
# st.dataframe(
#     df_chamadas_filtrado,
#     hide_index=True,
#     column_order=['Código', 'Nome', 'Data de Lançamento', 'Edital']
# )

# # --- PARCEIROS ---
# qtd_parceiros = len(df_parceiros)
# st.subheader(pluralizar(qtd_parceiros, "parceiro", "parceiros"))
# st.write('')
# st.dataframe(df_parceiros, hide_index=True, column_order=['Sigla', 'Nome'])

# # --- FINANCIADORES ---
# qtd_financiadores = len(df_financiadores)
# st.subheader(pluralizar(qtd_financiadores, "financiador", "financiadores"))
# st.write('')
# st.dataframe(df_financiadores, hide_index=True, column_order=['Sigla', 'Nome'])













# # EDITAIS ------------------------------------------------------

# st.subheader(f"{len(df_editais)} editais")
# st.write('')

# # Converte listas Parceiros e Financiadores em strings separadas por vírgula e espaço
# for col in ["Parceiros", "Financiadores"]:
#     if col in df_editais.columns:
#         df_editais[col] = df_editais[col].apply(
#             lambda x: ", ".join(x) if isinstance(x, list) else (x if pd.notna(x) else "")
#         )

# # Lista de editais
# st.dataframe(df_editais, hide_index=True, column_order=['Código', 'Nome', 'Data de Lançamento', 'Parceiros', 'Financiadores'],)

# st.write('')




# # CHAMADAS ------------------------------------------------------

# st.subheader(f"{len(df_chamadas)} chamadas")
# st.write('')

# # Lista de chamadas
# st.dataframe(df_chamadas, hide_index=True, column_order=['Código', 'Nome', 'Data de Lançamento', 'Edital'])




# # PARCEIROS ------------------------------------------------------

# st.subheader(f"{len(df_parceiros)} parceiros")
# st.write('')

# # Lista de parceiros
# st.dataframe(df_parceiros, hide_index=True, column_order=['Sigla', 'Nome'])




# # FINANCIADORES ------------------------------------------------------

# st.subheader(f"{len(df_financiadores)} financiadores")
# st.write('')


# # Lista de financiadores
# st.dataframe(df_financiadores, hide_index=True, column_order=['Sigla', 'Nome'])
