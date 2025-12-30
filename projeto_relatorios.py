import streamlit as st
import pandas as pd
from funcoes_auxiliares import conectar_mongo_cepf_gestao, sidebar_projeto
import streamlit_antd_components as sac


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

            # Busca o edital correspondente
            edital = col_editais.find_one(
                {"codigo_edital": projeto["edital"]}
            )

            pesquisas = edital.get("pesquisas_relatorio", []) if edital else []

            if not pesquisas:
                st.caption("Nenhuma pesquisa cadastrada.")
            else:
                st.markdown("### Pesquisas cadastradas")

                for idx, pesquisa in enumerate(pesquisas, start=1):
                    st.markdown(f"**{idx}. {pesquisa.get('nome_pesquisa')}**")



# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()