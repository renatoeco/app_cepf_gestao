import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao, calcular_status_projetos  # Função personalizada para conectar ao MongoDB
import plotly.express as px
import pandas as pd
import datetime
# import locale


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



# ###########################################################################################################
# # CONFIGURAÇÃO DE LOCALE
# ###########################################################################################################


# # CONFIGURAÇÃO DE LOCALIDADE PARA PORTUGUÊS
# try:
#     # Tenta a configuração comum em sistemas Linux/macOS
#     locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
# except locale.Error:
#     try:
#         # Tenta a configuração comum em alguns sistemas Windows
#         locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
#     except locale.Error:
#         # Se falhar, usa a configuração padrão (geralmente inglês)
#         print("Aviso: Não foi possível definir a localidade para Português. Usando a localidade padrão.")






###########################################################################################################
# FUNÇÕES
###########################################################################################################





# ============================================
# ÁREA DE NOTIFICAÇÕES
# ============================================


if "notificacoes" not in st.session_state:
    st.session_state.notificacoes = []




###########################################################################################################
# TRATAMENTO DE DADOS
###########################################################################################################

# ------------------------------------------------------------------------------
# 1. Limpa notificações anteriores
# ------------------------------------------------------------------------------
st.session_state.notificacoes = []


# ------------------------------------------------------------------------------
# 2. Calcula status dos projetos (status, dias_atraso, próximo evento, etc.)
# ------------------------------------------------------------------------------
df_projetos = calcular_status_projetos(df_projetos)


# ------------------------------------------------------------------------------
# 3. Filtra usuários relevantes (admin e equipe)
# ------------------------------------------------------------------------------
df_pessoas = df_pessoas[
    df_pessoas["tipo_usuario"].isin(["admin", "equipe"])
]


# ------------------------------------------------------------------------------
# 4. Relaciona projetos aos padrinhos
# ------------------------------------------------------------------------------

# Seleciona apenas colunas necessárias
df_pessoas_proj = df_pessoas[["nome_completo", "projetos"]].copy()

# Garante que "projetos" seja sempre uma lista
df_pessoas_proj["projetos"] = df_pessoas_proj["projetos"].apply(
    lambda x: x if isinstance(x, list) else []
)

# Cria uma linha por projeto (explode)
df_pessoas_proj = df_pessoas_proj.explode("projetos")

# Remove registros sem código de projeto
df_pessoas_proj = df_pessoas_proj.dropna(subset=["projetos"])

# Renomeia colunas para facilitar o merge
df_pessoas_proj = df_pessoas_proj.rename(columns={
    "projetos": "codigo",
    "nome_completo": "padrinho"
})

# Agrupa padrinhos por projeto (caso haja mais de um)
df_padrinhos = (
    df_pessoas_proj
    .groupby("codigo")["padrinho"]
    .apply(lambda nomes: ", ".join(sorted(set(nomes))))
    .reset_index()
)

# Junta padrinhos ao dataframe de projetos
df_projetos = df_projetos.merge(
    df_padrinhos,
    on="codigo",
    how="left"
)


# ------------------------------------------------------------------------------
# 5. Ajustes de tipos (IDs e datas)
# ------------------------------------------------------------------------------

# Converte ObjectId para string (evita problemas com Streamlit)
df_pessoas["_id"] = df_pessoas["_id"].astype(str)
df_projetos["_id"] = df_projetos["_id"].astype(str)

# Converte datas do contrato para datetime
df_projetos["data_inicio_contrato_dtime"] = pd.to_datetime(
    df_projetos["data_inicio_contrato"],
    format="%d/%m/%Y",
    dayfirst=True,
    errors="coerce"
)

df_projetos["data_fim_contrato_dtime"] = pd.to_datetime(
    df_projetos["data_fim_contrato"],
    format="%d/%m/%Y",
    dayfirst=True,
    errors="coerce"
)










###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################


# Logo do sidebar
st.logo("images/ieb_logo.svg", size='large')

# Título da página
st.header("Projetos")


st.write('')


# Área de notificações

if st.session_state.notificacoes:
    with st.expander("Notificações", expanded=False, icon=":material/warning:"):
        for msg in st.session_state.notificacoes:
            st.warning(msg)

st.write('')
st.write('')



# ============================================
# SELEÇÃO DO EDITAL
# ============================================


lista_editais = ["Todos"] + df_editais['codigo_edital'].tolist()
edital_selecionado = st.selectbox("Selecione o edital", lista_editais, width=300)





# ============================================
# TÍTULO + TOGGLE NO MESMO CONTAINER
# ============================================


