import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao
import pandas as pd
import bson
import time

###########################################################################################################
# CONEXÃO COM O BANCO
###########################################################################################################

db = conectar_mongo_cepf_gestao()

col_projetos = db["projetos"]
col_pessoas = db["pessoas"]
col_organizacoes = db["organizacoes"]
col_editais = db["editais"]
col_direcoes = db["direcoes_estrategicas"]
col_publicos = db["publicos"]

df_pessoas = pd.DataFrame(list(col_pessoas.find()))
df_direcoes = pd.DataFrame(list(col_direcoes.find()))
df_publicos = pd.DataFrame(list(col_publicos.find()))

###########################################################################################################
# SESSION STATE
###########################################################################################################

# Controle do formulário
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

# Dados do formulário
if "form_projeto" not in st.session_state:
    st.session_state.form_projeto = {
        "edital": "",
        "organizacao": "",
        "codigo": "",
        "sigla": "",
        "nome": "",
        "duracao": 1,
        "data_inicio": None,
        "data_fim": None,
        "responsavel": "",
        "direcoes": [],
        "publicos": [],
        "objetivo": ""
    }

###########################################################################################################
# INTERFACE
###########################################################################################################

st.logo("images/ieb_logo.svg", size="large")
st.header("Novo projeto")

st.write(
    "*Antes de cadastrar o **projeto**, cadastre a **Organização** e as **Pessoas** envolvidas.*"
)

###########################################################################################################
# FORMULÁRIO
###########################################################################################################

with st.form(key=f"form_novo_projeto_{st.session_state.form_key}", border=False):

    # EDITAL
    editais = list(col_editais.find().sort("data_lancamento", -1))
    lista_editais = [e["codigo_edital"] for e in editais]

    edital = st.selectbox(
        "Edital",
        lista_editais,
        index=lista_editais.index(st.session_state.form_projeto["edital"])
        if st.session_state.form_projeto["edital"] in lista_editais else 0
    )

    # ORGANIZAÇÃO
    orgs = list(col_organizacoes.find().sort("nome_organizacao", 1))
    lista_orgs = [o["nome_organizacao"] for o in orgs]

    organizacao = st.selectbox(
        "Organização",
        lista_orgs,
        index=lista_orgs.index(st.session_state.form_projeto["organizacao"])
        if st.session_state.form_projeto["organizacao"] in lista_orgs else 0
    )

    codigo_projeto = st.text_input(
        "Código do Projeto",
        value=st.session_state.form_projeto["codigo"]
    )

    sigla_projeto = st.text_input(
        "Sigla do Projeto",
        value=st.session_state.form_projeto["sigla"]
    )

    nome_projeto = st.text_input(
        "Nome do Projeto",
        value=st.session_state.form_projeto["nome"]
    )

    duracao = st.number_input(
        "Duração do Projeto (meses)",
        min_value=1,
        step=1,
        value=st.session_state.form_projeto["duracao"]
    )

    data_inicio = st.date_input(
        "Data de Início",
        value=st.session_state.form_projeto["data_inicio"],
        format="DD/MM/YYYY"
    )

    data_fim = st.date_input(
        "Data de Fim",
        value=st.session_state.form_projeto["data_fim"],
        format="DD/MM/YYYY"
    )


    responsaveis = df_pessoas[df_pessoas["tipo_usuario"].str.contains("beneficiario", na=False)]["nome_completo"].tolist()
    responsaveis.insert(0, "")

    responsavel = st.selectbox(
        "Responsável",
        responsaveis,
        index=responsaveis.index(st.session_state.form_projeto["responsavel"])
        if st.session_state.form_projeto["responsavel"] in responsaveis else 0
    )

    direcoes = st.multiselect(
        "Direções estratégicas",
        df_direcoes["tema"].tolist(),
        default=st.session_state.form_projeto["direcoes"]
    )

    publicos = st.multiselect(
        "Públicos",
        df_publicos["publico"].tolist(),
        default=st.session_state.form_projeto["publicos"]
    )

    objetivo = st.text_area(
        "Objetivo geral",
        value=st.session_state.form_projeto["objetivo"]
    )

    submit = st.form_submit_button("Cadastrar projeto", type="primary")

###########################################################################################################
# PROCESSAMENTO
###########################################################################################################

