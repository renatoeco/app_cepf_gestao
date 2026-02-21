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
        "responsavel": [],
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
# DADOS AUXILIARES (PESSOAS RESPONSÁVEIS)
###########################################################################################################

# apenas beneficiários
pessoas_benef = df_pessoas[
    df_pessoas["tipo_usuario"].str.contains("beneficiario", na=False)
][["_id", "nome_completo"]]

# mapa id -> nome (para exibição)
mapa_id_nome = {
    row["_id"]: row["nome_completo"]
    for _, row in pessoas_benef.iterrows()
}

lista_ids = list(mapa_id_nome.keys())



###########################################################################################################
# FORMULÁRIO
###########################################################################################################

with st.form(key=f"form_novo_projeto_{st.session_state.form_key}", border=False):

    editais = list(col_editais.find().sort("data_lancamento", -1))
    lista_editais = [e["codigo_edital"] for e in editais]

    edital = st.selectbox(
        "Edital",
        lista_editais,
        index=lista_editais.index(st.session_state.form_projeto["edital"])
        if st.session_state.form_projeto["edital"] in lista_editais else 0
    )

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


    responsaveis_ids = st.multiselect(
        "Responsáveis",
        lista_ids,
        default=st.session_state.form_projeto["responsavel"],
        format_func=lambda x: "" if x is None else mapa_id_nome[x]
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

    #######################################################################################################
    # SALVA NO SESSION STATE
    #######################################################################################################

    st.session_state.form_projeto.update({
        "edital": edital,
        "organizacao": organizacao,
        "codigo": codigo_projeto,
        "sigla": sigla_projeto,
        "nome": nome_projeto,
        "duracao": duracao,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "responsavel": responsaveis_ids,  # lista de _id
        "direcoes": direcoes,
        "publicos": publicos,
        "objetivo": objetivo
    })


    #######################################################################################################
    # VALIDAÇÃO
    #######################################################################################################

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
        st.warning(f":material/warning: Já existe um projeto com o código {codigo_projeto}.")

    elif col_projetos.find_one({"sigla": sigla_projeto}):
        st.warning(f":material/warning: Já existe um projeto com a sigla {sigla_projeto}.")

    else:

        ###################################################################################################
        # INSERE PROJETO (SEM RESPONSÁVEL)
        ###################################################################################################

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
            "direcoes_estrategicas": direcoes,
            "publicos": publicos,
            "status": "Em dia"
        })

        ###################################################################################################
        # ATUALIZA PESSOA (ADICIONA CÓDIGO DO PROJETO)
        ###################################################################################################


        if responsaveis_ids:

            col_pessoas.update_many(
                {"_id": {"$in": responsaveis_ids}},
                {
                    "$addToSet": {
                        "projetos": codigo_projeto
                    }
                }
            )


        st.success("Projeto cadastrado com sucesso!", icon=":material/check:")

        ###################################################################################################
        # RESET FORMULÁRIO 
        ###################################################################################################

        st.session_state.form_projeto = {
            "edital": "",
            "organizacao": "",
            "codigo": "",
            "sigla": "",
            "nome": "",
            "duracao": 1,
            "data_inicio": None,
            "data_fim": None,
            "responsavel": [],
            "direcoes": [],
            "publicos": [],
            "objetivo": ""
        }

        st.session_state.form_key += 1
        time.sleep(3)
        st.rerun()























# ###########################################################################################################
# # FORMULÁRIO
# ###########################################################################################################

# with st.form(key=f"form_novo_projeto_{st.session_state.form_key}", border=False):

#     # EDITAL
#     editais = list(col_editais.find().sort("data_lancamento", -1))
#     lista_editais = [e["codigo_edital"] for e in editais]

#     edital = st.selectbox(
#         "Edital",
#         lista_editais,
#         index=lista_editais.index(st.session_state.form_projeto["edital"])
#         if st.session_state.form_projeto["edital"] in lista_editais else 0
#     )

#     # ORGANIZAÇÃO
#     orgs = list(col_organizacoes.find().sort("nome_organizacao", 1))
#     lista_orgs = [o["nome_organizacao"] for o in orgs]

#     organizacao = st.selectbox(
#         "Organização",
#         lista_orgs,
#         index=lista_orgs.index(st.session_state.form_projeto["organizacao"])
#         if st.session_state.form_projeto["organizacao"] in lista_orgs else 0
#     )

#     codigo_projeto = st.text_input(
#         "Código do Projeto",
#         value=st.session_state.form_projeto["codigo"]
#     )

#     sigla_projeto = st.text_input(
#         "Sigla do Projeto",
#         value=st.session_state.form_projeto["sigla"]
#     )

