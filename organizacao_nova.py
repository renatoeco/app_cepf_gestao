
import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Funções personalizadas
import pandas as pd
import locale
import re
import time
import uuid


st.set_page_config(page_title="Nova Organização", page_icon=":material/add_business:")




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

# col_ciclos = db["ciclos_investimento"]
# df_ciclos = pd.DataFrame(list(col_ciclos.find()))

col_temas = db["temas_projetos"]
df_temas = pd.DataFrame(list(col_temas.find()))

col_publicos = db["publicos"]
df_publicos = pd.DataFrame(list(col_publicos.find()))

###########################################################################################################
# CONFIGURAÇÃO DE LOCALE
###########################################################################################################

try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
    except locale.Error:
        print("Aviso: Não foi possível definir a localidade para Português. Usando a localidade padrão.")

###########################################################################################################
# FUNÇÕES AUXILIARES
###########################################################################################################

def validar_cnpj(cnpj_str):
    """
    Valida apenas o formato do CNPJ.

    Aceita:
    - 99.999.999/9999-99
    - 99999999999999
    """

    cnpj_str = str(cnpj_str).strip()

    padrao_mascarado = re.compile(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")
    padrao_puro = re.compile(r"^\d{14}$")

    return bool(padrao_mascarado.match(cnpj_str) or padrao_puro.match(cnpj_str))


def formatar_cnpj(cnpj_str):
    """
    Converte qualquer CNPJ válido para o formato padrão.
    """

    cnpj_limpo = re.sub(r"\D", "", str(cnpj_str))

    return f"{cnpj_limpo[0:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:14]}"


def df_index1(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajusta o índice do dataframe para iniciar em 1.
    """

    df2 = df.copy()
    df2.index = range(1, len(df2) + 1)
    return df2




###########################################################################################################
# CONTROLE DE LIMPEZA DO FORMULÁRIO
###########################################################################################################

# Inicializa flag de limpeza do formulário
if "limpar_form_organizacao" not in st.session_state:
    st.session_state.limpar_form_organizacao = False

# Caso a flag esteja ativa, limpa os campos antes dos widgets serem renderizados
if st.session_state.limpar_form_organizacao:

    st.session_state.sigla_organizacao_input = ""
    st.session_state.nome_organizacao_input = ""
    st.session_state.cnpj_input = ""

    # Desativa a flag após limpar
    st.session_state.limpar_form_organizacao = False




###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################

# Logo do sidebar
st.logo("images/ieb_logo.svg", size='large')

# Título da página
st.header("Nova Organização")

# Seleção do tipo de cadastro
opcao_cadastro = st.radio(
    "",
    ["Cadastro individual", "Cadastro em massa"],
    key="opcao_cadastro",
    horizontal=True
)

st.write("")

###########################################################################################################
# CADASTRO INDIVIDUAL
###########################################################################################################

if opcao_cadastro == "Cadastro individual":

    # Criação do formulário
    with st.form(key="organizacao_form", border=False):

        # Campos de entrada com keys para controle via session_state
        sigla_organizacao = st.text_input(
            "Sigla da Organização",
            key="sigla_organizacao_input"
        )

        nome_organizacao = st.text_input(
            "Nome da Organização",
            key="nome_organizacao_input"
        )

        cnpj = st.text_input(
            "CNPJ",
            placeholder="00.000.000/0000-00",
            key="cnpj_input"
        )

        st.write("")

        # Botão de envio
        submit_button = st.form_submit_button(
            "Salvar",
            icon=":material/save:",
            type="primary"
        )


        ###################################################################################################
        # PROCESSAMENTO DO FORMULÁRIO
        ###################################################################################################

        if submit_button:

            # Obtém valores atuais do formulário a partir do session_state
            sigla_organizacao = st.session_state.sigla_organizacao_input.strip()
            nome_organizacao = st.session_state.nome_organizacao_input.strip()
            cnpj = st.session_state.cnpj_input.strip()

            # Verifica se todos os campos foram preenchidos
            if not sigla_organizacao or not nome_organizacao or not cnpj:

                st.error("Todos os campos devem ser preenchidos.")

            # Validação do formato do CNPJ
            elif not validar_cnpj(cnpj):

                st.error("CNPJ inválido. Utilize o formato **00.000.000/0000-00** ou apenas  14 números **00000000000000**.")

            else:

                # Padroniza o CNPJ para o formato oficial antes de consultar e salvar
                cnpj = formatar_cnpj(cnpj)

                # Verifica se já existe organização com a mesma sigla
                sigla_existente = col_organizacoes.find_one({
                    "sigla_organizacao": sigla_organizacao
                })

                # Verifica se já existe organização com o mesmo CNPJ
                cnpj_existente = col_organizacoes.find_one({
                    "cnpj": cnpj
                })

                # Tratamento de duplicidade de sigla
                if sigla_existente:

                    st.error(
                        f"A sigla '{sigla_organizacao}' já está cadastrada em outra Organização."
                    )

                # Tratamento de duplicidade de CNPJ
                elif cnpj_existente:

                    st.error(
                        f"O CNPJ '{cnpj}' já está cadastrado em outra organização."
                    )

                else:

                    ###########################################################################
                    # INSERÇÃO NO BANCO
                    ###########################################################################

                    # Documento a ser inserido
                    novo_doc = {
                        "sigla_organizacao": sigla_organizacao,
                        "nome_organizacao": nome_organizacao,
                        "cnpj": cnpj
                    }

                    # Insere o documento no MongoDB
                    col_organizacoes.insert_one(novo_doc)

                    ###########################################################################
                    # FEEDBACK E LIMPEZA DO FORMULÁRIO
                    ###########################################################################

                    # Mensagem de sucesso
                    st.success("Organização cadastrada com sucesso!", icon=":material/check:")

                    # Ativa flag para limpar o formulário no próximo ciclo da aplicação
                    st.session_state.limpar_form_organizacao = True

                    # Pequena pausa para exibir a mensagem de sucesso ao usuário
                    time.sleep(3)

                    # Recarrega a página
                    st.rerun()


                

elif opcao_cadastro == "Cadastro em massa":

    # Inicializa o 'key' do file_uploader se ele não existir
    if 'uploader_key' not in st.session_state:
        st.session_state['uploader_key'] = str(uuid.uuid4())

    st.write("Baixe aqui o modelo de tabela para cadastro em massa:")

    with open("modelos/modelo_cadastro_organizacoes_em_massa.xlsx", "rb") as f:
        st.download_button(
            label=":material/download: Baixar modelo XLSX",
            data=f,
            file_name="modelo_cadastro_organizacoes_em_massa.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.divider()

    # ------------------------------
    # Upload
    # ------------------------------

    arquivo = st.file_uploader(
        "Envie um arquivo XLSX preenchido para cadastrar múltiplas organizações:",
        type=["xlsx"],
        key=st.session_state['uploader_key'],
        width=400
    )


    st.write("")

    if arquivo is not None:

        try:

            df_upload = pd.read_excel(arquivo)

            st.success("Arquivo carregado com sucesso!")

            # ==========================================================
            # 0) Validar se o arquivo está vazio
            # ==========================================================
            if df_upload.empty or df_upload.dropna(how="all").empty:
                st.error(
                    ":material/error: O arquivo enviado está vazio!\n\n"
                    "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
                )
                st.stop()

            # Exibir com index iniciado em 1
            st.dataframe(df_index1(df_upload))
            st.write("")



            # ==========================================================
            # 1) Validar colunas obrigatórias
            # ==========================================================
            colunas_obrigatorias = ["sigla_organizacao", "nome_organizacao", "cnpj"]
            faltando = [c for c in colunas_obrigatorias if c not in df_upload.columns]

            if faltando:
                st.error(
                    f":material/error: Faltam colunas obrigatórias no arquivo: {faltando}\n\n"
                    "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
                )
                st.stop()

            # ==========================================================
            # 2) CNPJ — validar formato
            # ==========================================================
            invalidos = df_upload[~df_upload["cnpj"].astype(str).apply(validar_cnpj)]

            if not invalidos.empty:
                st.error(
                    ":material/error: Existem CNPJs com formato inválido!\n"
                    "Use **99.999.999/9999-99** ou **99999999999999**.\n\n"
                    "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
                )
                st.dataframe(df_index1(invalidos))
                st.stop()

            # Normalizar todos para máscara final
            df_upload["cnpj"] = df_upload["cnpj"].astype(str).apply(formatar_cnpj)

            # ==========================================================
            # 3) Verificar duplicidade interna no arquivo
            # ==========================================================
            dup_sigla = df_upload[df_upload.duplicated("sigla_organizacao", keep=False)]
            dup_nome = df_upload[df_upload.duplicated("nome_organizacao", keep=False)]
            dup_cnpj = df_upload[df_upload.duplicated("cnpj", keep=False)]

            if not dup_sigla.empty or not dup_nome.empty or not dup_cnpj.empty:
                st.error(
                    ":material/error: Existem duplicidades dentro do próprio arquivo.\n\n"
                    "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
                )

                if not dup_sigla.empty:
                    st.subheader("Siglas duplicadas")
                    st.dataframe(df_index1(dup_sigla))

                if not dup_nome.empty:
                    st.subheader("Nomes duplicados")
                    st.dataframe(df_index1(dup_nome))

                if not dup_cnpj.empty:
                    st.subheader("CNPJs duplicados")
                    st.dataframe(df_index1(dup_cnpj))

                st.stop()

            # ==========================================================
            # 4) Verificar duplicidades no banco
            # ==========================================================
            db = conectar_mongo_cepf_gestao()
            col_organizacoes = db["organizacoes"]

            existentes = pd.DataFrame(list(col_organizacoes.find(
                {},
                {"sigla_organizacao": 1, "nome_organizacao": 1, "cnpj": 1}
            )))

            conflitos_sigla = []
            conflitos_nome = []
            conflitos_cnpj = []

            if not existentes.empty:
                for _, row in df_upload.iterrows():

                    if row["sigla_organizacao"] in existentes["sigla_organizacao"].values:
                        conflitos_sigla.append(row.to_dict())

                    if row["nome_organizacao"] in existentes["nome_organizacao"].values:
                        conflitos_nome.append(row.to_dict())

                    if row["cnpj"] in existentes["cnpj"].values:
                        conflitos_cnpj.append(row.to_dict())

            if conflitos_sigla or conflitos_nome or conflitos_cnpj:
                st.error(
                    ":material/error: Existem conflitos com registros já existentes no banco de dados!\n\n"
                    "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
                )

                if conflitos_sigla:
                    st.write("")
                    st.write("**Siglas já existentes:**")
                    st.dataframe(df_index1(pd.DataFrame(conflitos_sigla)))

                if conflitos_nome:
                    st.write("")
                    st.write("**Nomes já existentes:**")
                    st.dataframe(df_index1(pd.DataFrame(conflitos_nome)))

                if conflitos_cnpj:
                    st.write("")
                    st.write("**CNPJs já existentes:**")
                    st.dataframe(df_index1(pd.DataFrame(conflitos_cnpj)))

                st.stop()

            # ==========================================================
            # 5) Inserir no banco
            # ==========================================================
            if st.button(":material/save: Cadastrar organizações", type="primary"):

                registros = df_upload.to_dict(orient="records")
                resultado = col_organizacoes.insert_many(registros)

                st.success(f":material/check: {len(resultado.inserted_ids)} organizações cadastradas com sucesso!")

                # 1. Troca a chave do uploader para forçar o reset no rerun
                st.session_state['uploader_key'] = str(uuid.uuid4()) 
                
                # 2. Rerun
                time.sleep(2)
                st.rerun()


        except Exception as e:
            st.error(
                ":material/error: Erro ao processar o arquivo.\n\n"
                "Nenhum cadastro foi realizado. Corrija os dados e carregue novamente."
            )
            st.exception(e)

