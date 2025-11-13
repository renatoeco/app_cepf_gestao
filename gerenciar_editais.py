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
df_chamadas = pd.DataFrame(list(col_chamadas.find()))

col_parceiros = db["parceiros"]
df_parceiros = pd.DataFrame(list(col_parceiros.find()))

col_financiadores = db["financiadores"]
df_financiadores = pd.DataFrame(list(col_financiadores.find()))

# Define as coleções específicas que serão utilizadas a partir do banco
# col_pessoas = db["pessoas"]


###########################################################################################################
# TRATAMENTO DOS DADOS
###########################################################################################################

# Renomear as colunas de df_editais
df_editais = df_editais.rename(columns={
    "codigo_edital": "Código",
    "nome_edital": "Nome",
    "data_lancamento": "Data de Lançamento",
    "parceiros": "Parceiros",
    "financiadores": "Financiadores"
})

# Converte o ObjectId para string (evita erro do PyArrow)
if "_id" in df_editais.columns:
    df_editais["_id"] = df_editais["_id"].astype(str)

if "_id" in df_chamadas.columns:
    df_chamadas["_id"] = df_chamadas["_id"].astype(str)

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
st.header("Gerenciar Editais")

tab1, tab2, tab3, tab4 = st.tabs(["Editais", "Chamadas", "Parceiros", "Financiadores"])



# Aba Editais ---------------------------------------------------------------------------------------
with tab1:

    st.write('')
    opcao_editais = st.radio("Selecione uma ação", ["Cadastrar Edital", "Editar Edital"], key="opcao_editais", horizontal=True)


    # CADASTRAR EDITAL
    if opcao_editais == "Cadastrar Edital":
        

        with st.form(key="cadastrar_edital_form" ,border=False):

            st.write('')

            codigo_edital = st.text_input("Codigo do edital:")
            nome_edital = st.text_input("Nome do edital:")
            
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

            submit = st.form_submit_button("Cadastrar Edital", icon=":material/save:", type="primary", key="btn_cadastrar_edital")


            if submit:

                # Validação de campos vazios
                if not codigo_edital or not nome_edital or not parceiro or not financiador:
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
                            "parceiros": parceiro,
                            "financiadores": financiador,
                            }
                        col_editais.insert_one(novo_edital)
                        st.success("Edital cadastrado com sucesso!")

                        time.sleep(2)
                        st.rerun()

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
                # Formulário de edição
                with st.form(key="editar_edital_form", border=False):

                    st.divider()

                    # Campos preenchidos com dados existentes
                    codigo_edital = st.text_input("Código do edital:", value=edital.get("codigo_edital", ""), disabled=True)
                    nome_edital = st.text_input("Nome do edital:", value=edital.get("nome_edital", ""))

                    # Parceiros
                    siglas_parceiros = sorted(col_parceiros.distinct("sigla_parceiro"))
                    siglas_parceiros.insert(0, "")
                    parceiros_selecionados = edital.get("parceiros", [])

                    parceiro = st.multiselect(
                        "Parceiro(s):",
                        options=siglas_parceiros,
                        default=parceiros_selecionados
                    )

                    # Financiadores
                    siglas_financiadores = sorted(col_financiadores.distinct("sigla_financiador"))
                    siglas_financiadores.insert(0, "")
                    financiadores_selecionados = edital.get("financiadores", [])

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
                        key="btn_editar_edital"
                    )

                    if submit_editar:
                        # Validação de campos vazios
                        if not nome_edital or not parceiro or not financiador:
                            st.error("Todos os campos devem ser preenchidos.")
                        else:
                            # Atualizar no MongoDB (sem verificar duplicidade de código)
                            col_editais.update_one(
                                {"_id": edital["_id"]},
                                {"$set": {
                                    "nome_edital": nome_edital,
                                    "parceiros": parceiro,
                                    "financiadores": financiador
                                }}
                            )

                            st.success("Edital atualizado com sucesso!")
                            time.sleep(2)
                            st.rerun()
                    else:
                        st.warning("Não foi possível localizar o edital selecionado.")






