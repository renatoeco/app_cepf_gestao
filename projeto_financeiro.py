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


        # Radio para escolher o que será editado
        opcao_editar_cron = st.radio(
            "O que deseja editar?",
            ["Valor total",
            "Parcelas", 
            "Relatórios"],
            horizontal=True
        )

        # st.divider()
        st.write('')
        st.write('')

        # -------------------------------------------------------
        # Editar o valor total do projeto


        if opcao_editar_cron == "Valor total":

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


        # -------------------------------------------------------
        # Editar Parcelas







        if opcao_editar_cron == "Parcelas":

            st.markdown("#### Parcelas")

            # -----------------------------------
            # Valor total do projeto
            # -----------------------------------
            valor_total = valor_atual if valor_atual is not None else 0.0

            # -----------------------------------
            # Dados atuais (fonte da verdade)
            # -----------------------------------
            parcelas = financeiro.get("parcelas", [])

            if parcelas:
                df_parcelas = pd.DataFrame(parcelas)

                df_parcelas["data_prevista"] = pd.to_datetime(
                    df_parcelas["data_prevista"],
                    errors="coerce"
                )

                if "numero" not in df_parcelas.columns:
                    df_parcelas["numero"] = None

            else:
                df_parcelas = pd.DataFrame(
                    columns=[
                        "numero",
                        "data_prevista",
                        "percentual",
                    ]
                )

            # -----------------------------------
            # Ordenar por data prevista
            # -----------------------------------
            if not df_parcelas.empty:
                df_parcelas = df_parcelas.sort_values(
                    by="data_prevista",
                    ascending=True
                ).reset_index(drop=True)

            # -----------------------------------
            # Calcular valor (fonte da verdade)
            # -----------------------------------
            df_parcelas["valor"] = (
                df_parcelas["percentual"].fillna(0) / 100 * valor_total
            )

            # -----------------------------------
            # Coluna de exibição (UI)
            # -----------------------------------
            df_parcelas["valor_fmt"] = df_parcelas["valor"].apply(
                lambda x: f"R$ {x:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

            # -----------------------------------
            # Editor (UI)
            # -----------------------------------
            df_editado = st.data_editor(
                df_parcelas[
                    [
                        "numero",
                        "percentual",
                        "valor_fmt",
                        "data_prevista",
                    ]
                ],
                num_rows="dynamic",
                width=800,
                column_config={
                    "numero": st.column_config.NumberColumn(
                        "Número",
                        min_value=1,
                        step=1
                    ),
                    "percentual": st.column_config.NumberColumn(
                        "Percentual (%)",
                        min_value=0.0,
                        max_value=100.0,
                        step=1.0,
                        format="%.0f%%"
                    ),
                    "valor_fmt": st.column_config.TextColumn(
                        "Valor (auto)",
                        disabled=True
                    ),
                    "data_prevista": st.column_config.DateColumn(
                        "Data prevista",
                        format="DD/MM/YYYY"
                    ),
                },
                key="editor_parcelas",
            )

            st.write("")

            # -----------------------------------
            # Sincronizar SOMENTE campos editáveis
            # -----------------------------------
            df_parcelas.loc[df_editado.index, "numero"] = df_editado["numero"]
            df_parcelas.loc[df_editado.index, "percentual"] = df_editado["percentual"]
            df_parcelas.loc[df_editado.index, "data_prevista"] = df_editado["data_prevista"]

            # Recalcular valor após edição
            df_parcelas["valor"] = (
                df_parcelas["percentual"].fillna(0) / 100 * valor_total
            )

            # -----------------------------------
            # Total das porcentagens
            # -----------------------------------
            soma_porcentagens = df_parcelas["percentual"].dropna().sum()
            st.write(f"**Total: {int(soma_porcentagens)}%**")

            # -----------------------------------
            # Salvar
            # -----------------------------------
            if st.button("Salvar parcelas", icon=":material/save:"):

                df_salvar = df_parcelas.dropna(
                    subset=["percentual", "data_prevista"],
                    how="any"
                ).copy()

                if df_salvar["percentual"].sum() != 100:
                    st.error(
                        "A soma das porcentagens deve ser 100%. Os dados não foram salvos.",
                        icon=":material/error:"
                    )
                    st.stop()

                df_salvar = df_salvar.sort_values(
                    by="data_prevista",
                    ascending=True
                ).reset_index(drop=True)

                parcelas_salvar = []

                for _, row in df_salvar.iterrows():

                    parcelas_salvar.append(
                        {
                            "numero": int(row["numero"]) if not pd.isna(row["numero"]) else None,
                            "percentual": float(row["percentual"]),
                            "valor": float(row["valor"]),
                            "data_prevista": (
                                pd.to_datetime(row["data_prevista"]).date().isoformat()
                            ),
                        }
                    )

                col_projetos.update_one(
                    {"codigo": codigo_projeto_atual},
                    {
                        "$set": {
                            "financeiro.parcelas": parcelas_salvar
                        }
                    }
                )

                st.success("Parcelas salvas com sucesso!")
                time.sleep(3)
                st.rerun()



















        # if opcao_editar_cron == "Parcelas":

        #     st.markdown("#### Parcelas")

        #     # -----------------------------------
        #     # Valor total do projeto
        #     # -----------------------------------
        #     valor_total = valor_atual if valor_atual is not None else 0.0

        #     # -----------------------------------
        #     # Dados atuais
        #     # -----------------------------------
        #     parcelas = financeiro.get("parcelas", [])

        #     if parcelas:
        #         df_parcelas = pd.DataFrame(parcelas)

        #         df_parcelas["data_prevista"] = pd.to_datetime(
        #             df_parcelas["data_prevista"],
        #             errors="coerce"
        #         )

        #         if "data_realizada" in df_parcelas.columns:
        #             df_parcelas["data_realizada"] = pd.to_datetime(
        #                 df_parcelas["data_realizada"],
        #                 errors="coerce"
        #             )
        #         else:
        #             df_parcelas["data_realizada"] = None

        #         if "numero" not in df_parcelas.columns:
        #             df_parcelas["numero"] = None

        #     else:
        #         df_parcelas = pd.DataFrame(
        #             columns=[
        #                 "numero",
        #                 "data_prevista",
        #                 "data_realizada",
        #                 "percentual",
        #             ]
        #         )

        #     # -----------------------------------
        #     # Ordenar por data prevista
        #     # -----------------------------------
        #     if not df_parcelas.empty:
        #         df_parcelas = df_parcelas.sort_values(
        #             by="data_prevista",
        #             ascending=True
        #         ).reset_index(drop=True)

        #     # -----------------------------------
        #     # Calcular valor da parcela
        #     # -----------------------------------
        #     df_parcelas["valor"] = (
        #         df_parcelas["percentual"].fillna(0) / 100 * valor_total
        #     )

        #     df_parcelas["valor_fmt"] = df_parcelas["valor"].apply(
        #         lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        #     )


        #     # -----------------------------------
        #     # Coluna de exibição da data realizada
        #     # -----------------------------------
        #     df_parcelas["data_realizada_view"] = df_parcelas["data_realizada"].apply(
        #         lambda x: "-" if pd.isna(x) else x.strftime("%d/%m/%Y")
        #     )


        #     # -----------------------------------
        #     # Editor
        #     # -----------------------------------
        #     df_editado = st.data_editor(
        #         df_parcelas[
        #             ["numero", "percentual", "valor_fmt", "data_prevista", "data_realizada_view"]
        #         ],
        #         num_rows="dynamic",
        #         width=800,
        #         column_config={
        #             "numero": st.column_config.NumberColumn(
        #                 "Número",
        #                 min_value=1,
        #                 step=1
        #             ),
        #             "percentual": st.column_config.NumberColumn(
        #                 "Percentual",
        #                 min_value=0.0,
        #                 max_value=100.0,
        #                 step=1.0,
        #                 format="%.0f%%"
        #             ),
        #             "valor_fmt": st.column_config.TextColumn(
        #                 "Valor (auto)",
        #                 disabled=True
        #             ),
        #             "data_prevista": st.column_config.DateColumn(
        #                 "Data prevista",
        #                 format="DD/MM/YYYY"
        #             ),
        #             "data_realizada_view": st.column_config.TextColumn(
        #                 "Data realizada (auto)",
        #                 disabled=True
        #             ),
        #         },
        #         key="editor_parcelas",
        #     )

        #     st.write("")

        #     # -----------------------------------
        #     # Total das porcentagens
        #     # -----------------------------------
        #     soma_porcentagens = df_editado["percentual"].dropna().sum()
        #     st.write(f"**Total: {int(soma_porcentagens)}%**")

        #     # -----------------------------------
        #     # Salvar
        #     # -----------------------------------
        #     if st.button("Salvar parcelas", icon=":material/save:"):

        #         df_salvar = df_editado.dropna(
        #             subset=["percentual", "data_prevista"],
        #             how="any"
        #         ).copy()

        #         if df_salvar["percentual"].sum() != 100:
        #             st.error(
        #                 "A soma das porcentagens deve ser 100%. Os dados não foram salvos.",
        #                 icon=":material/error:"
        #             )
        #             st.stop()

        #         df_salvar = df_salvar.sort_values(
        #             by="data_prevista",
        #             ascending=True
        #         ).reset_index(drop=True)

        #         parcelas_salvar = []

        #         for _, row in df_salvar.iterrows():

        #             parcelas_salvar.append(
        #                 {
        #                     "numero": int(row["numero"]) if not pd.isna(row["numero"]) else None,
        #                     "percentual": float(row["percentual"]),
        #                     "valor": float(row["valor"]),
        #                     "data_prevista": (
        #                         pd.to_datetime(row["data_prevista"]).date().isoformat()
        #                     ),
        #                     "data_realizada": (
        #                         None
        #                         if pd.isna(row["data_realizada"])
        #                         else pd.to_datetime(row["data_realizada"]).date().isoformat()
        #                     ),
        #                 }
        #             )

        #         col_projetos.update_one(
        #             {"codigo": codigo_projeto_atual},
        #             {
        #                 "$set": {
        #                     "financeiro.parcelas": parcelas_salvar
        #                 }
        #             }
        #         )

        #         st.success("Parcelas salvas com sucesso!")
        #         time.sleep(3)
        #         st.rerun()






















        # if opcao_editar_cron == "Parcelas":

        #     st.markdown("#### Parcelas")

        #     # -----------------------------------
        #     # Valor total
        #     # -----------------------------------
        #     valor_total = valor_atual if valor_atual is not None else 0.0

        #     if valor_atual is None:
        #         st.warning("Defina o valor total do projeto para calcular os valores das parcelas.")

        #     # -----------------------------------
        #     # Dados atuais
        #     # -----------------------------------


        #     parcelas = financeiro.get("parcelas", [])

        #     if parcelas:
        #         df_parcelas = pd.DataFrame(parcelas)

        #         # Data prevista
        #         df_parcelas["data_prevista"] = pd.to_datetime(
        #             df_parcelas["data_prevista"]
        #         ).dt.date

        #         # Data realizada (opcional)
        #         if "data_realizada" in df_parcelas.columns:
        #             df_parcelas["data_realizada"] = pd.to_datetime(
        #                 df_parcelas["data_realizada"],
        #                 errors="coerce"
        #             ).dt.date
        #         else:
        #             df_parcelas["data_realizada"] = pd.NaT

        #         # Número
        #         if "numero" not in df_parcelas.columns:
        #             df_parcelas.insert(0, "numero", None)

        #     else:
        #         df_parcelas = pd.DataFrame(
        #             columns=[
        #                 "numero",
        #                 "data_prevista",
        #                 "data_realizada",
        #                 "percentual"
        #             ]
        #         )




        #     # -----------------------------------
        #     # Ordenar por data prevista
        #     # -----------------------------------
        #     if not df_parcelas.empty:
        #         df_parcelas = df_parcelas.sort_values(
        #             by="data_prevista",
        #             ascending=True
        #         ).reset_index(drop=True)

        #     # -----------------------------------
        #     # Calcular valor da parcela
        #     # -----------------------------------
        #     df_parcelas["valor"] = (
        #         df_parcelas["percentual"].fillna(0) / 100 * valor_total
        #     )

        #     df_parcelas["valor_fmt"] = df_parcelas["valor"].apply(
        #         lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        #     )

        #     # -----------------------------------
        #     # Editor
        #     # -----------------------------------
        #     df_editado = st.data_editor(
        #         df_parcelas[
        #             ["numero", "data_prevista", "data_realizada", "percentual", "valor_fmt"]
        #         ],
        #         num_rows="dynamic",
        #         width=700,
        #         column_config={
        #             "numero": st.column_config.NumberColumn(
        #                 "Número",
        #                 min_value=1,
        #                 step=1
        #             ),
        #             "data_prevista": st.column_config.DateColumn(
        #                 "Data prevista",
        #                 format="DD/MM/YYYY"
        #             ),
        #             "data_realizada": st.column_config.DateColumn(
        #                 "Data realizada",
        #                 format="DD/MM/YYYY"
        #             ),
        #             "percentual": st.column_config.NumberColumn(
        #                 "Percentual (%)",
        #                 min_value=0.0,
        #                 max_value=100.0,
        #                 step=1.0,
        #                 format="%.0f%%"
        #             ),
        #             "valor_fmt": st.column_config.TextColumn(
        #                 "Valor (R$)",
        #                 disabled=True
        #             ),
        #         },
        #         key="editor_parcelas",
        #     )

        #     st.write("")

        #     # -----------------------------------
        #     # Total das porcentagens
        #     # -----------------------------------
        #     soma_porcentagens = df_editado["percentual"].dropna().sum()
        #     st.write(f"**Total: {int(soma_porcentagens)}%**")

        #     # -----------------------------------
        #     # Salvar
        #     # -----------------------------------
        #     if st.button("Salvar parcelas", icon=":material/save:"):

        #         df_salvar = df_editado.dropna(
        #             subset=["percentual", "data_prevista"],
        #             how="any"
        #         ).copy()

        #         # Validação
        #         if df_salvar["percentual"].sum() != 100:
        #             st.error(
        #                 "A soma das porcentagens deve ser 100%. Os dados não foram salvos.",
        #                 icon=":material/error:"
        #             )
        #             st.stop()

        #         df_salvar = df_salvar.sort_values(
        #             by="data_prevista",
        #             ascending=True
        #         ).reset_index(drop=True)

        #         parcelas_salvar = []

        #         for _, row in df_salvar.iterrows():

        #             # Data prevista
        #             dp = row["data_prevista"]
        #             data_prevista_str = dp if isinstance(dp, str) else dp.isoformat()

        #             # Data realizada (opcional)
        #             dr = row["data_realizada"]
        #             if pd.isna(dr) or dr == "":
        #                 data_realizada_str = None
        #             else:
        #                 data_realizada_str = dr if isinstance(dr, str) else dr.isoformat()

        #             percentual = float(row["percentual"])
        #             valor_parcela = percentual / 100 * valor_total

        #             parcelas_salvar.append(
        #                 {
        #                     "numero": int(row["numero"]) if not pd.isna(row["numero"]) else None,
        #                     "percentual": percentual,
        #                     "valor": float(valor_parcela),
        #                     "data_prevista": data_prevista_str,
        #                     "data_realizada": data_realizada_str,
        #                 }
        #             )

        #         col_projetos.update_one(
        #             {"codigo": codigo_projeto_atual},
        #             {
        #                 "$set": {
        #                     "financeiro.parcelas": parcelas_salvar
        #                 }
        #             }
        #         )

        #         st.success("Parcelas salvas com sucesso!")
        #         time.sleep(3)
        #         st.rerun()


























        # if opcao_editar_cron == "Parcelas":

        #     st.markdown("#### Parcelas")

        #     # -----------------------------------
        #     # Valor total do projeto
        #     # -----------------------------------
        #     valor_total = valor_atual if valor_atual is not None else 0.0

        #     if valor_atual is None:
        #         st.info("Defina o valor total do projeto para calcular o valor das parcelas.")

        #     # -----------------------------------
        #     # Dados atuais
        #     # -----------------------------------
        #     parcelas = financeiro.get("parcelas", [])

        #     if parcelas:
        #         df_parcelas = pd.DataFrame(parcelas)
        #         df_parcelas["data_prevista"] = pd.to_datetime(
        #             df_parcelas["data_prevista"]
        #         ).dt.date

        #         if "numero" not in df_parcelas.columns:
        #             df_parcelas.insert(0, "numero", None)
        #     else:
        #         df_parcelas = pd.DataFrame(
        #             columns=["numero", "percentual", "data_prevista"]
        #         )

        #     # -----------------------------------
        #     # Ordenar por data prevista
        #     # -----------------------------------
        #     if not df_parcelas.empty:
        #         df_parcelas = df_parcelas.sort_values(
        #             by="data_prevista",
        #             ascending=True
        #         ).reset_index(drop=True)

        #     # -----------------------------------
        #     # Calcular valor da parcela
        #     # -----------------------------------
        #     df_parcelas["valor"] = (
        #         df_parcelas["percentual"].fillna(0) / 100 * valor_total
        #     )

        #     # Formatar valor para padrão brasileiro (apenas visual)
        #     df_parcelas["valor_fmt"] = df_parcelas["valor"].apply(
        #         lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        #     )

        #     # -----------------------------------
        #     # Editor
        #     # -----------------------------------
        #     df_editado = st.data_editor(
        #         df_parcelas[["numero", "data_prevista", "percentual", "valor_fmt"]],
        #         num_rows="dynamic",
        #         width=700,
        #         # use_container_width=True,
        #         column_config={
        #             "numero": st.column_config.NumberColumn(
        #                 "Número",
        #                 min_value=1,
        #                 step=1,
        #             ),
        #             "percentual": st.column_config.NumberColumn(
        #                 "Percentual (%)",
        #                 min_value=0.0,
        #                 max_value=100.0,
        #                 step=1.0,
        #                 format="%.0f%%"
        #             ),
        #             "valor_fmt": st.column_config.TextColumn(
        #                 "Valor (R$)",
        #                 disabled=True,
        #             ),
        #             "data_prevista": st.column_config.DateColumn(
        #                 "Data prevista",
        #                 format="DD/MM/YYYY"
        #             ),
        #         },
        #         key="editor_parcelas",
        #     )


        #     # -----------------------------------
        #     # Total das porcentagens (visual)
        #     # -----------------------------------
        #     soma_porcentagens = df_editado["percentual"].dropna().sum()
        #     st.write(f"**Total: {int(soma_porcentagens)}%**")

        #     st.write("")

        #     # -----------------------------------
        #     # Salvar
        #     # -----------------------------------
        #     if st.button("Salvar parcelas", icon=":material/save:"):

        #         # Remove linhas incompletas
        #         df_salvar = df_editado.dropna(
        #             subset=["percentual", "data_prevista"],
        #             how="any"
        #         ).copy()

        #         # -----------------------------
        #         # Validação da soma
        #         # -----------------------------
        #         soma_percentual = df_salvar["percentual"].sum()

        #         if soma_percentual != 100:
        #             st.error(
        #                 "A soma das porcentagens deve ser 100%. Os dados não foram salvos.",
        #                 icon=":material/error:"
        #             )
        #             st.stop()

        #         # -----------------------------
        #         # Ordenar por data novamente
        #         # -----------------------------
        #         df_salvar = df_salvar.sort_values(
        #             by="data_prevista",
        #             ascending=True
        #         ).reset_index(drop=True)

        #         # -----------------------------
        #         # Converter para MongoDB
        #         # -----------------------------
        #         parcelas_salvar = []

        #         for _, row in df_salvar.iterrows():

        #             data_prevista = row["data_prevista"]
        #             if isinstance(data_prevista, str):
        #                 data_prevista_str = data_prevista
        #             else:
        #                 data_prevista_str = data_prevista.isoformat()


        #             percentual = float(row["percentual"])
        #             valor_parcela = percentual / 100 * valor_total

        #             parcelas_salvar.append(
        #                 {
        #                     "numero": int(row["numero"]) if not pd.isna(row["numero"]) else None,
        #                     "percentual": percentual,
        #                     "valor": float(valor_parcela),
        #                     "data_prevista": data_prevista_str
        #                 }
        #             )



        #         col_projetos.update_one(
        #             {"codigo": codigo_projeto_atual},
        #             {
        #                 "$set": {
        #                     "financeiro.parcelas": parcelas_salvar
        #                 }
        #             }
        #         )

        #         st.success("Parcelas salvas com sucesso!")
        #         time.sleep(3)
        #         st.rerun()





















with orcamento:
    st.write('*Bloco do cronograma de parcelas, relatórios e status // Em construção*')