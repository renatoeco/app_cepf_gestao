import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao, calcular_status_projetos  # Função personalizada para conectar ao MongoDB
import pandas as pd
import io
import datetime
import time


st.set_page_config(page_title="Relatórios", page_icon=":material/assignment:")




###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB E CARREGAMENTO DE DADOS
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()





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
        "organizacoes": list(db["organizacoes"].find()),
        "pessoas": list(db["pessoas"].find()) 
    }

dados_base = carregar_dados_base()

editais = dados_base["editais"]
ciclos = dados_base["ciclos"]
organizacoes = dados_base["organizacoes"]
pessoas = dados_base["pessoas"] 







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
# MAPA COMPLETO DE ORGANIZAÇÕES (DADOS GERAIS)
###########################################################################################################
mapa_organizacoes = {
    str(org.get("_id")): {
        "nome": org.get("nome_organizacao", ""),
        "sigla": org.get("sigla_organizacao", ""),
        "cep": org.get("cep", ""),

        # dados de UF
        "uf_sigla": org.get("uf", {}).get("sigla", ""),
        "uf_nome": org.get("uf", {}).get("nome", ""),

        # dados de município
        "municipio_nome": org.get("municipio", {}).get("nome", "")
    }
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
        "Relatório de acompanhamento completo",
        "Lista de comunidades"
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

                        org_info = mapa_organizacoes.get(str(id_org), {}) if id_org else {}

                        nome_org = org_info.get("nome", "")

                        # nome_org = mapa_organizacoes.get(str(id_org), "") if id_org else ""


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

            download_clicado = st.download_button(
                label="Baixar relatório",
                type="primary",
                icon=":material/download:",
                data=st.session_state.arquivo_salvaguardas,
                file_name=f"Relatorio_de_salvaguardas_{nome_edital_arquivo}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            ###################################################################################################
            # SE CLICOU NO DOWNLOAD, LIMPA O ESTADO
            ###################################################################################################
            if download_clicado:
                st.session_state.arquivo_salvaguardas = None
                st.rerun()




    #######################################################################################################
    # MENSAGEM ABAIXO DOS BOTÕES
    #######################################################################################################
    if st.session_state.arquivo_salvaguardas:
        st.caption("Relatório gerado. Clique para baixar.")


















###########################################################################################################
# RELATÓRIO DE ACOMPANHAMENTO DE DESEMBOLSOS
###########################################################################################################



###########################################################################################################
# RELATÓRIO DE ACOMPANHAMENTO DE DESEMBOLSOS
###########################################################################################################

elif opcao_relatorio == "Relatório de acompanhamento de desembolsos":

    st.subheader("Relatório de acompanhamento de desembolsos")

    # Filtro de edital
    projetos, edital_selecionado_obj = filtro_editais()

    ###################################################################################################
    # SESSION STATE
    ###################################################################################################
    if "ano_selecionado" not in st.session_state:
        st.session_state.ano_selecionado = ""

    if "df_cambio_desembolsos" not in st.session_state:
        st.session_state.df_cambio_desembolsos = None

    if "mostrar_inputs_ano" not in st.session_state:
        st.session_state.mostrar_inputs_ano = False

    if "mostrar_relatorio" not in st.session_state:
        st.session_state.mostrar_relatorio = False

    if "mostrar_download" not in st.session_state:
        st.session_state.mostrar_download = False

    if "arquivo_desembolsos" not in st.session_state:
        st.session_state.arquivo_desembolsos = None


    ###################################################################################################
    # VALIDAÇÃO DO EDITAL
    ###################################################################################################
    if not edital_selecionado_obj:
        st.caption("Selecione um edital para iniciar.")
        st.stop()

    st.session_state.mostrar_inputs_ano = True

    st.write(f"{len(projetos)} projetos")
    st.write('')
    st.write('')


    ###################################################################################################
    # SELECTBOX DE ANO
    ###################################################################################################
    if st.session_state.mostrar_inputs_ano:

        anos_set = set()

        for p in projetos:
            for parcela in p.get("financeiro", {}).get("parcelas", []):

                data_realizada = parcela.get("data_realizada")

                if data_realizada:
                    try:
                        ano = datetime.datetime.strptime(
                            data_realizada, "%d/%m/%Y"
                        ).year
                        anos_set.add(ano)
                    except:
                        pass

        anos = [""] + sorted(list(anos_set))

        ano = st.selectbox(
            "Selecione o ano",
            anos,
            width=250,
        )

        if ano != "":
            st.session_state.ano_selecionado = ano
            st.session_state.mostrar_relatorio = True


    ###################################################################################################
    # DATA EDITOR (APENAS APÓS SELEÇÃO DO ANO)
    ###################################################################################################
    if st.session_state.mostrar_relatorio:

        ano_selecionado = st.session_state.ano_selecionado

        # ------------------------------
        # COLETA MESES COM PAGAMENTO
        # ------------------------------
        datas = []

        for p in projetos:
            for parcela in p.get("financeiro", {}).get("parcelas", []):

                data_realizada = parcela.get("data_realizada")

                if data_realizada:
                    try:
                        data = datetime.datetime.strptime(
                            data_realizada, "%d/%m/%Y"
                        )

                        if str(data.year) == str(ano_selecionado):
                            datas.append(data)

                    except:
                        pass

        datas_ordenadas = sorted(datas)

        # Mapeamento seguro de meses
        mapa_meses = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março",
            4: "Abril", 5: "Maio", 6: "Junho",
            7: "Julho", 8: "Agosto", 9: "Setembro",
            10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }

        meses_nomes = [mapa_meses[data.month] for data in datas_ordenadas]

        # remove duplicados mantendo ordem
        meses_unicos = list(dict.fromkeys(meses_nomes))

        df_cambio = pd.DataFrame({
            "Mês": meses_unicos,
            "Cotação": [None] * len(meses_unicos)
        })

        st.write('')
        st.markdown("##### Câmbio US\\$ por mês")

        df_editado = st.data_editor(
            df_cambio,
            width=400,
            height="content",
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Mês": st.column_config.TextColumn(
                    "Mês",
                    disabled=True
                ),
                "Cotação": st.column_config.NumberColumn(
                    "Cotação",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f"
                )
            },
            key="data_editor_cambio"
        )


        ###################################################################################################
        # BOTÕES
        ###################################################################################################
        st.write('')

        with st.container(horizontal=True):



            if st.button("Gerar relatório", icon=":material/list_alt_add:"):

                # valida ano
                if ano_selecionado == "":
                    st.warning("Selecione um ano.")
                    # time.sleep(3)

                # valida cotações (todos os meses obrigatórios)
                else:

                    valores_cotacao = df_editado["Cotação"]

                    if valores_cotacao.isnull().any() or (valores_cotacao == 0).any():
                        st.warning("Preencha a cotação para todos os meses.")
                        # time.sleep(3)

                    else:

                        with st.spinner("Gerando relatório..."):


                            ###################################################################################################
                            # CONVERSÃO PARA DICIONÁRIO
                            ###################################################################################################
                            cambio_meses = {
                                row["Mês"]: row["Cotação"]
                                for _, row in df_editado.iterrows()
                            }

                            ###################################################################################################
                            # CALCULAR STATUS DOS PROJETOS
                            ###################################################################################################
                            df_projetos = pd.DataFrame(projetos)

                            df_projetos_status = calcular_status_projetos(df_projetos)

                            mapa_status = {
                                row["codigo"]: row.get("status")
                                for _, row in df_projetos_status.iterrows()
                            }






                            ###################################################################################################
                            # CRIAÇÃO DO EXCEL
                            ###################################################################################################
                            buffer = io.BytesIO()

                            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:

                                # ---------------------------------------------------------------------------------------------
                                # CRIA PLANILHA
                                # ---------------------------------------------------------------------------------------------
                                workbook = writer.book
                                worksheet = workbook.create_sheet(title="Desembolsos")
                                writer.sheets["Desembolsos"] = worksheet

                                # ---------------------------------------------------------------------------------------------
                                # TÍTULO
                                # ---------------------------------------------------------------------------------------------
                                worksheet.cell(
                                    row=1,
                                    column=1,
                                    value=f"Taxas de câmbio de {ano_selecionado}"
                                )

                                # ---------------------------------------------------------------------------------------------
                                # MESES
                                # ---------------------------------------------------------------------------------------------
                                meses = [
                                    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                                    "Jul", "Ago", "Set", "Out", "Nov", "Dez"
                                ]

                                meses_completos = [
                                    "Janeiro", "Fevereiro", "Março",
                                    "Abril", "Maio", "Junho",
                                    "Julho", "Agosto", "Setembro",
                                    "Outubro", "Novembro", "Dezembro"
                                ]

                                # ---------------------------------------------------------------------------------------------
                                # TABELA DE CÂMBIO (BLOCO SUPERIOR)
                                # ---------------------------------------------------------------------------------------------
                                trimestres = [
                                    meses_completos[0:3],
                                    meses_completos[3:6],
                                    meses_completos[6:9],
                                    meses_completos[9:12]
                                ]

                                col_offset = 1

                                for trimestre in trimestres:

                                    col_mes = col_offset
                                    col_valor = col_offset + 1

                                    for i, mes in enumerate(trimestre):

                                        linha_excel = i + 2

                                        worksheet.cell(row=linha_excel, column=col_mes, value=mes)
                                        worksheet.cell(
                                            row=linha_excel,
                                            column=col_valor,
                                            value=cambio_meses.get(mes, "")
                                        )

                                    col_offset += 2

                                # ---------------------------------------------------------------------------------------------
                                # CABEÇALHO DA TABELA DE PROJETOS
                                # ---------------------------------------------------------------------------------------------
                                colunas = [
                                    "Código",
                                    "Sigla",
                                    "Valor do contrato (R$)",
                                    "Valor do contrato (US$)",
                                ]

                                for mes in meses:
                                    colunas.append(f"{mes} R$")
                                    colunas.append(f"{mes} US$")

                                colunas += [
                                    "Já Pago",
                                    "Remanescente a receber",
                                    "Data de Encerramento",
                                    "Status do projeto"
                                ]

                                for col_idx, col_nome in enumerate(colunas, start=1):
                                    worksheet.cell(row=6, column=col_idx, value=col_nome)

                                # ---------------------------------------------------------------------------------------------
                                # MAPA DAS CÉLULAS DE CÂMBIO
                                # ---------------------------------------------------------------------------------------------
                                mapa_cambio = {
                                    "Jan": "B2", "Fev": "B3", "Mar": "B4",
                                    "Abr": "D2", "Mai": "D3", "Jun": "D4",
                                    "Jul": "F2", "Ago": "F3", "Set": "F4",
                                    "Out": "H2", "Nov": "H3", "Dez": "H4"
                                }

                                # ---------------------------------------------------------------------------------------------
                                # DADOS DOS PROJETOS
                                # ---------------------------------------------------------------------------------------------
                                linha_excel = 7

                                for p in projetos:

                                    financeiro = p.get("financeiro", {})
                                    parcelas = financeiro.get("parcelas", [])

                                    valor_total = (
                                        financeiro.get("valor_total", 0) +
                                        financeiro.get("valor_aditivo", 0)
                                    )

                                    linha = {
                                        "Código": p.get("codigo"),
                                        "Sigla": p.get("sigla"),
                                        "Valor do contrato (R$)": valor_total,
                                        "Valor do contrato (US$)": ""
                                    }

                                    # inicializa meses
                                    for mes in meses:
                                        linha[f"{mes} R$"] = 0
                                        linha[f"{mes} US$"] = ""

                                    ja_pago = 0

                                    # processamento das parcelas
                                    for parcela in parcelas:

                                        data_realizada = parcela.get("data_realizada")

                                        if not data_realizada:
                                            continue

                                        try:
                                            data = datetime.datetime.strptime(
                                                data_realizada, "%d/%m/%Y"
                                            )
                                        except:
                                            continue

                                        valor_parcela = parcela.get("valor", 0)
                                        ja_pago += valor_parcela

                                        if data.year == int(ano_selecionado):
                                            mes_nome = meses[data.month - 1]
                                            linha[f"{mes_nome} R$"] += valor_parcela

                                    # status
                                    linha["Status do projeto"] = mapa_status.get(p.get("codigo"), "")

                                    linha["Já Pago"] = ja_pago
                                    linha["Remanescente a receber"] = ""
                                    linha["Data de Encerramento"] = ""

                                    # -----------------------------------------------------------------------------------------
                                    # ESCRITA DAS CÉLULAS
                                    # -----------------------------------------------------------------------------------------
                                    for col_idx, col_nome in enumerate(colunas, start=1):

                                        valor = linha.get(col_nome, "")

                                        # fórmula remanescente
                                        if col_nome == "Remanescente a receber":

                                            celula_contrato = f"C{linha_excel}"
                                            celula_ja_pago = f"AC{linha_excel}"

                                            worksheet.cell(
                                                row=linha_excel,
                                                column=col_idx,
                                                value=f"={celula_contrato}-{celula_ja_pago}"
                                            )

                                            continue

                                        # fórmula US$
                                        if "US$" in col_nome and "Valor do contrato" not in col_nome:

                                            mes_sigla = col_nome.split()[0]

                                            celula_cambio = mapa_cambio.get(mes_sigla)

                                            col_rs_letra = worksheet.cell(
                                                row=6,
                                                column=col_idx - 1
                                            ).column_letter

                                            celula_rs = f"{col_rs_letra}{linha_excel}"

                                            formula = f'=IF({celula_rs}="","",{celula_rs}/{celula_cambio})'

                                            worksheet.cell(
                                                row=linha_excel,
                                                column=col_idx,
                                                value=formula
                                            )

                                            continue

                                        # valores padrão
                                        if valor == 0:
                                            valor = ""

                                        worksheet.cell(
                                            row=linha_excel,
                                            column=col_idx,
                                            value=valor
                                        )

                                    linha_excel += 1

                                
                            buffer.seek(0)

                            st.session_state.arquivo_desembolsos = buffer
                            st.session_state.mostrar_download = True


            ###################################################################################################
            # DOWNLOAD
            ###################################################################################################
            if st.session_state.mostrar_download:

                download = st.download_button(
                    label="Baixar relatório",
                    icon=":material/download:",
                    type="primary",
                    data=st.session_state.arquivo_desembolsos,
                    file_name=f"Relatorio_de_acompanhamento_de_desembolsos_{edital_selecionado_obj.get('nome_edital','').replace(' ','_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                ###################################################################################################
                # RESET COMPLETO
                ###################################################################################################
                if download:

                    st.session_state.ano_selecionado = ""
                    st.session_state.df_cambio_desembolsos = None
                    st.session_state.mostrar_inputs_ano = False
                    st.session_state.mostrar_relatorio = False
                    st.session_state.mostrar_download = False
                    st.session_state.arquivo_desembolsos = None

                    st.rerun()





    ###################################################################################################
    # MENSAGEM ABAIXO DOS BOTÕES
    ###################################################################################################
    if st.session_state.arquivo_desembolsos:
        st.caption("Relatório gerado. Clique para baixar.")








elif opcao_relatorio == "Relatório de acompanhamento de desembolsos por parcela":
    
    st.subheader("Relatório de acompanhamento de desembolsos por parcela")

    
    # Renderiza o filtro de editais 
    # projetos = filtro_editais()
    projetos, edital_selecionado_obj = filtro_editais()



    ###################################################################################################
    # VALIDAÇÃO DE EDITAL SELECIONADO
    ###################################################################################################
    if not edital_selecionado_obj:

        st.caption("Selecione um edital para iniciar a análise.")

        # impede execução do restante do fluxo
        st.stop()


    st.write(f"{len(projetos)} projetos")

    st.write('')
    st.write('')





    ###################################################################################################
    # SESSION STATE
    ###################################################################################################
    if "meses_parcelas" not in st.session_state:
        st.session_state.meses_parcelas = []

    if "df_cambio_parcelas" not in st.session_state:
        st.session_state.df_cambio_parcelas = None

    if "mostrar_gerar_relatorio" not in st.session_state:
        st.session_state.mostrar_gerar_relatorio = False

    if "mostrar_download" not in st.session_state:
        st.session_state.mostrar_download = False

    if "arquivo_parcelas" not in st.session_state:
        st.session_state.arquivo_parcelas = None


    ###################################################################################################
    # BOTÕES (RENDERIZAÇÃO CONDICIONAL)
    ###################################################################################################
    with st.container(horizontal=True):

        analisar_parcelas = st.button(
            "Analisar parcelas",
            icon=":material/search:",
            type="secondary"
        )

        gerar_relatorio = False
        baixar_relatorio = False

        if st.session_state.mostrar_gerar_relatorio:
            gerar_relatorio = st.button(
                "Gerar relatório",
                icon=":material/receipt_long:",
                type="secondary"
            )

        if st.session_state.mostrar_download:
            ###################################################################################################
            # BOTÃO DOWNLOAD
            ###################################################################################################
            download_clicado = st.download_button(
                label="Baixar relatório",
                icon=":material/download:",
                type="primary",
                data=st.session_state.arquivo_parcelas,
                file_name=f"Relatorio_de_acompanhamento_de_desembolsos_por_parcela_{edital_selecionado_obj.get('nome_edital','').replace(' ','_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


            ###################################################################################################
            # RESET DO ESTADO APÓS DOWNLOAD
            ###################################################################################################
            if download_clicado:

                # limpa dados do fluxo
                st.session_state.meses_parcelas = []
                st.session_state.df_cambio_parcelas = None

                # controla exibição dos botões
                st.session_state.mostrar_gerar_relatorio = False
                st.session_state.mostrar_download = False

                # limpa arquivo
                st.session_state.arquivo_parcelas = None

                # força rerun para voltar ao estado inicial
                st.rerun()



    ###################################################################################################
    # AÇÃO: ANALISAR PARCELAS
    ###################################################################################################
    if analisar_parcelas:

        # reseta estados seguintes
        st.session_state.mostrar_gerar_relatorio = False
        st.session_state.mostrar_download = False
        st.session_state.arquivo_parcelas = None

        if not projetos:
            st.warning("Nenhum projeto no edital selecionado.")
            time.sleep(3)

        else:

            ###################################################################################################
            # COLETA E TRATAMENTO DAS DATAS DAS PARCELAS
            ###################################################################################################
            datas = []

            for p in projetos:

                financeiro = p.get("financeiro", {})
                parcelas = financeiro.get("parcelas", [])

                for parcela in parcelas:

                    data_realizada = parcela.get("data_realizada")

                    if data_realizada:
                        try:
                            data = datetime.datetime.strptime(data_realizada, "%d/%m/%Y")
                            datas.append(data)
                        except:
                            pass


            ###################################################################################################
            # ORDENAÇÃO DAS DATAS
            ###################################################################################################
            datas_ordenadas = sorted(datas)


            ###################################################################################################
            # EXTRAÇÃO DE MÊS/ANO
            ###################################################################################################
            meses_ano = [data.strftime("%m/%Y") for data in datas_ordenadas]


            ###################################################################################################
            # REMOÇÃO DE DUPLICADOS
            ###################################################################################################
            meses_unicos = list(dict.fromkeys(meses_ano))


            ###################################################################################################
            # DATAFRAME BASE
            ###################################################################################################
            df_cambio = pd.DataFrame({
                "Mês": meses_unicos,
                "Cotação US$": [None] * len(meses_unicos)
            })


            ###################################################################################################
            # ARMAZENA NO SESSION STATE
            ###################################################################################################
            st.session_state.meses_parcelas = meses_unicos
            st.session_state.df_cambio_parcelas = df_cambio
            st.session_state.mostrar_gerar_relatorio = True

            st.rerun()


    ###################################################################################################
    # DATA EDITOR
    ###################################################################################################
    if st.session_state.df_cambio_parcelas is not None:

        st.write('')
        st.markdown("##### Câmbio US$ por mês")

        df_editado_parcelas = st.data_editor(
            st.session_state.df_cambio_parcelas,
            width=400,
            height="content",
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Mês": st.column_config.TextColumn(
                    "Mês",
                    disabled=True
                ),
                "Cotação US$": st.column_config.NumberColumn(
                    "Cotação US$",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f"
                )
            },
            key="data_editor_cambio_parcelas"
        )


    ###################################################################################################
    # AÇÃO: GERAR RELATÓRIO
    ###################################################################################################



    if gerar_relatorio:

        ###################################################################################################
        # VALIDAÇÃO DAS COTAÇÕES
        ###################################################################################################
        valores = df_editado_parcelas["Cotação US$"]

        if valores.isnull().any() or any(v == 0 for v in valores):

            st.warning("Preencha a cotação de todos os meses.")
            time.sleep(3)

        else:

            ###################################################################################################
            # CONVERSÃO PARA DICIONÁRIO
            ###################################################################################################
            cambio_dict = {
                row["Mês"]: row["Cotação US$"]
                for _, row in df_editado_parcelas.iterrows()
            }


            ###################################################################################################
            # CALCULAR STATUS DOS PROJETOS
            ###################################################################################################
            df_projetos = pd.DataFrame(projetos)

            df_projetos_status = calcular_status_projetos(df_projetos)

            # cria mapa: codigo -> status
            mapa_status = {
                row["codigo"]: row.get("status")
                for _, row in df_projetos_status.iterrows()
            }


            ###################################################################################################
            # CRIAÇÃO DO EXCEL
            ###################################################################################################
            buffer = io.BytesIO()

            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:



                workbook = writer.book
                worksheet = workbook.create_sheet(title="Desembolsos por parcela")

                writer.sheets["Desembolsos por parcela"] = worksheet


                ###################################################################################################
                # TÍTULO DA SEÇÃO DE CÂMBIO
                ###################################################################################################
                worksheet.cell(
                    row=1,
                    column=1,
                    value="Taxas de câmbio por mês"
                )


                ###################################################################################################
                # AGRUPAMENTO DOS MESES DE 3 EM 3
                ###################################################################################################
                meses_lista = list(cambio_dict.keys())

                grupos_meses = [
                    meses_lista[i:i+3]
                    for i in range(0, len(meses_lista), 3)
                ]


                ###################################################################################################
                # ESCRITA DOS BLOCOS (MÊS | COTAÇÃO)
                ###################################################################################################
                col_offset = 1

                for grupo in grupos_meses:

                    col_mes = col_offset
                    col_valor = col_offset + 1

                    for i, mes in enumerate(grupo):

                        linha_excel = i + 2  # começa na linha 2

                        # escreve mês
                        worksheet.cell(
                            row=linha_excel,
                            column=col_mes,
                            value=mes
                        )

                        # escreve cotação
                        worksheet.cell(
                            row=linha_excel,
                            column=col_valor,
                            value=cambio_dict.get(mes, "")
                        )

                    col_offset += 2  # avança para o próximo bloco











                ###################################################################################################
                # CABEÇALHO DA TABELA (LINHA 7)
                ###################################################################################################
                colunas = [
                    "id_cepf",
                    "UploadCG",
                    "Beneficiário",
                    "Valor do Contrato (R$)",
                    "Valor do Contrato Final",
                    "Diferença",
                ]

                # adiciona colunas das parcelas (1 a 6)
                for i in range(1, 7):
                    colunas.append(f"PARCELA {i}")
                    colunas.append(f"PARCELA {str(i).zfill(2)} (USD)")

                # colunas finais
                colunas.extend([
                    "ADITIVO (R$)",
                    "ADITIVO (US$)",
                    "Já Pago",
                    "Remanescente a receber",
                    "Devoluções R$",
                    "Devoluções US$",
                    "VALOR FINAL (R$)",
                    "VALOR FINAL (U$)",
                    "ADITIVOS",
                    "Data de Finalização (End Date)",
                    "Data de Encerramento (Close Date)",
                    "Status do projeto"
                ])






                # escreve cabeçalho
                for col_idx, col_nome in enumerate(colunas, start=1):
                    worksheet.cell(row=7, column=col_idx, value=col_nome)


                ###################################################################################################
                # PREENCHIMENTO DAS LINHAS (A PARTIR DA LINHA 8)
                ###################################################################################################
                linha_excel = 8

                for p in projetos:

                    ###################################################################################################
                    # CÓDIGO DO PROJETO 
                    ###################################################################################################

                    codigo_projeto = p.get("codigo", "")





                    ###################################################################################################
                    # ORGANIZAÇÃO
                    ###################################################################################################
                    id_org = p.get("id_organizacao")
                    org_info = mapa_organizacoes.get(str(id_org), {}) if id_org else {}
                    nome_organizacao = org_info.get("nome", "")


                    ###################################################################################################
                    # DADOS FINANCEIROS
                    ###################################################################################################
                    financeiro = p.get("financeiro", {})

                    valor_total = financeiro.get("valor_total", 0)
                    valor_aditivo = financeiro.get("valor_aditivo", 0)
                    valor_total_final = valor_total + valor_aditivo


                    ###################################################################################################
                    # PARCELAS
                    ###################################################################################################
                    parcelas = financeiro.get("parcelas", [])

                    # cria mapa de parcelas por número
                    mapa_parcelas = {
                        parcela.get("numero"): parcela
                        for parcela in parcelas
                    }

                    valores_parcelas = {}
                    valores_parcelas_usd = {}

                    for i in range(1, 7):

                        parcela = mapa_parcelas.get(i)

                        valor_rs = ""
                        valor_usd = ""

                        if parcela:

                            valor_rs = parcela.get("valor", "")

                            data_realizada = parcela.get("data_realizada")

                            if data_realizada:
                                try:
                                    data = datetime.datetime.strptime(data_realizada, "%d/%m/%Y")
                                    mes_ano = data.strftime("%m/%Y")

                                    cotacao = cambio_dict.get(mes_ano)

                                    if cotacao and valor_rs:
                                        valor_usd = valor_rs / cotacao  

                                except:
                                    pass

                        valores_parcelas[i] = valor_rs
                        valores_parcelas_usd[i] = valor_usd


                    ###################################################################################################
                    # JÁ PAGO (SOMA DAS PARCELAS PAGAS)
                    ###################################################################################################
                    ja_pago = 0

                    for parcela in parcelas:

                        if not parcela.get("data_realizada"):
                            continue

                        valor = parcela.get("valor", 0)

                        if isinstance(valor, (int, float)):
                            ja_pago += valor


                    ###################################################################################################
                    # REMANESCENTE A RECEBER (BASEADO NAS PARCELAS PAGAS)
                    ###################################################################################################

                    # garante que valor_aditivo seja numérico
                    valor_aditivo_seguro = valor_aditivo if isinstance(valor_aditivo, (int, float)) else 0

                    # soma das parcelas pagas (já calculado anteriormente como ja_pago)
                    remanescente = (valor_total + valor_aditivo_seguro) - ja_pago


                    ###################################################################################################
                    # DEVOLUÇÕES
                    ###################################################################################################
                    devolucao_rs = financeiro.get("valor_devolucao", "")
                    devolucao_usd = ""





                    ###################################################################################################
                    # VALOR FINAL (R$) - SOMA DE TODAS AS PARCELAS
                    ###################################################################################################
                    valor_final_rs = 0

                    for parcela in parcelas:

                        valor = parcela.get("valor", 0)

                        if isinstance(valor, (int, float)):
                            valor_final_rs += valor


                    ###################################################################################################
                    # VALOR FINAL (US$) - CONVERSÃO POR DATA DA PARCELA
                    ###################################################################################################
                    valor_final_usd = 0

                    for parcela in parcelas:

                        valor = parcela.get("valor", 0)
                        data_realizada = parcela.get("data_realizada")

                        if not data_realizada:
                            continue

                        try:
                            data = datetime.datetime.strptime(data_realizada, "%d/%m/%Y")
                            mes_ano = data.strftime("%m/%Y")

                            cotacao = cambio_dict.get(mes_ano)

                            if cotacao and isinstance(valor, (int, float)):
                                valor_final_usd += valor / cotacao  

                        except:
                            pass


                    ###################################################################################################
                    # ADITIVOS
                    ###################################################################################################
                    aditivos = valor_aditivo


                    ###################################################################################################
                    # DATA DE FINALIZAÇÃO (END DATE)
                    ###################################################################################################
                    data_finalizacao = p.get("data_fim_contrato", "")


                    ###################################################################################################
                    # DATA DE ENCERRAMENTO (CLOSE DATE)
                    ###################################################################################################
                    data_encerramento = ""

                    if parcelas:

                        # filtra parcelas que possuem data_realizada
                        parcelas_com_data = [
                            parcela for parcela in parcelas
                            if parcela.get("data_realizada")
                        ]

                        if parcelas_com_data:

                            # encontra a parcela com maior número
                            parcela_final = max(
                                parcelas_com_data,
                                key=lambda x: x.get("numero", 0)
                            )

                            data_encerramento = parcela_final.get("data_realizada", "")


                    ###################################################################################################
                    # STATUS DO PROJETO
                    ###################################################################################################
                    codigo_projeto = p.get("codigo")
                    status_projeto = mapa_status.get(codigo_projeto, "")






                    ###################################################################################################
                    # MONTAGEM DA LINHA
                    ###################################################################################################
                    linha = {
                        "id_cepf": codigo_projeto,
                        "UploadCG": "",
                        "Beneficiário": nome_organizacao,
                        "Valor do Contrato (R$)": valor_total,
                        "Valor do Contrato Final": valor_total_final,
                        "Diferença": valor_aditivo,
                    }

                    # adiciona parcelas
                    for i in range(1, 7):
                        linha[f"PARCELA {i}"] = valores_parcelas.get(i, "")
                        linha[f"PARCELA {str(i).zfill(2)} (USD)"] = valores_parcelas_usd.get(i, "")

                    # adiciona colunas finais
                    linha.update({
                        "ADITIVO (R$)": valor_aditivo,
                        "ADITIVO (US$)": "",
                        "Já Pago": ja_pago,
                        "Remanescente a receber": remanescente,
                        "Devoluções R$": devolucao_rs,
                        "Devoluções US$": devolucao_usd,
                        "VALOR FINAL (R$)": valor_final_rs,
                        "VALOR FINAL (U$)": valor_final_usd,
                        "ADITIVOS": aditivos,
                        "Data de Finalização (End Date)": data_finalizacao,
                        "Data de Encerramento (Close Date)": data_encerramento,
                        "Status do projeto": status_projeto                        
                    })


                    ###################################################################################################
                    # ESCRITA NA PLANILHA
                    ###################################################################################################
                    for col_idx, col_nome in enumerate(colunas, start=1):

                        valor = linha.get(col_nome, "")

                        # substitui zero por vazio
                        if valor == 0:
                            valor = ""

                        worksheet.cell(
                            row=linha_excel,
                            column=col_idx,
                            value=valor
                        )

                    linha_excel += 1




            ###################################################################################################
            # SALVA NO SESSION STATE
            ###################################################################################################
            st.session_state.arquivo_parcelas = buffer
            st.session_state.mostrar_download = True

            st.rerun()

















