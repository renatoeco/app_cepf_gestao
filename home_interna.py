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

# Pessoas
col_pessoas = db["pessoas"]
df_pessoas = pd.DataFrame(list(col_pessoas.find()))

# Projetos
col_projetos = db["projetos"]
df_projetos = pd.DataFrame(list(col_projetos.find()))

# Editais
col_editais = db["editais"]
df_editais = pd.DataFrame(list(col_editais.find()))



###########################################################################################################
# CONFIGURAÇÃO DE LOCALE
###########################################################################################################


# CONFIGURAÇÃO DE LOCALIDADE PARA PORTUGUÊS
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


# Função para calcular o status de cada projeto
def calcular_status_projetos(df_projetos: pd.DataFrame) -> pd.DataFrame:
    """Atualiza df_projetos com colunas 'status' e 'dias_atraso' com base nas regras fornecidas."""

    # Garante que as colunas existam
    if 'status' not in df_projetos.columns:
        df_projetos['status'] = None
    if 'dias_atraso' not in df_projetos.columns:
        df_projetos['dias_atraso'] = None

    hoje = datetime.datetime.now().date()

    def avaliar_projeto(projeto):
        # Se já está cancelado, mantém
        if projeto.get("status") == "Cancelado":
            return "Cancelado", None

        codigo = projeto.get("codigo", "Sem código")
        sigla = projeto.get("sigla", "Sem sigla")

        parcelas = projeto.get("parcelas", [])
        if not isinstance(parcelas, list):
            parcelas = []

        # Se não há parcelas cadastradas
        if len(parcelas) == 0:
            st.warning(
                f"O projeto {codigo} - {sigla} não tem parcelas cadastradas. "
                "Não é possível determinar o status."
            )
            return None, None

        status = None
        dias_atraso = None

        # Busca a primeira parcela sem relatório realizado
        parcela_sem_relatorio = next(
            (p for p in parcelas if isinstance(p, dict)
             and "data_relatorio_prevista" in p
             and "data_relatorio_realizada" not in p),
            None
        )

        if parcela_sem_relatorio:
            # Avalia diferença entre data prevista e hoje
            try:
                data_prev = datetime.datetime.strptime(
                    parcela_sem_relatorio["data_relatorio_prevista"], "%d/%m/%Y"
                ).date()
                diff = (data_prev - hoje).days  # positivo = ainda no prazo
                dias_atraso = diff
                status = "Em dia" if diff >= 0 else "Atrasado"
            except Exception:
                status = "Erro na data prevista"
                dias_atraso = None
        else:
            # Todas as parcelas têm relatório
            ultima_parcela = parcelas[-1] if len(parcelas) > 0 else None

            if isinstance(ultima_parcela, dict) and "data_monitoramento" in ultima_parcela:
                status = "Concluído"
                dias_atraso = 0
            else:
                try:
                    data_fim_str = projeto.get("data_fim_contrato")
                    if not data_fim_str:
                        st.warning(
                            f"O projeto {codigo} - {sigla} não possui data_fim_contrato registrada."
                        )
                        return None, None

                    data_fim = datetime.datetime.strptime(data_fim_str, "%d/%m/%Y").date()
                    diff = (data_fim - hoje).days
                    dias_atraso = diff
                    status = "Em dia" if diff >= 0 else "Atrasado"
                except Exception:
                    status = "Erro na data fim"
                    dias_atraso = None

        return status, dias_atraso

    # Aplica a função a cada linha do DataFrame
    resultados = df_projetos.apply(lambda row: avaliar_projeto(row), axis=1)
    df_projetos['status'], df_projetos['dias_atraso'] = zip(*resultados)

    return df_projetos






###########################################################################################################
# TRATAMENTO DE DADOS   
###########################################################################################################


# Inclulir o status no dataframe de projetos
df_projetos = calcular_status_projetos(df_projetos)


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


# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Projetos")


st.write('')



