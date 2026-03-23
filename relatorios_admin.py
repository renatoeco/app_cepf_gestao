import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import pandas as pd
import io
import datetime
import time


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
        "ciclos": list(db["ciclos_investimento"].find()),
        "organizacoes": list(db["organizacoes"].find())
    }



dados_base = carregar_dados_base()

editais = dados_base["editais"]
ciclos = dados_base["ciclos"]
organizacoes = dados_base["organizacoes"]










###########################################################################################################
# FUNÇÕES
###########################################################################################################



# FUNÇÃO DE FILTRO DE EDITAIS

def filtro_editais():
    """
    Cria um selectbox para escolha de edital e retorna os projetos filtrados.
    """

    #######################################################################################################
    # FUNÇÃO INTERNA PARA MONTAR O LABEL DO SELECTBOX
    #######################################################################################################
    def montar_label_edital(edital):
        """
        Monta o texto exibido no selectbox combinando:
        codigo_edital | nome_edital | doadores | investidores | nome_ciclo
        """

        # Código e nome do edital
        codigo = edital.get("codigo_edital", "")
        nome = edital.get("nome_edital", "")

        # Código do ciclo associado ao edital
        codigo_ciclo = edital.get("ciclo_investimento")

        # Busca os dados do ciclo no mapa previamente carregado
        ciclo = mapa_ciclos.get(codigo_ciclo, {})

        # Listas de doadores e investidores
        doadores = ciclo.get("doadores", [])
        investidores = ciclo.get("investidores", [])

        # Nome do ciclo
        nome_ciclo = ciclo.get("nome_ciclo", "")

        # Converte listas em string separada por vírgula
        doadores_str = ", ".join(doadores) if doadores else ""
        investidores_str = ", ".join(investidores) if investidores else ""

        # Monta as partes do label
        partes = [codigo, nome]

        if doadores_str:
            partes.append(doadores_str)

        if investidores_str:
            partes.append(investidores_str)

        if nome_ciclo:
            partes.append(nome_ciclo)

        # Junta tudo com separador
        return " | ".join(partes)


    #######################################################################################################
    # SELECTBOX DE ESCOLHA DO EDITAL
    #######################################################################################################
    edital_selecionado_obj = st.selectbox(
        "Selecione o edital",
        options=[None] + editais,
        format_func=lambda x: "Selecione..." if x is None else montar_label_edital(x)
    )


    #######################################################################################################
    # EXTRAÇÃO DO CÓDIGO DO EDITAL
    #######################################################################################################
    codigo_edital = None

    if edital_selecionado_obj:
        codigo_edital = edital_selecionado_obj.get("codigo_edital")


    #######################################################################################################
    # BUSCA DOS PROJETOS FILTRADOS
    #######################################################################################################
    # Caso nenhum edital seja selecionado, retorna lista vazia
    if not codigo_edital:
        return [], None

    # Consulta projetos vinculados ao edital selecionado
    projetos = list(db["projetos"].find({
        "edital": codigo_edital
    }))


    #######################################################################################################
    # RETORNO DOS PROJETOS FILTRADOS
    #######################################################################################################
    return projetos, edital_selecionado_obj








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
# MAPA DE ORGANIZAÇÕES (ACESSO RÁPIDO)
###########################################################################################################

