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

# Categorias de despesa
col_categorias_despesa = db["categorias_despesa"]

# Corredores
col_corredores = db["corredores"]

# KBAs
col_kbas = db["kbas"]




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



# abas = st.tabs(['Públicos', 'Direções Estratégicas', 'Indicadores'])

abas = st.tabs([
    'Públicos',
    'Direções Estratégicas',
    'Indicadores',
    'Categorias de despesa',
    'Corredores',
    'KBAs'
])




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

        if st.button("Salvar alterações", icon=":material/save:", type="primary", key="salvar_direcoes"):

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

        if st.button("Salvar alterações", icon=":material/save:", type="primary", key="salvar_indicadores"):

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





# ==========================================================
# ABA — CATEGORIAS DE DESPESA
# ==========================================================

with abas[3]:

    st.subheader("Categorias de despesa")
    st.write("")

    # 1) Carrega documentos da coleção (ordenados)
    dados_categorias = list(
        col_categorias_despesa.find({}, {"categoria": 1}).sort("categoria", 1)
    )

    df_categorias = pd.DataFrame(dados_categorias)

    # Converte ObjectId para string
    if "_id" in df_categorias.columns:
        df_categorias["_id"] = df_categorias["_id"].astype(str)
    else:
        df_categorias["_id"] = ""

    editar_categorias = st.toggle("Editar", key="editar_categorias_despesa")
    st.write("")

    # -------------------------
    # MODO VISUALIZAÇÃO
    # -------------------------
    if not editar_categorias:

        if df_categorias.empty:
            st.info("Nenhuma categoria de despesa cadastrada.")
        else:
            df_tabela = (
                df_categorias[["categoria"]]
                .sort_values("categoria")
                .reset_index(drop=True)
                .rename(columns={"categoria": "Categoria de despesa"})
            )

            ui.table(df_tabela)

    # -------------------------
    # MODO EDIÇÃO
    # -------------------------
    else:

        st.write("Edite, adicione e exclua linhas.")

        if df_categorias.empty:
           
            df_editor = pd.DataFrame(
                {"categoria": pd.Series(dtype="str")}
            )
        else:
            df_editor = df_categorias[["categoria"]].copy()
            df_editor["categoria"] = df_editor["categoria"].astype(str)

        df_editado = st.data_editor(
            df_editor,
            num_rows="dynamic",
            hide_index=True,
            key="editor_categorias_despesa",
            width=500
        )

        if st.button(
            "Salvar alterações",
            icon=":material/save:",
            type="primary",
            key="salvar_categorias_despesa"
        ):

            if "categoria" not in df_editado.columns:
                st.error("Nenhum dado válido para salvar.")
                st.stop()

            # Normaliza e remove vazios
            df_editado["categoria"] = (
                df_editado["categoria"]
                .astype(str)
                .str.strip()
            )
            df_editado = df_editado[df_editado["categoria"] != ""]

            if df_editado.empty:
                st.warning("Nenhuma categoria informada.")
                st.stop()

            df_editado = df_editado.sort_values("categoria")

            # ===========================
            # VERIFICAÇÃO DE DUPLICADOS
            # ===========================
            lista_editada = df_editado["categoria"].tolist()
            duplicados_local = {
                x for x in lista_editada if lista_editada.count(x) > 1
            }

            if duplicados_local:
                st.error(
                    "Existem categorias duplicadas: "
                    f"{', '.join(duplicados_local)}"
                )
                st.stop()

            valores_orig = (
                set(df_categorias["categoria"])
                if "categoria" in df_categorias.columns
                else set()
            )
            valores_editados = set(lista_editada)

            # 1) Removidos
            for categoria in valores_orig - valores_editados:
                col_categorias_despesa.delete_one(
                    {"categoria": categoria}
                )

            # 2) Novos
            for categoria in valores_editados - valores_orig:
                if col_categorias_despesa.find_one(
                    {"categoria": categoria}
                ):
                    st.error(
                        f"A categoria '{categoria}' já existe "
                        "e não será inserida."
                    )
                    st.stop()

                col_categorias_despesa.insert_one(
                    {"categoria": categoria}
                )

            st.success("Categorias de despesa atualizadas com sucesso!")
            time.sleep(3)
            st.rerun()