# ============================================
# SELEÇÃO DO EDITAL
# ============================================

# Lista de editais disponíveis
lista_editais = df_editais['codigo_edital'].tolist()

# Seletor de edital
edital_selecionado = st.selectbox("Selecione o edital", lista_editais, width=300)
st.write('')

# Nome do edital selecionado
nome_edital = df_editais.loc[
    df_editais["codigo_edital"] == edital_selecionado, "nome_edital"
].values[0]
st.subheader(f'{edital_selecionado} - {nome_edital}')

# Toggle para ver somente os projetos do usuário logado
with st.container(horizontal=True, horizontal_alignment="right"):
    ver_meus_projetos = st.toggle("Ver somente os meus projetos", False)


# ============================================
# FILTRO PRINCIPAL DE PROJETOS
# ============================================

# Base: todos os projetos
df_filtrado = df_projetos.copy()

# Filtrar pelo edital selecionado
df_filtrado = df_filtrado[df_filtrado["edital"] == edital_selecionado]

# Se o toggle estiver ativo, filtra apenas os projetos do padrinho/madrinha logado
if ver_meus_projetos:
    df_filtrado = df_filtrado[df_filtrado["padrinho"] == st.session_state.nome]

# Caso não existam projetos após o filtro
if df_filtrado.empty:
    st.warning(f"Nenhum projeto encontrado para o edital **{edital_selecionado}**.")
    st.stop()








# # ============================================
# # SELEÇÃO DO EDITAL
# # ============================================

# lista_editais = df_editais['codigo_edital'].tolist()
# edital_selecionado = st.selectbox("Selecione o edital", lista_editais, width=300)
# st.write('')

# # Nome do edital
# nome_edital = df_editais.loc[df_editais["codigo_edital"] == edital_selecionado, "nome_edital"].values[0]
# st.subheader(f'{edital_selecionado} - {nome_edital}')

# # Toggle para ver somente os meus projetos
# with st.container(horizontal=True, horizontal_alignment="right"):
#     ver_meus_projetos = st.toggle("Ver somente os meus projetos", False)

# # Filtra projetos de acordo com o toggle
# df_filtrado = df_projetos.copy()
# if ver_meus_projetos:
#     df_filtrado = df_filtrado[df_filtrado['padrinho'] == st.session_state.nome]

