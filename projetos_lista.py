import streamlit as st
from funcoes_auxiliares import conectar_mongo_cepf_gestao, calcular_status_projetos, notificar
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


# def notificar(mensagem: str):
#     st.session_state.notificacoes.append(mensagem)



###########################################################################################################
# TRATAMENTO DE DADOS   
###########################################################################################################

# Limpar as notificações, para preencher novamente.
st.session_state.notificacoes = []

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

# Filtar somente tipos de usuário admin e equipe em df_pessoas
df_pessoas = df_pessoas[(df_pessoas["tipo_usuario"] == "admin") | (df_pessoas["tipo_usuario"] == "equipe")]

# Incluir padrinho no dataframe de projetos
# Fazendo um dataframe auxiliar de relacionamento
# Seleciona apenas colunas necessárias
df_pessoas_proj = df_pessoas[["nome_completo", "projetos"]].copy()

# Garante que "projetos" seja sempre lista
df_pessoas_proj["projetos"] = df_pessoas_proj["projetos"].apply(
    lambda x: x if isinstance(x, list) else []
)

# Explode: uma linha por projeto
df_pessoas_proj = df_pessoas_proj.explode("projetos")

# Remove linhas sem código de projeto
df_pessoas_proj = df_pessoas_proj.dropna(subset=["projetos"])

# Renomeia para facilitar o merge
df_pessoas_proj = df_pessoas_proj.rename(columns={
    "projetos": "codigo",
    "nome_completo": "padrinho"
})

# Agrupar (caso haja mais de um padrinho por projeto)
df_padrinhos = (
    df_pessoas_proj
    .groupby("codigo")["padrinho"]
    .apply(lambda nomes: ", ".join(sorted(set(nomes))))
    .reset_index()
)

# Fazer o merge
df_projetos = df_projetos.merge(
    df_padrinhos,
    on="codigo",
    how="left"
)



###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################


# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

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

# Lista de editais disponíveis
lista_editais = sorted(df_editais['codigo_edital'].unique().tolist())

# Adiciona "Todos" no início
lista_editais = ["Todos"] + lista_editais

# Selectbox de edital
edital_selecionado = st.selectbox("Selecione o edital", lista_editais, width=300)


# TÍTULO + TOGGLE no mesmo container

with st.container(horizontal=True):
    
    # Colunas lado a lado dentro do container
    col_titulo, col_toggle = st.columns([4, 1])

    # --- TÍTULO ---
    with col_titulo:
        if edital_selecionado == "Todos":
            st.subheader("Todos os editais")
        else:
            nome_edital = df_editais.loc[
                df_editais["codigo_edital"] == edital_selecionado,
                "nome_edital"
            ].values[0]

            st.subheader(f"{edital_selecionado} — {nome_edital}")

    # --- TOGGLE ---
    with col_toggle:
        st.write('')
        ver_meus_projetos = st.toggle(
            "Ver somente os meus projetos",
            False,
        )



# ============================================
# FILTRO PRINCIPAL
# ============================================

df_filtrado = df_projetos.copy()


# Filtrar pelo edital selecionado
if edital_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["edital"] == edital_selecionado]


# Filtrar somente os projetos da pessoa logada
if ver_meus_projetos:

    nome_usuario = st.session_state.nome

    # Busca a pessoa logada no df_pessoas (nome CONTÉM o nome do usuário)
    pessoa = df_pessoas.loc[
        df_pessoas["nome_completo"]
            .fillna("")
            .str.contains(st.session_state.nome, case=False)
    ]

    # Busca a pessoa logada no df_pessoas
    if pessoa.empty:
        st.warning("Usuário não encontrado no cadastro de pessoas.")
        st.stop()

    # Pega a lista de projetos da primeira linha encontrada
    codigos_projetos = pessoa.iloc[0].get("projetos", [])

    # Garante que seja uma lista
    if not isinstance(codigos_projetos, list) or len(codigos_projetos) == 0:
        st.divider()
        st.caption("Nenhum projeto associado a você.")
        st.stop()

    df_meus = df_filtrado[
        df_filtrado["codigo"].isin(codigos_projetos)
    ]

    if df_meus.empty:
        st.divider()
        st.caption("Nenhum projeto associado a você.")
        st.stop()

    df_filtrado = df_meus


# Se nenhum projeto encontrado
if df_filtrado.empty:
    st.divider()
    st.warning("Nenhum projeto encontrado.")
    st.stop()



# ============================================
# INTERFACE - LISTAGEM DE PROJETOS
# ============================================

st.divider()

# larguras_colunas = [2, 2, 5, 2, 2, 2, 2]
# col_labels = ["Código", "Sigla", "Organização", "Padrinho/Madrinha", "Próxima parcela", "Status", "Botão"]

larguras_colunas = [2, 2, 5, 2, 2, 2]
col_labels = ["Código", "Sigla", "Organização", "Padrinho/Madrinha", "Status", "Botão"]

# Cabeçalhos
cols = st.columns(larguras_colunas)
for i, label in enumerate(col_labels):
    cols[i].markdown(f"**{label}**")
st.write('')


# --------------------------------------------
# Listagem linha por linha
# --------------------------------------------

for index, projeto in df_filtrado.iterrows():
    
    cols = st.columns(larguras_colunas)

    cols[0].write(projeto['codigo'])
    cols[1].write(projeto['sigla'])
    cols[2].write(projeto['organizacao'])

    # Padrinho
    valor = projeto.get("padrinho")

    if not valor or (isinstance(valor, float) and pd.isna(valor)):
        cols[3].markdown(
            "<span style='color:#d97706; font-style:italic;'>não definido</span>",
            unsafe_allow_html=True
        )
    else:
        cols[3].write(valor)



    # cols[3].write(projeto.get('padrinho', '—'))


    # # Próxima parcela
    # prox_parcela = ""
    # parcelas = projeto.get("parcelas", [])
    # if isinstance(parcelas, list) and parcelas:
    #     parcelas_ordenadas = sorted(parcelas, key=lambda x: x.get("parcela", 0))
    #     for p in parcelas_ordenadas:
    #         if "data_parcela_realizada" not in p:
    #             prox_parcela = p.get("parcela")
    #             break

    # cols[4].write(str(prox_parcela))

    # Status
    status = projeto.get("status", "")

    if status == "Sem cronograma":
        cols[4].markdown(
            "<span style='color:#d97706; font-style:italic;'>sem cronograma</span>",
            unsafe_allow_html=True
        )
    else:
        cols[4].write(status)


    # cols[4].write(projeto.get("status", ""))

    # Botão “Ver projeto”
    if cols[5].button("Ver projeto", key=f"ver_{projeto['codigo']}"):
        st.session_state.pagina_atual = "ver_projeto"
        st.session_state.projeto_atual = projeto["codigo"]
        st.rerun()


