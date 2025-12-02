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


col_ciclos = db["ciclos_investimento"]
df_ciclos = pd.DataFrame(list(col_ciclos.find()))

col_editais = db["editais"]
df_editais = pd.DataFrame(list(col_editais.find()))

col_parceiros = db["parceiros"]
df_parceiros = pd.DataFrame(list(col_parceiros.find()))

col_financiadores = db["financiadores"]
df_financiadores = pd.DataFrame(list(col_financiadores.find()))

# Define as coleções específicas que serão utilizadas a partir do banco
# col_pessoas = db["pessoas"]


###########################################################################################################
# TRATAMENTO DOS DADOS
###########################################################################################################

# Renomear as colunas de df_ciclos
df_ciclos = df_ciclos.rename(columns={
    "codigo_ciclo": "Código",
    "nome_ciclo": "Nome",
    "data_lancamento": "Data de Lançamento",
    "parceiros": "Parceiros",
    "financiadores": "Financiadores"
})

# Converte o ObjectId para string (evita erro do PyArrow)
if "_id" in df_ciclos.columns:
    df_ciclos["_id"] = df_ciclos["_id"].astype(str)

if "_id" in df_editais.columns:
    df_editais["_id"] = df_editais["_id"].astype(str)

if "_id" in df_parceiros.columns:
    df_parceiros["_id"] = df_parceiros["_id"].astype(str)

if "_id" in df_financiadores.columns:
    df_financiadores["_id"] = df_financiadores["_id"].astype(str)




###########################################################################################################
# FUNÇÕES
###########################################################################################################




###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################


# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Gerenciar Ciclos de Investimento")

tab1, tab2, tab3, tab4 = st.tabs(["Ciclos de Investimento", "Editais", "Parceiros", "Financiadores"])



# Aba Ciclos de Investimento ---------------------------------------------------------------------------------------
with tab1:

    st.write('')
    opcao_ciclos = st.radio("Selecione uma ação", ["Cadastrar Ciclo de Investimento", "Editar Ciclo de Investimento"], key="opcao_ciclos", horizontal=True)


    # CADASTRAR CICLO DE INVESTIMENTO
    if opcao_ciclos == "Cadastrar Ciclo de Investimento":
        

        with st.form(key="cadastrar_ciclo_form" ,border=False):

            st.write('')

            codigo_ciclo = st.text_input("Codigo do Ciclo de Investimento:")
            nome_ciclo = st.text_input("Nome do Ciclo de Investimento:")
            
            # Buscar siglas únicas dos parceiros no MongoDB
            siglas_parceiros = sorted(col_parceiros.distinct("sigla_parceiro"))
            siglas_parceiros.insert(0, "")  # adiciona uma opção vazia

            parceiro = st.multiselect(
                "Parceiros(s):",
                options=siglas_parceiros,
            )


            # Buscar siglas únicas dos financiadores no MongoDB
            siglas_financiadores = sorted(col_financiadores.distinct("sigla_financiador"))
            siglas_financiadores.insert(0, "")  # adiciona uma opção vazia

            financiador = st.multiselect(
                "Financiadores(s):",
                options=siglas_financiadores,
            )



            st.write('')

            submit = st.form_submit_button("Cadastrar Ciclo de Investimento", icon=":material/save:", type="primary", key="btn_cadastrar_ciclo")


            if submit:

                # Validação de campos vazios
                if not codigo_ciclo or not nome_ciclo or not parceiro or not financiador:
                    st.error("Todos os campos devem ser preenchidos.")

                else:

                    # Verifica se codigo já existe
                    codigo_existente = col_ciclos.find_one({"codigo_ciclo": codigo_ciclo})

                    if codigo_existente:
                        st.error(f"O codigo '{codigo_ciclo}' já está cadastrada.")

                    else:
                        # Inserir no MongoDB
                        novo_ciclo = {
                            "codigo_ciclo": codigo_ciclo,
                            "nome_ciclo": nome_ciclo,
                            "parceiros": parceiro,
                            "financiadores": financiador,
                            }
                        col_ciclos.insert_one(novo_ciclo)
                        st.success("Ciclo de Investimento cadastrado com sucesso!")

                        time.sleep(2)
                        st.rerun()

    elif opcao_ciclos == "Editar Ciclo de Investimento":

        st.write('')

        lista_ciclos = sorted(col_ciclos.distinct("codigo_ciclo"))

        ciclo_selecionado = st.selectbox(
            "Selecione o Ciclo de Investimento:", 
            options=[""] + lista_ciclos,
            index=0
        )

        if ciclo_selecionado:
            # Buscar o ciclo selecionado no MongoDB
            ciclo = col_ciclos.find_one({"codigo_ciclo": ciclo_selecionado})

            if ciclo:
                # Formulário de edição
                with st.form(key="editar_ciclo_form", border=False):

                    st.divider()

                    # Campos preenchidos com dados existentes
                    codigo_ciclo = st.text_input("Código do Ciclo de Investimento :", value=ciclo.get("codigo_ciclo", ""), disabled=True)
                    nome_ciclo = st.text_input("Nome do Ciclo de Investimento :", value=ciclo.get("nome_ciclo", ""))

                    # Parceiros
                    siglas_parceiros = sorted(col_parceiros.distinct("sigla_parceiro"))
                    siglas_parceiros.insert(0, "")
                    parceiros_selecionados = ciclo.get("parceiros", [])

                    parceiro = st.multiselect(
                        "Parceiro(s):",
                        options=siglas_parceiros,
                        default=parceiros_selecionados
                    )

                    # Financiadores
                    siglas_financiadores = sorted(col_financiadores.distinct("sigla_financiador"))
                    siglas_financiadores.insert(0, "")
                    financiadores_selecionados = ciclo.get("financiadores", [])

                    financiador = st.multiselect(
                        "Financiador(es):",
                        options=siglas_financiadores,
                        default=financiadores_selecionados
                    )

                    st.write('')

                    # Botão de submit
                    submit_editar = st.form_submit_button(
                        "Salvar alterações", 
                        icon=":material/save:", 
                        type="primary", 
                        key="btn_editar_ciclo"
                    )

                    if submit_editar:
                        # Validação de campos vazios
                        if not nome_ciclo or not parceiro or not financiador:
                            st.error("Todos os campos devem ser preenchidos.")
                        else:
                            # Atualizar no MongoDB (sem verificar duplicidade de código)
                            col_ciclos.update_one(
                                {"_id": ciclo["_id"]},
                                {"$set": {
                                    "nome_ciclo": nome_ciclo,
                                    "parceiros": parceiro,
                                    "financiadores": financiador
                                }}
                            )

                            st.success("Ciclo de Investimento atualizado com sucesso!")
                            time.sleep(2)
                            st.rerun()
                    else:
                        st.warning("Não foi possível localizar o Ciclo de Investimento selecionado.")






