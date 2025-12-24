import streamlit as st
from pymongo import MongoClient
import datetime
import pandas as pd

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


@st.cache_resource
def conectar_mongo_pls():
    cliente_2 = MongoClient(
    st.secrets["senhas"]["senha_mongo_pls"])
    db_pls = cliente_2["db_pls"]
    return db_pls



def ajustar_altura_dataframe(
    df_nao_atualizado,
    linhas_adicionais=0,
    altura_maxima=None,  # Se None, não aplica limite
    use_container_width=True,
    hide_index=True,
    column_config={
        "Link": st.column_config.Column(
            width="medium"  
        ),
        "Data da Última Ação Legislativa": st.column_config.Column(
            label="Última ação",  
        )
    }
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
        column_config=column_config
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


# Função para calcular o status de cada projeto
def calcular_status_projetos(df_projetos: pd.DataFrame) -> pd.DataFrame:
    """
    Atualiza o DataFrame de projetos com as colunas:
    - status
    - dias_atraso

    As regras de cálculo consideram:
    - parcelas localizadas em financeiro.parcelas
    - datas previstas de relatório
    - datas de conclusão ou fim de contrato
    """

    # ------------------------------------------------------------------
    # GARANTE QUE AS COLUNAS EXISTAM
    # ------------------------------------------------------------------
    if "status" not in df_projetos.columns:
        df_projetos["status"] = None

    if "dias_atraso" not in df_projetos.columns:
        df_projetos["dias_atraso"] = None

    hoje = datetime.datetime.now().date()

    # ------------------------------------------------------------------
    # FUNÇÃO INTERNA PARA AVALIAR UM PROJETO (UMA LINHA)
    # ------------------------------------------------------------------
    def avaliar_projeto(projeto: pd.Series):
        """
        Avalia um único projeto (linha do DataFrame)
        e retorna uma tupla (status, dias_atraso)
        """

        # --------------------------------------------------------------
        # SE JÁ ESTÁ CANCELADO, NÃO RECALCULA
        # --------------------------------------------------------------
        if projeto.get("status") == "Cancelado":
            return "Cancelado", None

        codigo = projeto.get("codigo", "Sem código")
        sigla = projeto.get("sigla", "Sem sigla")

        # --------------------------------------------------------------
        # ACESSO SEGURO AO FINANCEIRO
        # --------------------------------------------------------------
        financeiro = projeto.get("financeiro", {})

        if not isinstance(financeiro, dict):
            financeiro = {}

        parcelas = financeiro.get("parcelas", [])

        if not isinstance(parcelas, list):
            parcelas = []

        # --------------------------------------------------------------
        # SEM PARCELAS → NÃO É POSSÍVEL DEFINIR STATUS
        # --------------------------------------------------------------
        if len(parcelas) == 0:
            notificar(
                f"O projeto {codigo} - {sigla} não possui parcelas cadastradas. "
                "Não é possível determinar o status."
            )
            return None, None

        status = None
        dias_atraso = None

        # --------------------------------------------------------------
        # PROCURA A PRIMEIRA PARCELA SEM RELATÓRIO REALIZADO
        # --------------------------------------------------------------
        parcela_sem_relatorio = next(
            (
                p for p in parcelas
                if isinstance(p, dict)
                and "data_relatorio_prevista" in p
                and not p.get("data_relatorio_realizada")
            ),
            None
        )

        # --------------------------------------------------------------
        # CASO EXISTA PARCELA PENDENTE
        # --------------------------------------------------------------
        if parcela_sem_relatorio:
            try:
                data_prevista = datetime.datetime.strptime(
                    parcela_sem_relatorio["data_relatorio_prevista"],
                    "%d/%m/%Y"
                ).date()

                diff = (data_prevista - hoje).days
                dias_atraso = diff
                status = "Em dia" if diff >= 0 else "Atrasado"

            except Exception:
                status = "Erro na data prevista"
                dias_atraso = None

        # --------------------------------------------------------------
        # CASO TODAS AS PARCELAS TENHAM RELATÓRIO
        # --------------------------------------------------------------
        else:
            ultima_parcela = parcelas[-1] if parcelas else None

            # Projeto concluído
            if (
                isinstance(ultima_parcela, dict)
                and ultima_parcela.get("data_monitoramento")
            ):
                status = "Concluído"
                dias_atraso = 0

            # Caso contrário, avalia pela data fim do contrato
            else:
                try:
                    data_fim_str = projeto.get("data_fim_contrato")

                    if not data_fim_str:
                        st.warning(
                            f"O projeto {codigo} - {sigla} não possui data_fim_contrato registrada."
                        )
                        return None, None

                    data_fim = datetime.datetime.strptime(
                        data_fim_str,
                        "%d/%m/%Y"
                    ).date()

                    diff = (data_fim - hoje).days
                    dias_atraso = diff
                    status = "Em dia" if diff >= 0 else "Atrasado"

                except Exception:
                    status = "Erro na data fim"
                    dias_atraso = None

        return status, dias_atraso

    # ------------------------------------------------------------------
    # APLICA A FUNÇÃO A CADA LINHA DO DATAFRAME
    # ------------------------------------------------------------------
    resultados = df_projetos.apply(
        lambda row: avaliar_projeto(row),
        axis=1
    )

    df_projetos["status"], df_projetos["dias_atraso"] = zip(*resultados)

    return df_projetos



# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

def sidebar_projeto():
    # Botão de voltar para a home_interna só para admin, equipe e visitante
    if st.session_state.tipo_usuario in ['admin', 'equipe', 'visitante']:

        if st.sidebar.button("Voltar para home", icon=":material/arrow_back:", type="tertiary"):
            
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
        if st.sidebar.button("Voltar para home", icon=":material/arrow_back:", type="tertiary"):
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
