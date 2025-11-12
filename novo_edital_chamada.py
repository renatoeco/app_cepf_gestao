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

col_chamadas = db["chamadas"]


# Define as coleções específicas que serão utilizadas a partir do banco
# col_pessoas = db["pessoas"]



###########################################################################################################
# FUNÇÕES
###########################################################################################################




###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################


# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Cadastrar Editais e Chamadas")


opcoes = ["Nova Chamada", "Novo Edital"]
opcao = st.radio("", opcoes)


if opcao == "Nova Chamada":

    with st.form(key="chamada_form" ,border=False):

        st.write('')

        codigo_chamada = st.text_input("Codigo da chamada:")
        nome_chamada = st.text_input("Nome da chamada:")
        data_lancamento = st.date_input("Data de lançamento:", format="DD/MM/YYYY")

        st.write('')

        submit = st.form_submit_button("Salvar", icon=":material/save:", type="primary")


        if submit:

            # Validação de campos vazios
            if not codigo_chamada or not nome_chamada or not data_lancamento:
                st.error("Todos os campos devem ser preenchidos.")

            else:

                # Converte para datetime com hora zero
                data_lancamento_dt = datetime.datetime.combine(data_lancamento, datetime.datetime.min.time())

                # Verifica se codigo já existe
                codigo_existente = col_chamadas.find_one({"codigo_chamada": codigo_chamada})

                if codigo_existente:
                    st.error(f"O codigo '{codigo_chamada}' já está cadastrada.")

                else:
                    # Inserir no MongoDB
                    nova_chamada = {
                        "codigo_chamada": codigo_chamada,
                        "nome_chamada": nome_chamada,
                        "data_lancamento": data_lancamento_dt  
                    }
                    col_chamadas.insert_one(nova_chamada)
                    st.success("Chamada cadastrada com sucesso!")

                    time.sleep(2)
                    st.rerun()



elif opcao == "Novo Edital":

    with st.form(key="edital_form" ,border=False):

        st.write('')

        codigo_edital = st.text_input("Codigo do edital:")
        nome_edital = st.text_input("Nome do edital:")
        doador = st.text_input("Doador:")
        # data_lancamento = st.date_input("Data de lançamento:", format="DD/MM/YYYY")


        st.write('')

        submit = st.form_submit_button("Salvar", icon=":material/save:", type="primary")


        if submit:

            # Validação de campos vazios
            if not codigo_edital or not nome_edital or not doador:
                st.error("Todos os campos devem ser preenchidos.")

            else:

                # Verifica se codigo já existe
                codigo_existente = col_editais.find_one({"codigo_edital": codigo_edital})

                if codigo_existente:
                    st.error(f"O codigo '{codigo_edital}' já está cadastrada.")

                else:
                    # Inserir no MongoDB
                    novo_edital = {
                        "codigo_edital": codigo_edital,
                        "nome_edital": nome_edital,
                        "doador": doador  
                    }
                    col_editais.insert_one(novo_edital)
                    st.success("Edital cadastrado com sucesso!")

                    time.sleep(2)
                    st.rerun()