import streamlit as st
from pymongo import MongoClient
import datetime
import pandas as pd
import io

# Google Drive API
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload




###########################################################################################################
# CONEXÃO COM GOOGLE DRIVE
###########################################################################################################

# Escopo mínimo necessário para Drive
ESCOPO_DRIVE = ["https://www.googleapis.com/auth/drive"]

@st.cache_resource
def obter_servico_drive():
    """
    Retorna o cliente autenticado do Google Drive,
    usando as credenciais armazenadas em st.secrets.

    IMPORTANTE:
    - Não cria conexão automaticamente
    - Só executa quando chamada
    - Cache evita recriar o cliente
    """
    credenciais = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=ESCOPO_DRIVE
    )
    return build("drive", "v3", credentials=credenciais)


###########################################################################################################
# FUNÇÕES DE PASTAS NO GOOGLE DRIVE
###########################################################################################################

def obter_ou_criar_pasta(servico, nome_pasta, id_pasta_pai):
    """
    Busca uma pasta com o nome especificado dentro da pasta pai no Google Drive.
    Se não existir, cria a pasta.

    Retorna o ID da pasta.
    """

    consulta = (
        f"name='{nome_pasta}' and "
        f"'{id_pasta_pai}' in parents and "
        f"mimeType='application/vnd.google-apps.folder' and trashed=false"
    )

    resultado = servico.files().list(
        q=consulta,
        fields="files(id)",
        includeItemsFromAllDrives=True,
        supportsAllDrives=True
    ).execute()

    arquivos = resultado.get("files", [])

    if arquivos:
        return arquivos[0]["id"]

    pasta = servico.files().create(
        body={
            "name": nome_pasta,
            "parents": [id_pasta_pai],
            "mimeType": "application/vnd.google-apps.folder"
        },
        fields="id",
        supportsAllDrives=True
    ).execute()

    return pasta["id"]


def obter_pasta_projeto(servico, codigo, sigla):
    """
    Retorna o ID da pasta do projeto no Google Drive.
    Cria se não existir.

    Usa session_state para evitar duplicação.
    """

    chave = f"pasta_projeto_{codigo}"

    if chave in st.session_state:
        return st.session_state[chave]

    pasta_id = obter_ou_criar_pasta(
        servico,
        f"{codigo} - {sigla}",
        st.secrets["drive"]["pasta_drive_projetos"]
    )

    st.session_state[chave] = pasta_id
    return pasta_id


# Função para obter o ID da pasta 'Locais' no Drive, para salvar os anexos dos locais.

def obter_pasta_locais(servico, pasta_projeto_id):
    """
    Retorna o ID da subpasta 'Locais' dentro da pasta do projeto.

    Também usa cache no session_state para evitar múltiplas criações.
    """

    if "pasta_locais_id" in st.session_state:
        return st.session_state["pasta_locais_id"]

    pasta_id = obter_ou_criar_pasta(
        servico,
        "Locais",
        pasta_projeto_id
    )

    st.session_state["pasta_locais_id"] = pasta_id
    return pasta_id




# Função para obter o ID da pasta 'Pesquisas' no Drive, para salvar os anexos das pesquisas.
def obter_pasta_pesquisas(servico, pasta_projeto_id, codigo_projeto):
    """
    Retorna o ID da pasta 'Pesquisas' dentro da pasta do projeto.

    - Cria a pasta se não existir
    - Cache separado por projeto
    - Garante parent válido
    """

    # Cache por projeto (NUNCA global)
    chave = f"pasta_pesquisas_{codigo_projeto}"

    if chave in st.session_state:
        return st.session_state[chave]

    if not pasta_projeto_id:
        raise ValueError("ID da pasta do projeto inválido")

    pasta_id = obter_ou_criar_pasta(
        servico,
        "Pesquisas",
        pasta_projeto_id
    )

    # Guarda no session_state
    st.session_state[chave] = pasta_id
    return pasta_id

# Função para obter o ID da pasta 'Relatos_atividades' no Drive, para salvar os anexos das atividades.
def obter_pasta_relatos_atividades(servico, pasta_projeto_id):
    """
    Retorna o ID da pasta 'Relatos_atividades' dentro da pasta do projeto.

    - Cria a pasta se não existir
    - Usa cache no session_state
    """

    if "pasta_relatos_atividades_id" in st.session_state:
        return st.session_state["pasta_relatos_atividades_id"]

    pasta_id = obter_ou_criar_pasta(
        servico,
        "Relatos_atividades",
        pasta_projeto_id
    )

    st.session_state["pasta_relatos_atividades_id"] = pasta_id
    return pasta_id


