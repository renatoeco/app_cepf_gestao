import streamlit as st

# EXECUTA LOGOUT ASSIM QUE ENTRA NA PÁGINA
if "logout_executado" not in st.session_state:

    # limpa tudo
    st.session_state.clear()

    # recria estado mínimo
    st.session_state["logged_in"] = False
    st.session_state["logout_executado"] = True

# remove sidebar completamente
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# conteúdo da página
st.markdown(
    """
    <h1 style='text-align: center; margin-top: 100px;'>
        Sessão encerrada
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown("<br><br>", unsafe_allow_html=True)

st.markdown(
    """
    <div style='text-align: center; font-size: 18px'>
        <a href="https://valid-veredas.streamlit.app" target="_self">
            Voltar para tela de login (valid)
        </a>
        <br><br>
        <a href="https://veredas.streamlit.app" target="_self">
            Voltar para tela de login (pro)
        </a>
    </div>
    """,
    unsafe_allow_html=True
)