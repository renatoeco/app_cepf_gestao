import streamlit as st
import time
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Coleção de UFs e Municípios
col_ufs_munic = db["ufs_municipios"]

# Coleção de projetos
col_projetos = db["projetos"]


###########################################################################################################
# FUNÇÕES
###########################################################################################################




###########################################################################################################
# TRATAMENTO DE DADOS
###########################################################################################################



codigo_projeto_atual = st.session_state.get("projeto_atual")



###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################



# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Locais")


with st.expander("Cadastrar local"):
    opcao_cadastrar_local = st.radio(
        "O que deseja cadastrar?",
        ("Localidade", "Estados / Municípios", "Áreas especiais", "Mapa ou Shapefile"),
        horizontal=True    
    )

    if opcao_cadastrar_local == "Localidade":
        st.write("Cadastrar localidade")









    elif opcao_cadastrar_local == "Estados / Municípios":

        st.subheader("Estados e Municípios")
        st.write("")

        # --------------------------------------------------
        # COLEÇÃO COM UFs E MUNICÍPIOS
        # --------------------------------------------------
        col_ufs_munic = db["ufs_municipios"]

        # Buscar todos os documentos
        docs = list(col_ufs_munic.find({}))

        dados_ufs = []
        dados_municipios = []

        # Identificar documentos
        for doc in docs:
            if "ufs" in doc:
                dados_ufs = doc["ufs"]
            elif "municipios" in doc:
                dados_municipios = doc["municipios"]

        if not dados_ufs or not dados_municipios:
            st.error("Dados de UFs ou Municípios não encontrados no banco.")
            st.stop()

        # --------------------------------------------------
        # MAPEAMENTOS AUXILIARES
        # --------------------------------------------------

        # Código UF -> Sigla
        codigo_uf_para_sigla = {
            '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
            '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL',
            '28': 'SE', '29': 'BA',
            '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
            '41': 'PR', '42': 'SC', '43': 'RS',
            '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF'
        }

        # UF -> Label
        uf_codigo_para_label = {
            uf["codigo_uf"]: uf["nome_uf"]
            for uf in dados_ufs
        }



        # Município -> Label
        municipios_codigo_para_label = {
            int(m["codigo_municipio"]): (
                f"{m['nome_municipio']} - "
                f"{codigo_uf_para_sigla.get(str(m['codigo_municipio'])[:2], '')}"
            )
            for m in dados_municipios
        }

        # --------------------------------------------------
        # ORDENAÇÃO ALFABÉTICA DOS MUNICÍPIOS
        # --------------------------------------------------
        municipios_ordenados = sorted(
            municipios_codigo_para_label.values(),
            key=lambda x: x.lower()
        )

        ufs_ordenadas = sorted(
            uf_codigo_para_label.values(),
            key=lambda x: x.lower()
        )

        # --------------------------------------------------
        # MULTISELECTS
        # --------------------------------------------------
        ufs_selecionadas = st.multiselect(
            "Estados",
            options=ufs_ordenadas,
            placeholder="Selecione os estados"
        )

        municipios_selecionados = st.multiselect(
            "Municípios",
            options=municipios_ordenados,
            placeholder="Selecione os municípios"
        )




        # --------------------------------------------------
        # BOTÃO DE SALVAR
        # --------------------------------------------------
        st.write('')
        if st.button(
            "Salvar Estados e Municípios",
            icon=":material/save:",
            # type="primary",
            key="salvar_estados_municipios"
        ):

            # -----------------------------------
            # Função auxiliar: label → código
            # -----------------------------------
            def get_codigo_por_label(dicionario, valor):
                return next(
                    (codigo for codigo, label in dicionario.items() if label == valor),
                    None
                )

            # -----------------------------------
            # Montar listas finais
            # -----------------------------------
            estados_salvar = []
            municipios_salvar = []

            # Estados
            for uf_label in ufs_selecionadas:
                codigo_uf = get_codigo_por_label(uf_codigo_para_label, uf_label)
                if codigo_uf:
                    estados_salvar.append({
                        "codigo_uf": codigo_uf,
                        "label": uf_label
                    })

            # Municípios
            for mun_label in municipios_selecionados:
                codigo_municipio = get_codigo_por_label(
                    municipios_codigo_para_label,
                    mun_label
                )
                if codigo_municipio:
                    municipios_salvar.append({
                        "codigo_municipio": int(codigo_municipio),
                        "label": mun_label
                    })

            # -----------------------------------
            # Atualizar projeto no MongoDB
            # -----------------------------------
            col_projetos.update_one(
                {"codigo": codigo_projeto_atual},
                {
                    "$set": {
                        "locais.estados": estados_salvar,
                        "locais.municipios": municipios_salvar
                    }
                }
            )

            st.success("Estados e municípios salvos com sucesso!")
            time.sleep(3)
            st.rerun()
























    # elif opcao_cadastrar_local == "Estados / Municípios":


    #     # ---- Buscar todos os documentos ----
    #     docs = list(col_ufs_munic.find({}))

    #     # Inicializar variáveis
    #     dados_ufs = []
    #     dados_municipios = []

    #     # ---- Identificar cada documento pela chave existente ----
    #     for doc in docs:
    #         if "ufs" in doc:
    #             dados_ufs = doc["ufs"]

    #         elif "municipios" in doc:
    #             dados_municipios = doc["municipios"]
            
    #     # Criar dicionário código_uf -> sigla
    #     codigo_uf_para_sigla = {
    #         '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
    #         '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE', '29': 'BA',
    #         '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
    #         '41': 'PR', '42': 'SC', '43': 'RS',
    #         '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF'
    #     }
        
    #     uf_codigo_para_label = {
    #         uf["codigo_uf"]: f"{uf['nome_uf']} ({uf['codigo_uf']})"
    #         for uf in dados_ufs
    #     }


    #     # Criar mapeamento código -> "Município - UF"
    #     municipios_codigo_para_label = {
    #         int(m["codigo_municipio"]): f"{m['nome_municipio']} - {codigo_uf_para_sigla[str(m['codigo_municipio'])[:2]]}"
    #         for m in dados_municipios
    #     }


    #     ufs_selecionadas = st.multiselect(
    #         "Estados",
    #         options=list(uf_codigo_para_label.values()),
    #         placeholder=""
    #     )

    #     municipios_selecionadas = st.multiselect(
    #         "Municípios",
    #         options=list(municipios_codigo_para_label.values()),
    #         placeholder=""
    #     )
















    elif opcao_cadastrar_local == "Áreas especiais":
        st.write("Cadastrar Áreas especiais")
    elif opcao_cadastrar_local == "Mapa ou Shapefile":
        st.write("Cadastrar Mapa ou Shapefile")