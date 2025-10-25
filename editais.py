import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import plotly.express as px


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Define as coleções específicas que serão utilizadas a partir do banco
col_pessoas = db["pessoas"]



###########################################################################################################
# FUNÇÕES
###########################################################################################################




###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################

# Define o layout da página como largura total
st.set_page_config(layout="wide")

# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Editais")




###########################################################################################################
# EDITAIS
###########################################################################################################

st.write('')

# Seleção do edital
st.selectbox("Selecione o edital", ["Edital 1", "Edital 2", "Edital 3"], width=300)


# Informações sobre o edital

st.write('')
st.write('')

st.metric("Projetos", 10)


# GRÁFICO DE PIZZA DO STATUS -----------------------------------------------------------------------------

# Labels e valores (exemplo – substitua pelos seus dados reais)
labels = ['Em dia', 'Atrasado', 'Concluído', 'Cancelado']
values = [10, 5, 15, 2]

# Gráfico de pizza com cores personalizadas
fig = px.pie(
    names=labels,
    values=values,
    title="Status dos Projetos",
    color=labels,
    color_discrete_map={
        'Concluído': '#2176AE',   # Azul
        'Em dia': '#99C1B9',      # Verde
        'Atrasado': '#CFB1B7',    # Vermelho
        'Cancelado': '#7f8c8d'    # Cinza
    }
)

# Exibir no Streamlit
st.plotly_chart(fig)