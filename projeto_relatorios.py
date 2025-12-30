import streamlit as st
import pandas as pd
from funcoes_auxiliares import conectar_mongo_cepf_gestao, sidebar_projeto, ajustar_altura_data_editor
import streamlit_antd_components as sac
import time




###########################################################################################################
# CONFIGURAÇÕES DO STREAMLIT
###########################################################################################################


# Traduzindo o texto do st.file_uploader
# Texto interno
st.markdown("""
<style>
/* Esconde o texto padrão */
[data-testid="stFileUploaderDropzone"] div div::before {
    content: "";
    color: rgba(49, 51, 63, 0.7);
    font-size: 0.9rem;
    font-weight: 400;
    position: absolute;
    top: 50px;              /* fixa no topo */
    left: 50%;
    transform: translate(-50%, 10%);
    pointer-events: none;
}
/* Esconde o texto original */
[data-testid="stFileUploaderDropzone"] div div span {
    visibility: hidden !important;
}
</style>
""", unsafe_allow_html=True)

# Traduzindo Botão do file_uploader
st.markdown("""
<style>
/* Alvo: apenas o botão dentro do componente de upload */
section[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] {
    font-size: 0px !important;   /* esconde o texto original */
    padding-left: 14px !important;
    padding-right: 14px !important;
    min-width: 160px !important;
}
/* Insere o texto traduzido */
section[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"]::after {
    content: "Selecionar arquivo";
    font-size: 14px !important;
    color: inherit;
}
</style>
""", unsafe_allow_html=True)





###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

col_projetos = db["projetos"]

col_editais = db["editais"]



###########################################################################################################
# CARREGAMENTO DOS DADOS
###########################################################################################################

codigo_projeto_atual = st.session_state.projeto_atual

df_projeto = pd.DataFrame(
    list(
        col_projetos.find(
            {"codigo": codigo_projeto_atual}
        )
    )
)

if df_projeto.empty:
    st.error("Projeto não encontrado.")
    st.stop()

projeto = df_projeto.iloc[0]

relatorios = projeto.get("relatorios", [])

###########################################################################################################
# FUNÇÕES
###########################################################################################################


def extrair_atividades(projeto):
    atividades = []

    plano = projeto.get("plano_trabalho", {})
    componentes = plano.get("componentes", [])

    for componente in componentes:
        for entrega in componente.get("entregas", []):
            for atividade in entrega.get("atividades", []):
                atividades.append({
                    "id": atividade.get("id"),
                    "nome": atividade.get("atividade"),
                    "data_inicio": atividade.get("data_inicio"),
                    "data_fim": atividade.get("data_fim"),
                    "componente": componente.get("componente"),
                    "entrega": entrega.get("entrega"),
                })

    return atividades




###########################################################################################################
# TRATAMENTO DOS DADOS
###########################################################################################################

# -------------------------------------------
# CONTROLE DE STEP DO RELATÓRIO
# -------------------------------------------

if "step_relatorio" not in st.session_state:
    st.session_state.step_relatorio = "Atividades"




###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################



# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página e identificação
col_titulo, col_identificacao = st.columns([3, 2])

with col_titulo:
    st.header("Relatórios")

with col_identificacao:
    st.markdown(
        f"<div style='text-align: right; margin-top: 30px;'>{df_projeto['codigo'].values[0]} - {df_projeto['sigla'].values[0]}</div>",
        unsafe_allow_html=True
    )





###########################################################################################################
# UMA ABA PRA CADA RELATÓRIO
###########################################################################################################

steps_relatorio = [
    "Atividades",
    "Despesas",
    "Beneficiários",
    "Pesquisas",
    "Formulário"
]


if not relatorios:
    st.info("Este projeto ainda não possui relatórios cadastrados.")
    st.stop()


# Cria uma aba para cada relatório
abas = [f"Relatório {r.get('numero')}" for r in relatorios]
tabs = st.tabs(abas)