# ==========================================================
# ABA — CORREDORES
# ==========================================================

with abas[4]:

    st.subheader("Corredores")
    st.write("")

    # -----------------------------------
    # Carregar dados da coleção
    # -----------------------------------
    dados_corredores = list(
        col_corredores.find(
            {},
            {"id_corredor": 1, "nome_corredor": 1}
        ).sort("nome_corredor", 1)
    )

    df_corredores = pd.DataFrame(dados_corredores)

    # Garante colunas
    if df_corredores.empty:
        df_corredores = pd.DataFrame(
            columns=["id_corredor", "nome_corredor"]
        )

    # Remove _id do Mongo (não será usado)
    if "_id" in df_corredores.columns:
        df_corredores = df_corredores.drop(columns=["_id"])

    editar_corredores = st.toggle(
        "Editar",
        key="editar_corredores"
    )

    st.write("")

    # ==================================================
    # MODO VISUALIZAÇÃO
    # ==================================================
    if not editar_corredores:

        if df_corredores.empty:
            st.info("Nenhum corredor cadastrado.")
        else:

            df_tabela = (
                df_corredores
                .sort_values("nome_corredor")
                .reset_index(drop=True)
                .rename(columns={
                    "id_corredor": "ID do corredor",
                    "nome_corredor": "Nome do corredor"
                })
            )

            ui.table(df_tabela)

    # ==================================================
    # MODO EDIÇÃO
    # ==================================================
    else:

        st.write("Edite, adicione e exclua corredores.")

        df_editor = df_corredores.copy()

        # Normalização defensiva
        df_editor["id_corredor"] = (
            df_editor["id_corredor"]
            .astype(str)
            .str.strip()
        )
        df_editor["nome_corredor"] = (
            df_editor["nome_corredor"]
            .astype(str)
            .str.strip()
        )

        df_editado = st.data_editor(
            df_editor,
            num_rows="dynamic",
            hide_index=True,
            key="editor_corredores",
            # width=700,
            column_config={
                "id_corredor": st.column_config.TextColumn(
                    "ID do corredor",
                    required=True,
                    help="Identificador único do corredor (texto livre)",
                    width=20
                ),
                "nome_corredor": st.column_config.TextColumn(
                    "Nome do corredor",
                    required=True,
                    width=900
                ),
            }
        )

        if st.button(
            "Salvar alterações",
            icon=":material/save:",
            type="primary"
        ):

            # Remove linhas vazias
            df_salvar = df_editado.copy()

            df_salvar["id_corredor"] = (
                df_salvar["id_corredor"]
                .astype(str)
                .str.strip()
            )
            df_salvar["nome_corredor"] = (
                df_salvar["nome_corredor"]
                .astype(str)
                .str.strip()
            )

            df_salvar = df_salvar[
                (df_salvar["id_corredor"] != "")
                & (df_salvar["nome_corredor"] != "")
            ]

            if df_salvar.empty:
                st.warning("Nenhum corredor válido para salvar.")
                st.stop()

            # ===========================
            # VALIDAÇÃO DE DUPLICADOS
            # ===========================
            duplicados_id = df_salvar[
                df_salvar["id_corredor"].duplicated()
            ]["id_corredor"].tolist()

            duplicados_nome = df_salvar[
                df_salvar["nome_corredor"].duplicated()
            ]["nome_corredor"].tolist()

            if duplicados_id:
                st.error(
                    "IDs de corredor duplicados: "
                    f"{', '.join(set(duplicados_id))}"
                )
                st.stop()

            if duplicados_nome:
                st.error(
                    "Nomes de corredor duplicados: "
                    f"{', '.join(set(duplicados_nome))}"
                )
                st.stop()

            # ===========================
            # SINCRONIZAÇÃO COM O BANCO
            # ===========================
            col_corredores.delete_many({})

            col_corredores.insert_many(
                df_salvar.to_dict(orient="records")
            )

            st.success("Corredores atualizados com sucesso!")
            time.sleep(3)
            st.rerun()