with st.container(horizontal=True):

    col_titulo, col_toggle = st.columns([4, 1])

    with col_titulo:
        if edital_selecionado == "Todos":
            st.subheader("Todos os editais")
        else:
            nome_edital = df_editais.loc[
                df_editais["codigo_edital"] == edital_selecionado,
                "nome_edital"
            ].values[0]

            st.subheader(f"{edital_selecionado} - {nome_edital}")

    with col_toggle:
        st.write("")
        ver_meus_projetos = st.toggle(
            "Ver somente os meus projetos",
            False
        )




# ============================================
# APLICAÇÃO DOS FILTROS
# ============================================


# -------------------------------------------------
# FILTRO POR EDITAL
# -------------------------------------------------

df_filtrado = df_projetos.copy()


if edital_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["edital"] == edital_selecionado]

# Se não há projetos no edital
if df_filtrado.empty:
    st.divider()
    st.warning("Nenhum projeto encontrado.")
    st.stop()


# -------------------------------------------------
# FILTRO POR PADRINHO LOGADO
# -------------------------------------------------
if ver_meus_projetos:

    # Se a coluna padrinho não existir
    if "padrinho" not in df_filtrado.columns:
        st.divider()
        st.caption("Nenhum projeto associado a você.")
        st.stop()


    df_meus = df_filtrado[
        df_filtrado["padrinho"]
            .fillna("")  # evita erro se houver NaN
            .str.contains(st.session_state.nome, case=False)
    ]



    # df_meus = df_filtrado[
    #     df_filtrado["padrinho"] == st.session_state.nome
    # ]

    if df_meus.empty:
        st.divider()
        st.caption("Nenhum projeto associado a você.")
        st.stop()

    # Se encontrou projetos do usuário
    df_filtrado = df_meus


# Caso não existam projetos após os filtros
if df_filtrado.empty:
    st.divider()
    st.warning("Nenhum projeto encontrado.")
    st.stop()



else:

    # ============================================
    # INTERFACE
    # ============================================

    st.divider()

    sobre_col1, sobre_col2 = st.columns([7, 3])

    sobre_col1.write("**Projetos atrasados**")
    sobre_col2.write("**Status dos projetos**")

    # -------------------------------------------------
    # FILTRO DE PROJETOS ATRASADOS (ÚNICO PONTO)
    # -------------------------------------------------
    if edital_selecionado == "Todos":
        projetos_atrasados = df_filtrado[df_filtrado["status"] == "Atrasado"]
    else:
        projetos_atrasados = df_filtrado[
            (df_filtrado["edital"] == edital_selecionado) &
            (df_filtrado["status"] == "Atrasado")
        ]

    # -------------------------------------------------
    # COLUNAS
    # -------------------------------------------------
    col1, col2, col3 = st.columns([1, 6, 3], gap="large")

    # -------------------------------------------------
    # COLUNA 1 — MÉTRICA
    # -------------------------------------------------
    with col1:
        total_atrasados = len(projetos_atrasados)
        st.metric("", total_atrasados)
        st.write("")

    # -------------------------------------------------
    # COLUNA 2 — LISTA DE PROJETOS ATRASADOS
    # -------------------------------------------------
    with col2:
        st.write("")

        if not projetos_atrasados.empty:
            df_exibir = projetos_atrasados.copy()

            df_exibir = df_exibir[
                ["codigo", "sigla", "padrinho", "edital", "dias_atraso"]
            ]

            df_exibir = df_exibir.rename(columns={
                "codigo": "Código",
                "sigla": "Sigla",
                "padrinho": "Padrinho/Madrinha",
                "dias_atraso": "Dias de atraso",
                "edital": "Edital"
            })

            df_exibir = df_exibir.sort_values(
                by="Dias de atraso",
                ascending=False
            )

            st.dataframe(df_exibir, hide_index=True)

        else:
            st.write("Não há projetos atrasados.")














# else:

#     # ============================================
#     # INTERFACE
#     # ============================================


#     st.divider()

#     sobre_col1, sobre_col2 = st.columns([7,3])

#     sobre_col1.write(
#         "**Projetos atrasados**"
#     )

#     sobre_col2.write(
#         "**Status dos projetos**"
#     )

#     col1, col2, col3 = st.columns([1, 6, 3], gap="large")


#     # Contagem de projetos no edital selecionado

#     with col1:
#         if edital_selecionado == "Todos":
#             total_projetos = len(df_filtrado)
#         else:
#             total_projetos = len(df_filtrado[df_filtrado['edital'] == edital_selecionado])

#         st.metric("", total_projetos)

#         st.write('')


#     # Lista de projetos atrasados
#     with col2:
#         st.write('')

