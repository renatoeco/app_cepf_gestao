import streamlit as st


st.set_page_config(page_title="Eventos", page_icon=":material/event:")






###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################



# Logo do sidebar
st.logo("images/ieb_logo.svg", size='large')

# Título da página e identificação
col_titulo, col_identificacao = st.columns([3, 2])

with col_titulo:
    st.header("Eventos")


# Embed da agenda Google
st.markdown(
    """
    <iframe
        src="https://calendar.google.com/calendar/embed?src=pt.brazilian%23holiday%40group.v.calendar.google.com&ctz=America%2FSao_Paulo"
        style="border:0"
        width="100%"
        height="700"
        frameborder="0"
        scrolling="no">
    </iframe>
    """,
    unsafe_allow_html=True
)


st.write('')