#     nome_projeto = st.text_input(
#         "Nome do Projeto",
#         value=st.session_state.form_projeto["nome"]
#     )

#     duracao = st.number_input(
#         "Duração do Projeto (meses)",
#         min_value=1,
#         step=1,
#         value=st.session_state.form_projeto["duracao"]
#     )

#     data_inicio = st.date_input(
#         "Data de Início",
#         value=st.session_state.form_projeto["data_inicio"],
#         format="DD/MM/YYYY"
#     )

#     data_fim = st.date_input(
#         "Data de Fim",
#         value=st.session_state.form_projeto["data_fim"],
#         format="DD/MM/YYYY"
#     )


#     responsaveis = df_pessoas[df_pessoas["tipo_usuario"].str.contains("beneficiario", na=False)]["nome_completo"].tolist()
#     responsaveis.insert(0, "")


#     # cria lista de beneficiários mantendo id + nome
#     pessoas_benef = df_pessoas[
#         df_pessoas["tipo_usuario"].str.contains("beneficiario", na=False)
#     ][["_id", "nome_completo"]]

#     # dicionário: nome -> _id
#     mapa_responsaveis = {
#         row["nome_completo"]: row["_id"]
#         for _, row in pessoas_benef.iterrows()
#     }

#     lista_nomes = [""] + list(mapa_responsaveis.keys())

#     responsavel_nome = st.selectbox(
#         "Responsável",
#         lista_nomes,
#         index=0
#     )



#     # responsavel = st.selectbox(
#     #     "Responsável",
#     #     responsaveis,
#     #     index=responsaveis.index(st.session_state.form_projeto["responsavel"])
#     #     if st.session_state.form_projeto["responsavel"] in responsaveis else 0
#     # )

#     direcoes = st.multiselect(
#         "Direções estratégicas",
#         df_direcoes["tema"].tolist(),
#         default=st.session_state.form_projeto["direcoes"]
#     )

#     publicos = st.multiselect(
#         "Públicos",
#         df_publicos["publico"].tolist(),
#         default=st.session_state.form_projeto["publicos"]
#     )

#     objetivo = st.text_area(
#         "Objetivo geral",
#         value=st.session_state.form_projeto["objetivo"]
#     )

#     submit = st.form_submit_button("Cadastrar projeto", type="primary")




# ###########################################################################################################
# # PROCESSAMENTO
# ###########################################################################################################

# if submit:

#     # Salva valores atuais no session_state
#     st.session_state.form_projeto.update({
#         "edital": edital,
#         "organizacao": organizacao,
#         "codigo": codigo_projeto,
#         "sigla": sigla_projeto,
#         "nome": nome_projeto,
#         "duracao": duracao,
#         "data_inicio": data_inicio,
#         "data_fim": data_fim,
#         "responsavel": responsavel,
#         "direcoes": direcoes,
#         "publicos": publicos,
#         "objetivo": objetivo
#     })

#     # Validação
#     obrigatorios = {
#         "Edital": edital,
#         "Código": codigo_projeto,
#         "Sigla": sigla_projeto,
#         "Nome": nome_projeto,
#         "Objetivo": objetivo,
#         "Data início": data_inicio,
#         "Data fim": data_fim,
#         "Direções": direcoes,
#         "Públicos": publicos
#     }

#     faltando = [k for k, v in obrigatorios.items() if not v]

#     if faltando:
#         st.error(f"Preencha os campos obrigatórios: {', '.join(faltando)}")

#     elif col_projetos.find_one({"codigo": codigo_projeto}):
#         st.warning(
#             f":material/warning: Já existe um projeto com o código {codigo_projeto}. O projeto não foi cadastrado."
#         )

#     elif col_projetos.find_one({"sigla": sigla_projeto}):
#         st.warning(
#             f":material/warning: Já existe um projeto com a sigla {sigla_projeto}. O projeto não foi cadastrado."
#         )

#     else:
#         ###################################################################################################
#         # 1) INSERE O PROJETO (SEM RESPONSÁVEL)
#         ###################################################################################################

#         col_projetos.insert_one({
#             "_id": bson.ObjectId(),
#             "edital": edital,
#             "codigo": codigo_projeto,
#             "sigla": sigla_projeto,
#             "organizacao": organizacao,
#             "nome_do_projeto": nome_projeto,
#             "objetivo_geral": objetivo,
#             "duracao": duracao,
#             "data_inicio_contrato": data_inicio.strftime("%d/%m/%Y"),
#             "data_fim_contrato": data_fim.strftime("%d/%m/%Y"),
#             "direcoes_estrategicas": direcoes,
#             "publicos": publicos,
#             "status": "Em dia"
#         })