elif opcao_relatorio == "Relatório de acompanhamento completo":

    st.subheader("Relatório de acompanhamento completo")

    # Renderiza o filtro de editais 
    # projetos = filtro_editais()
    projetos, edital_selecionado_obj = filtro_editais()


    st.write(f"{len(projetos)} projetos")

    st.write('')
    st.write('')



    ###################################################################################################
    # SESSION STATE
    ###################################################################################################
    if "arquivo_acompanhamento_completo" not in st.session_state:
        st.session_state.arquivo_acompanhamento_completo = None


    ###################################################################################################
    # BOTÕES
    ###################################################################################################
    with st.container(horizontal=True):

        ###################################################################################################
        # BOTÃO GERAR RELATÓRIO
        ###################################################################################################
        if st.button("Gerar relatório", icon=":material/list_alt_add:"):

            ###################################################################################################
            # VALIDAÇÃO DE PROJETOS
            ###################################################################################################
            if not projetos:
                st.warning("Nenhum projeto encontrado para o edital selecionado.", icon=":material/warning:")
                st.session_state.arquivo_acompanhamento_completo = None
                time.sleep(3)

            else:

                with st.spinner("Gerando relatório..."):

                    ###################################################################################################
                    # MONTAGEM DOS DADOS
                    ###################################################################################################
                    dados = []


                    ###################################################################################################
                    # CALCULAR STATUS DOS PROJETOS (APENAS PROJETOS FILTRADOS DO EDITAL)
                    ###################################################################################################
                    df_projetos = pd.DataFrame(projetos)

                    df_projetos_status = calcular_status_projetos(df_projetos)

                    # cria mapa: codigo -> status
                    mapa_status = {
                        row["codigo"]: row.get("status")
                        for _, row in df_projetos_status.iterrows()
                    }





                    for p in projetos:


                        ###################################################################################################
                        # CÓDIGO DO PROJETO
                        ###################################################################################################
                        codigo_projeto = p["codigo"]

                        ###################################################################################################
                        # CONTRATO
                        ###################################################################################################
                        contrato_nome = p.get("contrato_nome", "")


                        ###################################################################################################
                        # DIREÇÕES ESTRATÉGICAS
                        ###################################################################################################
                        direcoes = p.get("direcoes_estrategicas", [])

                        lista_direcoes_formatadas = []

                        for direcao in direcoes:

                            tema = direcao.get("tema", "")
                            subcategorias = direcao.get("subcategorias", [])

                            subcategorias_limpo = [
                                sub.strip().replace("\n", " ")
                                for sub in subcategorias
                                if sub
                            ]

                            if subcategorias_limpo:
                                sub_str = ", ".join(subcategorias_limpo)
                                direcao_formatada = f"{tema} ({sub_str})"
                            else:
                                direcao_formatada = tema

                            lista_direcoes_formatadas.append(direcao_formatada)

                        direcoes_str = ", ".join(lista_direcoes_formatadas)


                        ###################################################################################################
                        # NOME DA PROPOSTA
                        ###################################################################################################
                        nome_projeto = p.get("nome_do_projeto", "")


                        ###################################################################################################
                        # ORGANIZAÇÃO (NOME + SIGLA)
                        ###################################################################################################
                        id_org = p.get("id_organizacao")

                        org_info = mapa_organizacoes.get(str(id_org), {}) if id_org else {}

                        nome_organizacao = org_info.get("nome", "")
                        sigla_organizacao = org_info.get("sigla", "")



                        ###################################################################################################
                        # UF (ESTADOS DO PROJETO)
                        ###################################################################################################
                        estados = p.get("locais", {}).get("estados", [])

                        nomes_estados = [
                            estado.get("nome_estado", "")
                            for estado in estados
                            if estado.get("nome_estado")
                        ]

                        uf_str = ", ".join(nomes_estados)




                        ###################################################################################################
                        # CONTATOS DO PROJETO
                        ###################################################################################################
                        contatos = p.get("contatos", [])


                        ###################################################################################################
                        # RESPONSÁVEIS LEGAIS (ASSINAM DOCUMENTOS)
                        ###################################################################################################
                        nomes_responsaveis = [
                            contato.get("nome", "")
                            for contato in contatos
                            if contato.get("assina_docs") is True and contato.get("nome")
                        ]

                        responsaveis_str = ", ".join(nomes_responsaveis)


                        ###################################################################################################
                        # E-MAIL RESPONSÁVEL LEGAL
                        ###################################################################################################
                        emails_responsaveis = [
                            contato.get("email", "")
                            for contato in contatos
                            if contato.get("assina_docs") is True and contato.get("email")
                        ]

                        emails_responsaveis_str = "; ".join(emails_responsaveis)


                        ###################################################################################################
                        # E-MAILS DA EQUIPE (TODOS OS CONTATOS)
                        ###################################################################################################
                        emails_equipe = [
                            contato.get("email", "")
                            for contato in contatos
                            if contato.get("email")
                        ]

                        emails_equipe_str = "; ".join(emails_equipe)


                        ###################################################################################################
                        # TELEFONES (TODOS OS CONTATOS)
                        ###################################################################################################
                        telefones = [
                            contato.get("telefone", "")
                            for contato in contatos
                            if contato.get("telefone")
                        ]

                        telefones_str = "; ".join(telefones)





                        ###################################################################################################
                        # RESPONSÁVEIS PELO PROJETO (USUÁRIOS VINCULADOS PELO CÓDIGO)
                        ###################################################################################################
                        codigo_projeto = p.get("codigo", "")

                        nomes_responsaveis_projeto = []

                        # percorre todos os usuários do sistema
                        for pessoa in pessoas:

                            ###################################################################################################
                            # FILTRO: APENAS USUÁRIOS DO TIPO BENEFICIÁRIO
                            ###################################################################################################
                            if pessoa.get("tipo_usuario") != "beneficiario":
                                continue

                            projetos_pessoa = pessoa.get("projetos", [])

                            # verifica se o código do projeto atual está vinculado ao usuário
                            if codigo_projeto in projetos_pessoa:

                                nome = pessoa.get("nome_completo", "")

                                if nome:
                                    nomes_responsaveis_projeto.append(nome)

                        # remove duplicidades e ordena para padronização do relatório
                        nomes_responsaveis_projeto = sorted(set(nomes_responsaveis_projeto))

                        responsaveis_projeto_str = ", ".join(nomes_responsaveis_projeto)





                        ###################################################################################################
                        # CEP DA ORGANIZAÇÃO
                        ###################################################################################################
                        cep_organizacao = org_info.get("cep", "")




                        ###################################################################################################
                        # CIDADE(S) DO PROJETO (MUNICÍPIOS)
                        ###################################################################################################
                        municipios = p.get("locais", {}).get("municipios", [])

                        nomes_municipios = [
                            m.get("nome_municipio", "")
                            for m in municipios
                            if m.get("nome_municipio")
                        ]

                        cidades_str = ", ".join(nomes_municipios)



                        ###################################################################################################
                        # VALORES FINANCEIROS   (VALOR TOTAL (R$), VALOR TOTAL + ADITIVO e VALOR TOTAL FINAL)
                        ###################################################################################################
                        financeiro = p.get("financeiro", {})

                        # valor total previsto do projeto
                        valor_total = financeiro.get("valor_total", 0)

                        # valor de aditivo (caso exista)
                        valor_aditivo = financeiro.get("valor_aditivo", 0)

                        # soma valor total + aditivo
                        valor_total_com_aditivo = valor_total + valor_aditivo

                        ###################################################################################################
                        # VALOR TOTAL FINAL (SOMA DOS LANÇAMENTOS)
                        ###################################################################################################
                        orcamentos = financeiro.get("orcamento", [])

                        valor_total_final = 0

                        # percorre todas as despesas do orçamento
                        for despesa in orcamentos:

                            lancamentos = despesa.get("lancamentos", [])

                            # soma todos os lançamentos de cada despesa
                            for lanc in lancamentos:

                                valor = lanc.get("valor_despesa", 0)

                                # garante que apenas valores válidos sejam somados
                                if isinstance(valor, (int, float)):
                                    valor_total_final += valor



                        ###################################################################################################
                        # STATUS DO PROJETO
                        ###################################################################################################
                        codigo_projeto = p.get("codigo", "")

                        status_projeto = mapa_status.get(codigo_projeto, "")



                        ###################################################################################################
                        # PARCELA 1 (ENTRADA)
                        ###################################################################################################
                        financeiro = p.get("financeiro", {})
                        parcelas = financeiro.get("parcelas", [])

                        valor_entrada = ""
                        data_pagto_entrada = ""

                        # busca parcela com numero = 1
                        for parcela in parcelas:

                            if parcela.get("numero") == 1:

                                valor_entrada = parcela.get("valor", "")
                                data_pagto_entrada = parcela.get("data_realizada", "")

                                break  # interrompe ao encontrar


                        ###################################################################################################
                        # RELATÓRIO 1
                        ###################################################################################################
                        relatorios = p.get("relatorios", [])

                        data_solicitacao_pagto = ""
                        data_programada_r01 = ""
                        data_entrega_r01 = ""

                        # busca relatório com numero = 1
                        for rel in relatorios:

                            if rel.get("numero") == 1:

                                data_solicitacao_pagto = rel.get("data_aprovacao", "")   # ??????????????????????????? está correto?
                                data_programada_r01 = rel.get("data_prevista", "")
                                data_entrega_r01 = rel.get("data_envio", "")

                                break  # interrompe ao encontrar




                        ###################################################################################################
                        # PARCELA 2
                        ###################################################################################################
                        valor_parcela_2 = ""

                        # busca parcela com numero = 2
                        for parcela in parcelas:

                            if parcela.get("numero") == 2:

                                valor_parcela_2 = parcela.get("valor", "")

                                break  # interrompe ao encontrar


                        ###################################################################################################
                        # RELATÓRIOS (REGRAS ESPECÍFICAS)
                        ###################################################################################################
                        data_solicitacao_pagto_p02 = ""
                        data_programada_r02 = ""
                        data_entrega_r02 = ""

                        for rel in relatorios:

                            numero_rel = rel.get("numero")

                            # P02 usa relatório 1
                            # regra de negócio: P02 usa aprovação do R01, mas datas operacionais do R02
                            if numero_rel == 1:
                                data_solicitacao_pagto_p02 = rel.get("data_aprovacao", "")

                            # demais campos usam relatório 2
                            if numero_rel == 2:
                                data_programada_r02 = rel.get("data_prevista", "")
                                data_entrega_r02 = rel.get("data_envio", "")






                        ###################################################################################################
                        # PARCELA 3
                        ###################################################################################################
                        valor_parcela_3 = ""

                        # busca parcela com numero = 3
                        for parcela in parcelas:

                            if parcela.get("numero") == 3:

                                valor_parcela_3 = parcela.get("valor", "")

                                break  # interrompe ao encontrar


                        ###################################################################################################
                        # RELATÓRIOS (REGRAS ESPECÍFICAS)
                        ###################################################################################################
                        data_solicitacao_pagto_p03 = ""
                        data_programada_r03 = ""
                        data_entrega_r03 = ""

                        for rel in relatorios:

                            numero_rel = rel.get("numero")

                            # regra de negócio: P03 usa aprovação do R02
                            if numero_rel == 2:
                                data_solicitacao_pagto_p03 = rel.get("data_aprovacao", "")

                            # datas operacionais do R03
                            if numero_rel == 3:
                                data_programada_r03 = rel.get("data_prevista", "")
                                data_entrega_r03 = rel.get("data_envio", "")






                        ###################################################################################################
                        # PARCELA 4
                        ###################################################################################################
                        valor_parcela_4 = ""
                        data_solicitacao_pagto_p04 = ""
                        data_programada_r04 = ""
                        data_entrega_r04 = ""

                        for parcela in parcelas:
                            if parcela.get("numero") == 4:
                                valor_parcela_4 = parcela.get("valor", "")
                                break

                        for rel in relatorios:
                            numero_rel = rel.get("numero")

                            if numero_rel == 3:
                                data_solicitacao_pagto_p04 = rel.get("data_aprovacao", "")

                            if numero_rel == 4:
                                data_programada_r04 = rel.get("data_prevista", "")
                                data_entrega_r04 = rel.get("data_envio", "")


                        ###################################################################################################
                        # PARCELA 5
                        ###################################################################################################
                        valor_parcela_5 = ""
                        data_solicitacao_pagto_p05 = ""
                        data_programada_r05 = ""
                        data_entrega_r05 = ""

                        for parcela in parcelas:
                            if parcela.get("numero") == 5:
                                valor_parcela_5 = parcela.get("valor", "")
                                break

                        for rel in relatorios:
                            numero_rel = rel.get("numero")

                            if numero_rel == 4:
                                data_solicitacao_pagto_p05 = rel.get("data_aprovacao", "")

                            if numero_rel == 5:
                                data_programada_r05 = rel.get("data_prevista", "")
                                data_entrega_r05 = rel.get("data_envio", "")


                        ###################################################################################################
                        # PARCELA 6
                        ###################################################################################################
                        valor_parcela_6 = ""
                        data_solicitacao_pagto_p06 = ""

                        for parcela in parcelas:
                            if parcela.get("numero") == 6:
                                valor_parcela_6 = parcela.get("valor", "")
                                break

                        for rel in relatorios:
                            numero_rel = rel.get("numero")

                            if numero_rel == 5:
                                data_solicitacao_pagto_p06 = rel.get("data_aprovacao", "")






                        ###################################################################################################
                        # ADITIVO E DESEMBOLSO
                        ###################################################################################################
                        financeiro = p.get("financeiro", {})

                        valor_aditivo = financeiro.get("valor_aditivo", 0)

                        parcelas = financeiro.get("parcelas", [])

                        valor_total_desembolsado = 0

                        # soma todas as parcelas pagas do projeto
                        for parcela in parcelas:

                            # considera apenas parcelas que possuem data de pagamento
                            if not parcela.get("data_realizada"):
                                continue

                            valor = parcela.get("valor", 0)

                            if isinstance(valor, (int, float)):
                                valor_total_desembolsado += valor




                        ###################################################################################################
                        # KBAs
                        ###################################################################################################
                        kbas = p.get("locais", {}).get("kbas", [])

                        nomes_kbas = [
                            kba.get("nome_kba", "")
                            for kba in kbas
                            if kba.get("nome_kba")
                        ]

                        kbas_str = ", ".join(nomes_kbas)


                        ###################################################################################################
                        # ÁREAS PROTEGIDAS
                        ###################################################################################################
                        areas_protegidas = p.get("locais", {}).get("areas_protegidas", [])

                        nomes_areas = [
                            area.get("nome_area_protegida", "")
                            for area in areas_protegidas
                            if area.get("nome_area_protegida")
                        ]

                        areas_protegidas_str = ", ".join(nomes_areas)


                        ###################################################################################################
                        # CORREDORES
                        ###################################################################################################
                        corredores = p.get("locais", {}).get("corredores", [])

                        nomes_corredores = [
                            corredor.get("nome_corredor", "")
                            for corredor in corredores
                            if corredor.get("nome_corredor")
                        ]

                        corredores_str = ", ".join(nomes_corredores)







                        dados.append({
                            "id_CEPF": codigo_projeto,
                            "Contrato": contrato_nome,
                            "Direções estratégicas": direcoes_str,
                            "Nome da proposta": nome_projeto,
                            "Organização": nome_organizacao,
                            "Sigla": sigla_organizacao,
                            "UF": uf_str,
                            "Nome Responsável Legal (Quem vai assinar o contrato e os recibos)": responsaveis_str,
                            "E-mail responsável legal": emails_responsaveis_str,
                            "E-mails da equipe": emails_equipe_str,
                            "Telefone": telefones_str,
                            "Responsável(is) pelo projeto": responsaveis_projeto_str,
                            "CEP": cep_organizacao,
                            "Cidade(s)": cidades_str,
                            "KBAs": kbas_str,
                            "Áreas protegidas": areas_protegidas_str,
                            "Corredores": corredores_str,

                            "Verificação de Segurança (CSI Number)": "",

                            "VALOR TOTAL (R$)": valor_total,
                            "VALOR TOTAL + ADITIVO": valor_total_com_aditivo,
                            "VALOR TOTAL FINAL": valor_total_final,
                            "VALOR TOTAL EM US$": "",
                            "Deobligation": "",
                            "Status": status_projeto,

                            "RISK ASSESSMENT": "",	
                            "FINANCIAL RISK ASSESSMENT (Low, Medium, High)": "",
                            "FINANCIAL RISK ASSESSMENT (NOTA GERAL (/100))": "",


                            "Valor Entrada": valor_entrada,
                            "P01_Data da Solicitação_Pagto": "",
                            "Data de Pagto_Entrada": data_pagto_entrada,
                            "Data Programada_R01": data_programada_r01,
                            "Data de Entrega_R01": data_entrega_r01,

                            "P02_Data da Solicitação_Pagto": data_solicitacao_pagto_p02,
                            "Valor (R$) P02": valor_parcela_2,
                            "Data Programada_R02": data_programada_r02,
                            "Data de Entrega_R02": data_entrega_r02,

                            "P03_Data da Solicitação_Pagto": data_solicitacao_pagto_p03,
                            "Valor (R$) P03": valor_parcela_3,
                            "Data Programada_R03": data_programada_r03,
                            "Data de Entrega_R03": data_entrega_r03,

                            "P04_Data da Solicitação_Pagto": data_solicitacao_pagto_p04,
                            "Valor (R$) P04": valor_parcela_4,
                            "Data Programada_R04": data_programada_r04,
                            "Data de Entrega_R04": data_entrega_r04,

                            "P05_Data da Solicitação_Pagto": data_solicitacao_pagto_p05,
                            "Valor (R$) P05": valor_parcela_5,
                            "Data Programada_R05": data_programada_r05,
                            "Data de Entrega_R05": data_entrega_r05,

                            "P06_Data da Solicitação_Pagto": data_solicitacao_pagto_p06,
                            "Valor (R$) P06": valor_parcela_6,

                            "Upload no CG": "",

                            "ADITIVOS": valor_aditivo,
                            "Valor Total Desembolsado (soma das parcelas) R$": valor_total_desembolsado,
         
                            "Valor Total Desembolsado (soma das parcelas)_U$": "",

                            # A última coluna "Valor residual R$" será preenchida posteriormente com fórmula

                        })



                    ###################################################################################################
                    # CRIA DATAFRAME
                    ###################################################################################################
                    df = pd.DataFrame(dados)


                    ###################################################################################################
                    # COLUNA "Valor residual_R$" COM FÓRMULA 
                    ###################################################################################################
                    # calcula saldo: (VALOR TOTAL + ADITIVO) - VALOR TOTAL FINAL
                    # colunas Q e R

                    df["Valor residual R$"] = [
                        f"=T{idx+2}-U{idx+2}"
                        for idx in range(len(df))
                    ]

                    ###################################################################################################
                    # CRIAÇÃO DO EXCEL
                    ###################################################################################################
                    buffer = io.BytesIO()

                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        df.to_excel(
                            writer,
                            index=False,
                            sheet_name="Acompanhamento Completo"
                        )

                    buffer.seek(0)


                    ###################################################################################################
                    # SALVA NO SESSION STATE
                    ###################################################################################################
                    st.session_state.arquivo_acompanhamento_completo = buffer

                    st.rerun()


        ###################################################################################################
        # BOTÃO DOWNLOAD
        ###################################################################################################
        if st.session_state.arquivo_acompanhamento_completo:

            # Nome do edital (seguro para arquivo)
            nome_edital = edital_selecionado_obj.get("nome_edital", "") if edital_selecionado_obj else ""
            nome_edital_arquivo = nome_edital.replace(" ", "_")

            download_clicado = st.download_button(
                label="Baixar relatório",
                type="primary",
                icon=":material/download:",
                data=st.session_state.arquivo_acompanhamento_completo,
                file_name=f"Relatorio_acompanhamento_completo_{nome_edital_arquivo}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            ###################################################################################################
            # LIMPA SESSION STATE APÓS DOWNLOAD
            ###################################################################################################
            if download_clicado:
                st.session_state.arquivo_acompanhamento_completo = None
                st.rerun()


    ###################################################################################################
    # MENSAGEM FINAL
    ###################################################################################################
    if st.session_state.arquivo_acompanhamento_completo:
        st.caption("Relatório gerado. Clique para baixar.")












elif opcao_relatorio == "Lista de comunidades":

    st.subheader("Lista de comunidades")

    ###################################################################################################
    # FILTRO DE EDITAIS
    ###################################################################################################
    projetos, edital_selecionado_obj = filtro_editais()

    st.write(f"{len(projetos)} projetos")

    st.write('')
    st.write('')


    ###################################################################################################
    # SESSION STATE
    ###################################################################################################
    if "arquivo_lista_comunidades" not in st.session_state:
        st.session_state.arquivo_lista_comunidades = None


    ###################################################################################################
    # BOTÕES
    ###################################################################################################
    with st.container(horizontal=True):

        ###################################################################################################
        # BOTÃO GERAR RELATÓRIO (APENAS SE EDITAL FOI SELECIONADO)
        ###################################################################################################
        if edital_selecionado_obj:

            gerar = st.button("Gerar relatório", icon=":material/list_alt_add:")

            if gerar:

                ###################################################################################################
                # VALIDAÇÃO
                ###################################################################################################
                if not projetos:
                    st.warning("Nenhum projeto encontrado para o edital selecionado.", icon=":material/warning:")
                    st.session_state.arquivo_lista_comunidades = None
                    time.sleep(3)

                else:

                    with st.spinner("Gerando relatório..."):

                        ###################################################################################################
                        # MONTAGEM DOS DADOS
                        ###################################################################################################
                        dados = []

                        for p in projetos:

                            ###################################################################################################
                            # DADOS BÁSICOS
                            ###################################################################################################
                            codigo = p.get("codigo", "")
                            sigla = p.get("sigla", "")

                            id_org = p.get("id_organizacao")
                            org_info = mapa_organizacoes.get(str(id_org), {}) if id_org else {}
                            nome_organizacao = org_info.get("nome", "")

                            linha = {
                                "Código": codigo,
                                "Sigla": sigla,
                                "Organização": nome_organizacao
                            }

                            ###################################################################################################
                            # LOCALIDADES
                            ###################################################################################################
                            localidades = p.get("locais", {}).get("localidades", [])

                            for idx, loc in enumerate(localidades, start=1):

                                linha[f"Nome da localidade {idx}"] = loc.get("nome_localidade", "")
                                linha[f"Município {idx}"] = loc.get("municipio", "")
                                linha[f"Latitude {idx}"] = loc.get("latitude", "")
                                linha[f"Longitude {idx}"] = loc.get("longitude", "")

                                ###################################################################################################
                                # BENEFICIÁRIOS
                                ###################################################################################################
                                beneficiarios = loc.get("beneficiarios", [])

                                tipos_beneficiarios = [
                                    b.get("tipo_beneficiario", "")
                                    for b in beneficiarios
                                    if b.get("tipo_beneficiario")
                                ]

                                linha[f"Beneficiários {idx}"] = ", ".join(tipos_beneficiarios)

                            dados.append(linha)

                        ###################################################################################################
                        # DATAFRAME E EXCEL
                        ###################################################################################################
                        df = pd.DataFrame(dados)

                        buffer = io.BytesIO()

                        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                            df.to_excel(writer, index=False, sheet_name="Lista de comunidades")

                        buffer.seek(0)

                        st.session_state.arquivo_lista_comunidades = buffer

                        st.rerun()


        ###################################################################################################
        # BOTÃO DOWNLOAD (PRIMARY)
        ###################################################################################################
        if st.session_state.arquivo_lista_comunidades:

            nome_edital = edital_selecionado_obj.get("nome_edital", "") if edital_selecionado_obj else ""
            nome_edital_arquivo = nome_edital.replace(" ", "_")

            download_clicado = st.download_button(
                label="Baixar relatório",
                icon=":material/download:",
                data=st.session_state.arquivo_lista_comunidades,
                file_name=f"Lista_de_comunidades_{nome_edital_arquivo}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

            ###################################################################################################
            # LIMPA APÓS DOWNLOAD
            ###################################################################################################
            if download_clicado:
                st.session_state.arquivo_lista_comunidades = None
                st.rerun()









    ###################################################################################################
    # MENSAGEM FINAL
    ###################################################################################################
    if st.session_state.arquivo_lista_comunidades:
        st.caption("Relatório gerado. Clique para baixar.")