def obter_pasta_relatos_financeiros(servico, pasta_projeto_id):
    return obter_ou_criar_pasta(
        servico,
        "Relatos_financeiros",
        pasta_projeto_id
    )



###########################################################################################################
# UPLOAD E LINK DE ARQUIVOS
###########################################################################################################

def enviar_arquivo_drive(servico, id_pasta, arquivo):
    """
    Faz upload seguro de um arquivo do Streamlit para o Google Drive.

    - Usa upload resumable (mais estável)
    - Trata erros de rede/SSL
    - NÃO propaga exceção para a UI
    - Retorna None em caso de erro
    """

    try:
        # Garante que o ponteiro do arquivo está no início
        arquivo.seek(0)

        media = MediaIoBaseUpload(
            arquivo,
            mimetype=arquivo.type,
            resumable=True
        )

        arq = servico.files().create(
            body={
                "name": arquivo.name,
                "parents": [id_pasta]
            },
            media_body=media,
            fields="id",
            supportsAllDrives=True
        ).execute()

        return arq["id"]

    except Exception as e:
        st.error("Erro temporário ao enviar arquivo. Tente novamente mais tarde.")

        # Retorna None para a camada de UI decidir o que fazer
        return None



def gerar_link_drive(id_arquivo):
    """
    Gera o link público padrão de visualização do Google Drive.
    """
    return f"https://drive.google.com/file/d/{id_arquivo}/view"






def gerar_cronograma_financeiro(parcelas: list, relatorios: list) -> pd.DataFrame:
    """
    Gera um DataFrame com o cronograma financeiro (parcelas + relatórios).

    :param parcelas: lista de parcelas (financeiro["parcelas"])
    :param relatorios: lista de relatórios (projeto["relatorios"])
    :return: DataFrame formatado para exibição
    """

    linhas_cronograma = []

    # =====================
    # PARCELAS
    # =====================
    for p in parcelas or []:
        numero = p.get("numero")
        valor = p.get("valor")
        data_prevista = p.get("data_prevista")
        data_realizada = p.get("data_realizada")

        linhas_cronograma.append(
            {
                "evento": f"Parcela {numero}",
                "Entregas": "",
                "Valor R$": (
                    f"{valor:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                    if valor is not None else ""
                ),
                "Data prevista": pd.to_datetime(data_prevista, errors="coerce"),
                "Data realizada": (
                    pd.to_datetime(data_realizada).strftime("%d/%m/%Y")
                    if data_realizada else ""
                ),
            }
        )

    # =====================
    # RELATÓRIOS
    # =====================
    for r in relatorios or []:
        numero = r.get("numero")
        entregas = r.get("entregas", [])
        data_prevista = r.get("data_prevista")
        data_realizada = r.get("data_realizada")

        linhas_cronograma.append(
            {
                "evento": f"Relatório {numero}",
                "Entregas": " / ".join(entregas) if isinstance(entregas, list) else "",
                "Valor R$": "",
                "Data prevista": pd.to_datetime(data_prevista, errors="coerce"),
                "Data realizada": (
                    pd.to_datetime(data_realizada).strftime("%d/%m/%Y")
                    if data_realizada else ""
                ),
            }
        )

    # =====================
    # DataFrame final
    # =====================
    df_cronograma = pd.DataFrame(linhas_cronograma)

    if df_cronograma.empty:
        return df_cronograma

    return df_cronograma.sort_values(by="Data prevista", ascending=True)






@st.cache_resource
def conectar_mongo_cepf_gestao():
    # CONEXÃO LOCAL
    cliente = MongoClient(st.secrets["senhas"]["senha_mongo_cepf_gestao"])
    db_cepf_gestao = cliente["cepf_gestao"] 
    return db_cepf_gestao


    # REMOTO NO ATLAS
    # cliente = MongoClient(
    # st.secrets["senhas"]["senha_mongo_portal_ispn"])
    # db_portal_ispn = cliente["ISPN_Hub"]                   
    # return db_portal_ispn


# @st.cache_resource
# def conectar_mongo_pls():
#     cliente_2 = MongoClient(
#     st.secrets["senhas"]["senha_mongo_pls"])
#     db_pls = cliente_2["db_pls"]
#     return db_pls