# Aba Editais ---------------------------------------------------------------------------------------
with tab2:
 
    st.write("")
    opcao_editais = st.radio("Selecione uma ação:", ["Cadastrar Edital", "Editar Edital"], key="opcao_editais", horizontal=True)


    # CADASTRAR EDITAL
    if opcao_editais == "Cadastrar Edital":
        

        with st.form(key="cadastrar_edital_form" ,border=False):

            st.write('')

            codigo_edital = st.text_input("Codigo do edital:")
            nome_edital = st.text_input("Nome do edital:")
            data_lancamento = st.date_input("Data de lançamento:", format="DD/MM/YYYY")
            
            codigos_ciclos = sorted(col_ciclos.distinct("codigo_ciclo"))
            codigos_ciclos.insert(0, "")  # adiciona uma opção vazia

            ciclo = st.selectbox(
                "Ciclo de Investimento:",
                options=sorted(codigos_ciclos),
            )

            st.write('')

            submit = st.form_submit_button("Salvar", icon=":material/save:", type="primary", key="btn_cadastrar_edital")

            if submit:

                # Validação de campos vazios
                if not codigo_edital or not nome_edital or not data_lancamento or not ciclo:
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
                            "data_lancamento": data_lancamento_dt,
                            "ciclo_investimento": ciclo  
                        }
                        col_editais.insert_one(novo_edital)
                        st.success("Edital cadastrado com sucesso!")

                        time.sleep(2)
                        st.rerun()


    # EDITAR EDITAL
    elif opcao_editais == "Editar Edital":
        
        st.write('')

        lista_editais = sorted(col_editais.distinct("codigo_edital"))

        edital_selecionado = st.selectbox(
            "Selecione o Edital:", 
            options=[""] + lista_editais,
            index=0
        )

        if edital_selecionado:
            # Buscar o edital selecionado no MongoDB
            edital = col_editais.find_one({"codigo_edital": edital_selecionado})

            if edital:
                # Formulário de edição (sem aninhar forms!)
                with st.form(key="editar_edital_form", border=False):

                    st.divider()

                    # Campos preenchidos com dados existentes
                    codigo_edital = st.text_input(
                        "Código do edital:",
                        value=edital.get("codigo_edital", ""),
                        disabled=True
                    )

                    nome_edital = st.text_input(
                        "Nome do edital:",
                        value=edital.get("nome_edital", "")
                    )

                    # Data de lançamento
                    data_lancamento = edital.get("data_lancamento")
                    if isinstance(data_lancamento, str):
                        try:
                            from datetime import datetime
                            data_lancamento = datetime.strptime(data_lancamento, "%d/%m/%Y").date()
                        except:
                            data_lancamento = None
                    elif data_lancamento:
                        data_lancamento = data_lancamento.date()

                    data_lancamento = st.date_input(
                        "Data de lançamento:",
                        value=data_lancamento,
                        format="DD/MM/YYYY"
                    )

                    # Ciclo de investimento vinculado
                    codigos_ciclos = sorted(col_ciclos.distinct("codigo_ciclo"))
                    codigos_ciclos.insert(0, "")

                    ciclo_atual = edital.get("ciclo_investimento", "")
                    ciclo = st.selectbox(
                        "Ciclo de Investimento:",
                        options=codigos_ciclos,
                        index=codigos_ciclos.index(ciclo_atual) if ciclo_atual in codigos_ciclos else 0
                    )

                    st.write('')
                    submit_editar = st.form_submit_button(
                        "Salvar alterações", 
                        icon=":material/save:", 
                        type="primary", 
                        key="btn_editar_edital"
                    )

                    if submit_editar:
                        # Validação de campos obrigatórios
                        if not nome_edital or not ciclo:
                            st.error("Todos os campos obrigatórios devem ser preenchidos.")
                        else:
                            # Atualizar no MongoDB
                            col_editais.update_one(
                                {"_id": edital["_id"]},
                                {"$set": {
                                    "nome_edital": nome_edital,
                                    "data_lancamento": data_lancamento.strftime("%d/%m/%Y") if data_lancamento else None,
                                    "ciclo_investimento": ciclo,
                                    "parceiros": parceiro,
                                    "financiadores": financiador
                                }}
                            )

                            st.success("Edital atualizado com sucesso!")
                            time.sleep(2)
                            st.rerun()
            else:
                st.warning("Não foi possível localizar o edital selecionado.")







