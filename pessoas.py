import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import pandas as pd
from bson import ObjectId
import time

###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Importa coleções e cria dataframes

# Pessoas
col_pessoas = db["pessoas"]



###########################################################################################################
# TRATAMENTO DOS DADOS
###########################################################################################################

# Busca todos os documentos, mas exclui o campo "senha"
df_pessoas = pd.DataFrame(list(col_pessoas.find({}, {"senha": 0})))

# Converte ObjectId para string
df_pessoas["_id"] = df_pessoas["_id"].astype(str)

# Renomeia as colunas
df_pessoas = df_pessoas.rename(columns={
    "nome_completo": "Nome",
    "tipo_usuario": "Tipo de usuário",
    "e_mail": "E-mail",
    "telefone": "Telefone",
    "status": "Status",
    "projetos": "Projetos"
})


# Projetos
col_projetos = db["projetos"]
df_projetos = pd.DataFrame(list(col_projetos.find()))
# Converte objectId para string
df_projetos['_id'] = df_projetos['_id'].astype(str)





###########################################################################################################
# Funções
###########################################################################################################

# Diálogo para editar uma pessoa
@st.dialog("Editar Pessoa", width="medium")
def editar_pessoa(_id: str):
    """Abre o diálogo para editar uma pessoa"""
    
    # Busca a pessoa no banco pelo _id
    pessoa = col_pessoas.find_one({"_id": ObjectId(_id)})
    if not pessoa:
        st.error("Pessoa não encontrada.")
        return

    # Inputs pré-carregados com os dados atuais

    nome = st.text_input("Nome", value=pessoa.get("nome_completo", ""))

    email = st.text_input("E-mail", value=pessoa.get("e_mail", ""))

    telefone = st.text_input("Telefone", value=pessoa.get("telefone", ""))


    # tipo_usuario --------------
    tipo_usuario_raw = pessoa.get("tipo_usuario", "")

    # Compatibilidade: se ainda for lista no banco, pega o primeiro valor
    if isinstance(tipo_usuario_raw, list):
        tipo_usuario_default = tipo_usuario_raw[0] if tipo_usuario_raw else ""
    elif isinstance(tipo_usuario_raw, str):
        tipo_usuario_default = tipo_usuario_raw.strip()
    else:
        tipo_usuario_default = ""

    # Campo de seleção único
    tipo_usuario = st.selectbox(
        "Tipo de usuário",
        options=["admin", "monitor", "beneficiario", "visitante"],
        index=["admin", "monitor", "beneficiario", "visitante"].index(tipo_usuario_default)
        if tipo_usuario_default in ["admin", "monitor", "beneficiario", "visitante"]
        else 0
    )

    status = st.selectbox(
        "Status",
        options=["ativo", "inativo"],
        index=0 if pessoa.get("status", "ativo") == "ativo" else 1
    )

    projetos = st.multiselect(
        "Projetos",
        options=df_projetos["sigla"].tolist(),
        default=pessoa.get("projetos", []),
    )

    st.write('')

    # Botão de salvar ---------
    if st.button("Salvar alterações", icon=":material/save:"):
        # Atualiza o registro no MongoDB
        col_pessoas.update_one(
            {"_id": ObjectId(_id)},
            {"$set": {
                "nome_completo": nome,
                "e_mail": email,
                "telefone": telefone,
                "tipo_usuario": tipo_usuario,
                "status": status,
                "projetos": projetos
            }}
        )

        st.success("Pessoa atualizada com sucesso!")
        time.sleep(3)
        st.rerun() 



###########################################################################################################
# INTERFACE
###########################################################################################################



st.header('Pessoas')

st.write('')

aba_equipe, aba_beneficiarios = st.tabs(["Equipe", "Beneficiários"])