mapa_organizacoes = {
    str(org.get("_id")): org.get("nome_organizacao", "")
    for org in organizacoes
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
# RELATÓRIO DE SALVAGUARDAS
###########################################################################################################

# Inicializa session_state
if "arquivo_salvaguardas" not in st.session_state:
    st.session_state.arquivo_salvaguardas = None



if opcao_relatorio == "Relatório de salvaguardas":

    st.subheader("Relatório de salvaguardas")

    # Filtro de editais
    # projetos = filtro_editais()
    projetos, edital_selecionado_obj = filtro_editais()

    st.write(f"{len(projetos)} projetos")

    st.write('')

    #######################################################################################################
    # BOTÕES (EM CONTAINER HORIZONTAL)
    #######################################################################################################
    with st.container(horizontal=True):

        ###################################################################################################
        # BOTÃO GERAR
        ###################################################################################################
        if st.button("Gerar relatório", icon=":material/list_alt_add:"):

            ###################################################################################################
            # VALIDAÇÃO DE PROJETOS
            ###################################################################################################
            if not projetos:
                st.warning("Nenhum projeto encontrado para o edital selecionado.", icon=":material/warning:")
                st.session_state.arquivo_salvaguardas = None
                time.sleep(3)

            else:

                with st.spinner("Gerando relatório..."):

                    ###################################################################################################
                    # MONTAGEM DOS DADOS DO RELATÓRIO
                    ###################################################################################################
                    dados = []

                    for p in projetos:

                        # Recupera o id da organização
                        id_org = p.get("id_organizacao")

                        # Busca nome no mapa (já cacheado)
                        nome_org = mapa_organizacoes.get(str(id_org), "") if id_org else ""


                        # Recupera dados de salvaguardas
                        salvaguardas = p.get("salvaguardas", {})

                        # POLÍTICA 2
                        pol2 = salvaguardas.get("pol_2_trabalho", {})
                        aplicavel2 = pol2.get("aplicavel", "")
                        detalhes2 = pol2.get("detalhes", "")
                        categoria2 = pol2.get("categoria", "")

                        # POLÍTICA 3
                        pol3 = salvaguardas.get("pol_3_poluicao", {})
                        aplicavel3 = pol3.get("aplicavel", "")
                        detalhes_pesticidas = pol3.get("detalhes_pesticidas", "")
                        detalhes_poluicao = pol3.get("detalhes_poluicao", "")
                        categoria3 = pol3.get("categoria", "")

                        # POLÍTICA 4
                        pol4 = salvaguardas.get("pol_4_comunidade", {})
                        aplicavel4 = pol4.get("aplicavel", "")
                        detalhes4 = pol4.get("detalhes", "")
                        categoria4 = pol4.get("categoria", "")

                        # POLÍTICA 5
                        pol5 = salvaguardas.get("pol_5_reassentamento", {})
                        aplicavel5 = pol5.get("aplicavel", "")
                        detalhes5 = pol5.get("detalhes", "")
                        categoria5 = pol5.get("categoria", "")

                        # POLÍTICA 6
                        pol6 = salvaguardas.get("pol_6_biodiversidade", {})
                        aplicavel6 = pol6.get("aplicavel", "")
                        detalhes6 = pol6.get("detalhes", "")
                        categoria6 = pol6.get("categoria", "")

                        # POLÍTICA 7
                        pol7 = salvaguardas.get("pol_7_indigenas", {})
                        aplicavel7 = pol7.get("aplicavel", "")
                        detalhes7 = pol7.get("detalhes", "")
                        categoria7 = pol7.get("categoria", "")

                        # POLÍTICA 8
                        pol8 = salvaguardas.get("pol_8_patrimonio", {})
                        aplicavel8 = pol8.get("aplicavel", "")
                        detalhes8 = pol8.get("detalhes", "")
                        categoria8 = pol8.get("categoria", "")

                        # POLÍTICA 9
                        pol9 = salvaguardas.get("pol_9_genero", {})
                        detalhes9 = pol9.get("detalhes", "")
                        categoria9 = pol9.get("categoria", "")

                        # CAMPOS GERAIS DE SALVAGUARDAS
                        categoria_geral_risco = salvaguardas.get("categoria_geral_risco", "")
                        fortalecimento_capacidades = salvaguardas.get("fortalecimento_capacidades", "")


                        # Criando as colunas na tabela
                        dados.append({
                            "Código do projeto": p.get("codigo"),
                            "Nome da organização": nome_org,
                            "Nome do projeto": p.get("nome_do_projeto"),

                            ###################################################################################################
                            # POLÍTICA 1
                            ###################################################################################################
                            "1. Avaliação Ambiental e Social": "",
                            "1. Aplicável?": "Sim",
                            "1. Avaliação de Risco": "N/A",
                            "1. Categoria de Risco": "N/A",

                            ###################################################################################################
                            # POLÍTICA 2
                            ###################################################################################################
                            "2. Condições de Trabalho e Trabalhistas": "",
                            "2. Aplicável?": aplicavel2,
                            "2. Avaliação de Risco": f"O projeto proposto apresenta riscos significativos em relação às condições de trabalho e trabalhistas?\nDetalhes: {detalhes2}" if detalhes2 else "",
                            "2. Categoria de Risco": categoria2,

                            ###################################################################################################
                            # POLÍTICA 3
                            ###################################################################################################
                            "3. Eficiência de Recursos e Prevenção de Poluição": "",
                            "3. Aplicável?": aplicavel3,
                            "3. Avaliação de Risco": (
                                f"O projeto proposto apresenta riscos significativos relacionados a pesticidas?\n"
                                f"Detalhes: {detalhes_pesticidas}\n\n"
                                f"O projeto proposto apresenta riscos significativos relacionados ao uso insustentável de recursos e/ou formas de poluição que não sejam pesticidas?\n"
                                f"Detalhes: {detalhes_poluicao}"
                                if detalhes_pesticidas or detalhes_poluicao else ""
                            ),
                            "3. Categoria de Risco": categoria3,

                            ###################################################################################################
                            # POLÍTICA 4
                            ###################################################################################################
                            "4. Saúde, Segurança e Proteção da Comunidade": "",
                            "4. Aplicável?": aplicavel4,
                            "4. Avaliação de Risco": f"O projeto proposto apresenta riscos significativos relacionados à saúde, segurança e proteção da comunidade?\nDetalhes: {detalhes4}" if detalhes4 else "",
                            "4. Categoria de Risco": categoria4,

                            ###################################################################################################
                            # POLÍTICA 5
                            ###################################################################################################
                            "5. Restrições de Uso da Terra e Reassentamento Involuntário": "",
                            "5. Aplicável?": aplicavel5,
                            "5. Avaliação de Risco": f"O projeto proposto apresenta riscos significativos relacionados a restrições de acesso associadas a impactos negativos nos meios de subsistência?\nDetalhes: {detalhes5}" if detalhes5 else "",
                            "5. Categoria de Risco": categoria5,

                            ###################################################################################################
                            # POLÍTICA 6
                            ###################################################################################################
                            "6. Conservação da Biodiversidade e Gestão Sustentável de Recursos Naturais Vivos": "",
                            "6. Aplicável?": aplicavel6,
                            "6. Avaliação de Risco": f"O projeto proposto apresenta riscos significativos relacionados à degradação ou perda de habitat crítico ou outros habitats naturais?\nDetalhes: {detalhes6}" if detalhes6 else "",
                            "6. Categoria de Risco": categoria6,

                            ###################################################################################################
                            # POLÍTICA 7
                            ###################################################################################################
                            "7. Povos Indígenas": "",
                            "7. Aplicável?": aplicavel7,
                            "7. Avaliação de Risco": f"O projeto proposto apresenta riscos significativos relacionados aos impactos sobre Povos Indígenas?\nDetalhes: {detalhes7}" if detalhes7 else "",
                            "7. Categoria de Risco": categoria7,                        

                            ###################################################################################################
                            # POLÍTICA 8
                            ###################################################################################################
                            "8. Patrimônio Cultural": "",
                            "8. Aplicável?": aplicavel8,
                            "8. Avaliação de Risco": f"O projeto proposto apresenta riscos significativos relacionados aos impactos sobre o patrimônio cultural tangível e/ou intangível?\nDetalhes: {detalhes8}" if detalhes8 else "",
                            "8. Categoria de Risco": categoria8,

                            ###################################################################################################
                            # POLÍTICA 9
                            ###################################################################################################
                            "9. Igualdade de Gênero": "",
                            "9. Aplicável?": "Sim",
                            "9. Avaliação de Risco": f"O projeto proposto apresenta riscos significativos relacionados a impactos na promoção, proteção e respeito à igualdade de gênero?\nDetalhes: {detalhes9}" if detalhes9 else "",
                            "9. Categoria de Risco": categoria9,

                            ###################################################################################################
                            # POLÍTICA 10
                            ###################################################################################################
                            "10. Engajamento de Partes Interessadas": "",
                            "10. Aplicável?": "Sim",
                            "10. Avaliação de Risco": "N/A",
                            "10. Categoria de Risco": "N/A",

                            ###################################################################################################
                            # CAMPOS FINAIS
                            ###################################################################################################
                            "CATEGORIA GERAL DE RISCO": categoria_geral_risco,
                            "FORTALECIMENTO DE CAPACIDADE": fortalecimento_capacidades,

                        })



                    ###################################################################################################
                    # CRIAÇÃO DO EXCEL
                    ###################################################################################################
                    df = pd.DataFrame(dados)

                    buffer = io.BytesIO()

                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        df.to_excel(writer, index=False, sheet_name="Salvaguardas")

                    buffer.seek(0)

                    ###################################################################################################
                    # SALVAR NO SESSION STATE
                    ###################################################################################################
                    st.session_state.arquivo_salvaguardas = buffer

                    st.rerun()



        ###################################################################################################
        # BOTÃO DOWNLOAD
        ###################################################################################################
        if st.session_state.arquivo_salvaguardas:

            # Nome do edital (seguro para arquivo)
            nome_edital = edital_selecionado_obj.get("nome_edital", "") if edital_selecionado_obj else ""
            nome_edital_arquivo = nome_edital.replace(" ", "_")

            st.download_button(
                label="Baixar relatório",
                icon=":material/download:",
                data=st.session_state.arquivo_salvaguardas,
                file_name=f"Relatorio_de_salvaguardas_{nome_edital_arquivo}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )



    #######################################################################################################
    # MENSAGEM ABAIXO DOS BOTÕES
    #######################################################################################################
    if st.session_state.arquivo_salvaguardas:
        st.caption("Relatório gerado. Clique para baixar.")


















###########################################################################################################
# RELATÓRIO DE ACOMPANHAMENTO DE DESEMBOLSOS
###########################################################################################################

elif opcao_relatorio == "Relatório de acompanhamento de desembolsos":

    st.subheader("Relatório de acompanhamento de desembolsos")


    # Renderiza o filtro de editais 
    # projetos = filtro_editais()
    projetos, edital_selecionado_obj = filtro_editais()


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
    # projetos = filtro_editais()
    projetos, edital_selecionado_obj = filtro_editais()


    st.write(f"{len(projetos)} projetos")

    st.write('')
    st.write('')











elif opcao_relatorio == "Relatório de acompanhamento completo":

    st.subheader("Relatório de acompanhamento completo")

    # Renderiza o filtro de editais 
    # projetos = filtro_editais()
    projetos, edital_selecionado_obj = filtro_editais()


    st.write(f"{len(projetos)} projetos")

    st.write('')
    st.write('')
