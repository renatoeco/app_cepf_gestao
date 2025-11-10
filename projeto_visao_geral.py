import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Define as coleções específicas que serão utilizadas a partir do banco
# col_pessoas = db["pessoas"]



###########################################################################################################
# FUNÇÕES
###########################################################################################################




###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################



# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header(f"Projeto {st.session_state.projeto_atual}")


# ???????????????????????
# st.write(st.session_state)




# Botão de voltar para a home_interna só para admin, monitor e visitante
if st.session_state.tipo_usuario in ['admin', 'monitor', 'visitante']:

    if st.sidebar.button("Voltar para home", icon=":material/arrow_back:", type="tertiary"):
        
        if st.session_state.tipo_usuario == 'admin':
            st.session_state.pagina_atual = 'home_admin'
            st.rerun()

        elif st.session_state.tipo_usuario == 'monitor':
            st.session_state.pagina_atual = 'home_monitor'
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