with aba_equipe:

    # Separando só os monitores e administradores
    df_equipe = df_pessoas[
        df_pessoas["Tipo de usuário"].isin(["admin", "monitor"])
    ]


    st.write('')

    dist_colunas = [3, 4, 3, 2, 3, 2, 1]

    # Colunas
    col1, col2, col3, col4, col5, col6, col7 = st.columns(dist_colunas)

    # Cabeçalho da lista
    col1.write('**Nome**')
    col2.write('**Projetos**')
    col3.write('**E-mail**')
    col4.write('**Telefone**')
    col5.write('**Tipo de usuário**')
    col6.write('**Status**')
    col7.write('')
    
    st.write('')

    # Pra cada linha, criar colunas para os dados
    for _, row in df_equipe.iterrows():
        col1, col2, col3, col4, col5, col6, col7 = st.columns(dist_colunas)

        # NOME -----------------
        col1.write(row["Nome"])

        # PROJETOS -----------------

        # Tratando a coluna projetos, que pode ter múltiplos valores------
        projetos = row.get("Projetos", [])
        # Garante que 'projetos' seja uma lista
        if isinstance(projetos, str):
            projetos = [projetos]
        elif not isinstance(projetos, list):
            projetos = []
        # Exibe de forma amigável
        if len(projetos) == 0:
            col2.write("")
        elif len(projetos) == 1:
            col2.write(projetos[0])
        else:
            col2.write(", ".join(projetos))
        

        # E-MAIL -----------------

        col3.write(row["E-mail"])

        # TELEFONE -----------------
        col4.write(row["Telefone"])

        # TIPO DE USUÁRIO -----------------
        tipo_usuario = row.get("Tipo de usuário", "").strip()

        col5.write(tipo_usuario)

        # STATUS -----------------       
        col6.write(row["Status"])

        # BOTÃO DE EDITAR -----------------
        col7.button(":material/edit:", key=row["_id"], on_click=editar_pessoa, args=(row["_id"],))



with aba_beneficiarios:

    # Separando só os beneficiários
    df_benef = df_pessoas[
        df_pessoas["Tipo de usuário"].apply(
            lambda tipos: isinstance(tipos, list) and any(t in tipos for t in ["beneficiario"])
        )
    ]

    st.write('')

    dist_colunas = [3, 4, 3, 2, 3, 2, 1]

    # Colunas
    col1, col2, col3, col4, col5, col6, col7 = st.columns(dist_colunas)

    # Cabeçalho da lista
    col1.write('**Nome**')
    col2.write('**Projetos**')
    col3.write('**E-mail**')
    col4.write('**Telefone**')
    col5.write('**Tipo de usuário**')
    col6.write('**Status**')
    col7.write('')
    
    st.write('')

    # Pra cada linha, criar colunas para os dados
    for _, row in df_benef.iterrows():
        col1, col2, col3, col4, col5, col6, col7 = st.columns(dist_colunas)

        # NOME -----------------
        col1.write(row["Nome"])

        # PROJETOS -----------------

        # Tratando a coluna projetos, que pode ter múltiplos valores------
        projetos = row.get("Projetos", [])
        # Garante que 'projetos' seja uma lista
        if isinstance(projetos, str):
            projetos = [projetos]
        elif not isinstance(projetos, list):
            projetos = []
        # Exibe de forma amigável
        if len(projetos) == 0:
            col2.write("")
        elif len(projetos) == 1:
            col2.write(projetos[0])
        else:
            col2.write(", ".join(projetos))
        

        # E-MAIL -----------------

        col3.write(row["E-mail"])

        # TELEFONE -----------------
        col4.write(row["Telefone"])


        # TIPO DE USUARIO -----------------
        # Tratando a coluna Tipo de usuário
        tipo_usuario = str(row.get("Tipo de usuário", ""))

        # Garante que é uma lista de strings legíveis
        if isinstance(tipo_usuario, list):
            tipos = [str(t).strip() for t in tipo_usuario if str(t).strip()]
        else:
            tipos = []

        # Exibição
        if not tipos:
            col5.write("")  # ou "" se quiser vazio
        elif len(tipos) == 1:
            col5.write(tipos[0])
        else:
            col5.write(", ".join(tipos))


        # STATUS -----------------       
        col6.write(row["Status"])

        # BOTÃO DE EDITAR -----------------
        col7.button(":material/edit:", key=row["_id"], on_click=editar_pessoa, args=(row["_id"],))
