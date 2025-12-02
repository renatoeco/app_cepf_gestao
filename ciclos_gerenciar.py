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

col_doadores = db["doadores"]
df_doadores = pd.DataFrame(list(col_doadores.find()))

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
    "doadores": "Doadores"
})

# Converte o ObjectId para string (evita erro do PyArrow)
if "_id" in df_ciclos.columns:
    df_ciclos["_id"] = df_ciclos["_id"].astype(str)

if "_id" in df_editais.columns:
    df_editais["_id"] = df_editais["_id"].astype(str)

if "_id" in df_parceiros.columns:
    df_parceiros["_id"] = df_parceiros["_id"].astype(str)

if "_id" in df_doadores.columns:
    df_doadores["_id"] = df_doadores["_id"].astype(str)




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

tab1, tab2, tab3, tab4 = st.tabs(["Ciclos de Investimento", "Editais", "Parceiros", "Doadores"])



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


            # Buscar siglas únicas dos doadores no MongoDB
            siglas_doadores = sorted(col_doadores.distinct("sigla_doador"))
            siglas_doadores.insert(0, "")  # adiciona uma opção vazia

            doador = st.multiselect(
                "Doador(es):",
                options=siglas_doadores,
            )



            st.write('')

            submit = st.form_submit_button("Cadastrar Ciclo de Investimento", icon=":material/save:", type="primary", key="btn_cadastrar_ciclo")


            if submit:

                # Validação de campos vazios
                if not codigo_ciclo or not nome_ciclo or not parceiro or not doador:
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
                            "doadores": doador,
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

                    # Doadores
                    siglas_doadores = sorted(col_doadores.distinct("sigla_doador"))
                    siglas_doadores.insert(0, "")
                    doadores_selecionados = ciclo.get("doadores", [])

                    doador = st.multiselect(
                        "Doador(es):",
                        options=siglas_doadores,
                        default=doadores_selecionados
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
                        if not nome_ciclo or not parceiro or not doador:
                            st.error("Todos os campos devem ser preenchidos.")
                        else:
                            # Atualizar no MongoDB (sem verificar duplicidade de código)
                            col_ciclos.update_one(
                                {"_id": ciclo["_id"]},
                                {"$set": {
                                    "nome_ciclo": nome_ciclo,
                                    "parceiros": parceiro,
                                    "doadores": doador
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
                                    "doadores": doador
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
# ABA DOADORES
# ----------------------------------------

with tab4:

    st.write("")

    opcao_doadores = st.radio(
        "Selecione uma ação:",
        ["Cadastrar Doador", "Editar Doador"],
        horizontal=True
    )

    # ----------------------------------------
    # CADASTRAR DOADOR
    # ----------------------------------------
    if opcao_doadores == "Cadastrar Doador":

        with st.form(key="doador_cadastro_form", border=False):
            st.write("")

            sigla_doador = st.text_input("Sigla:")
            nome_doador = st.text_input("Nome do doador:")

            st.write("")
            submit = st.form_submit_button("Salvar", icon=":material/save:", type="primary")

            if submit:
                # Validação
                if not sigla_doador or not nome_doador:
                    st.error("Todos os campos devem ser preenchidos.")
                else:
                    # Verifica se a sigla já existe
                    sigla_existente = col_doadores.find_one({"sigla_doador": sigla_doador})

                    if sigla_existente:
                        st.error(f"A sigla '{sigla_doador}' já está sendo utilizada.")
                    else:
                        # Inserir no MongoDB
                        novo_doador = {
                            "sigla_doador": sigla_doador,
                            "nome_doador": nome_doador,
                        }
                        col_doadores.insert_one(novo_doador)
                        st.success("Doador cadastrado com sucesso!")
                        time.sleep(2)
                        st.rerun()

    # ----------------------------------------
    # EDITAR DOADOR
    # ----------------------------------------
    elif opcao_doadores == "Editar Doador":
        st.write("")

        # Selectbox fora do form — evita erro "Missing Submit Button"
        lista_doadores = sorted(col_doadores.distinct("sigla_doador"))
        doador_selecionado = st.selectbox(
            "Selecione o doador:",
            options=[""] + lista_doadores,
            index=0
        )

        if doador_selecionado:
            # Buscar o doador no MongoDB
            doador = col_doadores.find_one({"sigla_doador": doador_selecionado})

            if doador:
                # Form somente quando há um doador válido
                with st.form(key="doador_editar_form", border=False):
                    st.divider()

                    sigla_doador = st.text_input(
                        "Sigla do doador:",
                        value=doador.get("sigla_doador", ""),
                        disabled=True
                    )
                    nome_doador = st.text_input(
                        "Nome do doador:",
                        value=doador.get("nome_doador", "")
                    )

                    st.write("")
                    submit_editar = st.form_submit_button(
                        "Salvar alterações",
                        icon=":material/save:",
                        type="primary"
                    )

                    if submit_editar:
                        # Validação
                        if not nome_doador:
                            st.error("O campo nome do doador deve ser preenchido.")
                        else:
                            # Atualizar no MongoDB
                            col_doadores.update_one(
                                {"_id": doador["_id"]},
                                {"$set": {"nome_doador": nome_doador}}
                            )

                            st.success("Doador atualizado com sucesso!")
                            time.sleep(2)
                            st.rerun()
            else:
                st.warning("Não foi possível localizar o doador selecionado.")