# Aba Chamadas ---------------------------------------------------------------------------------------
with tab2:
 
    st.write("")
    opcao_chamadas = st.radio("Selecione uma ação:", ["Cadastrar Chamada", "Editar Chamada"], key="opcao_chamadas", horizontal=True)


    # CADASTRAR CHAMADA
    if opcao_chamadas == "Cadastrar Chamada":
        

        with st.form(key="cadastrar_chamada_form" ,border=False):

            st.write('')

            codigo_chamada = st.text_input("Codigo da chamada:")
            nome_chamada = st.text_input("Nome da chamada:")
            data_lancamento = st.date_input("Data de lançamento:", format="DD/MM/YYYY")
            
            codigos_editais = sorted(col_editais.distinct("codigo_edital"))
            codigos_editais.insert(0, "")  # adiciona uma opção vazia

            edital = st.selectbox(
                "Edital:",
                options=sorted(codigos_editais),
            )

            st.write('')

            submit = st.form_submit_button("Salvar", icon=":material/save:", type="primary", key="btn_cadastrar_chamada")

            if submit:

                # Validação de campos vazios
                if not codigo_chamada or not nome_chamada or not data_lancamento or not edital:
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
                            "data_lancamento": data_lancamento_dt,
                            "edital": edital  
                        }
                        col_chamadas.insert_one(nova_chamada)
                        st.success("Chamada cadastrada com sucesso!")

                        time.sleep(2)
                        st.rerun()


    # EDITAR CHAMADA
    elif opcao_chamadas == "Editar Chamada":
        
        st.write('')

        lista_chamadas = sorted(col_chamadas.distinct("codigo_chamada"))

        chamada_selecionada = st.selectbox(
            "Selecione a Chamada:", 
            options=[""] + lista_chamadas,
            index=0
        )

        if chamada_selecionada:
            # Buscar a chamada selecionada no MongoDB
            chamada = col_chamadas.find_one({"codigo_chamada": chamada_selecionada})

            if chamada:
                # Formulário de edição (sem aninhar forms!)
                with st.form(key="editar_chamada_form", border=False):

                    st.divider()

                    # Campos preenchidos com dados existentes
                    codigo_chamada = st.text_input(
                        "Código da chamada:",
                        value=chamada.get("codigo_chamada", ""),
                        disabled=True
                    )

                    nome_chamada = st.text_input(
                        "Nome da chamada:",
                        value=chamada.get("nome_chamada", "")
                    )

                    # Data de lançamento
                    data_lancamento = chamada.get("data_lancamento")
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

                    # Edital vinculado
                    codigos_editais = sorted(col_editais.distinct("codigo_edital"))
                    codigos_editais.insert(0, "")

                    edital_atual = chamada.get("edital", "")
                    edital = st.selectbox(
                        "Edital:",
                        options=codigos_editais,
                        index=codigos_editais.index(edital_atual) if edital_atual in codigos_editais else 0
                    )

                    st.write('')
                    submit_editar = st.form_submit_button(
                        "Salvar alterações", 
                        icon=":material/save:", 
                        type="primary", 
                        key="btn_editar_chamada"
                    )

                    if submit_editar:
                        # Validação de campos obrigatórios
                        if not nome_chamada or not edital:
                            st.error("Todos os campos obrigatórios devem ser preenchidos.")
                        else:
                            # Atualizar no MongoDB
                            col_chamadas.update_one(
                                {"_id": chamada["_id"]},
                                {"$set": {
                                    "nome_chamada": nome_chamada,
                                    "data_lancamento": data_lancamento.strftime("%d/%m/%Y") if data_lancamento else None,
                                    "edital": edital,
                                    "parceiros": parceiro,
                                    "financiadores": financiador
                                }}
                            )

                            st.success("Chamada atualizada com sucesso!")
                            time.sleep(2)
                            st.rerun()
            else:
                st.warning("Não foi possível localizar a chamada selecionada.")







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
        "Escolha a ação:",
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
