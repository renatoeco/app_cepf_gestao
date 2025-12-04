import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao, sidebar_projeto  # Função personalizada para conectar ao MongoDB
import pandas as pd
import streamlit_shadcn_ui as ui
import datetime
import time
import bson

###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Define as coleções específicas que serão utilizadas a partir do banco
# col_pessoas = db["pessoas"]

# Projetos
col_projetos = db["projetos"]


###########################################################################################################
# FUNÇÕES
###########################################################################################################




###########################################################################################################
# TRATAMENTO DE DADOS
###########################################################################################################


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

if df_projeto.empty:
    st.error("Projeto não encontrado no banco de dados.")
    st.stop()


# Transformar o id em string
df_projeto = df_projeto.copy()

if "_id" in df_projeto.columns:
    df_projeto["_id"] = df_projeto["_id"].astype(str)



###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################

# ???????????????????????
# with st.expander("Colunas do projeto"):
#     st.write(df_projeto.columns)


# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')


# Título da página
# st.header("Atividades")


impactos, indicadores, plano_trabalho, monitoramento = st.tabs(["Impactos", "Indicadores", "Plano de trabalho", "Monitoramento"])



# ###################################################################################################
# IMPACTOS
# ###################################################################################################

with impactos:


    @st.dialog("Editar impactos", width="medium")
    def editar_impactos():

        tab_cadastrar, tab_editar = st.tabs(["Cadastrar impacto", "Editar impactos"])

        # ========================================================
        # CADASTRAR IMPACTO
        # ========================================================
        with tab_cadastrar:

            tipo = st.radio(
                "Tipo de impacto",
                ["Longo prazo", "Curto prazo"],
                horizontal=True
            )

            texto_impacto = st.text_area(
                "Descrição do impacto",
                height=150
            )

            if st.button(
                "Salvar impacto",
                type="primary",
                icon=":material/save:"
            ):

                if not texto_impacto.strip():
                    st.warning("O impacto não pode estar vazio.")
                    return

                chave = (
                    "impactos_longo_prazo"
                    if tipo == "Longo prazo"
                    else "impactos_curto_prazo"
                )

                impacto = {
                    "id": str(bson.ObjectId()),
                    "texto": texto_impacto.strip()
                }

                resultado = col_projetos.update_one(
                    {"codigo": st.session_state.projeto_atual},
                    {"$push": {chave: impacto}}
                )

                if resultado.modified_count == 1:
                    st.success("Impacto salvo com sucesso!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Erro ao salvar impacto.")

        # ========================================================
        # EDITAR IMPACTO
        # ========================================================
        with tab_editar:

            tipo = st.radio(
                "Tipo de impacto",
                ["Longo prazo", "Curto prazo"],
                horizontal=True,
                key="tipo_editar_impacto"
            )

            chave = (
                "impactos_longo_prazo"
                if tipo == "Longo prazo"
                else "impactos_curto_prazo"
            )

            impactos = (
                df_projeto[chave].values[0]
                if chave in df_projeto.columns
                else []
            )

            if not impactos:
                st.write("Não há impactos cadastrados.")
                return

            mapa_impactos = {
                f"{i['texto'][:80]}": i
                for i in impactos
            }

            impacto_label = st.selectbox(
                "Selecione o impacto",
                list(mapa_impactos.keys())
            )

            impacto_selecionado = mapa_impactos[impacto_label]

            novo_texto = st.text_area(
                "Editar impacto",
                value=impacto_selecionado["texto"],
                height=150
            )

            if st.button(
                "Salvar alterações",
                type="primary",
                icon=":material/save:"
            ):

                if not novo_texto.strip():
                    st.warning("O impacto não pode estar vazio.")
                    return

                resultado = col_projetos.update_one(
                    {
                        "codigo": st.session_state.projeto_atual,
                        f"{chave}.id": impacto_selecionado["id"],
                    },
                    {
                        "$set": {
                            f"{chave}.$.texto": novo_texto.strip()
                        }
                    }
                )

                if resultado.modified_count == 1:
                    st.success("Impacto atualizado com sucesso!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Erro ao atualizar impacto.")

    st.write('')

    # Toggle do modo de edição

    if st.session_state.tipo_usuario in ["admin", "equipe"]:

        with st.container(horizontal=True, horizontal_alignment="right"):
            modo_edicao = st.toggle("Modo de edição", key="editar_impactos")



    # LISTAGEM DOS IMPACTOS DE LONGO PRAZO E CURTO PRAZO

    col_lp, col_cp = st.columns(2, gap="large")

    with col_lp:
        st.subheader("Impactos de longo prazo")
        st.write('Entre 3 a 5 anos após o final do projeto')

        # Botões de edição só para admin e equipe. Por isso o try.
        try:
            if modo_edicao:

                with st.container(horizontal=True):
                    if st.button("Editar impactos", icon=":material/edit:", type="secondary"):
                        editar_impactos()
        except:
            pass


        st.write('')

        impactos_lp = (
            df_projeto["impactos_longo_prazo"].values[0]
            if "impactos_longo_prazo" in df_projeto.columns
            else []
        )

        if not impactos_lp:
            st.write("Não há impactos de longo prazo cadastrados")
        else:
            for i, impacto in enumerate(impactos_lp, start=1):
                st.write(f"**{i}**. {impacto['texto']}")




    with col_cp:
        st.subheader("Impactos de curto prazo")
        st.write("Durante o projeto ou até o final da subvenção")

        # Botões de edição só para admin e equipe. Por isso o try.
        try:
            if modo_edicao:
                with st.container(horizontal=True):
                    if st.button("Editar impactos", icon=":material/edit:", type="secondary", key="editar_impactos_cp"):
                        editar_impactos()
        except:
            pass


        st.write('')

        impactos_cp = (
            df_projeto["impactos_curto_prazo"].values[0]
            if "impactos_curto_prazo" in df_projeto.columns
            else []
        )

        if not impactos_cp:
            st.write("Não há impactos de curto prazo cadastrados")
        else:
            for i, impacto in enumerate(impactos_cp, start=1):
                st.write(f"**{i}**. {impacto['texto']}")





# ###################################################################################################
# INDICADORES
# ###################################################################################################
















# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()

