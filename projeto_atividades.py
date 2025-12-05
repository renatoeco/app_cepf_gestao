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

# Indicadores
col_indicadores = db["indicadores"]

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



df_indicadores = pd.DataFrame(
    list(
        col_indicadores.find()
    )
)

# Transformar o id em string
df_indicadores = df_indicadores.copy()
if "_id" in df_indicadores.columns:
    df_indicadores["_id"] = df_indicadores["_id"].astype(str)


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



with indicadores:

    st.write("")

    # --------------------------------------------------
    # PERMISSÃO
    # --------------------------------------------------
    usuario_pode_editar = st.session_state.tipo_usuario in ["admin", "equipe"]

    # Valor padrão
    modo_edicao = False

    # --------------------------------------------------
    # TOGGLE (somente para quem pode)
    # --------------------------------------------------
    if usuario_pode_editar:
        with st.container(horizontal=True, horizontal_alignment="right"):
            modo_edicao = st.toggle(
                "Modo de edição",
                key="editar_indicadores"
            )

    # --------------------------------------------------
    # RENDERIZAÇÃO CONDICIONAL
    # --------------------------------------------------
    if not modo_edicao:


        # -------------------------
        # MODO VISUALIZAÇÃO — INDICADORES
        # -------------------------

        st.write("")

        # Recupera indicadores do projeto
        indicadores_projeto = (
            df_projeto["indicadores"].values[0]
            if "indicadores" in df_projeto.columns
            else []
        )

        if not indicadores_projeto:
            st.info("Nenhum indicador associado a este projeto.")

        else:
            # --------------------------------------------------
            # Mapeia id_indicador -> nome do indicador
            # --------------------------------------------------
            mapa_indicadores = {
                row["_id"]: row["indicador"]
                for _, row in df_indicadores.iterrows()
            }

            dados_tabela = []

            for item in indicadores_projeto:

                id_indicador = item.get("id_indicador")
                valor = item.get("valor")
                descricao = item.get("descricao_contribuicao", "")

                nome_indicador = mapa_indicadores.get(
                    id_indicador,
                    "Indicador não encontrado"
                )

                dados_tabela.append({
                    "Indicadores": nome_indicador,
                    "Contribuição esperada": valor,
                    "Descrição da contribuição": descricao
                })

            df_visualizacao = pd.DataFrame(dados_tabela)

            ui.table(df_visualizacao)








    else:


        # -------------------------
        # MODO EDIÇÃO — INDICADORES
        # -------------------------

        st.write("Selecione os indicadores que serão acompanhados no projeto.")
        st.write("")

        # --------------------------------------------------
        # INICIALIZA / NORMALIZA ESTADO
        # --------------------------------------------------
        if "valores_indicadores" not in st.session_state:

            indicadores_salvos = (
                df_projeto["indicadores"].values[0]
                if "indicadores" in df_projeto.columns
                else []
            )

            estado = {}

            for item in indicadores_salvos:
                estado[item["id_indicador"]] = {
                    "valor": item.get("valor", 0),
                    "descricao": item.get("descricao_contribuicao", "")
                }

            st.session_state.valores_indicadores = estado

        else:
            # NORMALIZA ESTADO ANTIGO (int → dict)
            for k, v in list(st.session_state.valores_indicadores.items()):
                if isinstance(v, int):
                    st.session_state.valores_indicadores[k] = {
                        "valor": v,
                        "descricao": ""
                    }

        # --------------------------------------------------
        # GARANTIA DE DADOS
        # --------------------------------------------------
        if df_indicadores.empty:
            st.info("Não há indicadores cadastrados.")

        else:
            # --------------------------------------------------
            # CABEÇALHO
            # --------------------------------------------------
            col_h1, col_h2, col_h3 = st.columns([5, 2, 3])

            with col_h1:
                st.markdown("**Indicadores do CEPF**")

            with col_h2:
                st.markdown("**Contribuição esperada**")

            with col_h3:
                st.markdown("**Descrição da contribuição esperada**")

            st.divider()

            # --------------------------------------------------
            # LISTAGEM DOS INDICADORES
            # --------------------------------------------------
            for _, row in df_indicadores.sort_values("indicador").iterrows():

                id_indicador = row["_id"]
                nome_indicador = row["indicador"]

                dados_atual = st.session_state.valores_indicadores.get(
                    id_indicador,
                    {"valor": 0, "descricao": ""}
                )

                valor_atual = dados_atual.get("valor", 0)
                descricao_atual = dados_atual.get("descricao", "")

                col_check, col_valor, col_desc = st.columns([5, 2, 3])

                # -------------------------
                # CHECKBOX
                # -------------------------
                with col_check:
                    marcado = st.checkbox(
                        nome_indicador,
                        key=f"chk_{id_indicador}",
                        value=id_indicador in st.session_state.valores_indicadores
                    )

                # -------------------------
                # VALOR NUMÉRICO
                # -------------------------
                with col_valor:
                    if marcado:
                        valor = st.number_input(
                            "",
                            step=1,
                            value=valor_atual,
                            key=f"num_{id_indicador}"
                        )

                # -------------------------
                # DESCRIÇÃO
                # -------------------------
                with col_desc:
                    if marcado:
                        descricao = st.text_area(
                            "",
                            value=descricao_atual,
                            key=f"desc_{id_indicador}",
                            height=80
                        )

                # -------------------------
                # ATUALIZA ESTADO
                # -------------------------
                if marcado:
                    st.session_state.valores_indicadores[id_indicador] = {
                        "valor": valor,
                        "descricao": descricao
                    }
                else:
                    st.session_state.valores_indicadores.pop(id_indicador, None)

                st.divider()

            # --------------------------------------------------
            # BOTÃO SALVAR
            # --------------------------------------------------
            salvar = st.button(
                "Salvar indicadores",
                icon=":material/save:",
                type="primary"
            )

            # --------------------------------------------------
            # VALIDAÇÃO + SALVAMENTO
            # --------------------------------------------------
            if salvar:

                if not st.session_state.valores_indicadores:
                    st.warning("Selecione pelo menos um indicador.")
                    st.stop()

                for dados in st.session_state.valores_indicadores.values():

                    if dados["valor"] <= 0:
                        st.error(
                            "Todos os valores dos indicadores devem ser maiores que zero."
                        )
                        st.stop()

                    if not dados["descricao"].strip():
                        st.error(
                            "A descrição da contribuição esperada não pode estar vazia."
                        )
                        st.stop()

                indicadores_para_salvar = [
                    {
                        "id_indicador": id_indicador,
                        "valor": dados["valor"],
                        "descricao_contribuicao": dados["descricao"].strip()
                    }
                    for id_indicador, dados in st.session_state.valores_indicadores.items()
                ]

                resultado = col_projetos.update_one(
                    {"codigo": codigo_projeto_atual},
                    {
                        "$set": {
                            "indicadores": indicadores_para_salvar
                        }
                    }
                )

                if resultado.matched_count == 1:
                    st.success("Indicadores atualizados com sucesso!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Erro ao salvar indicadores.")













# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()