if submit:

    # Salva valores atuais
    st.session_state.form_projeto.update({
        "edital": edital,
        "organizacao": organizacao,
        "codigo": codigo_projeto,
        "sigla": sigla_projeto,
        "nome": nome_projeto,
        "duracao": duracao,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "responsavel": responsavel,
        "direcoes": direcoes,
        "publicos": publicos,
        "objetivo": objetivo
    })

    # Validação
    obrigatorios = {
        "Edital": edital,
        "Código": codigo_projeto,
        "Sigla": sigla_projeto,
        "Nome": nome_projeto,
        "Objetivo": objetivo,
        "Data início": data_inicio,
        "Data fim": data_fim,
        "Direções": direcoes,
        "Públicos": publicos
    }

    faltando = [k for k, v in obrigatorios.items() if not v]

    if faltando:
        st.error(f"Preencha os campos obrigatórios: {', '.join(faltando)}")

    elif col_projetos.find_one({"codigo": codigo_projeto}):
        st.warning(f":material/warning: Já existe um projeto com o código {codigo_projeto}. O projeto não foi cadastrado.")

    elif col_projetos.find_one({"sigla": sigla_projeto}):
        st.warning(f":material/warning: Já existe um projeto com a sigla {sigla_projeto}. O projeto não foi cadastrado.")

    else:
        col_projetos.insert_one({
            "_id": bson.ObjectId(),
            "edital": edital,
            "codigo": codigo_projeto,
            "sigla": sigla_projeto,
            "organizacao": organizacao,
            "nome_do_projeto": nome_projeto,
            "objetivo_geral": objetivo,
            "duracao": duracao,
            "data_inicio_contrato": data_inicio.strftime("%d/%m/%Y"),
            "data_fim_contrato": data_fim.strftime("%d/%m/%Y"),
            "responsavel": responsavel,
            "direcoes_estrategicas": direcoes,
            "publicos": publicos,
            "status": "Em dia"
        })

        st.success("Projeto cadastrado com sucesso!")

        # RESET TOTAL DO FORMULÁRIO
        st.session_state.form_projeto = {
            "edital": "",
            "organizacao": "",
            "codigo": "",
            "sigla": "",
            "nome": "",
            "duracao": 1,
            "data_inicio": None,
            "data_fim": None,
            "responsavel": "",
            "direcoes": [],
            "publicos": [],
            "objetivo": ""
        }

        # força recriação do formulário
        st.session_state.form_key += 1
        time.sleep(3)
        st.rerun()




































# import streamlit as st
# from funcoes_auxiliares import conectar_mongo_cepf_gestao # Funções personalizadas
# import pandas as pd
# import locale
# import re
# import time
# from geobr import read_indigenous_land, read_conservation_units, read_biomes, read_state, read_municipality
# import geopandas as gpd
# import bson

# ###########################################################################################################
# # CONEXÃO COM O BANCO DE DADOS MONGODB
# ###########################################################################################################

# # Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
# db = conectar_mongo_cepf_gestao()

# # Importa coleções e cria dataframes
# col_pessoas = db["pessoas"]
# df_pessoas = pd.DataFrame(list(col_pessoas.find()))

# col_projetos = db["projetos"]
# df_projetos = pd.DataFrame(list(col_projetos.find()))

# col_organizacoes = db["organizacoes"]
# df_organizacoes = pd.DataFrame(list(col_organizacoes.find()))

# col_editais = db["editais"]
# # df_editais = pd.DataFrame(list(col_editais.find()))

# col_direcoes = db["direcoes_estrategicas"]
# df_direcoes = pd.DataFrame(list(col_direcoes.find()))

# col_publicos = db["publicos"]
# df_publicos = pd.DataFrame(list(col_publicos.find()))

# ###########################################################################################################
# # CONFIGURAÇÃO DE LOCALE
# ###########################################################################################################


# # # CONFIGURAÇÃO DE LOCALIDADE PARA PORTUGUÊS
# # try:
# #     # Tenta a configuração comum em sistemas Linux/macOS
# #     locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
# # except locale.Error:
# #     try:
# #         # Tenta a configuração comum em alguns sistemas Windows
# #         locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
# #     except locale.Error:
# #         # Se falhar, usa a configuração padrão (geralmente inglês)
# #         print("Aviso: Não foi possível definir a localidade para Português. Usando a localidade padrão.")





# ###########################################################################################################
# # FUNÇÕES
# ###########################################################################################################






# ###########################################################################################################
# # TRATAMENTO DE DADOS   
# ###########################################################################################################