# Aba Parceiros ---------------------------------------------------------------------------------------

with tab3:

    st.write("")

    # Escolha da ação
    opcao_parceiros = st.radio(
        "Selecione uma ação:",
        ["Cadastrar Parceiro", "Editar Parceiro"],
        horizontal=True
    )

    # ----------------------------------------
    # CADASTRAR PARCEIRO
    # ----------------------------------------
    if opcao_parceiros == "Cadastrar Parceiro":
        with st.form(key="parceiro_cadastro_form", border=False):
            st.write("")

            sigla_parceiro = st.text_input("Sigla do parceiro:")
            nome_parceiro = st.text_input("Nome do parceiro:")

            st.write("")
            submit_cadastro = st.form_submit_button(
                "Salvar novo parceiro", 
                icon=":material/save:", 
                type="primary"
            )

            if submit_cadastro:
                # Validação
                if not sigla_parceiro or not nome_parceiro:
                    st.error("Todos os campos devem ser preenchidos.")
                else:
                    # Verifica se a sigla já existe
                    sigla_existente = col_parceiros.find_one({"sigla_parceiro": sigla_parceiro})
                    if sigla_existente:
                        st.error(f"A sigla '{sigla_parceiro}' já está sendo utilizada.")
                    else:
                        # Inserir no MongoDB
                        novo_parceiro = {
                            "sigla_parceiro": sigla_parceiro,
                            "nome_parceiro": nome_parceiro
                        }
                        col_parceiros.insert_one(novo_parceiro)
                        st.success("Parceiro cadastrado com sucesso!")
                        time.sleep(2)
                        st.rerun()

    # ----------------------------------------
    # EDITAR PARCEIRO
    # ----------------------------------------
    elif opcao_parceiros == "Editar Parceiro":
        st.write("")

        # Selectbox fora do form — assim o form de edição só existe quando há um parceiro selecionado
        lista_parceiros = sorted(col_parceiros.distinct("sigla_parceiro"))
        parceiro_selecionado = st.selectbox(
            "Selecione o parceiro:",
            options=[""] + lista_parceiros,
            index=0
        )

        if parceiro_selecionado:
            # Buscar o parceiro no MongoDB
            parceiro = col_parceiros.find_one({"sigla_parceiro": parceiro_selecionado})

            if parceiro:
                # Form somente quando temos o parceiro — garante que sempre haverá um botão de submit
                with st.form(key="parceiro_editar_form", border=False):
                    st.divider()

                    # Sigla não editável
                    sigla_parceiro = st.text_input(
                        "Sigla do parceiro:",
                        value=parceiro.get("sigla_parceiro", ""),
                        disabled=True
                    )
                    nome_parceiro = st.text_input(
                        "Nome do parceiro:",
                        value=parceiro.get("nome_parceiro", "")
                    )

                    st.write("")
                    submit_editar = st.form_submit_button(
                        "Salvar alterações",
                        icon=":material/save:",
                        type="primary"
                    )

                    if submit_editar:
                        # Validação
                        if not nome_parceiro:
                            st.error("O campo nome do parceiro deve ser preenchido.")
                        else:
                            # Atualizar no MongoDB (sem checar duplicidade)
                            col_parceiros.update_one(
                                {"_id": parceiro["_id"]},
                                {"$set": {
                                    "nome_parceiro": nome_parceiro
                                }}
                            )

                            st.success("Parceiro atualizado com sucesso!")
                            time.sleep(2)
                            st.rerun()
            else:
                st.warning("Não foi possível localizar o parceiro selecionado.")