# ==========================================================
# ABA — KBAs
# ==========================================================

with abas[5]:

    st.subheader("KBAs")
    st.write("")

    # -----------------------------------
    # Carregar dados da coleção
    # -----------------------------------
    dados_kbas = list(
        col_kbas.find(
            {},
            {"id_kba": 1, "nome_kba": 1}
        ).sort("nome_kba", 1)
    )

    df_kbas = pd.DataFrame(dados_kbas)

    # Garante colunas
    if df_kbas.empty:
        df_kbas = pd.DataFrame(
            columns=["id_kba", "nome_kba"]
        )

    # Remove _id do Mongo
    if "_id" in df_kbas.columns:
        df_kbas = df_kbas.drop(columns=["_id"])

    editar_kbas = st.toggle(
        "Editar",
        key="editar_kbas"
    )

    st.write("")

    # ==================================================
    # MODO VISUALIZAÇÃO
    # ==================================================
    if not editar_kbas:

        if df_kbas.empty:
            st.info("Nenhuma KBA cadastrada.")
        else:

            df_tabela = (
                df_kbas
                .sort_values("nome_kba")
                .reset_index(drop=True)
                .rename(columns={
                    "id_kba": "ID da KBA",
                    "nome_kba": "Nome da KBA"
                })
            )

            ui.table(df_tabela)

    # ==================================================
    # MODO EDIÇÃO
    # ==================================================
    else:

        st.write("Edite, adicione e exclua KBAs.")

        df_editor = df_kbas.copy()

        # Normalização defensiva
        df_editor["id_kba"] = (
            df_editor["id_kba"]
            .astype(str)
            .str.strip()
        )
        df_editor["nome_kba"] = (
            df_editor["nome_kba"]
            .astype(str)
            .str.strip()
        )

        df_editado = st.data_editor(
            df_editor,
            num_rows="dynamic",
            hide_index=True,
            key="editor_kbas",
            column_config={
                "id_kba": st.column_config.TextColumn(
                    "ID da KBA",
                    required=True,
                    help="Identificador único da KBA (texto livre)",
                    width=20
                ),
                "nome_kba": st.column_config.TextColumn(
                    "Nome da KBA",
                    required=True,
                    width=900
                ),
            }
        )

        if st.button(
            "Salvar alterações",
            icon=":material/save:",
            type="primary",
            key="salvar_kbas"
        ):


            # Remove linhas vazias
            df_salvar = df_editado.copy()

            df_salvar["id_kba"] = (
                df_salvar["id_kba"]
                .astype(str)
                .str.strip()
            )
            df_salvar["nome_kba"] = (
                df_salvar["nome_kba"]
                .astype(str)
                .str.strip()
            )

            df_salvar = df_salvar[
                (df_salvar["id_kba"] != "")
                & (df_salvar["nome_kba"] != "")
            ]

            if df_salvar.empty:
                st.warning("Nenhuma KBA válida para salvar.")
                st.stop()

            # ===========================
            # VALIDAÇÃO DE DUPLICADOS
            # ===========================
            duplicados_id = df_salvar[
                df_salvar["id_kba"].duplicated()
            ]["id_kba"].tolist()

            duplicados_nome = df_salvar[
                df_salvar["nome_kba"].duplicated()
            ]["nome_kba"].tolist()

            if duplicados_id:
                st.error(
                    "IDs de KBA duplicados: "
                    f"{', '.join(set(duplicados_id))}"
                )
                st.stop()

            if duplicados_nome:
                st.error(
                    "Nomes de KBA duplicados: "
                    f"{', '.join(set(duplicados_nome))}"
                )
                st.stop()

            # ===========================
            # SINCRONIZAÇÃO COM O BANCO
            # ===========================
            col_kbas.delete_many({})

            col_kbas.insert_many(
                df_salvar.to_dict(orient="records")
            )

            st.success("KBAs atualizadas com sucesso!")
            time.sleep(3)
            st.rerun()