#         ###################################################################################################
#         # 2) ATUALIZA A PESSOA RESPONSÁVEL (ADICIONA O CÓDIGO NA LISTA projetos[])
#         ###################################################################################################
#         # Usa $addToSet para evitar duplicação automática


#         if responsavel_nome:
#             responsavel_id = mapa_responsaveis[responsavel_nome]

#             col_pessoas.update_one(
#                 {"_id": responsavel_id},  # agora é único e seguro
#                 {
#                     "$addToSet": {
#                         "projetos": codigo_projeto
#                     }
#                 }
#             )



#         # if responsavel:
#         #     col_pessoas.update_one(
#         #         {"nome_completo": responsavel},
#         #         {
#         #             "$addToSet": {
#         #                 "projetos": codigo_projeto
#         #             }
#         #         }
#         #     )

#         st.success("Projeto cadastrado com sucesso!", icon=":material/check:")

#         ###################################################################################################
#         # RESET TOTAL DO FORMULÁRIO (mantido igual ao seu)
#         ###################################################################################################

#         st.session_state.form_projeto = {
#             "edital": "",
#             "organizacao": "",
#             "codigo": "",
#             "sigla": "",
#             "nome": "",
#             "duracao": 1,
#             "data_inicio": None,
#             "data_fim": None,
#             "responsavel": "",
#             "direcoes": [],
#             "publicos": [],
#             "objetivo": ""
#         }

#         st.session_state.form_key += 1
#         time.sleep(3)
#         st.rerun()




# # ###########################################################################################################
# # # PROCESSAMENTO
# # ###########################################################################################################

# # if submit:

# #     # Salva valores atuais
# #     st.session_state.form_projeto.update({
# #         "edital": edital,
# #         "organizacao": organizacao,
# #         "codigo": codigo_projeto,
# #         "sigla": sigla_projeto,
# #         "nome": nome_projeto,
# #         "duracao": duracao,
# #         "data_inicio": data_inicio,
# #         "data_fim": data_fim,
# #         "responsavel": responsavel,
# #         "direcoes": direcoes,
# #         "publicos": publicos,
# #         "objetivo": objetivo
# #     })

# #     # Validação
# #     obrigatorios = {
# #         "Edital": edital,
# #         "Código": codigo_projeto,
# #         "Sigla": sigla_projeto,
# #         "Nome": nome_projeto,
# #         "Objetivo": objetivo,
# #         "Data início": data_inicio,
# #         "Data fim": data_fim,
# #         "Direções": direcoes,
# #         "Públicos": publicos
# #     }

# #     faltando = [k for k, v in obrigatorios.items() if not v]

# #     if faltando:
# #         st.error(f"Preencha os campos obrigatórios: {', '.join(faltando)}")

# #     elif col_projetos.find_one({"codigo": codigo_projeto}):
# #         st.warning(f":material/warning: Já existe um projeto com o código {codigo_projeto}. O projeto não foi cadastrado.")

# #     elif col_projetos.find_one({"sigla": sigla_projeto}):
# #         st.warning(f":material/warning: Já existe um projeto com a sigla {sigla_projeto}. O projeto não foi cadastrado.")

# #     else:
# #         col_projetos.insert_one({
# #             "_id": bson.ObjectId(),
# #             "edital": edital,
# #             "codigo": codigo_projeto,
# #             "sigla": sigla_projeto,
# #             "organizacao": organizacao,
# #             "nome_do_projeto": nome_projeto,
# #             "objetivo_geral": objetivo,
# #             "duracao": duracao,
# #             "data_inicio_contrato": data_inicio.strftime("%d/%m/%Y"),
# #             "data_fim_contrato": data_fim.strftime("%d/%m/%Y"),
# #             "responsavel": responsavel,
# #             "direcoes_estrategicas": direcoes,
# #             "publicos": publicos,
# #             "status": "Em dia"
# #         })

# #         st.success("Projeto cadastrado com sucesso!")

# #         # RESET TOTAL DO FORMULÁRIO
# #         st.session_state.form_projeto = {
# #             "edital": "",
# #             "organizacao": "",
# #             "codigo": "",
# #             "sigla": "",
# #             "nome": "",
# #             "duracao": 1,
# #             "data_inicio": None,
# #             "data_fim": None,
# #             "responsavel": "",
# #             "direcoes": [],
# #             "publicos": [],
# #             "objetivo": ""
# #         }

# #         # força recriação do formulário
# #         st.session_state.form_key += 1
# #         time.sleep(3)
# #         st.rerun()


