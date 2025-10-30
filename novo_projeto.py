import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao # Funções personalizadas
import pandas as pd
import locale
import re
import time
from geobr import read_indigenous_land, read_conservation_units, read_biomes, read_state, read_municipality
import geopandas as gpd
import bson

###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Importa coleções e cria dataframes
col_pessoas = db["pessoas"]
df_pessoas = pd.DataFrame(list(col_pessoas.find()))

col_projetos = db["projetos"]
df_projetos = pd.DataFrame(list(col_projetos.find()))

col_organizacoes = db["organizacoes"]
df_organizacoes = pd.DataFrame(list(col_organizacoes.find()))

col_editais = db["editais"]
df_editais = pd.DataFrame(list(col_editais.find()))

col_temas = db["temas_projetos"]
df_temas = pd.DataFrame(list(col_temas.find()))

col_publicos = db["publicos"]
df_publicos = pd.DataFrame(list(col_publicos.find()))

###########################################################################################################
# CONFIGURAÇÃO DE LOCALE
###########################################################################################################


# CONFIGURAÇÃO DE LOCALIDADE PARA PORTUGUÊS (Ajuste conforme seu SO)
try:
    # Tenta a configuração comum em sistemas Linux/macOS
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        # Tenta a configuração comum em alguns sistemas Windows
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
    except locale.Error:
        # Se falhar, usa a configuração padrão (geralmente inglês)
        print("Aviso: Não foi possível definir a localidade para Português. Usando a localidade padrão.")






###########################################################################################################
# FUNÇÕES
###########################################################################################################






###########################################################################################################
# TRATAMENTO DE DADOS   
###########################################################################################################


# Inclulir o status no dataframe de projetos
df_projetos['status'] = 'Em dia'

# Converter object_id para string
# df_pessoas['_id'] = df_pessoas['_id'].astype(str)
df_projetos['_id'] = df_projetos['_id'].astype(str)

# Convertendo datas de string para datetime
df_projetos['data_inicio_contrato_dtime'] = pd.to_datetime(
    df_projetos['data_inicio_contrato'], 
    format="%d/%m/%Y", 
    dayfirst=True, 
    errors="coerce"
)

df_projetos['data_fim_contrato_dtime'] = pd.to_datetime(
    df_projetos['data_fim_contrato'], 
    format="%d/%m/%Y", 
    dayfirst=True, 
    errors="coerce"
)




###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################

# Define o layout da página como largura total
st.set_page_config(layout="wide")

# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Novo projeto")


tab_organizacao, tab_projeto = st.tabs(["Cadastrar Organização", "Cadastrar Projeto"])

with tab_organizacao:

    st.write('')

    st.write("**Verifique se a Organização já está cadastrada:**")

    st.write('')

    df_organizacoes= df_organizacoes[['sigla_organizacao', 'nome_organizacao', 'cnpj']]

    st.dataframe(df_organizacoes,
                 hide_index=True,
                 column_order=['sigla_organizacao', 'nome_organizacao', 'cnpj'],
                 column_config={
                     "sigla_organizacao": st.column_config.Column(
                         label="Sigla",
                         width="small"
                     ),
                     "nome_organizacao": st.column_config.Column(
                         label="Nome da organização",
                         width="large"
                     ),
                     "cnpj": st.column_config.Column(
                         label="CNPJ",
                         width="small"
                     )
                 })

    st.write('')

    st.write("**Se a Organização não aparece na lista, faça o cadastro:**")

    with st.expander("Cadastrar Organização"):

        with st.form(key="organizacao_form", border=False):

            # Regex para CNPJ no formato XX.XXX.XXX/XXXX-XX
            CNPJ_REGEX = r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$"

            sigla_organizacao = st.text_input("Sigla da Organização")
            nome_organizacao = st.text_input("Nome da Organização")
            cnpj = st.text_input("CNPJ", placeholder="00.000.000/0000-00")

            submit_button = st.form_submit_button("Salvar", icon=":material/save:", type="primary")

            if submit_button:

                # Verifica campos vazios
                if not sigla_organizacao or not nome_organizacao or not cnpj:
                    st.error("Todos os campos devem ser preenchidos.")
                
                # Verifica formato do CNPJ usando regex
                elif not re.match(CNPJ_REGEX, cnpj):
                    st.error("CNPJ inválido! Use o formato 00.000.000/0000-00")
                
                else:
                    # Verifica duplicidade no banco
                    sigla_existente = col_organizacoes.find_one({"sigla_organizacao": sigla_organizacao})
                    cnpj_existente = col_organizacoes.find_one({"cnpj": cnpj})

                    if sigla_existente:
                        st.error(f"A sigla '{sigla_organizacao}' já está cadastrada em outra Organização.")
                    elif cnpj_existente:
                        st.error(f"O CNPJ '{cnpj}' já está cadastrado em outra organização.")
                    else:
                        # Inserção no banco
                        novo_doc = {
                            "sigla_organizacao": sigla_organizacao,
                            "nome_organizacao": nome_organizacao,
                            "cnpj": cnpj
                        }
                        col_organizacoes.insert_one(novo_doc)
                        st.success("Organização cadastrada com sucesso!")
                        
                        time.sleep(3)
                        st.rerun()