def ajustar_altura_dataframe(
    df_nao_atualizado,
    linhas_adicionais=0,
    altura_maxima=None,  # Se None, não aplica limite
    use_container_width=True,
    hide_index=True,
    # column_config={
    #     "Link": st.column_config.Column(
    #         width="medium"  
    #     ),
    #     "Data da Última Ação Legislativa": st.column_config.Column(
    #         label="Última ação",  
    #     )
    # }
):
    """
    Ajusta a altura da exibição de um DataFrame no Streamlit com base no número de linhas.
    Se 'altura_maxima' for informado, limita a altura até esse valor.
    """

    # Define a altura em pixels de cada linha
    altura_por_linha = 35  

    # Calcula a altura total necessária
    altura_total = ((df_nao_atualizado.shape[0] + linhas_adicionais) * altura_por_linha) + 2

    # Se altura_maxima foi informada, aplica o limite
    if altura_maxima is not None:
        altura_total = min(altura_total, altura_maxima)

    # Exibe o DataFrame no Streamlit
    st.dataframe(
        df_nao_atualizado,
        height=altura_total,
        use_container_width=use_container_width,
        hide_index=hide_index,
        # column_config=column_config
    )



def ajustar_altura_data_editor(df, linhas_adicionais=1):
    """
    Calcula a altura ideal para st.data_editor,
    garantindo que todas as linhas fiquem visíveis
    sem barra de rolagem.

    Parâmetros:
    - df: DataFrame exibido no data_editor
    - linhas_adicionais: linhas extras de folga (default=1)

    Retorna:
    - altura em pixels (int)
    """

    ALTURA_LINHA = 35      # altura média de cada linha
    ALTURA_HEADER = 38    # cabeçalho do data_editor

    try:
        total_linhas = len(df) + linhas_adicionais
    except Exception:
        total_linhas = linhas_adicionais

    altura = (total_linhas * ALTURA_LINHA) + ALTURA_HEADER

    return altura


# Envia mensagem para a área de notificação
def notificar(mensagem: str):
    st.session_state.notificacoes.append(mensagem)



