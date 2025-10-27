import streamlit as st
from pymongo import MongoClient
import time

@st.fragment
def cadastrar_parcelas(colecao):

    # Se session_state.cadastrando_parcela existir e for diferente de 'finalizado', mostra o formulário
    if 'cadastrando_parcela' in st.session_state and st.session_state['cadastrando_parcela'] != 'finalizado':

        st.write('**Cadastre as parcelas**')

        # Escolhe o número de parcelas, para
        parcelas = st.number_input("Quantidade de parcelas:", min_value=1, max_value=100, value=1, step=1, width=150)

        # Formulário de parcelas
        with st.form(key="parcelas", border=False):

            parcelas_data = []  # Lista para armazenar as parcelas

            for i in range(1, parcelas + 1):
                st.write('')
                st.write(f"**Parcela {i}:**")

                with st.container():
                    data_inicio_parcela = st.date_input(
                        f"Data prevista", 
                        key=f"data_parcela_{i}", 
                        format="DD/MM/YYYY"
                    )
                    valor_parcela = st.number_input(
                        f"Valor (R$)", 
                        key=f"valor_parcela_{i}", 
                        min_value=0.0, 
                        value=0.0, 
                        step=0.01
                    )

                    # Adiciona os dados à lista (convertendo date para string)
                    parcelas_data.append({
                        "parcela": i,
                        "data_prevista": data_inicio_parcela.strftime("%d/%m/%Y"),
                        "valor": float(valor_parcela)
                    })

            st.write('')
            submit = st.form_submit_button("Salvar", icon=":material/save:", type="primary", width=200)

            # Após o submit, salvar no MongoDB
            if submit:

                # Verifica se existe um código de projeto salvo na sessão
                if "cadastrando_projeto_codigo" not in st.session_state or not st.session_state.cadastrando_projeto_codigo:
                    st.error("Código do projeto não encontrado na sessão.")
                else:
                    codigo = st.session_state.cadastrando_projeto_codigo

                    # Busca documento no MongoDB
                    projeto = colecao.find_one({"codigo": codigo})

                    if not projeto:
                        st.error(f"Projeto com código '{codigo}' não encontrado no banco.")
                    else:
                        # Atualiza documento adicionando ou sobrescrevendo 'parcelas'
                        colecao.update_one(
                            {"codigo": codigo},
                            {"$set": {"parcelas": parcelas_data}}
                        )

                        st.session_state.cadastrando_parcelas = 'Finalizado'

                        st.success("Parcelas cadastradas com sucesso!")
                        time.sleep(3)
                        st.rerun()

    # Se session_state.cadastrando_parcelas existir e for igual a 'finalizado': 
    # significa que já foi preenchido o passo 2, segue para o passo 3:
    else:
        st.success("Passo 2 concluido! Continue para o passo 3.")









@st.cache_resource
def conectar_mongo_cepf_gestao():
    # CONEXÃO LOCAL
    cliente = MongoClient("mongodb://localhost:27017/")
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