with tab_projeto:

    st.write('')

    # st.write("**Passo 1: Informações cadastrais**")

    ######################################################################################################
    # Carregamento da geografia
    ######################################################################################################

    # FUNÇÕES ------------------------------------------------------------------------

    @st.cache_data(show_spinner="Carregando estados...")
    def carregar_ufs(ano=2020):
        return read_state(year=ano)

    @st.cache_data(show_spinner="Carregando municipios...")
    def carregar_municipios(ano=2024):
        return read_municipality(year=ano)

    @st.cache_data(show_spinner="Carregando terras indígenas...")
    def carregar_terras_indigenas(data=201907):
        return read_indigenous_land(date=data)

    @st.cache_data(show_spinner="Carregando unidades de conservação...")
    def carregar_uc(data=201909):
        return read_conservation_units(date=data)

    @st.cache_data(show_spinner="Carregando biomas...")
    def carregar_biomas(ano=2019):
        return read_biomes(year=ano)

    @st.cache_data(show_spinner="Carregando assentamentos...")
    def carregar_assentamentos():
        return gpd.read_file("shapefiles/Assentamentos-SAB-INCRA.shp")

    @st.cache_data(show_spinner="Carregando quilombos...")
    def carregar_quilombos():
        return gpd.read_file("shapefiles/Quilombos-SAB-INCRA.shp")

    @st.cache_data(show_spinner="Carregando bacias hidrográficas (micro)...")
    def carregar_bacias_micro():
        return gpd.read_file("shapefiles/micro_RH.shp")

    @st.cache_data(show_spinner="Carregando bacias hidrográficas (meso)...")
    def carregar_bacias_meso():
        return gpd.read_file("shapefiles/meso_RH.shp")

    @st.cache_data(show_spinner="Carregando bacias hidrográficas (macro)...")
    def carregar_bacias_macro():
        return gpd.read_file("shapefiles/macro_RH.shp")

    # CARREGAR DADOS -----------------------------------------------------------------

    dados_ufs = carregar_ufs()
    dados_municipios = carregar_municipios()
    dados_ti = carregar_terras_indigenas()
    dados_uc = carregar_uc()
    dados_assentamentos = carregar_assentamentos()
    dados_quilombos = carregar_quilombos()
    dados_bacias_macro = carregar_bacias_macro()
    dados_bacias_meso = carregar_bacias_meso()
    dados_bacias_micro = carregar_bacias_micro()

    # dados_biomas = carregar_biomas()
    # # Remover linha "Sistema Costeiro" e ordenar alfabeticamente
    # dados_biomas = (
    #     dados_biomas[dados_biomas["name_biome"] != "Sistema Costeiro"]
    #     .sort_values(by="name_biome", ascending=True)
    #     .reset_index(drop=True)
    # )

    # --- Padronizar nomes das colunas das bacias ---
    dados_bacias_macro = dados_bacias_macro.rename(columns={"cd_macroRH": "codigo", "nm_macroRH": "nome"})
    dados_bacias_meso = dados_bacias_meso.rename(columns={"cd_mesoRH": "codigo", "nm_mesoRH": "nome"})
    dados_bacias_micro = dados_bacias_micro.rename(columns={"cd_microRH": "codigo", "nm_microRH": "nome"})

    # Padronizar assentamentos e quilombos (ajuste conforme seus shapefiles)
    if "cd_sipra" in dados_assentamentos.columns:
        dados_assentamentos = dados_assentamentos.rename(columns={"cd_sipra": "codigo", "nome_proje": "nome"})
    if "id" in dados_quilombos.columns:
        dados_quilombos = dados_quilombos.rename(columns={"id": "codigo", "name": "nome"})
        
    # --- Ordenar alfabeticamente pelo nome ---
    dados_ti = dados_ti.sort_values(by="terrai_nom", ascending=True, ignore_index=True) if "terrai_nom" in dados_ti.columns else dados_ti
    dados_uc = dados_uc.sort_values(by="name_conservation_unit", ascending=True, ignore_index=True) if "name_conservation_unit" in dados_uc.columns else dados_uc
    # dados_biomas = dados_biomas.sort_values(by="name_biome", ascending=True, ignore_index=True) if "name_biome" in dados_biomas.columns else dados_biomas
    dados_bacias_macro = dados_bacias_macro.sort_values(by="nome", ascending=True, ignore_index=True)
    dados_bacias_meso = dados_bacias_meso.sort_values(by="nome", ascending=True, ignore_index=True)
    dados_bacias_micro = dados_bacias_micro.sort_values(by="nome", ascending=True, ignore_index=True)
    dados_assentamentos = dados_assentamentos.sort_values(by="nome", ascending=True, ignore_index=True)
    dados_quilombos = dados_quilombos.sort_values(by="nome", ascending=True, ignore_index=True)
    dados_municipios = dados_municipios.sort_values(by="name_muni", ascending=True, ignore_index=True) if "name_muni" in dados_municipios.columns else dados_municipios
    dados_ufs = dados_ufs.sort_values(by="name_state", ascending=True, ignore_index=True) if "name_state" in dados_ufs.columns else dados_ufs

    # --- Corrigir tipos de código para int (sem casas decimais) ---
    def corrigir_codigo(df, colunas):
        for col in colunas:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: int(x) if pd.notna(x) else None)
        return df

    dados_ufs = corrigir_codigo(dados_ufs, ["code_state"])
    dados_municipios = corrigir_codigo(dados_municipios, ["code_muni"])
    # dados_biomas = corrigir_codigo(dados_biomas, ["code_biome"])


    # Mapeamentos de código para label
    
    # Estados
    uf_codigo_para_label = {
        str(row["code_state"]): f"{row['name_state']} ({int(row['code_state'])})"
        for _, row in dados_ufs.iterrows()
    }

    # Municípios
    municipios_codigo_para_label = {
        str(row["code_muni"]): f"{row['name_muni']} ({int(row['code_muni'])})"
        for _, row in dados_municipios.iterrows()
    }

    # Terras Indígenas
    ti_codigo_para_label = {
        str(row["code_terrai"]): f"{row['terrai_nom']} ({int(row['code_terrai'])})"
        for _, row in dados_ti.iterrows()
    }

    # Unidades de Conservação
    uc_codigo_para_label = {
        str(row["code_conservation_unit"]): f"{row['name_conservation_unit']} ({row['code_conservation_unit']})"
        for _, row in dados_uc.iterrows()
    }

    # Assentamentos
    assent_codigo_para_label = {
        str(row["codigo"]): f"{row['nome']} ({row['codigo']})"
        for _, row in dados_assentamentos.iterrows()
    }

    # Quilombos
    quilombo_codigo_para_label = {
        str(row["codigo"]): f"{row['nome']} ({row['codigo']})"
        for _, row in dados_quilombos.iterrows()
    }
    
    # Bacias Hidrográficas
    bacia_micro_codigo_para_label = {
        str(row["codigo"]): f"{row['nome']} ({row['codigo']})" for _, row in dados_bacias_micro.iterrows()
    }

    bacia_meso_codigo_para_label = {
        str(row["codigo"]): f"{row['nome']} ({row['codigo']})" for _, row in dados_bacias_meso.iterrows()
    }

    bacia_macro_codigo_para_label = {
        str(row["codigo"]): f"{row['nome']} ({row['codigo']})" for _, row in dados_bacias_macro.iterrows()
    }


    # FIM DA PREPARAÇÃO DA GEOGRAFIA -------------------------------------------------------------------------------------




    # ##############################################################################################################
    # FORMULARIO DE CADASTRO DE PROJETO
    # ##############################################################################################################

    # nro_parcelas = st.number_input("Nro de Parcelas:", min_value=1, value=1, width=200)

    try:
        st.write(f"**Cadastrando o projeto {st.session_state.cadastrando_projeto_codigo} - {st.session_state.cadastrando_projeto_sigla}**")
    except:
        pass

    # PASSO 1: Informações cadastrais ---------------------------------------
    with st.expander("**Passo 1: Informações cadastrais**", expanded=False):

        # Se o projeto ainda não foi cadastrado, mostra o formulário
        # Se session_state.cadastrando_projeto_codigo não existir ou estiver vazio, mostra o formulário:
        if 'cadastrando_projeto_codigo' not in st.session_state or not st.session_state.cadastrando_projeto_codigo:

            with st.form(key="projeto_passo_1", border=False):

                # EDITAL        
                # Obtém a lista de editais e ordena pela coluna data_lancamento
                editais = col_editais.find().sort("data_lancamento", -1)
                editais = [edital['codigo_edital'] for edital in editais]
                # Lista editais
                edital = st.selectbox("Edital", editais)

                # ORGANIZAÇÃO
                # Obtém a lista de organizações
                organizacoes = col_organizacoes.find().sort("sigla_organizacao", 1)
                siglas_organizacoes = [organizacao['sigla_organizacao'] for organizacao in organizacoes]
                # Lista organizações
                organizacao = st.selectbox("Organização:", siglas_organizacoes)

                # CÓDIGO DO PROJETO
                codigo_projeto = st.text_input("Código do Projeto:")

                # SIGLA DO PROJETO
                sigla_projeto = st.text_input("Sigla do Projeto:")

                # NOME DO PROJETO
                nome_projeto = st.text_input("Nome do Projeto:")

                # LATITUDE
                latitude = st.text_input("Latitude: (ex: -19.015224)")

                # LONGITUDE
                longitude = st.text_input("Longitude: (ex: -47.856324)")

                # DURAÇÃO DO PROJETO EM MESES
                duracao_projeto = st.number_input(
                    "Duração do Projeto (em meses):",
                    min_value=1,
                    step=1,
                    format="%d"
                )

                # DATA DE INÍCIO DO CONTRATO
                data_inicio_contrato = st.date_input("Data de Início do Contrato:", format="DD/MM/YYYY")

                # DATA DE FIM DO CONTRATO
                data_fim_contrato = st.date_input("Data de Fim do Contrato:", format="DD/MM/YYYY")

                # # VALOR DO CONTRATO
                # valor_contrato = st.number_input("Valor do Contrato:", format="%f")

                # Padrinho/Madrinha
                # Filtrar nomes que contenham a palavra "monitor" na coluna tipo_usuario
                padrinhos = df_pessoas[df_pessoas['tipo_usuario'].str.contains("monitor", case=False, na=False)]['nome_completo'].tolist()

                # Selectbox com a lista filtrada
                padrinho = st.selectbox("Padrinho/Madrinha:", padrinhos)

                # Responsável
                responsaveis = df_pessoas[df_pessoas['tipo_usuario'].str.contains("beneficiario", case=False, na=False)]['nome_completo'].tolist()
                responsavel = st.selectbox("Responsável:", responsaveis)

                # Temas
                temas = df_temas['tema'].tolist()
                temas = st.multiselect("Temas", temas)

                # Público
                publicos = df_publicos['publico'].tolist()
                publicos = st.multiselect("Público", publicos)

                # Objetivo geral
                objetivo_geral = st.text_area("Objetivo geral:")




                # Geografia ------------------------------------------------------------------------------------------------------

                #  ESTADOS E MUNICÍPIOS -----------------------
                col1, col2, col3 = st.columns(3)

                ufs_selecionadas = col1.multiselect(
                    "Estados",
                    options=list(uf_codigo_para_label.values()),
                    placeholder=""
                )

                municipios_selecionadas = col2.multiselect(
                    "Municípios",
                    options=list(municipios_codigo_para_label.values()),
                    placeholder=""
                )

                # biomas_selecionados = col3.multiselect(
                #     "Biomas",
                #     options=list(biomas_codigo_para_label.values()),
                #     placeholder=""
                # )

                #  TERRAS INDÍGENAS -----------------------
                col1, col2 = st.columns(2)

                tis_selecionadas = col1.multiselect(
                    "Terras Indígenas",
                    options=list(ti_codigo_para_label.values()),
                    placeholder=""
                )

                #  UNIDADES DE CONSERVAÇÃO -----------------------
                ucs_selecionadas = col2.multiselect(
                    "Unidades de Conservação",
                    options=list(uc_codigo_para_label.values()),
                    placeholder=""
                )

                #  ASSENTAMENTOS -----------------------
                col1, col2 = st.columns(2)
                assentamentos_selecionados = col1.multiselect(
                    "Assentamentos",
                    options=list(assent_codigo_para_label.values()),
                    placeholder=""
                )

                #  QUILOMBOS -----------------------
                quilombos_selecionados = col2.multiselect(
                    "Quilombos",
                    options=list(quilombo_codigo_para_label.values()),
                    placeholder=""
                )

                #  BACIAS HIDROGRÁFICAS -----------------------
                col1, col2, col3 = st.columns(3)

                bacias_macro_sel = col1.multiselect(
                    "Bacias Hidrográficas - Macro",
                    options=list(bacia_macro_codigo_para_label.values()),
                    placeholder=""
                )

                bacias_meso_sel = col2.multiselect(
                    "Bacias Hidrográficas - Meso",
                    options=list(bacia_meso_codigo_para_label.values()),
                    placeholder=""
                )

                bacias_micro_sel = col3.multiselect(
                    "Bacias Hidrográficas - Micro",
                    options=list(bacia_micro_codigo_para_label.values()),
                    placeholder=""
                )

                st.write('')



                # --- Botão de salvar ---
                submit = st.form_submit_button("Cadastrar projeto", icon=":material/save:", width=200, type="primary")
                
                if submit:

                    # Lista de campos obrigatórios com nome e valor
                    campos_obrigatorios = {
                        "Edital": edital,
                        "Código do Projeto": codigo_projeto,
                        "Sigla do Projeto": sigla_projeto,
                        "Organização": organizacao,
                        "Nome do Projeto": nome_projeto,
                        "Objetivo Geral": objetivo_geral,
                        "Duração do Projeto": duracao_projeto,
                        "Data de Início": data_inicio_contrato,
                        "Data de Fim": data_fim_contrato,
                        # "Valor do Contrato": valor_contrato,
                        "Padrinho/Madrinha": padrinho,
                        "Responsável": responsavel,
                        "Temas": temas,
                        "Públicos": publicos,
                        "Latitude": latitude,
                        "Longitude": longitude,
                        "Estados (UF)": ufs_selecionadas,
                        "Municípios": municipios_selecionadas
                    }

                    # Verificar se algum campo está vazio
                    campos_faltando = [nome for nome, valor in campos_obrigatorios.items() if not valor]

                    if campos_faltando:
                        st.error(f"Preencha os campos obrigatórios: {', '.join(campos_faltando)}")
                    else:

                        # --- Validar unicidade de sigla e código ---
                        sigla_existente = (
                            False if df_projetos.empty or "sigla_projeto" not in df_projetos.columns 
                            else (df_projetos["sigla_projeto"] == sigla_projeto).any()
                        )

                        codigo_existente = (
                            False if df_projetos.empty or "codigo_projeto" not in df_projetos.columns
                            else (df_projetos["codigo_projeto"] == codigo_projeto).any()
                        )


                        if sigla_existente:
                            st.warning(f"A sigla '{sigla_projeto}' já está cadastrada em outro projeto.")
                        elif codigo_existente:
                            st.warning(f"O código '{codigo_projeto}' já está cadastrado em outro projeto.")
                        else:
                            # --- Criar ObjectIds ---
                            projeto_id = bson.ObjectId()

                            # ----------------------------------------------------------
                            # MONTAR LISTA DE REGIÕES DE ATUAÇÃO PARA SALVAR NO MONGODB
                            # ----------------------------------------------------------

                            # Função auxiliar
                            def get_codigo_por_label(dicionario, valor):
                                return next((codigo for codigo, label in dicionario.items() if label == valor), None)

                            regioes_atuacao = []

                            # Tipos simples com lookup
                            for tipo, selecionados, dicionario in [
                                ("uf", ufs_selecionadas, uf_codigo_para_label),
                                ("municipio", municipios_selecionadas, municipios_codigo_para_label),
                                # ("bioma", biomas_selecionados, biomas_codigo_para_label),
                                ("terra_indigena", tis_selecionadas, ti_codigo_para_label),
                                ("uc", ucs_selecionadas, uc_codigo_para_label),
                                ("assentamento", assentamentos_selecionados, assent_codigo_para_label),
                                ("quilombo", quilombos_selecionados, quilombo_codigo_para_label),
                                ("bacia_micro", bacias_micro_sel, bacia_micro_codigo_para_label),
                                ("bacia_meso", bacias_meso_sel, bacia_meso_codigo_para_label),
                                ("bacia_macro", bacias_macro_sel, bacia_macro_codigo_para_label),
                            ]:
                                for item in selecionados:
                                    codigo_atuacao = get_codigo_por_label(dicionario, item)
                                    if codigo_atuacao:
                                        regioes_atuacao.append({"tipo": tipo, "codigo": codigo_atuacao})

                            # ----------------------------------------------------------

                            # --- Montar documento ---
                            doc = {
                                "_id": projeto_id,
                                "edital": edital,
                                "codigo": codigo_projeto,
                                "sigla": sigla_projeto,
                                "organizacao": organizacao,
                                "nome_do_projeto": nome_projeto,
                                "objetivo_geral": objetivo_geral,
                                "duracao": duracao_projeto,
                                "data_inicio_contrato": data_inicio_contrato.strftime("%d/%m/%Y"),
                                "data_fim_contrato": data_fim_contrato.strftime("%d/%m/%Y"),
                                # "valor": valor_contrato,
                                # "valor_da_contrapartida_em_r$": float_to_br(contrapartida),
                                "padrinho": padrinho,
                                "responsavel": responsavel,
                                "temas": temas,
                                "publicos": publicos,
                                "latitude": latitude,
                                "longitude": longitude,
                                "regioes_atuacao": regioes_atuacao,

                            }

                            # --- Inserir no MongoDB ---
                            col_projetos.insert_one(doc)

                            st.session_state.cadastrando_projeto_codigo = codigo_projeto
                            st.session_state.cadastrando_projeto_sigla = sigla_projeto

                            st.success("Projeto cadastrado com sucesso!")
                            time.sleep(3)
                            st.rerun()

        # Se session_state.cadastrando_projeto_codigo existir e não estiver vazio, 
        # significa que já foi preenchido o passo 1, segue para o passo 2:
        else:
            st.success("Passo 1 concluido! Continue para o passo 2.")


    # ?????????????????????????/
    st.write(st.session_state)






    # PASSO 2: Cadastro de Parcelas ---------------------------------------
    with st.expander("**Passo 2: Parcelas**", expanded=False):

        # Inicializando a variável session_state.cadastrando_parcela
        if 'cadastrando_parcela' not in st.session_state:
            st.session_state['cadastrando_parcela'] = None                                                                                                                                                                                                                                  

        # Se não preencheu o passo 1, dá um aviso
        if 'cadastrando_projeto_codigo' not in st.session_state:
            st.warning("Conclua o passo 1 antes de prosseguir para o passo 2.")

        @st.fragment
        def cadastrar_parcelas(colecao):

            # Se session_state.cadastrando_parcela existir e for diferente de 'finalizado', mostra o formulário
            if 'cadastrando_parcela' in st.session_state and st.session_state['cadastrando_parcela'] != 'finalizado':

                st.write('**Cadastre as parcelas**')

                # Escolhe o número de parcelas, para
                parcelas = st.number_input("Quantidade de parcelas:", min_value=1, max_value=100, value=1, step=1, width=150)

                # Formulário de parcelas
                with st.form(key="parcelas", border=False):

                    parcelas_data = []  # Lista para armazenar as parcelas

                    for i in range(1, parcelas + 1):
                        st.write('')
                        st.write(f"**Parcela {i}:**")

                        with st.container():
                            data_inicio_parcela = st.date_input(
                                f"Data prevista", 
                                key=f"data_parcela_{i}", 
                                format="DD/MM/YYYY"
                            )
                            valor_parcela = st.number_input(
                                f"Valor (R$)", 
                                key=f"valor_parcela_{i}", 
                                min_value=0.0, 
                                value=0.0, 
                                step=0.01
                            )

                            # Adiciona os dados à lista (convertendo date para string)
                            parcelas_data.append({
                                "parcela": i,
                                "data_prevista": data_inicio_parcela.strftime("%d/%m/%Y"),
                                "valor": float(valor_parcela)
                            })

                    st.write('')
                    submit = st.form_submit_button("Salvar", icon=":material/save:", type="primary", width=200)

                    # Após o submit, salvar no MongoDB
                    if submit:

                        # Verifica se existe um código de projeto salvo na sessão
                        if "cadastrando_projeto_codigo" not in st.session_state or not st.session_state.cadastrando_projeto_codigo:
                            st.error("Código do projeto não encontrado na sessão.")
                        else:
                            codigo = st.session_state.cadastrando_projeto_codigo

                            # Busca documento no MongoDB
                            projeto = colecao.find_one({"codigo": codigo})

                            if not projeto:
                                st.error(f"Projeto com código '{codigo}' não encontrado no banco.")
                            else:
                                # Atualiza documento adicionando ou sobrescrevendo 'parcelas'
                                colecao.update_one(
                                    {"codigo": codigo},
                                    {"$set": {"parcelas": parcelas_data}}
                                )

                                st.session_state.cadastrando_parcelas = 'Finalizado'

                                st.success("Parcelas cadastradas com sucesso!")
                                time.sleep(3)
                                st.rerun()

            # Se session_state.cadastrando_parcelas existir e for igual a 'finalizado': 
            # significa que já foi preenchido o passo 2, segue para o passo 3:
            else:
                st.success("Passo 2 concluido! Continue para o passo 3.")


            # Chama a função para cadastrar parcelas
        
            cadastrar_parcelas(col_projetos)






    # PASSO 3: Cadastro de Locais ---------------------------------------
    with st.expander("**Passo 3: Locais**", expanded=False):

        # Inicializando a variável session_state.cadastrando_locais
        if 'cadastrando_locais' not in st.session_state:
            st.session_state['cadastrando_locais'] = None                                                                                                                                                                                                                                  

        # Se não preencheu o passo 2, dá um aviso        
        if "cadastrando_parcelas" not in st.session_state or st.session_state.cadastrando_parcelas != 'Finalizado':
            st.warning("Conclua o passo 2 antes de prosseguir para o passo 3.")


        @st.fragment
        def cadastrar_locais(colecao):

            # Se session_state.cadastrando_locais existir e for diferente de 'finalizado', mostra o formulário
            # if 'cadastrando_locais' in st.session_state and st.session_state['cadastrando_locais'] != 'Finalizado':

            st.write('**Cadastre as localidades em que o projeto irá atuar**')

            # lista_locais = []  # Lista para armazenar os locais


            # Formulário de locais

            opcao_local = st.radio("", ("Inserir link do Google Maps", "Inserir Latitude e Logitude"), key="local")

            nome_local = st.text_input("Nome do local")


            if opcao_local == "Inserir link do Google Maps":
                link_google_maps = st.text_input("Link do Google Maps")

                def extrair_lat_long_google_maps(link):
                    try:
                        # Extrai a parte após o "@"
                        coordenadas = link.split("@")[1].split(",")
                        latitude = coordenadas[0]
                        longitude = coordenadas[1]
                        return latitude, longitude
                    except (IndexError, AttributeError):
                        return None, None


                # Extrai a latitude e longitude do link do google maps
                latitude, longitude = extrair_lat_long_google_maps(link_google_maps)

                with st.container(horizontal=True):

                    if st.button("Salvar local", key="local_google_maps", type="primary", icon=":material/save:"):
                        # Salva o local no banco de dados, atualizando o documento que tem o código == st.session_state.cadastrando_projeto_codigo. Deve criar a chave locais (uma lista de dicionários) e adicionar o novo local
                        colecao.update_one(
                            {"codigo": st.session_state.cadastrando_projeto_codigo},
                            {"$push": {"locais": {"nome": nome_local, "latitude": latitude, "longitude": longitude}}}
                        )

                        st.success("Local cadastrado com sucesso!")
                        # time.sleep(3)
                        # st.rerun()

                    if st.button("Finalizar cadastro de locais", key="finalizar_locais_google_maps", type="secondary", icon=":material/check:"):
                        st.session_state.cadastrando_locais = 'Finalizado'
                        st.success("Cadastro de locais concluido!")
                        time.sleep(3)
                        st.rerun(
                    )


            elif opcao_local == "Inserir Latitude e Logitude":
                latitude = st.text_input("Latitude (exemplo: -23.5505)")
                longitude = st.text_input("Longitude (exemplo: -46.6333)")

                # Regex para validar número decimal (aceita sinal e ponto)
                regex_decimal = r"^-?\d+(\.\d+)?$"

                # Função para validar formato numérico
                def validar_formato(valor):
                    return bool(re.match(regex_decimal, valor.strip()))

                # Função para validar intervalo geográfico
                def validar_intervalo(lat, lon):
                    try:
                        lat = float(lat)
                        lon = float(lon)
                        return -90 <= lat <= 90 and -180 <= lon <= 180
                    except ValueError:
                        return False

                # --------------------------------------------------------------------------------
                # BOTÃO DE SALVAR
                # --------------------------------------------------------------------------------

                with st.container(horizontal=True):

                    if st.button("Salvar local", type="primary", icon=":material/save:"):

                        # Etapa 1 — Validação de preenchimento
                        if not nome_local or not latitude or not longitude:
                            st.warning("⚠️ Preencha todos os campos antes de salvar.")
                        else:
                            erro = False

                            # Etapa 2 — Validação de formato
                            if not validar_formato(latitude):
                                st.error("❌ Latitude inválida. Use apenas números e ponto decimal (ex: -23.5505)")
                                erro = True
                            if not validar_formato(longitude):
                                st.error("❌ Longitude inválida. Use apenas números e ponto decimal (ex: -46.6333)")
                                erro = True

                            # Etapa 3 — Validação de intervalo geográfico
                            if not erro and not validar_intervalo(latitude, longitude):
                                st.error("❌ Coordenadas fora do intervalo válido (-90 ≤ lat ≤ 90, -180 ≤ lon ≤ 180)")
                                erro = True

                            # Etapa 4 — Se tudo estiver ok, salvar no banco
                            if not erro:
                                try:
                                    colecao.update_one(
                                        {"codigo": st.session_state.cadastrando_projeto_codigo},
                                        {"$push": {
                                            "locais": {
                                                "nome": nome_local.strip(),
                                                "latitude": latitude,
                                                "longitude": longitude
                                            }
                                        }},
                                        upsert=True  # cria o documento se não existir
                                    )

                                    st.success("Local salvo com sucesso!")

                                except Exception as e:
                                    st.error(f"❌ Erro ao salvar no banco de dados: {e}")

                    if st.button("Finalizar cadastro de locais", key="finalizar_locais_lat_long", type="secondary", icon=":material/check:"):
                        st.session_state.cadastrando_locais = 'Finalizado'
                        st.success("Cadastro de locais concluido!")
                        time.sleep(3)
                        st.rerun(
                    )

        cadastrar_locais(col_projetos)