# # Inclulir o status no dataframe de projetos
# # df_projetos['status'] = 'Em dia'

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






# ###########################################################################################################
# # INTERFACE PRINCIPAL DA PÁGINA
# ###########################################################################################################


# # Logo do sidebar
# st.logo("images/cepf_logo.png", size='large')

# # Título da página
# st.header("Novo projeto")






# # ##############################################################################################################
# # FORMULARIO DE CADASTRO DE PROJETO
# # ##############################################################################################################



# st.write('\* Antes de cadastrar o **projeto**, cadastre a **Organização** e as **Pessoas** que estarão envolvidas.')
# st.write('')


# with st.form(key="form_novo_projeto", border=False, clear_on_submit=True):

#     # EDITAL        
#     # Obtém a lista de editais e ordena pela coluna data_lancamento
#     editais = col_editais.find().sort("data_lancamento", -1)
#     editais = [edital['codigo_edital'] for edital in editais]
#     # Lista editais
#     edital = st.selectbox("Edital", editais)

#     # ORGANIZAÇÃO
#     # Obtém a lista de organizações
#     organizacoes = col_organizacoes.find().sort("nome_organizacao", 1)
#     siglas_organizacoes = [organizacao['nome_organizacao'] for organizacao in organizacoes]
#     # Lista organizações
#     organizacao = st.selectbox("Organização:", siglas_organizacoes)

#     # CÓDIGO DO PROJETO
#     codigo_projeto = st.text_input("Código do Projeto:")

#     # SIGLA DO PROJETO
#     sigla_projeto = st.text_input("Sigla do Projeto:")

#     # NOME DO PROJETO
#     nome_projeto = st.text_input("Nome do Projeto:")


#     # DURAÇÃO DO PROJETO EM MESES
#     duracao_projeto = st.number_input(
#         "Duração do Projeto (em meses):",
#         min_value=1,
#         step=1,
#         format="%d"
#     )

#     # DATA DE INÍCIO DO CONTRATO
#     data_inicio_contrato = st.date_input("Data de Início do Contrato:", format="DD/MM/YYYY")

#     # DATA DE FIM DO CONTRATO
#     data_fim_contrato = st.date_input("Data de Fim do Contrato:", format="DD/MM/YYYY")

#     # Responsável
#     responsiveis = df_pessoas[df_pessoas['tipo_usuario'].str.contains("beneficiario", case=False, na=False)]['nome_completo'].tolist()
#     responsiveis.insert(0, "")
#     responsavel = st.selectbox("Responsável:", responsiveis, index=0)

#     # Direções estratégicas
#     direcoes = df_direcoes['tema'].tolist()
#     direcoes = st.multiselect("Direções estratégicas", direcoes)

#     # Público
#     publicos = df_publicos['publico'].tolist()
#     publicos = st.multiselect("Público", publicos)

#     # Objetivo geral
#     objetivo_geral = st.text_area("Objetivo geral:")





#     # --- Botão de salvar ---
#     submit = st.form_submit_button("Cadastrar projeto", icon=":material/save:", width=200, type="primary")
    
#     if submit:

#         # VALIDAÇÕES --------------------------------------------------------
#         # Lista de campos obrigatórios com nome e valor
#         campos_obrigatorios = {
#             "Edital": edital,
#             "Código do Projeto": codigo_projeto,
#             "Sigla do Projeto": sigla_projeto,
#             "Organização": organizacao,
#             "Nome do Projeto": nome_projeto,
#             "Objetivo Geral": objetivo_geral,
#             "Duração do Projeto": duracao_projeto,
#             "Data de Início": data_inicio_contrato,
#             "Data de Fim": data_fim_contrato,
#             "Direções estratégicas": direcoes,
#             "Públicos": publicos,

#         }

#         # Verificar se algum campo está vazio
#         campos_faltando = [nome for nome, valor in campos_obrigatorios.items() if not valor]

#         if campos_faltando:
#             st.error(f"Preencha os campos obrigatórios: {', '.join(campos_faltando)}")
#             expand_passo_1 = True
#         else:

#             # --- Validar unicidade de sigla e código diretamente no MongoDB ---
#             sigla_existente = col_projetos.find_one({"sigla": sigla_projeto})
#             codigo_existente = col_projetos.find_one({"codigo": codigo_projeto})

