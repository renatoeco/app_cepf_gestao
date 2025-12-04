import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import pandas as pd
from bson import ObjectId
import time
import streamlit_shadcn_ui as ui


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

# Indicadores
col_indicadores = db["indicadores"]

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



abas = st.tabs(['Públicos', 'Direções Estratégicas', 'Indicadores'])




# ==========================================================
# ABA — PÚBLICOS
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

        if df_publicos.empty:
            st.warning("Ainda não há públicos cadastrados. Você pode adicionar novos abaixo.")

            df_editor = pd.DataFrame(
                {"publico": pd.Series(dtype="str")}
            )
        else:
            df_editor = df_publicos[["publico"]].copy()
            df_editor["publico"] = df_editor["publico"].astype(str)

        df_editado = st.data_editor(
            df_editor,
            num_rows="dynamic",
            hide_index=True,
            key="editor_publicos",
            width=500
        )

        if st.button("Salvar alterações", icon=":material/save:", type="primary"):

            if "publico" not in df_editado.columns:
                st.error("Nenhum dado válido para salvar.")
                st.stop()

            # Normaliza e remove vazios
            df_editado["publico"] = df_editado["publico"].astype(str).str.strip()
            df_editado = df_editado[df_editado["publico"] != ""]

            if df_editado.empty:
                st.warning("Nenhum público informado.")
                st.stop()

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

            valores_orig = (
                set(df_publicos["publico"])
                if "publico" in df_publicos.columns
                else set()
            )
            valores_editados = set(lista_editada)

            # 1) Removidos
            for publico in valores_orig - valores_editados:
                col_publicos.delete_one({"publico": publico})

            # 2) Novos
            for publico in valores_editados - valores_orig:
                if col_publicos.find_one({"publico": publico}):
                    st.error(f"O valor '{publico}' já existe e não será inserido.")
                    st.stop()
                col_publicos.insert_one({"publico": publico})

            st.success("Públicos atualizados com sucesso!")
            time.sleep(3)
            st.rerun()





# ==========================================================
# ABA — DIREÇÕES ESTRATÉGICAS
# ==========================================================

with abas[1]:

    st.subheader("Direções Estratégicas")
    st.write('')

    # 1) Carrega documentos da coleção (ordenados)
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

            df_tabela = (
                df_direcoes[["tema"]]
                .sort_values("tema")
                .reset_index(drop=True)
                .rename(columns={"tema": "Direções estratégicas"})
            )

            ui.table(df_tabela)



    # -------------------------
    # MODO EDIÇÃO
    # -------------------------
    else:
        st.write("Edite, adicione e exclua linhas.")

        if df_direcoes.empty:
            st.warning(
                "Ainda não há direções estratégicas cadastradas. "
                "Você pode adicionar novas abaixo."
            )

            df_editor = pd.DataFrame(
                {"tema": pd.Series(dtype="str")}
            )
        else:
            df_editor = df_direcoes[["tema"]].copy()
            df_editor["tema"] = df_editor["tema"].astype(str)

        df_editado = st.data_editor(
            df_editor,
            num_rows="dynamic",
            hide_index=True,
            key="editor_direcoes",
            # width=500
        )

        if st.button("Salvar alterações", icon=":material/save:", type="primary"):

            if "tema" not in df_editado.columns:
                st.error("Nenhum dado válido para salvar.")
                st.stop()

            # Normaliza e remove vazios
            df_editado["tema"] = df_editado["tema"].astype(str).str.strip()
            df_editado = df_editado[df_editado["tema"] != ""]

            if df_editado.empty:
                st.warning("Nenhuma direção estratégica informada.")
                st.stop()

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

            valores_orig = (
                set(df_direcoes["tema"])
                if "tema" in df_direcoes.columns
                else set()
            )
            valores_editados = set(lista_editada)

            # 1) Removidos
            for tema in valores_orig - valores_editados:
                col_direcoes.delete_one({"tema": tema})

            # 2) Novos
            for tema in valores_editados - valores_orig:
                if col_direcoes.find_one({"tema": tema}):
                    st.error(f"O valor '{tema}' já existe e não será inserido.")
                    st.stop()
                col_direcoes.insert_one({"tema": tema})

            st.success("Direções Estratégicas atualizadas com sucesso!")
            time.sleep(3)
            st.rerun()





# ==========================================================
# ABA — INDICADORES
# ==========================================================