for idx, (tab, relatorio) in enumerate(zip(tabs, relatorios)):
    with tab:

        st.write('')
        st.write('')

        # STEPS --------------------------
        step_key = f"steps_relatorio_{idx}"


        step = sac.steps(
            items=[sac.StepsItem(title=s) for s in steps_relatorio],
            index=steps_relatorio.index(st.session_state.step_relatorio),
            key=f"steps_relatorio_{idx}"
        )




        # step = sac.steps(
        #     items=[
        #         sac.StepsItem(title="Atividades"),
        #         sac.StepsItem(title="Despesas"),
        #         sac.StepsItem(title="Beneficiários"),
        #         sac.StepsItem(title="Pesquisas"),
        #         sac.StepsItem(title="Formulário"),
        #     ],
        #     index=1,   # 👈 sempre começa em 1
        #     key=step_key
        # )



        # ---------- ATIVIDADES ----------

        if step == "Atividades":

            # # Atualiza o estado global do step
            # if step != st.session_state.step_relatorio:
            #     st.session_state.step_relatorio = step


            atividades = []

            plano = projeto.get("plano_trabalho", {})
            componentes = plano.get("componentes", [])

            for componente in componentes:
                for entrega in componente.get("entregas", []):
                    for atividade in entrega.get("atividades", []):
                        atividades.append({
                            "atividade": atividade.get("atividade"),
                            "componente": componente.get("componente"),
                            "entrega": entrega.get("entrega"),
                            "data_inicio": atividade.get("data_inicio"),
                            "data_fim": atividade.get("data_fim"),
                        })

            # SELECTBOX
            if atividades:
                atividade_selecionada = st.selectbox(
                    "Atividades",
                    options=atividades,
                    format_func=lambda x: x["atividade"],
                    key=f"atividade_select_{idx}"
                )

                st.markdown("### Detalhes da atividade")

                st.write(f"**Atividade:** {atividade_selecionada['atividade']}")
                st.write(f"**Componente:** {atividade_selecionada['componente']}")
                st.write(f"**Entrega:** {atividade_selecionada['entrega']}")

                if atividade_selecionada["data_inicio"]:
                    st.write(f"**Início:** {atividade_selecionada['data_inicio']}")

                if atividade_selecionada["data_fim"]:
                    st.write(f"**Fim:** {atividade_selecionada['data_fim']}")

            else:
                st.info("Nenhuma atividade cadastrada.")





        # ---------- PESQUISAS ----------
        if step == "Pesquisas":

            # ============================
            # CONTROLE DE USUÁRIO
            # ============================
            tipo_usuario = st.session_state.get("tipo_usuario")

            usuario_admin = tipo_usuario == "admin"
            usuario_equipe = tipo_usuario == "equipe"
            usuario_beneficiario = tipo_usuario == "beneficiario"
            usuario_visitante = tipo_usuario not in ["admin", "equipe", "beneficiario"]

            pode_editar = usuario_admin or usuario_equipe or usuario_beneficiario
            pode_verificar = usuario_admin or usuario_equipe

            # ============================
            # BUSCA DADOS
            # ============================
            edital = col_editais.find_one({"codigo_edital": projeto["edital"]})
            pesquisas = edital.get("pesquisas_relatorio", []) if edital else []

            if not pesquisas:
                st.caption("Nenhuma pesquisa cadastrada.")
                st.stop()

            st.markdown("### Pesquisas cadastradas")

            pesquisas_projeto = projeto.get("pesquisas", [])
            status_map = {p["id_pesquisa"]: p for p in pesquisas_projeto}

            # ============================
            # RENDERIZAÇÃO DAS LINHAS
            # ============================
            novos_status = []

            for pesquisa in pesquisas:

                status = status_map.get(pesquisa["id"], {})

                col1, col2, col3, col4 = st.columns([4, 3, 1, 1])

                # -------- PESQUISA --------
                with col1:
                    st.markdown(f"**{pesquisa['nome_pesquisa']}**")

                # -------- ANEXO --------
                with col2:
                    if pesquisa.get("upload_arquivo"):
                        st.file_uploader(
                            "Anexo",
                            disabled=not pode_editar,
                            key=f"upload_{pesquisa['id']}",
                            width=400
                        )

                # -------- RESPONDIDA --------
                with col3:
                    respondida = st.checkbox(
                        "Respondida",
                        value=status.get("respondida", False),
                        disabled=not pode_editar,
                        key=f"resp_{pesquisa['id']}"
                    )

                # -------- VERIFICADA --------
                with col4:
                    verificada = st.checkbox(
                        "Verificada",
                        value=status.get("verificada", False),
                        disabled=not pode_verificar,
                        key=f"verif_{pesquisa['id']}"
                    )

                novos_status.append({
                    "id_pesquisa": pesquisa["id"],
                    "respondida": respondida,
                    "verificada": verificada
                })

                st.divider()

            # ============================
            # BOTÃO SALVAR
            # ============================
            if pode_editar:
                if st.button("Salvar alterações", type="primary", icon=":material/save:"):

                    col_projetos.update_one(
                        {"codigo": projeto["codigo"]},
                        {"$set": {"pesquisas": novos_status}}
                    )

                    st.success(":material/check: Pesquisas atualizadas com sucesso!")
                    time.sleep(3)
                    st.rerun()














        # # ---------- PESQUISAS ----------
        # if step == "Pesquisas":

        #     # Tipos de usuário
        #     usuario_interno = st.session_state.tipo_usuario in ["admin", "equipe"]
        #     usuario_beneficiario = st.session_state.tipo_usuario == "beneficiario"
        #     usuario_visitante = not (usuario_interno or usuario_beneficiario)

        #     # Busca o edital
        #     edital = col_editais.find_one(
        #         {"codigo_edital": projeto["edital"]}
        #     )

        #     pesquisas = edital.get("pesquisas_relatorio", []) if edital else []

        #     st.write('')


        #     if not pesquisas:
        #         st.caption("Nenhuma pesquisa cadastrada.")
        #     else:
        #         st.markdown("##### Pesquisas / Ferramentas de monitoramento")
        #         st.write('')

        #         # -------------------------------
        #         # Monta dados para o Data Editor
        #         # -------------------------------

        #         pesquisas_projeto = projeto.get("pesquisas", [])

        #         status_map = {
        #             p["id_pesquisa"]: p
        #             for p in pesquisas_projeto
        #         }

        #         linhas = []

        #         for p in pesquisas:
        #             status = status_map.get(p["id"], {})

        #             linhas.append({
        #                 "Pesquisa": p["nome_pesquisa"],
        #                 "respondida": status.get("respondida", False),
        #                 "verificada": status.get("verificada", False),
        #                 "id_pesquisa": p["id"],
        #             })

        #         df_pesquisas = pd.DataFrame(linhas)

        #         # -------------------------------
        #         # CONTROLE DE COLUNAS
        #         # -------------------------------

        #         # Se for visitante, bloqueia tudo
        #         if usuario_visitante:
        #             disabled_cols = ["Pesquisa", "respondida", "verificada"]

        #         # Se for beneficiário, oculta "verificada"
        #         elif usuario_beneficiario:
        #             disabled_cols = ["Pesquisa"]
        #             df_pesquisas = df_pesquisas.drop(columns=["verificada"])

        #         # Admin ou equipe
        #         else:
        #             disabled_cols = ["Pesquisa"]

        #         # -------------------------------
        #         # DATA EDITOR
        #         # -------------------------------

        #         altura_tabela = ajustar_altura_data_editor(df_pesquisas, 0)

        #         df_editado = st.data_editor(
        #             df_pesquisas,
        #             hide_index=True,
        #             use_container_width=True,
        #             height=altura_tabela,
        #             column_config={
        #                 "Pesquisa": st.column_config.TextColumn(
        #                     "Pesquisa",
        #                     disabled=True
        #                 ),
        #                 "respondida": st.column_config.CheckboxColumn(
        #                     "Enviada / Respondida",
        #                     disabled="respondida" in disabled_cols
        #                 ),
        #                 "verificada": st.column_config.CheckboxColumn(
        #                     "Verificada",
        #                     disabled="verificada" in disabled_cols
        #                 ),
        #                 "id_pesquisa": None
        #             }
        #         )

        #         # -------------------------------
        #         # BOTÃO SALVAR (somente se puder editar)
        #         # -------------------------------

        #         if not usuario_visitante:

        #             st.write("")

        #             if st.button("Salvar alterações", type="primary", icon=":material/save:"):

        #                 novas_pesquisas = []

        #                 for _, row in df_editado.iterrows():
        #                     novas_pesquisas.append({
        #                         "id_pesquisa": row["id_pesquisa"],
        #                         "respondida": bool(row["respondida"]),
        #                         "verificada": bool(row.get("verificada", False))
        #                     })

        #                 col_projetos.update_one(
        #                     {"codigo": projeto["codigo"]},
        #                     {"$set": {"pesquisas": novas_pesquisas}}
        #                 )

        #                 st.success(":material/check: Pesquisas atualizadas com sucesso!")
        #                 time.sleep(3)
        #                 st.rerun()






        # # ---------- PESQUISAS ----------
        # if step == "Pesquisas":

        #     # Busca o edital
        #     edital = col_editais.find_one(
        #         {"codigo_edital": projeto["edital"]}
        #     )

        #     pesquisas = edital.get("pesquisas_relatorio", []) if edital else []

        #     if not pesquisas:
        #         st.caption("Nenhuma pesquisa cadastrada.")
        #     else:
        #         st.markdown("### Pesquisas cadastradas")

        #         # -------------------------------
        #         # Monta dados para o Data Editor
        #         # -------------------------------

        #         pesquisas_projeto = projeto.get("pesquisas", [])

        #         # Mapeia status existentes
        #         status_map = {
        #             p["id_pesquisa"]: p
        #             for p in pesquisas_projeto
        #         }

        #         linhas = []

        #         for p in pesquisas:
        #             status = status_map.get(p["id"], {})

        #             linhas.append({
        #                 "Pesquisa": p["nome_pesquisa"],
        #                 "respondida": status.get("respondida", False),
        #                 "verificada": status.get("verificada", False),
        #                 "id_pesquisa": p["id"],  # controle interno
        #             })

        #         df_pesquisas = pd.DataFrame(linhas)

        #         # -------------------------------
        #         # DATA EDITOR
        #         # -------------------------------

        #         # Calcula altura dinâmica
        #         altura_tabela = ajustar_altura_data_editor(df_pesquisas, 0)

        #         df_editado = st.data_editor(
        #             df_pesquisas,
        #             hide_index=True,
        #             use_container_width=True,
        #             height=altura_tabela,  # 👈 aqui
        #             column_config={
        #                 "Pesquisa": st.column_config.TextColumn(
        #                     "Pesquisa",
        #                     disabled=True
        #                 ),
        #                 "respondida": st.column_config.CheckboxColumn(
        #                     "Enviada / Respondida"
        #                 ),
        #                 "verificada": st.column_config.CheckboxColumn(
        #                     "Verificada"
        #                 ),
        #                 "id_pesquisa": None
        #             }
        #         )



        #         # -------------------------------
        #         # BOTÃO SALVAR
        #         # -------------------------------

        #         st.write("")

        #         if st.button("Salvar alterações", type="primary", icon=":material/save:"):

        #             novas_pesquisas = []

        #             for _, row in df_editado.iterrows():
        #                 novas_pesquisas.append({
        #                     "id_pesquisa": row["id_pesquisa"],
        #                     "respondida": bool(row["respondida"]),
        #                     "verificada": bool(row["verificada"])
        #                 })

        #             col_projetos.update_one(
        #                 {"codigo": projeto["codigo"]},
        #                 {"$set": {"pesquisas": novas_pesquisas}}
        #             )

        #             st.success(":material/check: Pesquisas atualizadas com sucesso!")
        #             time.sleep(3)
        #             st.rerun()



# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()