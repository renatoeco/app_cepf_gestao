import streamlit as st
import pandas as pd
from funcoes_auxiliares import conectar_mongo_cepf_gestao, sidebar_projeto


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

col_projetos = db["projetos"]





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


if not relatorios:
    st.info("Este projeto ainda não possui relatórios cadastrados.")
    st.stop()


# Cria uma aba para cada relatório
abas = [f"Relatório {r.get('numero')}" for r in relatorios]
tabs = st.tabs(abas)


# ------------------------------------------------------------
# CONTEÚDO DE CADA RELATÓRIO
# ------------------------------------------------------------
for tab, relatorio in zip(tabs, relatorios):
    with tab:

        numero = relatorio.get("numero")
        entregas = relatorio.get("entregas", [])
        data_prevista = relatorio.get("data_prevista")

        st.subheader(f"Relatório {numero}")

        # Data prevista
        if data_prevista:
            data_formatada = pd.to_datetime(data_prevista).strftime("%d/%m/%Y")
            st.write(f"**Data prevista:** {data_formatada}")
        else:
            st.write("**Data prevista:** Não informada")

        st.divider()

      # Entregas
        st.markdown("### Entregas previstas")

        if entregas:
            for i, entrega in enumerate(entregas, start=1):
                st.markdown(f"- {entrega}")
        else:
            st.info("Nenhuma entrega cadastrada para este relatório.")









# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()