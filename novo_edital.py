import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import pandas as pd
import time
import datetime

###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()


col_editais = db["editais"]
df_editais = pd.DataFrame(list(col_editais.find()))

# Define as coleções específicas que serão utilizadas a partir do banco
# col_pessoas = db["pessoas"]



###########################################################################################################
# FUNÇÕES
###########################################################################################################




###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################

# Define o layout da página como largura total
st.set_page_config(layout="wide")

# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Novo edital")

with st.form(key="edital_form" ,border=False):

    st.write('')

    codigo_edital = st.text_input("Codigo do edital:")
    nome_edital = st.text_input("Nome do edital:")
    data_lancamento = st.date_input("Data de lançamento:", format="DD/MM/YYYY")


    st.write('')

    submit = st.form_submit_button("Salvar", icon=":material/save:", type="primary")


    if submit:

        # Validação de campos vazios
        if not codigo_edital or not nome_edital or not data_lancamento:
            st.error("Todos os campos devem ser preenchidos.")

        else:

            # Converte para datetime com hora zero
            data_lancamento_dt = datetime.datetime.combine(data_lancamento, datetime.datetime.min.time())

            # Verifica se codigo já existe
            codigo_existente = col_editais.find_one({"codigo_edital": codigo_edital})

            if codigo_existente:
                st.error(f"O codigo '{codigo_edital}' já está cadastrada.")

            else:
                # Inserir no MongoDB
                novo_edital = {
                    "codigo_edital": codigo_edital,
                    "nome_edital": nome_edital,
                    "data_lancamento": data_lancamento_dt  
                }
                col_editais.insert_one(novo_edital)
                st.success("Edital cadastrado com sucesso!")

                time.sleep(3)
                st.rerun()