# # Verifica se o DataFrame filtrado está vazio
# if df_filtrado.empty:
#     st.warning(f'Nenhum projeto cadastrado com o padrinho/madrinha {st.session_state.nome}.')
else:

    # ============================================
    # ABAS
    # ============================================
    tab1, tab2 = st.tabs(["Visão geral", "Projetos"])


    # ============================================
    # ABA 1: VISÃO GERAL
    # ============================================
    with tab1:

        # Contagem de projetos no edital selecionado
        st.metric("Projetos", len(df_filtrado[df_filtrado['edital'] == edital_selecionado]))
        st.write('')

        col1, espaco, col2 = st.columns([6, 1, 3])

        # Lista de projetos atrasados
        with col1:
            st.write('**Projetos atrasados**')
            st.write('')

            # ???????????????
            st.write(df_filtrado)

            projetos_atrasados = df_filtrado[
                (df_filtrado['edital'] == edital_selecionado) & (df_filtrado['status'] == 'Atrasado')
            ]

            if not projetos_atrasados.empty:
                projetos_atrasados = projetos_atrasados.copy()
                projetos_atrasados['dias_atraso'] = projetos_atrasados['dias_atraso'] * -1
                projetos_atrasados = projetos_atrasados[['codigo', 'sigla', 'padrinho', 'dias_atraso']]
                projetos_atrasados = projetos_atrasados.rename(columns={
                    'codigo': 'Código',
                    'sigla': 'Sigla',
                    'padrinho': 'Padrinho/Madrinha',
                    'dias_atraso': 'Dias de atraso'
                })



                projetos_atrasados = projetos_atrasados.sort_values(by='Dias de atraso', ascending=False)
                st.dataframe(projetos_atrasados)
            else:
                st.info("Não há projetos atrasados no momento.")

        # Gráfico de pizza do status
        with col2:
            st.write('**Status dos projetos**')
            
            mapa_cores_status = {
                'Concluído': '#74a7e4',   # Azul
                'Em dia': '#aedddd',      # Verde
                'Atrasado': '#ffbfb0',    # Vermelho
                'Cancelado': '#bbb'       # Cinza
            }

            contagens = df_filtrado['status'].value_counts(dropna=True)
            status = contagens.index.tolist()
            contagem_status = contagens.values.tolist()


            # status = df_filtrado['status'].unique().tolist()
            # contagem_status = df_filtrado['status'].value_counts().tolist()

            fig = px.pie(
                names=status,
                values=contagem_status,
                color=status,
                color_discrete_map=mapa_cores_status,
                height=350
            )
            st.plotly_chart(fig)

        # Cronograma de contratos
        st.write("**Cronograma de contratos**")

        df_filtrado_sorted = df_filtrado.sort_values(by='data_fim_contrato', ascending=False)

        altura_base = 400
        altura_extra = sum([10 / (1 + i * 0.01) for i in range(len(df_filtrado_sorted))])
        altura = int(altura_base + altura_extra)

        fig = px.timeline(
            df_filtrado_sorted,
            x_start='data_inicio_contrato_dtime',
            x_end='data_fim_contrato_dtime',
            y='codigo',
            color='status',
            color_discrete_map=mapa_cores_status,
            height=altura,
            labels={
                'codigo': 'Projeto',
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
            customdata=df_filtrado_sorted[['data_inicio_contrato', 'data_fim_contrato']].values
        )

        fig.add_vline(
            x=datetime.datetime.today(),
            line_width=2,
            line_dash="dash",
            line_color="red",
        )

        fig.update_layout(
            showlegend=False,
            yaxis=dict(title=None, side="right"),
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                tickmode='linear',
                dtick="M1",
                tickformat="%m/%Y"
            )
        )

        st.plotly_chart(fig)




    # ============================================
    # ABA 2: PROJETOS (tabela com colunas + botão)
    # ============================================
      
   
    with tab2:

        larguras_colunas = [1, 2, 5, 2, 2, 2, 2]  # Código, Sigla, Organização, Padrinho, Próxima parcela, Status, Botão
        col_labels = ["Código", "Sigla", "Organização", "Padrinho/Madrinha", "Próxima parcela", "Status", "Botão"]

        # Cabeçalhos
        cols = st.columns(larguras_colunas)
        for i, label in enumerate(col_labels):
            cols[i].markdown(f"**{label}**")
        st.write('')

        # Linhas de projetos
        for index, projeto in df_filtrado.iterrows():
            cols = st.columns(larguras_colunas)
            cols[0].write(projeto['codigo'])
            cols[1].write(projeto['sigla'])
            cols[2].write(projeto['organizacao'])
            cols[3].write(projeto['padrinho'])

            # Próxima parcela
            prox_parcela = ""
            parcelas = projeto.get('parcelas', [])
            if isinstance(parcelas, list) and len(parcelas) > 0:
                parcelas_ordenadas = sorted(parcelas, key=lambda x: x.get('parcela', 0))
                for p in parcelas_ordenadas:
                    if 'data_parcela_realizada' not in p:
                        prox_parcela = p.get('parcela')
                        break
            cols[4].write(str(prox_parcela))

            # Status
            cols[5].write(projeto.get('status', ""))


            # Botão para ver projeto
            if cols[6].button("Ver projeto", key=f"ver_{projeto['codigo']}"):

                st.session_state.pagina_atual = "ver_projeto"
                st.session_state.projeto_atual = f"{projeto['codigo']}"

                st.rerun()