#             if sigla_existente:
#                 st.warning(f"A sigla '{sigla_projeto}' já está cadastrada em outro projeto.")
#             elif codigo_existente:
#                 st.warning(f"O código '{codigo_projeto}' já está cadastrado em outro projeto.")
#             else:


#                 # --- Criar ObjectIds ---
#                 projeto_id = bson.ObjectId()

#                 # --- Montar documento ---
#                 doc = {
#                     "_id": projeto_id,
#                     "edital": edital,
#                     "codigo": codigo_projeto,
#                     "sigla": sigla_projeto,
#                     "organizacao": organizacao,
#                     "nome_do_projeto": nome_projeto,
#                     "objetivo_geral": objetivo_geral,
#                     "duracao": duracao_projeto,
#                     "data_inicio_contrato": data_inicio_contrato.strftime("%d/%m/%Y"),
#                     "data_fim_contrato": data_fim_contrato.strftime("%d/%m/%Y"),
#                     "responsavel": responsavel,
#                     "direcoes_estrategicas": direcoes,
#                     "publicos": publicos,
#                     "status": "Em dia",
#                     # "regioes_atuacao": regioes_atuacao,

#                 }

#                 # --- Inserir no MongoDB ---
#                 col_projetos.insert_one(doc)



#                 st.success("Projeto cadastrado com sucesso!")
#                 time.sleep(3)
#                 st.rerun()















# # PASSO 4: Cadastro de Contatos ---------------------------------------
# with st.expander("**Passo 4: Contatos**", expanded=st.session_state.expand_contatos):

#     # Inicializando a variável session_state.cadastrando_contatos
#     if 'cadastrando_contatos' not in st.session_state:
#         st.session_state['cadastrando_contatos'] = None                                                                                                                                                                                                                                  

#     # Se não preencheu o passo 3, dá um aviso        
#     if "cadastrando_locais" not in st.session_state or st.session_state.cadastrando_locais != 'Finalizado':
#         st.warning("Conclua o passo 3 antes de prosseguir para o passo 4.")

#     # Se preecheu o passo 3, segue para o passo 4
#     else:
#         @st.fragment
#         def cadastrar_contatos():

#             # Se session_state.cadastrando_contatos existir e for diferente de 'finalizado', mostra o formulário
#             if 'cadastrando_contatos' in st.session_state and st.session_state['cadastrando_contatos'] != 'Finalizado':

#                 st.write('**Cadastre os contatos do projeto**')

#                 # Estrutura inicial do DataFrame
#                 colunas = ["Nome", "Função no projeto", "Telefones", "E-mail"]

#                 # Se já existirem contatos salvos, carrega do banco
#                 projeto = col_projetos.find_one({"codigo": st.session_state.cadastrando_projeto_codigo})
#                 contatos_existentes = projeto.get("contatos", []) if projeto else []

#                 if contatos_existentes:
#                     df_contatos = pd.DataFrame(contatos_existentes)
#                 else:
#                     df_contatos = pd.DataFrame(columns=colunas)

#                 # Editor de dados

#                 edited_df = st.data_editor(
#                     df_contatos,
#                     num_rows="dynamic",  # permite adicionar/remover linhas
#                     use_container_width=True,
#                     key="tabela_contatos",
#                 )

#                 # Botão de salvamento
#                 if st.button("Salvar contatos", type="primary", icon=":material/save:"):
#                     # Converte DataFrame em lista de dicionários
#                     contatos_lista = edited_df.to_dict(orient="records")

#                     try:
#                         col_projetos.update_one(
#                             {"codigo": st.session_state.cadastrando_projeto_codigo},
#                             {"$set": {"contatos": contatos_lista}},
#                             upsert=True
#                         )

#                         st.session_state.cadastrando_contatos = 'Finalizado'

#                         # Deletando as variáveis do session_state
#                         del st.session_state.expand_parcelas
#                         del st.session_state.expand_locais
#                         del st.session_state.expand_contatos
#                         del st.session_state.cadastrando_projeto_codigo
#                         del st.session_state.cadastrando_projeto_sigla
#                         del st.session_state.cadastrando_parcelas
#                         del st.session_state.cadastrando_locais
#                         del st.session_state.cadastrando_contatos

#                         st.success("Contatos salvos com sucesso!")
#                         time.sleep(3)
#                         st.rerun()

#                     except Exception as e:
#                         st.error(f"Erro ao salvar contatos: {e}")

#         cadastrar_contatos()