def calcular_status_projetos(df_projetos: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula o status dos projetos com base em parcelas e relatórios.

    Regras:
    - Se status == "Cancelado", mantém.
    - Se NÃO houver parcelas OU relatórios → "Sem cronograma".
    - Se houver ambos, calcula normalmente.
    - Totalmente seguro contra campos ausentes, None ou NaN.
    """

    if df_projetos.empty:
        return df_projetos

    # Garante colunas necessárias
    for col in ["status", "dias_atraso", "proximo_evento", "data_proximo_evento"]:
        if col not in df_projetos.columns:
            df_projetos[col] = None

    hoje = datetime.date.today()

    for idx, projeto in df_projetos.iterrows():

        codigo = projeto.get("codigo")
        sigla = projeto.get("sigla")

        # ----------------------------------------------------------
        # MANTÉM STATUS CANCELADO
        # ----------------------------------------------------------
        if projeto.get("status") == "Cancelado":
            df_projetos.at[idx, "status"] = "Cancelado"
            df_projetos.at[idx, "dias_atraso"] = None
            df_projetos.at[idx, "proximo_evento"] = None
            df_projetos.at[idx, "data_proximo_evento"] = None
            continue

        # ----------------------------------------------------------
        # COLETA SEGURA DOS DADOS
        # ----------------------------------------------------------
        financeiro = projeto.get("financeiro")
        if not isinstance(financeiro, dict):
            financeiro = {}

        parcelas = financeiro.get("parcelas")
        if not isinstance(parcelas, list):
            parcelas = []

        relatorios = projeto.get("relatorios")
        if not isinstance(relatorios, list):
            relatorios = []

        # ----------------------------------------------------------
        # REGRA: precisa ter parcelas E relatórios
        # ----------------------------------------------------------
        if not parcelas or not relatorios:
            notificar(
                f"O projeto {codigo} - {sigla} não possui parcelas e/ou relatórios cadastrados. Não é possível determinar o status."
            )

            df_projetos.at[idx, "status"] = "Sem cronograma"
            df_projetos.at[idx, "dias_atraso"] = None
            df_projetos.at[idx, "proximo_evento"] = None
            df_projetos.at[idx, "data_proximo_evento"] = None
            continue

        # ----------------------------------------------------------
        # MONTA EVENTOS
        # ----------------------------------------------------------
        eventos = []

        for p in parcelas:
            if isinstance(p, dict):
                eventos.append({
                    "tipo": "Parcela",
                    "numero": p.get("numero"),
                    "data_prevista": pd.to_datetime(p.get("data_prevista"), errors="coerce"),
                    "realizado": p.get("data_realizada") is not None
                })

        for r in relatorios:
            if isinstance(r, dict):
                eventos.append({
                    "tipo": "Relatório",
                    "numero": r.get("numero"),
                    "data_prevista": pd.to_datetime(r.get("data_prevista"), errors="coerce"),
                    "realizado": r.get("data_realizada") is not None
                })

        # Remove eventos inválidos
        eventos = [e for e in eventos if pd.notna(e["data_prevista"])]

        if not eventos:
            notificar(
                f"O projeto {codigo} - {sigla} não possui eventos com data válida."
            )

            df_projetos.at[idx, "status"] = "Sem cronograma"
            df_projetos.at[idx, "dias_atraso"] = None
            df_projetos.at[idx, "proximo_evento"] = None
            df_projetos.at[idx, "data_proximo_evento"] = None
            continue

        # ----------------------------------------------------------
        # ORDENA E DEFINE PRÓXIMO EVENTO
        # ----------------------------------------------------------
        eventos.sort(key=lambda x: x["data_prevista"])

        proximo = next((e for e in eventos if not e["realizado"]), None)

        if not proximo:
            df_projetos.at[idx, "status"] = "Concluído"
            df_projetos.at[idx, "dias_atraso"] = 0
            df_projetos.at[idx, "proximo_evento"] = None
            df_projetos.at[idx, "data_proximo_evento"] = None
            continue

        # ----------------------------------------------------------
        # CALCULA STATUS
        # ----------------------------------------------------------
        data_prevista = proximo["data_prevista"].date()
        dias_atraso = (hoje - data_prevista).days

        status = "Atrasado" if dias_atraso > 0 else "Em dia"

        df_projetos.at[idx, "status"] = status
        df_projetos.at[idx, "dias_atraso"] = dias_atraso
        df_projetos.at[idx, "proximo_evento"] = f"{proximo['tipo']} {proximo['numero']}"
        df_projetos.at[idx, "data_proximo_evento"] = data_prevista

    return df_projetos







# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

def sidebar_projeto():
    # Botão de voltar para a home_interna só para admin, equipe e visitante
    if st.session_state.tipo_usuario in ['admin', 'equipe', 'visitante']:

        # if st.sidebar.button("Voltar para Home", icon=":material/arrow_back:", type="tertiary"):
        if st.sidebar.button("Sair do projeto", icon=":material/arrow_back:", type="tertiary"):
            
            if st.session_state.tipo_usuario == 'admin':
                st.session_state.pagina_atual = 'home_admin'
                st.rerun()

            elif st.session_state.tipo_usuario == 'equipe':
                st.session_state.pagina_atual = 'home_equipe'
                st.rerun()


    # Botão de voltar para beneficiário — apenas se tiver mais de um projeto
    if (
        st.session_state.get("tipo_usuario") == "beneficiario"
        and len(st.session_state.get("projetos", [])) > 1
    ):
        if st.sidebar.button("Voltar", icon=":material/arrow_back:", type="tertiary"):
        # if st.sidebar.button("Fechar projeto", icon=":material/close:", type="tertiary"):
            st.session_state.pagina_atual = "ben_selec_projeto"
            st.session_state.projeto_atual = None
            st.rerun()










# # --- Conversor string brasileira -> float ---
# def br_to_float(valor_str: str) -> float:
#     """
#     Converte string no formato brasileiro (1.234,56) para float (1234.56).
#     """
#     if not valor_str or not isinstance(valor_str, str):
#         return 0.00
#     # Remove pontos (milhares) e troca vírgula por ponto
#     valor_str = valor_str.replace(".", "").replace(",", ".")
#     try:
#         return round(float(valor_str), 2)
#     except ValueError:
#         return 0.00


# # --- Conversor float -> string brasileira ---
# def float_to_br(valor_float: float) -> str:
#     """
#     Converte float (1234.56) para string no formato brasileiro (1.234,56).
#     """
#     if valor_float is None:
#         return "0,00"
#     return f"{valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
