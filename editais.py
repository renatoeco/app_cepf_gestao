import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB
import plotly.express as px
import pandas as pd
import datetime
import locale


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Importa coleções e cria dataframes
col_pessoas = db["pessoas"]
df_pessoas = pd.DataFrame(list(col_pessoas.find()))

col_projetos = db["projetos"]
df_projetos = pd.DataFrame(list(col_projetos.find()))


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################


# CONFIGURAÇÃO DE LOCALIDADE PARA PORTUGUÊS (Ajuste conforme seu SO)
try:
    # Tenta a configuração comum em sistemas Linux/macOS
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        # Tenta a configuração comum em alguns sistemas Windows
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
    except locale.Error:
        # Se falhar, usa a configuração padrão (geralmente inglês)
        print("Aviso: Não foi possível definir a localidade para Português. Usando a localidade padrão.")






###########################################################################################################
# FUNÇÕES
###########################################################################################################






###########################################################################################################
# TRATAMENTO DE DADOS   
###########################################################################################################


# Inclulir o status no dataframe de projetos
df_projetos['status'] = 'Em dia'

# Converter object_id para string
df_pessoas['_id'] = df_pessoas['_id'].astype(str)
df_projetos['_id'] = df_projetos['_id'].astype(str)

# Convertendo datas de string para datetime
df_projetos['data_inicio_contrato_dtime'] = pd.to_datetime(
    df_projetos['data_inicio_contrato'], 
    format="%d/%m/%Y", 
    dayfirst=True, 
    errors="coerce"
)

df_projetos['data_fim_contrato_dtime'] = pd.to_datetime(
    df_projetos['data_fim_contrato'], 
    format="%d/%m/%Y", 
    dayfirst=True, 
    errors="coerce"
)




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

mapa_cores_status = {
    'Concluído': '#74a7e4',   # Azul
    'Em dia': '#aedddd',      # Verde
    'Atrasado': '#ffbfb0',    # Vermelho
    'Cancelado': '#bbb'         # Cinza
    }


col1, col2 = st.columns([2, 3])

# Labels e valores (exemplo – substitua pelos seus dados reais)
labels = ['Em dia', 'Atrasado', 'Concluído', 'Cancelado']
values = [10, 5, 15, 2]

# Gráfico de pizza com cores personalizadas
fig = px.pie(
    names=labels,
    values=values,
    title="Status dos Projetos",
    color=labels,
    color_discrete_map=mapa_cores_status
)

# Exibir no Streamlit
col1.plotly_chart(fig)



# Cronograma de contratos -----------------------------------------------------------------------------

st.write("**Cronograma de contratos**")

# Gráfico de gantt cronograma 

# Organizando o df por ordem de data_fim_contrato

df_projetos_filtrados = df_projetos.sort_values(by='data_fim_contrato', ascending=False)


# ??????????????????
# st.write(df_projetos_filtrados)


# Tentando calcular a altura do gráfico dinamicamente
altura_base = 400  # altura mínima
altura_extra = sum([10 / (1 + i * 0.01) for i in range(len(df_projetos))])
altura = int(altura_base + altura_extra)


# Configuração do gráfico
fig = px.timeline(
    df_projetos,
    x_start='data_inicio_contrato_dtime',
    x_end='data_fim_contrato_dtime',
    y='codigo_projeto',
    color='status',
    color_discrete_map = mapa_cores_status,
    height=altura,  
    labels={
        'codigo_projeto': 'Projeto',
        # 'status': 'Situação',
        'data_inicio_contrato_dtime': 'Início',
        'data_fim_contrato_dtime': 'Fim'
    },
)

fig.update_traces(
    hovertemplate=(
        '<b>Projeto:</b> %{y}<br>' +
        '<b>Início:</b> %{customdata[0]}<br>' +
        '<b>Fim:</b> %{customdata[1]}<br>' +
        '<extra></extra>'
    ),
    customdata=df_projetos[['data_inicio_contrato', 'data_fim_contrato']].values
)

# Adiciona a linha vertical para o dia de hoje
fig.add_vline(
    x=datetime.datetime.today(),
    line_width=2,
    line_dash="dash",
    line_color="red",
)

# Ajusta layout
fig.update_layout(
    showlegend=False,     # ← esconde a legenda
    yaxis=dict(
        title=None,
        side="right"       # coloca labels do eixo Y à direita
    ),
    xaxis=dict(
        showgrid=True,
        gridcolor='lightgray',
        tickmode='linear',
        dtick="M1",        # Mostra 1 tick por ano (12 meses)
        tickformat="%m/%Y"
    )
)

st.plotly_chart(fig)



