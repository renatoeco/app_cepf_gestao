import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao # Funções personalizadas
import pandas as pd
import locale
import re
import time


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


# # Inclulir o status no dataframe de projetos
# df_projetos['status'] = 'Em dia'

# # Converter object_id para string
# # df_pessoas['_id'] = df_pessoas['_id'].astype(str)
# df_projetos['_id'] = df_projetos['_id'].astype(str)

# # Convertendo datas de string para datetime
# df_projetos['data_inicio_contrato_dtime'] = pd.to_datetime(
#     df_projetos['data_inicio_contrato'], 
#     format="%d/%m/%Y", 
#     dayfirst=True, 
#     errors="coerce"
# )

# df_projetos['data_fim_contrato_dtime'] = pd.to_datetime(
#     df_projetos['data_fim_contrato'], 
#     format="%d/%m/%Y", 
#     dayfirst=True, 
#     errors="coerce"
# )






###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################


# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Nova Organização")


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