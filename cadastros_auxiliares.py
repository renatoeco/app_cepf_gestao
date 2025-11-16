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

# Públicos
col_publicos = db["publicos"]


# Direções Estratégicas
col_direcoes = db["direcoes_estrategicas"]


###########################################################################################################
# TRATAMENTO DOS DADOS
###########################################################################################################







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




# ==========================================================
# 1) ABA — PÚBLICOS
# ==========================================================


with abas[0]:

    st.subheader("Públicos")
    st.write('')

    # 1) Carrega documentos da coleção (ordenados)
    dados_publicos = list(
        col_publicos.find({}, {"publico": 1}).sort("publico", 1)
    )

    df_publicos = pd.DataFrame(dados_publicos)

    # Converte ObjectId para string
    if "_id" in df_publicos.columns:
        df_publicos["_id"] = df_publicos["_id"].astype(str)
    else:
        df_publicos["_id"] = ""

    editar_publicos = st.toggle("Editar", key="editar_publicos")
    st.write('')

    # -------------------------
    # MODO VISUALIZAÇÃO
    # -------------------------
    if not editar_publicos:
        if df_publicos.empty:
            st.info("Nenhum público cadastrado.")
        else:
            st.dataframe(
                df_publicos[["publico"]].sort_values("publico"),
                hide_index=True,
                width=500
            )

    # -------------------------
    # MODO EDIÇÃO
    # -------------------------
    else:
        st.write("Edite, adicione e exclua linhas.")

        df_editor = df_publicos[["publico"]].copy()

        df_editado = st.data_editor(
            df_editor,
            num_rows="dynamic",
            hide_index=True,
            key="editor_publicos",
            width=500
        )

        if st.button("Salvar alterações", icon=":material/save:", type="primary"):

            # Normaliza e remove vazios
            df_editado["publico"] = df_editado["publico"].astype(str).str.strip()
            df_editado = df_editado[df_editado["publico"] != ""]

            # Ordena o DataFrame antes de processar
            df_editado = df_editado.sort_values("publico")

            # ===========================
            # VERIFICAÇÃO DE DUPLICADOS
            # ===========================
            lista_editada = df_editado["publico"].tolist()
            duplicados_local = {
                x for x in lista_editada if lista_editada.count(x) > 1
            }

            if duplicados_local:
                st.error(
                    f"Existem valores duplicados na lista: {', '.join(duplicados_local)}"
                )
                st.stop()

            # Banco atual
            valores_orig = set(df_publicos["publico"])
            valores_editados = set(lista_editada)

            # 1) Removidos
            removidos = valores_orig - valores_editados
            for publico in removidos:
                col_publicos.delete_one({"publico": publico})

            # 2) Novos
            novos = valores_editados - valores_orig
            for publico in novos:

                # Verifica valor já cadastrado (proteção adicional)
                if col_publicos.find_one({"publico": publico}):
                    st.error(f"O valor '{publico}' já existe e não será inserido.")
                    st.stop()

                col_publicos.insert_one({"publico": publico})

            st.success("Públicos atualizados com sucesso!")
            st.rerun()









# ==========================================================
# 2) ABA — DIREÇÕES ESTRATÉGICAS
# ==========================================================
with abas[1]:

    st.subheader("Direções Estratégicas")
    st.write('')

    # Carrega documentos da coleção (ordenados)
    dados_direcoes = list(
        col_direcoes.find({}, {"tema": 1}).sort("tema", 1)
    )

    df_direcoes = pd.DataFrame(dados_direcoes)

    # Converte ObjectId para string
    if "_id" in df_direcoes.columns:
        df_direcoes["_id"] = df_direcoes["_id"].astype(str)
    else:
        df_direcoes["_id"] = ""

    editar_direcoes = st.toggle("Editar", key="editar_direcoes")
    st.write('')

    # -------------------------
    # MODO VISUALIZAÇÃO
    # -------------------------
    if not editar_direcoes:
        if df_direcoes.empty:
            st.info("Nenhuma direção estratégica cadastrada.")
        else:
            st.dataframe(
                df_direcoes[["tema"]].sort_values("tema"),
                hide_index=True,
                width=500
            )

    # -------------------------
    # MODO EDIÇÃO
    # -------------------------
    else:
        st.write("Edite, adicione e exclua linhas.")

        df_editor = df_direcoes[["tema"]].copy()

        df_editado = st.data_editor(
            df_editor,
            num_rows="dynamic",
            hide_index=True,
            key="editor_direcoes",
            width=500
        )

        if st.button("Salvar alterações", icon=":material/save:", type="primary"):

            # Normaliza e remove vazios
            df_editado["tema"] = df_editado["tema"].astype(str).str.strip()
            df_editado = df_editado[df_editado["tema"] != ""]

            # Ordena antes de salvar
            df_editado = df_editado.sort_values("tema")

            # ===========================
            # VERIFICAÇÃO DE DUPLICADOS
            # ===========================
            lista_editada = df_editado["tema"].tolist()
            duplicados_local = {
                x for x in lista_editada if lista_editada.count(x) > 1
            }

            if duplicados_local:
                st.error(
                    f"Existem valores duplicados na lista: {', '.join(duplicados_local)}"
                )
                st.stop()

            # Banco atual
            valores_orig = set(df_direcoes["tema"])
            valores_editados = set(lista_editada)

            # 1) Removidos
            removidos = valores_orig - valores_editados
            for tema in removidos:
                col_direcoes.delete_one({"tema": tema})

            # 2) Novos
            novos = valores_editados - valores_orig
            for tema in novos:

                # Verificação extra de duplicidade
                if col_direcoes.find_one({"tema": tema}):
                    st.error(f"O valor '{tema}' já existe e não será inserido.")
                    st.stop()

                col_direcoes.insert_one({"tema": tema})

            st.success("Direções Estratégicas atualizadas com sucesso!")
            st.rerun()






