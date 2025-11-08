import streamlit as st


st.write(st.session_state)

# Recupera a sigla da sessão
sigla = st.session_state.get("sigla_atual", "Desconhecido")

st.title(f"Detalhes do projeto {sigla}")



with st.sidebar:
    st.write(f"Projeto selecionado: {sigla}")

    st.write('teste 555')




