import streamlit as st
from pymongo import MongoClient



@st.cache_resource
def conectar_mongo_cepf_gestao():
    # CONEXÃO LOCAL
    cliente = MongoClient(st.secrets["senhas"]["senha_mongo_cepf_gestao"])
    db_cepf_gestao = cliente["cepf_gestao"] 
    return db_cepf_gestao


    # REMOTO NO ATLAS
    # cliente = MongoClient(
    # st.secrets["senhas"]["senha_mongo_portal_ispn"])
    # db_portal_ispn = cliente["ISPN_Hub"]                   
    # return db_portal_ispn


@st.cache_resource
def conectar_mongo_pls():
    cliente_2 = MongoClient(
    st.secrets["senhas"]["senha_mongo_pls"])
    db_pls = cliente_2["db_pls"]
    return db_pls



def ajustar_altura_dataframe(
    df_nao_atualizado,
    linhas_adicionais=0,
    altura_maxima=None,  # Se None, não aplica limite
    use_container_width=True,
    hide_index=True,
    column_config={
        "Link": st.column_config.Column(
            width="medium"  
        ),
        "Data da Última Ação Legislativa": st.column_config.Column(
            label="Última ação",  
        )
    }
):
    """
    Ajusta a altura da exibição de um DataFrame no Streamlit com base no número de linhas.
    Se 'altura_maxima' for informado, limita a altura até esse valor.
    """

    # Define a altura em pixels de cada linha
    altura_por_linha = 35  

    # Calcula a altura total necessária
    altura_total = ((df_nao_atualizado.shape[0] + linhas_adicionais) * altura_por_linha) + 2

    # Se altura_maxima foi informada, aplica o limite
    if altura_maxima is not None:
        altura_total = min(altura_total, altura_maxima)

    # Exibe o DataFrame no Streamlit
    st.dataframe(
        df_nao_atualizado,
        height=altura_total,
        use_container_width=use_container_width,
        hide_index=hide_index,
        column_config=column_config
    )



def ajustar_altura_data_editor(df, linhas_adicionais=1):
    """
    Calcula a altura ideal para st.data_editor,
    garantindo que todas as linhas fiquem visíveis
    sem barra de rolagem.

    Parâmetros:
    - df: DataFrame exibido no data_editor
    - linhas_adicionais: linhas extras de folga (default=1)

    Retorna:
    - altura em pixels (int)
    """

    ALTURA_LINHA = 35      # altura média de cada linha
    ALTURA_HEADER = 38    # cabeçalho do data_editor

    try:
        total_linhas = len(df) + linhas_adicionais
    except Exception:
        total_linhas = linhas_adicionais

    altura = (total_linhas * ALTURA_LINHA) + ALTURA_HEADER

    return altura





# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

def sidebar_projeto():
    # Botão de voltar para a home_interna só para admin, equipe e visitante
    if st.session_state.tipo_usuario in ['admin', 'equipe', 'visitante']:

        if st.sidebar.button("Voltar para home", icon=":material/arrow_back:", type="tertiary"):
            
            if st.session_state.tipo_usuario == 'admin':
                st.session_state.pagina_atual = 'home_admin'
                st.rerun()

            elif st.session_state.tipo_usuario == 'equipe':
                st.session_state.pagina_atual = 'home_equipe'
                st.rerun()


    # Botão de voltar para beneficiário — apenas se tiver mais de um projeto
    if (
        st.session_state.get("tipo_usuario") == "beneficiario"
        and len(st.session_state.get("projetos", [])) > 1
    ):
        if st.sidebar.button("Voltar para home", icon=":material/arrow_back:", type="tertiary"):
            st.session_state.pagina_atual = "ben_selec_projeto"
            st.session_state.projeto_atual = None
            st.rerun()










# # --- Conversor string brasileira -> float ---
# def br_to_float(valor_str: str) -> float:
#     """
#     Converte string no formato brasileiro (1.234,56) para float (1234.56).
#     """
#     if not valor_str or not isinstance(valor_str, str):
#         return 0.00
#     # Remove pontos (milhares) e troca vírgula por ponto
#     valor_str = valor_str.replace(".", "").replace(",", ".")
#     try:
#         return round(float(valor_str), 2)
#     except ValueError:
#         return 0.00


# # --- Conversor float -> string brasileira ---
# def float_to_br(valor_float: float) -> str:
#     """
#     Converte float (1234.56) para string no formato brasileiro (1.234,56).
#     """
#     if valor_float is None:
#         return "0,00"
#     return f"{valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
