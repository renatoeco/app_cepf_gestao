import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import pandas as pd
# from bson import ObjectId
# import time
# import streamlit_shadcn_ui as ui
# from streamlit_sortables import sort_items
# import uuid
import io
import datetime



###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Importa coleções e cria dataframes

# Beneficiários
col_publicos = db["publicos"]

# Benefícios
col_beneficios = db["beneficios"]

# Direções Estratégicas
# col_direcoes = db["direcoes_estrategicas"]

# Indicadores
# col_indicadores = db["indicadores"]

# Categorias de despesa
col_categorias_despesa = db["categorias_despesa"]

# Corredores
col_corredores = db["corredores"]

# KBAs
col_kbas = db["kbas"]

# Editais
col_editais = db["editais"]



###########################################################################################################
# INTERFACE
###########################################################################################################


# Logo do sidebar
st.logo("images/ieb_logo.svg", size='large')

st.header('Relatórios')

st.write('')




###########################################################################################################
# ESCOLHA DO RELATÓRIO
###########################################################################################################

st.subheader("Escolha o tipo de relatório")

opcao_relatorio = st.radio(
    "Selecione o relatório que deseja gerar:",
    [
        "Relatório de salvaguardas",
        "Relatório de acompanhamento de desembolsos",
        "Relatório de acompanhamento de desembolsos por parcela",
        "Relatório de acompanhamento completo"
    ]
)

st.divider()









###########################################################################################################
# LÓGICA PARA CADA RELATÓRIO
###########################################################################################################

if opcao_relatorio == "Relatório de salvaguardas":






    ###########################################################################################################
    # RELATÓRIO DE SALVAGUARDAS
    ###########################################################################################################

    if "relatorio_salvaguardas_pronto" not in st.session_state:
        st.session_state.relatorio_salvaguardas_pronto = False

    if "arquivo_salvaguardas" not in st.session_state:
        st.session_state.arquivo_salvaguardas = None


    if opcao_relatorio == "Relatório de salvaguardas":

        # BOTÃO GERAR
        if not st.session_state.relatorio_salvaguardas_pronto:

            if st.button("Gerar relatório"):

                with st.spinner("Gerando relatório..."):

                    projetos = list(db["projetos"].find())

                    dados = []

                    for p in projetos:
                        dados.append({
                            "Código do projeto": p.get("codigo"),
                            "Nome da entidade": p.get("organizacao"),
                            "Nome do projeto": p.get("nome_do_projeto")
                        })

                    df = pd.DataFrame(dados)

                    buffer = io.BytesIO()

                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        df.to_excel(writer, index=False, sheet_name="Salvaguardas")

                    buffer.seek(0)

                    st.session_state.arquivo_salvaguardas = buffer
                    st.session_state.relatorio_salvaguardas_pronto = True

                st.rerun()


        # BOTÃO DOWNLOAD
        else:

            st.download_button(
                label="Baixar relatório",
                data=st.session_state.arquivo_salvaguardas,
                file_name="Relatorio_de_salvaguardas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )























###########################################################################################################
# RELATÓRIO DE ACOMPANHAMENTO DE DESEMBOLSOS
###########################################################################################################

elif opcao_relatorio == "Relatório de acompanhamento de desembolsos":

    # ---- INPUTS ----

    cotacao_dolar = st.number_input(
        "Cotação do dólar (R$)",
        min_value=0.01,
        value=5.0,
        step=0.01
    )

    # gerar lista de anos
    ano_atual = datetime.datetime.now().year
    anos = [""] + [ano_atual + i for i in range(-5, 6)]

    ano_selecionado = st.selectbox(
        "Selecione o ano",
        anos
    )

    meses = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
        "Jul", "Ago", "Set", "Out", "Nov", "Dez"
    ]

    # session state
    if "relatorio_desembolsos_pronto" not in st.session_state:
        st.session_state.relatorio_desembolsos_pronto = False

    if "arquivo_desembolsos" not in st.session_state:
        st.session_state.arquivo_desembolsos = None


    # ---- BOTÃO GERAR ----

    if not st.session_state.relatorio_desembolsos_pronto:

        if st.button("Gerar relatório"):

            if ano_selecionado == "":
                st.warning("Selecione um ano.")
                st.stop()

            with st.spinner("Gerando relatório..."):

                projetos = list(db["projetos"].find())

                dados = []

                for p in projetos:

                    financeiro = p.get("financeiro", {})
                    parcelas = financeiro.get("parcelas", [])

                    valor_total = financeiro.get("valor_total", 0)

                    linha = {
                        "Código": p.get("codigo"),
                        "Sigla": p.get("sigla"),
                        "Valor do contrato (R$)": valor_total,
                        "Valor do contrato (US$)": valor_total / cotacao_dolar
                    }

                    # inicializar meses
                    for mes in meses:
                        linha[mes] = 0

                    # verificar parcelas pagas
                    for parcela in parcelas:

                        data_realizada = parcela.get("data_realizada")

                        if not data_realizada:
                            continue

                        data = datetime.datetime.strptime(data_realizada, "%Y-%m-%d")

                        if data.year == int(ano_selecionado):

                            mes_nome = meses[data.month - 1]
                            linha[mes_nome] += parcela.get("valor", 0)

                    dados.append(linha)

                df = pd.DataFrame(dados)

                buffer = io.BytesIO()

                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Desembolsos")

                buffer.seek(0)

                st.session_state.arquivo_desembolsos = buffer
                st.session_state.relatorio_desembolsos_pronto = True

            st.rerun()


    # ---- BOTÃO DOWNLOAD ----

    else:

        st.download_button(
            label="Baixar relatório",
            data=st.session_state.arquivo_desembolsos,
            file_name="Relatorio_acompanhamento_desembolsos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )























elif opcao_relatorio == "Relatório de acompanhamento de desembolsos por parcela":
    st.write("Gerando relatório de desembolsos por parcela...")
    # código aqui


elif opcao_relatorio == "Relatório de acompanhamento completo":
    st.write("Gerando relatório completo...")
    # código aqui