with abas[2]:

    st.subheader("Indicadores")
    st.write('')

    # 1) Carrega documentos da coleção (ordenados)
    dados_indicadores = list(
        col_indicadores.find({}, {"indicador": 1}).sort("indicador", 1)
    )

    df_indicadores = pd.DataFrame(dados_indicadores)

    # Converte ObjectId para string
    if "_id" in df_indicadores.columns:
        df_indicadores["_id"] = df_indicadores["_id"].astype(str)
    else:
        df_indicadores["_id"] = ""

    editar_indicadores = st.toggle("Editar", key="editar_indicadores")
    st.write('')

    # -------------------------
    # MODO VISUALIZAÇÃO
    # -------------------------
    if not editar_indicadores:
        if df_indicadores.empty:
            st.info("Nenhum indicador cadastrado.")
        else:

            df_tabela = (
                df_indicadores[["indicador"]]
                .sort_values("indicador")
                .reset_index(drop=True)
                .rename(columns={"indicador": "Indicadores"})
            )

            ui.table(df_tabela)

    # -------------------------
    # MODO EDIÇÃO
    # -------------------------
    else:
        st.write("Edite, adicione e exclua linhas.")

        if df_indicadores.empty:
            st.warning(
                "Ainda não há indicadores cadastrados. "
                "Você pode adicionar novos abaixo."
            )

            df_editor = pd.DataFrame(
                {"indicador": pd.Series(dtype="str")}
            )
        else:
            df_editor = df_indicadores[["indicador"]].copy()
            df_editor["indicador"] = df_editor["indicador"].astype(str)

        df_editado = st.data_editor(
            df_editor,
            num_rows="dynamic",
            hide_index=True,
            key="editor_indicadores",
            # width=500
        )

        if st.button("Salvar alterações", icon=":material/save:", type="primary"):

            if "indicador" not in df_editado.columns:
                st.error("Nenhum dado válido para salvar.")
                st.stop()

            # Normaliza e remove vazios
            df_editado["indicador"] = (
                df_editado["indicador"]
                .astype(str)
                .str.strip()
            )
            df_editado = df_editado[df_editado["indicador"] != ""]

            if df_editado.empty:
                st.warning("Nenhum indicador informado.")
                st.stop()

            df_editado = df_editado.sort_values("indicador")

            # ===========================
            # VERIFICAÇÃO DE DUPLICADOS
            # ===========================
            lista_editada = df_editado["indicador"].tolist()
            duplicados_local = {
                x for x in lista_editada if lista_editada.count(x) > 1
            }

            if duplicados_local:
                st.error(
                    f"Existem valores duplicados na lista: "
                    f"{', '.join(duplicados_local)}"
                )
                st.stop()

            valores_orig = (
                set(df_indicadores["indicador"])
                if "indicador" in df_indicadores.columns
                else set()
            )
            valores_editados = set(lista_editada)

            # 1) Removidos
            for indicador in valores_orig - valores_editados:
                col_indicadores.delete_one({"indicador": indicador})

            # 2) Novos
            for indicador in valores_editados - valores_orig:
                if col_indicadores.find_one({"indicador": indicador}):
                    st.error(
                        f"O valor '{indicador}' já existe e não será inserido."
                    )
                    st.stop()
                col_indicadores.insert_one({"indicador": indicador})

            st.success("Indicadores atualizados com sucesso!")
            time.sleep(3)
            st.rerun()









# # ==========================================================
# # ABA — INDICADORES
# # ==========================================================
# with abas[2]:

#     st.subheader("Indicadores")
#     st.write("")

#     # Coleção MongoDB
#     col_indicadores = db["indicadores"]

#     # Carrega documentos da coleção (ordenados)
#     dados_indicadores = list(
#         col_indicadores.find({}, {"indicador": 1}).sort("indicador", 1)
#     )

#     df_indicadores = pd.DataFrame(dados_indicadores)

#     # Converte ObjectId para string
#     if "_id" in df_indicadores.columns:
#         df_indicadores["_id"] = df_indicadores["_id"].astype(str)
#     else:
#         df_indicadores["_id"] = ""

#     editar_indicadores = st.toggle("Editar", key="editar_indicadores")
#     st.write("")

#     # -------------------------
#     # MODO VISUALIZAÇÃO
#     # -------------------------
#     if not editar_indicadores:
#         if df_indicadores.empty:
#             st.info("Nenhum indicador cadastrado.")
#         else:
#             st.dataframe(
#                 df_indicadores[["indicador"]].sort_values("indicador"),
#                 hide_index=True,
#                 width=500
#             )

#     # -------------------------
#     # MODO EDIÇÃO
#     # -------------------------
#     else:
#         st.write("Edite, adicione e exclua linhas.")

#         df_editor = df_indicadores[["indicador"]].copy()

#         df_editado = st.data_editor(
#             df_editor,
#             num_rows="dynamic",
#             hide_index=True,
#             key="editor_indicadores",
#             width=500
#         )

#         if st.button(
#             "Salvar alterações",
#             icon=":material/save:",
#             type="primary"
#         ):

#             # Normaliza e remove vazios
#             df_editado["indicador"] = (
#                 df_editado["indicador"]
#                 .astype(str)
#                 .str.strip()
#             )
#             df_editado = df_editado[df_editado["indicador"] != ""]

#             # Ordena antes de salvar
#             df_editado = df_editado.sort_values("indicador")

#             # ===========================
#             # VERIFICAÇÃO DE DUPLICADOS
#             # ===========================
#             lista_editada = df_editado["indicador"].tolist()
#             duplicados_local = {
#                 x for x in lista_editada if lista_editada.count(x) > 1
#             }

#             if duplicados_local:
#                 st.error(
#                     f"Existem valores duplicados na lista: "
#                     f"{', '.join(duplicados_local)}"
#                 )
#                 st.stop()

#             # Banco atual
#             valores_orig = set(df_indicadores["indicador"])
#             valores_editados = set(lista_editada)

#             # 1) Removidos
#             removidos = valores_orig - valores_editados
#             for indicador in removidos:
#                 col_indicadores.delete_one(
#                     {"indicador": indicador}
#                 )

#             # 2) Novos
#             novos = valores_editados - valores_orig
#             for indicador in novos:

#                 # Verificação extra de duplicidade
#                 if col_indicadores.find_one({"indicador": indicador}):
#                     st.error(
#                         f"O valor '{indicador}' já existe "
#                         "e não será inserido."
#                     )
#                     st.stop()

#                 col_indicadores.insert_one(
#                     {"indicador": indicador}
#                 )

#             st.success("Indicadores atualizados com sucesso!")
#             st.rerun()