#         if edital_selecionado == "Todos":
#             projetos_atrasados = df_filtrado[df_filtrado['status'] == 'Atrasado']
#         else:
#             projetos_atrasados = df_filtrado[
#                 (df_filtrado['edital'] == edital_selecionado) &
#                 (df_filtrado['status'] == 'Atrasado')
#             ]


#         if not projetos_atrasados.empty:
#             projetos_atrasados = projetos_atrasados.copy()
#             projetos_atrasados['dias_atraso'] = projetos_atrasados['dias_atraso']
#             projetos_atrasados = projetos_atrasados[['codigo', 'sigla', 'padrinho', 'edital', 'dias_atraso']]
#             projetos_atrasados = projetos_atrasados.rename(columns={
#                 'codigo': 'Código',
#                 'sigla': 'Sigla',
#                 'padrinho': 'Padrinho/Madrinha',
#                 'dias_atraso': 'Dias de atraso',
#                 'edital': 'edital'
#             })



#             projetos_atrasados = projetos_atrasados.sort_values(by='Dias de atraso', ascending=False)
#             st.dataframe(projetos_atrasados, hide_index=True)
#         else:
#             st.write("Não há projetos atrasados.")

    # Gráfico de pizza do status
    with col3:
        
        mapa_cores_status = {
            'Concluído': '#74a7e4',   # Azul
            'Em dia': '#aedddd',      # Verde
            'Atrasado': '#ffbfb0',    # Vermelho
            'Cancelado': '#bbb',        # Cinza,
            'Sem cronograma': '#fff099'

        }

        contagens = df_filtrado['status'].value_counts(dropna=True)
        status = contagens.index.tolist()
        contagem_status = contagens.values.tolist()

        fig = px.pie(
            names=status,
            values=contagem_status,
            color=status,
            color_discrete_map=mapa_cores_status,
            height=300
        )
        st.plotly_chart(fig)

    # Cronograma de contratos
    st.write("**Cronograma de contratos**")

    # Criando uma nova coluna com a data de fim no formato datetime, pra poder usar o sort por data
    df_filtrado['data_fim_contrato_dt'] = pd.to_datetime(
        df_filtrado['data_fim_contrato'],
        format='%d/%m/%Y',
        errors='coerce'
    )

    # Sort pela data de fim
    df_filtrado_sorted = df_filtrado.sort_values(
        by='data_fim_contrato_dt',
        ascending=False
    )

    altura_base = 400
    altura_extra = sum([10 / (1 + i * 0.01) for i in range(len(df_filtrado_sorted))])
    altura = int(altura_base + altura_extra)


    fig = px.timeline(
        df_filtrado_sorted.assign(
            _texto_barra=(
                df_filtrado_sorted['codigo'].astype(str)
                + ' - '
                + df_filtrado_sorted['sigla'].astype(str)
            )
        ),
        x_start='data_inicio_contrato_dtime',
        x_end='data_fim_contrato_dtime',
        y='codigo',
        text='_texto_barra',  # 👈 inline: codigo - sigla
        color='status',
        color_discrete_map=mapa_cores_status,
        height=altura,
    )


    # fig = px.timeline(
    #     df_filtrado_sorted,
    #     x_start='data_inicio_contrato_dtime',
    #     x_end='data_fim_contrato_dtime',
    #     y='codigo',
    #     text='codigo',  # 👈 texto dentro da barra
    #     color='status',
    #     color_discrete_map=mapa_cores_status,
    #     height=altura,
    #     labels={
    #         'codigo': 'Projeto',
    #         'data_inicio_contrato_dtime': 'Início',
    #         'data_fim_contrato_dtime': 'Fim'
    #     },
    # )



    # fig = px.timeline(
    #     df_filtrado_sorted,
    #     x_start='data_inicio_contrato_dtime',
    #     x_end='data_fim_contrato_dtime',
    #     y='codigo',
    #     color='status',
    #     color_discrete_map=mapa_cores_status,
    #     height=altura,
    #     labels={
    #         'codigo': 'Projeto',
    #         'data_inicio_contrato_dtime': 'Início',
    #         'data_fim_contrato_dtime': 'Fim'
    #     },
    # )

    fig.update_traces(
        hovertemplate=(
            '<b>Projeto:</b> %{y}<br>' +
            '<b>Início:</b> %{customdata[0]}<br>' +
            '<b>Fim:</b> %{customdata[1]}<br>' +
            '<extra></extra>'
        ),
        textposition='inside',
        insidetextanchor='middle',
        textfont=dict(size=14),
        cliponaxis=False,
        customdata=df_filtrado_sorted[['data_inicio_contrato', 'data_fim_contrato']].values
    )

    fig.update_yaxes(
        visible=False,
        showticklabels=False
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


