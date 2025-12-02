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
            # area_notificacoes.warning(
            notificar(
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



# ============================================
# ÁREA DE NOTIFICAÇÕES
# ============================================


if "notificacoes" not in st.session_state:
    st.session_state.notificacoes = []


def notificar(mensagem: str):
    st.session_state.notificacoes.append(mensagem)



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

# Filtrar somente os projetos do padrinho logado
if ver_meus_projetos:
    df_filtrado = df_filtrado[df_filtrado["padrinho"] == st.session_state.nome]


# Se nenhum projeto encontrado
if df_filtrado.empty:
    st.divider()
    st.warning("Nenhum projeto encontrado.")
    st.stop()



# ============================================
# INTERFACE - LISTAGEM DE PROJETOS
# ============================================

st.divider()

larguras_colunas = [2, 2, 5, 2, 2, 2, 2]
col_labels = ["Código", "Sigla", "Organização", "Padrinho/Madrinha", "Próxima parcela", "Status", "Botão"]

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
    cols[3].write(projeto['padrinho'])

    # Próxima parcela
    prox_parcela = ""
    parcelas = projeto.get("parcelas", [])
    if isinstance(parcelas, list) and parcelas:
        parcelas_ordenadas = sorted(parcelas, key=lambda x: x.get("parcela", 0))
        for p in parcelas_ordenadas:
            if "data_parcela_realizada" not in p:
                prox_parcela = p.get("parcela")
                break

    cols[4].write(str(prox_parcela))

    # Status
    cols[5].write(projeto.get("status", ""))

    # Botão “Ver projeto”
    if cols[6].button("Ver projeto", key=f"ver_{projeto['codigo']}"):
        st.session_state.pagina_atual = "ver_projeto"
        st.session_state.projeto_atual = projeto["codigo"]
        st.rerun()













# # ============================================
# # SELEÇÃO DO EDITAL
# # ============================================

# # Lista de editais disponíveis
# lista_editais = df_editais['codigo_edital'].tolist()

# # Seletor de edital
# edital_selecionado = st.selectbox("Selecione o edital", lista_editais, width=300)
# # st.write('')


# # Nome do edital selecionado
# nome_edital = df_editais.loc[
#     df_editais["codigo_edital"] == edital_selecionado, "nome_edital"
# ].values[0]
# st.subheader(f'{edital_selecionado} - {nome_edital}')

# # Toggle para ver somente os projetos do usuário logado
# with st.container(horizontal=True, horizontal_alignment="right"):
#     ver_meus_projetos = st.toggle("Ver somente os meus projetos", False)


# # ============================================
# # FILTRO PRINCIPAL DE EDITAL
# # ============================================

# # Base: todos os projetos
# df_filtrado = df_projetos.copy()

# # Filtrar pelo edital selecionado
# df_filtrado = df_filtrado[df_filtrado["edital"] == edital_selecionado]

# # Se o toggle estiver ativo, filtra apenas os projetos do padrinho/madrinha logado
# if ver_meus_projetos:
#     df_filtrado = df_filtrado[df_filtrado["padrinho"] == st.session_state.nome]

# # Caso não existam projetos após o filtro
# if df_filtrado.empty:
#     st.warning(f"Nenhum projeto encontrado para o edital **{edital_selecionado}**.")
#     st.stop()


# # ============================================
# # INTERFACE
# # ============================================


# st.divider()


# larguras_colunas = [1, 2, 5, 2, 2, 2, 2]  # Código, Sigla, Organização, Padrinho, Próxima parcela, Status, Botão
# col_labels = ["Código", "Sigla", "Organização", "Padrinho/Madrinha", "Próxima parcela", "Status", "Botão"]

# # Cabeçalhos
# cols = st.columns(larguras_colunas)
# for i, label in enumerate(col_labels):
#     cols[i].markdown(f"**{label}**")
# st.write('')

# # Linhas de projetos
# for index, projeto in df_filtrado.iterrows():
#     cols = st.columns(larguras_colunas)
#     cols[0].write(projeto['codigo'])
#     cols[1].write(projeto['sigla'])
#     cols[2].write(projeto['organizacao'])
#     cols[3].write(projeto['padrinho'])

#     # Próxima parcela
#     prox_parcela = ""
#     parcelas = projeto.get('parcelas', [])
#     if isinstance(parcelas, list) and len(parcelas) > 0:
#         parcelas_ordenadas = sorted(parcelas, key=lambda x: x.get('parcela', 0))
#         for p in parcelas_ordenadas:
#             if 'data_parcela_realizada' not in p:
#                 prox_parcela = p.get('parcela')
#                 break
#     cols[4].write(str(prox_parcela))

#     # Status
#     cols[5].write(projeto.get('status', ""))


#     # Botão para ver projeto
#     if cols[6].button("Ver projeto", key=f"ver_{projeto['codigo']}"):

#         st.session_state.pagina_atual = "ver_projeto"
#         st.session_state.projeto_atual = f"{projeto['codigo']}"

#         st.rerun()


