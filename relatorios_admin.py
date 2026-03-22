import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import pandas as pd
import io
import datetime



###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB E CARREGAMENTO DE DADOS
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()









# Carregamento de várias coleções cacheadas
@st.cache_data(ttl=600)  # 10 minutos
def carregar_dados_base():

    return {
        "publicos": list(db["publicos"].find()),
        "beneficios": list(db["beneficios"].find()),
        "categorias_despesa": list(db["categorias_despesa"].find()),
        "corredores": list(db["corredores"].find()),
        "kbas": list(db["kbas"].find()),
        "editais": list(db["editais"].find()),
        "ciclos": list(db["ciclos_investimento"].find())
    }



dados_base = carregar_dados_base()

editais = dados_base["editais"]
ciclos = dados_base["ciclos"]










###########################################################################################################
# FUNÇÕES
###########################################################################################################







# FILTRO DE EDITAL

def filtro_editais():



    def montar_label_edital(edital):

        codigo = edital.get("codigo_edital", "")
        nome = edital.get("nome_edital", "")
        codigo_ciclo = edital.get("ciclo_investimento")

        ciclo = mapa_ciclos.get(codigo_ciclo, {})

        doadores = ciclo.get("doadores", [])
        investidores = ciclo.get("investidores", [])
        nome_ciclo = ciclo.get("nome_ciclo", "")

        doadores_str = ", ".join(doadores) if doadores else ""
        investidores_str = ", ".join(investidores) if investidores else ""

        # 👇 agora começa com o código
        partes = [codigo, nome]

        if doadores_str:
            partes.append(doadores_str)

        if investidores_str:
            partes.append(investidores_str)

        if nome_ciclo:
            partes.append(nome_ciclo)

        return " | ".join(partes)




    edital_selecionado_obj = st.selectbox(
        "Selecione o edital",
        options=[None] + editais,
        format_func=lambda x: "Selecione..." if x is None else montar_label_edital(x)
    )


    codigo_edital = None

    if edital_selecionado_obj:
        codigo_edital = edital_selecionado_obj.get("codigo_edital")



    projetos = list(db["projetos"].find({
        "edital": codigo_edital
    }))

    return projetos









###########################################################################################################
# TRATAMENTO DE DADOS
###########################################################################################################


# Mapa de ciclos de editais, pra ajudar no join de edital com ciclos_investimento, usado no selectbox do filtro
# que tem concatenado "nome_edital | doadores | investidores | nome_ciclo" 
mapa_ciclos = {
    c.get("codigo_ciclo"): c
    for c in ciclos
}











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

    st.subheader("Relatório de salvaguardas")

    # Renderiza o filtro de editais 
    projetos = filtro_editais()

    st.write(f"{len(projetos)} projetos")

    ###########################################################################################################
    # RELATÓRIO DE SALVAGUARDAS
    ###########################################################################################################

    if "relatorio_salvaguardas_pronto" not in st.session_state:
        st.session_state.relatorio_salvaguardas_pronto = False

    if "arquivo_salvaguardas" not in st.session_state:
        st.session_state.arquivo_salvaguardas = None


    if opcao_relatorio == "Relatório de salvaguardas":


        st.write('')

        # BOTÃO GERAR
        if not st.session_state.relatorio_salvaguardas_pronto:

            if st.button("Gerar relatório"):

                with st.spinner("Gerando relatório..."):


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

    st.subheader("Relatório de acompanhamento de desembolsos")


    # Renderiza o filtro de editais 
    projetos = filtro_editais()

    st.write(f"{len(projetos)} projetos")

    st.write('')
    st.write('')

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
    
    st.subheader("Relatório de acompanhamento de desembolsos por parcela")

    
    # Renderiza o filtro de editais 
    projetos = filtro_editais()

    st.write(f"{len(projetos)} projetos")

    st.write('')
    st.write('')


elif opcao_relatorio == "Relatório de acompanhamento completo":

    st.subheader("Relatório de acompanhamento completo")

    # Renderiza o filtro de editais 
    projetos = filtro_editais()

    st.write(f"{len(projetos)} projetos")

    st.write('')
    st.write('')