# ----------------------------------------
# ABA FINANCIADORES
# ----------------------------------------

with tab4:

    st.write("")

    opcao_financiadores = st.radio(
        "Selecione uma ação:",
        ["Cadastrar Financiador", "Editar Financiador"],
        horizontal=True
    )

    # ----------------------------------------
    # CADASTRAR FINANCIADOR
    # ----------------------------------------
    if opcao_financiadores == "Cadastrar Financiador":

        with st.form(key="financiador_cadastro_form", border=False):
            st.write("")

            sigla_financiador = st.text_input("Sigla:")
            nome_financiador = st.text_input("Nome do financiador:")

            st.write("")
            submit = st.form_submit_button("Salvar", icon=":material/save:", type="primary")

            if submit:
                # Validação
                if not sigla_financiador or not nome_financiador:
                    st.error("Todos os campos devem ser preenchidos.")
                else:
                    # Verifica se a sigla já existe
                    sigla_existente = col_financiadores.find_one({"sigla_financiador": sigla_financiador})

                    if sigla_existente:
                        st.error(f"A sigla '{sigla_financiador}' já está sendo utilizada.")
                    else:
                        # Inserir no MongoDB
                        novo_financiador = {
                            "sigla_financiador": sigla_financiador,
                            "nome_financiador": nome_financiador,
                        }
                        col_financiadores.insert_one(novo_financiador)
                        st.success("Financiador cadastrado com sucesso!")
                        time.sleep(2)
                        st.rerun()

    # ----------------------------------------
    # EDITAR FINANCIADOR
    # ----------------------------------------
    elif opcao_financiadores == "Editar Financiador":
        st.write("")

        # Selectbox fora do form — evita erro "Missing Submit Button"
        lista_financiadores = sorted(col_financiadores.distinct("sigla_financiador"))
        financiador_selecionado = st.selectbox(
            "Selecione o financiador:",
            options=[""] + lista_financiadores,
            index=0
        )

        if financiador_selecionado:
            # Buscar o financiador no MongoDB
            financiador = col_financiadores.find_one({"sigla_financiador": financiador_selecionado})

            if financiador:
                # Form somente quando há um financiador válido
                with st.form(key="financiador_editar_form", border=False):
                    st.divider()

                    sigla_financiador = st.text_input(
                        "Sigla do financiador:",
                        value=financiador.get("sigla_financiador", ""),
                        disabled=True
                    )
                    nome_financiador = st.text_input(
                        "Nome do financiador:",
                        value=financiador.get("nome_financiador", "")
                    )

                    st.write("")
                    submit_editar = st.form_submit_button(
                        "Salvar alterações",
                        icon=":material/save:",
                        type="primary"
                    )

                    if submit_editar:
                        # Validação
                        if not nome_financiador:
                            st.error("O campo nome do financiador deve ser preenchido.")
                        else:
                            # Atualizar no MongoDB
                            col_financiadores.update_one(
                                {"_id": financiador["_id"]},
                                {"$set": {"nome_financiador": nome_financiador}}
                            )

                            st.success("Financiador atualizado com sucesso!")
                            time.sleep(2)
                            st.rerun()
            else:
                st.warning("Não foi possível localizar o financiador selecionado.")
