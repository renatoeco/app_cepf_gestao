import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao # Funções personalizadas
import pandas as pd
import time
import re


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()


col_projetos = db["projetos"]
df_projetos = pd.DataFrame(list(col_projetos.find()))

col_organizacoes = db["organizacoes"]
df_organizacoes = pd.DataFrame(list(col_organizacoes.find()))

# Organiza em ordem alfabética pela sigla
df_organizacoes = df_organizacoes.sort_values(by=["sigla_organizacao"])






###########################################################################################################
# FUNÇÕES
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











@st.dialog("Editar organização", width="medium")
def editar_organizacao_dialog():

    # Coleção de organizações no MongoDB
    col_organizacoes = db["organizacoes"]

    # ----------------------------------------------------------------------------------------------------
    # SELECTBOX PARA ESCOLHER A ORGANIZAÇÃO
    # ----------------------------------------------------------------------------------------------------


    # Cria coluna concatenada
    df_organizacoes["org_label"] = (
        df_organizacoes["sigla_organizacao"]
        + " - "
        + df_organizacoes["nome_organizacao"]
    )

    # Lista de opções
    opcoes = df_organizacoes["org_label"].tolist()

    # Mapa label -> id
    mapa_org_label_id = {
        row["org_label"]: row["_id"]
        for _, row in df_organizacoes.iterrows()
    }

    # Selectbox
    escolha = st.selectbox(
        "Selecione a organização",
        options=opcoes,
        index=None,
        placeholder="Escolha uma organização"
    )



    # ----------------------------------------------------------------------------------------------------
    # CARREGAMENTO DOS DADOS DA ORGANIZAÇÃO SELECIONADA
    # ----------------------------------------------------------------------------------------------------

    if escolha:

        # Extrai apenas a sigla da organização selecionada
        
        # Recupera o id da organização selecionada
        org_id = mapa_org_label_id.get(escolha)

        # Busca no banco pelo _id
        org = col_organizacoes.find_one({"_id": org_id})
        
        
        
        # sigla = escolha.split(" - ")[0]


        if org:

            # ----------------------------------------------------------------------------------------------
            # CAMPOS DE EDIÇÃO
            # ----------------------------------------------------------------------------------------------

            # Campo para edição da sigla
            st.text_input(
                "Sigla da organização",
                value=org.get("sigla_organizacao", ""),
                key="sigla_organizacao_input"
            )

            # Campo para edição do nome
            st.text_input(
                "Nome da organização",
                value=org.get("nome_organizacao", ""),
                key="nome_organizacao_input"
            )

            # Campo para edição do CNPJ
            st.text_input(
                "CNPJ",
                value=org.get("cnpj", ""),
                key="cnpj_input"
            )

            # ----------------------------------------------------------------------------------------------
            # BOTÃO DE SALVAR ALTERAÇÕES
            # ----------------------------------------------------------------------------------------------

            if st.button("Salvar alterações", type="primary"):

                ###################################################################################################
                # PROCESSAMENTO DO FORMULÁRIO
                ###################################################################################################

                # Obtém valores atuais do formulário
                sigla_organizacao = st.session_state.sigla_organizacao_input.strip()
                nome_organizacao = st.session_state.nome_organizacao_input.strip()
                cnpj = st.session_state.cnpj_input.strip()

                # Verifica se todos os campos foram preenchidos
                if not sigla_organizacao or not nome_organizacao or not cnpj:

                    st.error("Todos os campos devem ser preenchidos.")

                # Validação do formato do CNPJ
                elif not validar_cnpj(cnpj):

                    st.error(
                        "CNPJ inválido. Utilize o formato **00.000.000/0000-00** ou apenas 14 números **00000000000000**."
                    )

                else:

                    # Padroniza o CNPJ antes de salvar no banco
                    cnpj = formatar_cnpj(cnpj)

                    # ------------------------------------------------------------------------------------------
                    # VERIFICAÇÃO DE DUPLICIDADE
                    # ------------------------------------------------------------------------------------------

                    # Busca outra organização com a mesma sigla (ignorando o documento atual)
                    sigla_existente = col_organizacoes.find_one({
                        "sigla_organizacao": sigla_organizacao,
                        "_id": {"$ne": org["_id"]}
                    })

                    # Busca outra organização com o mesmo CNPJ (ignorando o documento atual)
                    cnpj_existente = col_organizacoes.find_one({
                        "cnpj": cnpj,
                        "_id": {"$ne": org["_id"]}
                    })

                    # Tratamento de duplicidade de sigla
                    if sigla_existente:

                        st.error(
                            f"A sigla '{sigla_organizacao}' já está cadastrada em outra organização."
                        )

                    # Tratamento de duplicidade de CNPJ
                    elif cnpj_existente:

                        st.error(
                            f"O CNPJ '{cnpj}' já está cadastrado em outra organização."
                        )

                    else:

                        ###################################################################################################
                        # ATUALIZAÇÃO DO DOCUMENTO NO BANCO
                        ###################################################################################################

                        col_organizacoes.update_one(
                            {"_id": org["_id"]},
                            {
                                "$set": {
                                    "sigla_organizacao": sigla_organizacao,
                                    "nome_organizacao": nome_organizacao,
                                    "cnpj": cnpj
                                }
                            }
                        )

                        st.success(
                            "Organização atualizada com sucesso!",
                            icon=":material/check:"
                        )

                        time.sleep(3)

                        st.rerun()








###########################################################################################################
# TRATAMENTO DE DADOS   
###########################################################################################################


# --------------------------------------------------
# CONTAGEM DE PROJETOS POR ORGANIZAÇÃO (USANDO ID)
# --------------------------------------------------

# Conta projetos agrupando pelo id da organização
contagem_projetos = df_projetos["id_organizacao"].value_counts()

# Merge usando o _id da organização
df_organizacoes = df_organizacoes.merge(
    contagem_projetos.rename("quantidade_projetos"),
    left_on="_id",
    right_index=True,
    how="left"
)

# Organizações sem projeto ficam com 0
df_organizacoes["quantidade_projetos"] = (
    df_organizacoes["quantidade_projetos"].fillna(0).astype(int)
)





###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################


# Logo do sidebar
st.logo("images/ieb_logo.svg", size='large')

# Título da página
st.header("Organizações")

st.write('')
st.write('')

# Contagem de organizações
st.write(f"**{df_organizacoes['sigla_organizacao'].nunique()} organizações cadastradas**")
st.write('')


with st.container(horizontal=True, horizontal_alignment="right"):

    if st.button("Editar organização", icon=":material/edit:", width=250):
        editar_organizacao_dialog()

st.write('')


st.dataframe(df_organizacoes, 
             column_order=["sigla_organizacao", "nome_organizacao", "cnpj", "quantidade_projetos"], 
             hide_index=True,
             column_config={
                 "sigla_organizacao": st.column_config.Column(
                     label="Sigla",
                     width="small" 
                 ),
                 "nome_organizacao": st.column_config.Column(
                     label="Nome",
                     width="large" 
                 ),
                 "cnpj": st.column_config.Column(
                     label="CNPJ", 
                     width="small" 
                 ),
                 "quantidade_projetos": st.column_config.Column(
                     label="Quantidade de Projetos", 
                     width="small" 
                 )
             })

