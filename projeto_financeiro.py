import streamlit as st
import pandas as pd
import time
from funcoes_auxiliares import conectar_mongo_cepf_gestao  # Função personalizada para conectar ao MongoDB


###########################################################################################################
# CONEXÃO COM O BANCO DE DADOS MONGODB
###########################################################################################################

# Conecta-se ao banco de dados MongoDB (usa cache automático para melhorar performance)
db = conectar_mongo_cepf_gestao()

# Define as coleções específicas que serão utilizadas a partir do banco
col_projetos = db["projetos"]


###########################################################################################################
# TRATAMENTO DE DADOS
###########################################################################################################

codigo_projeto_atual = st.session_state.get("projeto_atual")

if not codigo_projeto_atual:
    st.error("Nenhum projeto selecionado.")
    st.stop()

# Capturando o projeto atual no bd
df_projeto = pd.DataFrame(
    list(
        col_projetos.find(
            {"codigo": codigo_projeto_atual}
        )
    )
)

if df_projeto.empty:
    st.error("Projeto não encontrado no banco de dados.")
    st.stop()


# Transformar o id em string
df_projeto = df_projeto.copy()
if "_id" in df_projeto.columns:
    df_projeto["_id"] = df_projeto["_id"].astype(str)


projeto = df_projeto.iloc[0]

# Capturando o financeiro no banco de dados
financeiro = projeto.get("financeiro", {})



###########################################################################################################
# FUNÇÕES
###########################################################################################################




###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################



# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página
st.header("Financeiro")








# Abas para o "Cronograma de Desembolsos e Relatórios" e "Orçamento"
cron_desemb, orcamento = st.tabs(["Cronograma", "Orçamento"])



with cron_desemb:

    # Capturando os dados no bd
    valor_atual = financeiro.get("valor_total")




    # --------------------------------------------------
    # PERMISSÃO E MODO DE EDIÇÃO
    # --------------------------------------------------
    usuario_interno = st.session_state.tipo_usuario in ["admin", "equipe"]

    with st.container(horizontal=True, horizontal_alignment="right"):
        if usuario_interno:
            modo_edicao = st.toggle("Modo de edição", key="editar_cronograma")
        else:
            modo_edicao = False



    # --------------------------------------------------
    # MODO VISUALIZAÇÃO
    # --------------------------------------------------
    if not modo_edicao:

        if valor_atual is not None:
            st.metric(
                label="Valor total do projeto",
                value=f"R$ {valor_atual:,.2f}"
            )
        else:
            st.caption("Valor total do projeto ainda não cadastrado.")

    # --------------------------------------------------
    # MODO EDIÇÃO
    # --------------------------------------------------
    else:

        st.markdown("#### Valor total do projeto")

        with st.form("form_valor_total", border=False):

            valor_total = st.number_input(
                "Valor total do projeto (R$)",
                min_value=0.0,
                step=1000.0,
                format="%.2f",
                value=float(valor_atual) if valor_atual is not None else 0.0,
                width=300
            )

            st.write('')
            salvar = st.form_submit_button("Salvar", icon=":material/save:")

            if salvar:
                col_projetos.update_one(
                    {"codigo": codigo_projeto_atual},
                    {
                        "$set": {
                            "financeiro.valor_total": float(valor_total)
                        }
                    }
                )

                st.success("Valor total do projeto salvo com sucesso!")
                time.sleep(3)
                st.rerun()



                st.success("Valor total do projeto salvo com sucesso!")
                time.sleep(3)
                st.rerun()





















# with cron_desemb:

#     st.write('')

#     # --------------------------------------------------
#     # PERMISSÃO DE USUÁRIOS INTERNOS
#     # --------------------------------------------------
#     usuario_interno = st.session_state.tipo_usuario in ["admin", "equipe"]

#     # Toggle do modo de edição
#     with st.container(horizontal=True, horizontal_alignment="right"):
#         if usuario_interno:
#             modo_edicao = st.toggle("Modo de edição", key="editar_cronograma")


#     # --------------------------------------------------
#     # MODO EDIÇÃO
#     # --------------------------------------------------

#     if modo_edicao:


#         financeiro = projeto.get("financeiro", {})
#         valor_atual = financeiro.get("valor_total")

#         st.markdown("#### Valor total do projeto")

#         # ==========================
#         # VISUALIZAÇÃO (sempre)
#         # ==========================
#         if valor_atual is not None:
#             st.metric(
#                 label="Valor total cadastrado",
#                 value=f"R$ {valor_atual:,.2f}"
#             )
#         else:
#             st.warning("Valor total do projeto ainda não cadastrado.")

#         # ==========================
#         # EDIÇÃO (somente modo edição)
#         # ==========================
#         if usuario_interno and st.session_state.get("editar_cronograma"):

#             with st.form("form_valor_total"):

#                 valor_total = st.number_input(
#                     "Valor total do projeto (R$)",
#                     min_value=0.0,
#                     step=1000.0,
#                     format="%.2f",
#                     value=float(valor_atual) if valor_atual is not None else 0.0
#                 )

#                 salvar = st.form_submit_button("Salvar")

#                 if salvar:
#                     col_projetos.update_one(
#                         {"_id": projeto["_id"]},
#                         {
#                             "$set": {
#                                 "financeiro.valor_total": float(valor_total),
#                                 "financeiro.parcelas": financeiro.get("parcelas", []),
#                                 "financeiro.orcamento": financeiro.get("orcamento", [])
#                             }
#                         }
#                     )

#                     st.success("Valor total do projeto salvo com sucesso!")
#                     st.rerun()

    










































with orcamento:
    st.write('*Bloco do cronograma de parcelas, relatórios e status // Em construção*')