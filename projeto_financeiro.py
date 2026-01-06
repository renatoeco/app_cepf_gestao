import streamlit as st
import pandas as pd
import time
from datetime import timedelta

import streamlit_shadcn_ui as ui

from funcoes_auxiliares import conectar_mongo_cepf_gestao, ajustar_altura_data_editor, sidebar_projeto  # Função personalizada para conectar ao MongoDB


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


def atualizar_datas_relatorios(col_projetos, codigo_projeto):
    projeto = col_projetos.find_one({"codigo": codigo_projeto})

    parcelas = projeto.get("financeiro", {}).get("parcelas", [])
    relatorios = projeto.get("relatorios", [])

    if not parcelas or not relatorios:
        return

    # Mapear parcelas por número
    mapa_parcelas = {
        p["numero"]: p for p in parcelas if p.get("numero") is not None
    }

    novos_relatorios = []

    for r in relatorios:
        numero = r.get("numero")

        if numero in mapa_parcelas:
            data_parcela = pd.to_datetime(
                mapa_parcelas[numero]["data_prevista"]
            )
            data_relatorio = (data_parcela + timedelta(days=15)).date().isoformat()
        else:
            data_relatorio = None

        novos_relatorios.append(
            {
                "numero": numero,
                "entregas": r.get("entregas", []),
                "data_prevista": data_relatorio
            }
        )

    col_projetos.update_one(
        {"codigo": codigo_projeto},
        {"$set": {"relatorios": novos_relatorios}}
    )



# ==========================================================================================
# DIÁLOGO: VER RELATOS FINANCEIROS
# ==========================================================================================
@st.dialog("Lançamentos de despesa", width="large")
def dialog_relatos_fin():

    despesa = st.session_state.get("despesa_selecionada")

    # Se por algum motivo vier vazio/None
    if not isinstance(despesa, dict):
        st.warning("Nenhuma despesa selecionada. Feche o diálogo e selecione uma despesa na tabela.")
        return

    # Tenta pegar primeiro "despesa", depois "Despesa", depois usa texto padrão
    nome_despesa = (
        despesa.get("despesa")
        or despesa.get("Despesa")
        or "Despesa sem nome"
    )

    st.markdown(f"### {nome_despesa}")
    st.write("")



    # ==========================================================
    # Usamos fragment para evitar rerun completo
    # ==========================================================
    @st.fragment
    def corpo_dialogo_relatos_fin():
        st.write('corpo')
        

    # Renderiza o fragment do corpo
    corpo_dialogo_relatos_fin()








###########################################################################################################
# INTERFACE PRINCIPAL DA PÁGINA
###########################################################################################################



# Logo do sidebar
st.logo("images/cepf_logo.png", size='large')

# Título da página e identificação
col_titulo, col_identificacao = st.columns([3, 2])

with col_titulo:
    st.header("Financeiro")

with col_identificacao:
    st.markdown(
        f"<div style='text-align: right; margin-top: 30px;'>{df_projeto['codigo'].values[0]} - {df_projeto['sigla'].values[0]}</div>",
        unsafe_allow_html=True
    )







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
    # MODO VISUALIZAÇÃO CRONOGRAMA
    # --------------------------------------------------
    if not modo_edicao:

        st.markdown('#### Cronograma de Parcelas e Relatórios')

        st.write("")


        # OPÇÃO 1 DE LAYOUT DA TABELA


        st.write("")

        # -----------------------------
        # Construir cronograma
        # -----------------------------
        linhas_cronograma = []

        # ===== Parcelas =====
        parcelas = financeiro.get("parcelas", [])

        for p in parcelas:
            numero = p.get("numero")
            percentual = p.get("percentual")
            valor = p.get("valor")
            data_prevista = p.get("data_prevista")
            data_realizada = p.get("data_realizada")

            linhas_cronograma.append(
                {
                    "evento": f"Parcela {numero}",
                    "Entregas": "",
                    "Valor R$": (
                        f"{valor:,.2f}".replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                        if valor is not None else ""
                    ),
                    # "Percentual": (
                    #     f"{int(percentual)} %"
                    #     if percentual is not None else ""
                    # ),
                    "Data prevista": pd.to_datetime(
                        data_prevista, errors="coerce"
                    ),
                    "Data realizada": (
                        pd.to_datetime(data_realizada).strftime("%d/%m/%Y")
                        if data_realizada else ""
                    ),
                }
            )

        # ===== Relatórios =====
        relatorios = projeto.get("relatorios", [])

        for r in relatorios:
            numero = r.get("numero")
            entregas = r.get("entregas", [])
            data_prevista = r.get("data_prevista")
            data_realizada = r.get("data_realizada")

            linhas_cronograma.append(
                {
                    "evento": f"Relatório {numero}",
                    "Entregas": "\n".join(entregas) if entregas else "",
                    # "Entregas": "<br>".join(entregas) if entregas else "",
                    "Valor R$": "",
                    # "Percentual": "",
                    "Data prevista": pd.to_datetime(
                        data_prevista, errors="coerce"
                    ),
                    "Data realizada": (
                        pd.to_datetime(data_realizada).strftime("%d/%m/%Y")
                        if data_realizada else ""
                    ),
                }
            )

        # -----------------------------
        # DataFrame final
        # -----------------------------
        df_cronograma = pd.DataFrame(linhas_cronograma)


        if df_cronograma.empty:
            st.caption("Não há dados financeiros para exibição.")
        else:
            
            # Ordenar por data prevista
            df_cronograma = df_cronograma.sort_values(
                by="Data prevista",
                ascending=True
            )

            # Formatar data prevista para exibição
            df_cronograma["Data prevista"] = df_cronograma["Data prevista"].dt.strftime(
                "%d/%m/%Y"
            )

            # Renomear a coluna evento
            df_cronograma = df_cronograma.rename(
                columns={"evento": "Evento"}
            )


            # -----------------------------
            # Tabela
            # -----------------------------
            
            ui.table(df_cronograma)
        




            # st.write('')
            # st.write('')
            # st.write('')



            # st.markdown('#### OPÇÃO 2 de layout da tabela de cronograma')


            # # -----------------------------
            # # Construir cronograma
            # # -----------------------------
            # linhas_cronograma = []

            # # ===== Parcelas =====
            # parcelas = financeiro.get("parcelas", [])

            # for p in parcelas:
            #     linhas_cronograma.append(
            #         {
            #             "evento": f"Parcela {p.get('numero')}",
            #             "entregas": [],
            #             "valor": (
            #                 f"R$ {p['valor']:,.2f}".replace(",", "X")
            #                 .replace(".", ",")
            #                 .replace("X", ".")
            #                 if p.get("valor") is not None else ""
            #             ),
            #             "percentual": (
            #                 f"{int(p['percentual'])} %"
            #                 if p.get("percentual") is not None else ""
            #             ),
            #             "data_prevista": (
            #                 pd.to_datetime(p.get("data_prevista")).strftime("%d/%m/%Y")
            #                 if p.get("data_prevista") else ""
            #             ),
            #             "data_realizada": (
            #                 pd.to_datetime(p.get("data_realizada")).strftime("%d/%m/%Y")
            #                 if p.get("data_realizada") else ""
            #             ),
            #         }
            #     )

            # # ===== Relatórios =====
            # relatorios = projeto.get("relatorios", [])

            # for r in relatorios:
            #     linhas_cronograma.append(
            #         {
            #             "evento": f"Relatório {r.get('numero')}",
            #             "entregas": r.get("entregas", []),
            #             "valor": "",
            #             "percentual": "",
            #             "data_prevista": (
            #                 pd.to_datetime(r.get("data_prevista")).strftime("%d/%m/%Y")
            #                 if r.get("data_prevista") else ""
            #             ),
            #             "data_realizada": (
            #                 pd.to_datetime(r.get("data_realizada")).strftime("%d/%m/%Y")
            #                 if r.get("data_realizada") else ""
            #             ),
            #         }
            #     )

            # # Ordenar por data prevista
            # linhas_cronograma = sorted(
            #     linhas_cronograma,
            #     key=lambda x: pd.to_datetime(
            #         x["data_prevista"], dayfirst=True, errors="coerce"
            #     )
            # )

            # # -----------------------------
            # # Layout das colunas
            # # -----------------------------
            # layout_colunas = [2, 7, 2, 2, 2, 2]


            # # -----------------------------
            # # Cabeçalho
            # # -----------------------------
            # col_header = st.columns(layout_colunas)
            # col_header[0].write("**Evento**")
            # col_header[1].write("**Entregas**")
            # col_header[2].write("**Valor**")
            # col_header[3].write("**Percentual**")
            # col_header[4].write("**Data prevista**")
            # col_header[5].write("**Data realizada**")

            # st.divider()

            # # -----------------------------
            # # Linhas
            # # -----------------------------
            # for row in linhas_cronograma:

            #     cols = st.columns(layout_colunas)

            #     # Evento
            #     cols[0].write(row["evento"])

            #     # Entregas (multilinha real)
            #     if row["entregas"]:
            #         for entrega in row["entregas"]:
            #             cols[1].write(f"{entrega}")
            #     else:
            #         cols[1].write("")

            #     # Valor
            #     cols[2].write(row["valor"])

            #     # Percentual
            #     cols[3].write(row["percentual"])

            #     # Datas
            #     cols[4].write(row["data_prevista"])
            #     cols[5].write(row["data_realizada"])

            #     st.divider()




    # --------------------------------------------------
    # MODO EDIÇÃO CRONOGRAMA
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
            # Dados atuais
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
            # Calcular valor
            # -----------------------------------
            df_parcelas["valor"] = (
                df_parcelas["percentual"].fillna(0) / 100 * valor_total
            )

            # -----------------------------------
            # Coluna de exibição
            # -----------------------------------
            df_parcelas["valor_fmt"] = df_parcelas["valor"].apply(
                lambda x: f"R$ {x:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

            # -----------------------------------
            # Editor
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
                        step=1,
                        width=60
                    ),
                    "percentual": st.column_config.NumberColumn(
                        "Percentual (%)",
                        min_value=0.0,
                        max_value=100.0,
                        step=1.0,
                        format="%.0f%%",
                        width=100
                    ),
                    "valor_fmt": st.column_config.TextColumn(
                        "Valor (auto)",
                        disabled=True,
                        width=150
                    ),
                    "data_prevista": st.column_config.DateColumn(
                        "Data prevista",
                        format="DD/MM/YYYY",
                        width=150
                    ),
                },
                key="editor_parcelas",
            )

            st.write("")

            # -----------------------------------
            # Reconstruir df_parcelas a partir do editor
            # -----------------------------------
            df_parcelas = df_editado.copy()

            # Garantir tipos
            df_parcelas["numero"] = df_parcelas["numero"].astype("Int64")
            df_parcelas["percentual"] = df_parcelas["percentual"].astype(float)
            df_parcelas["data_prevista"] = pd.to_datetime(
                df_parcelas["data_prevista"], errors="coerce"
            )

            # Recalcular valor
            df_parcelas["valor"] = (
                df_parcelas["percentual"].fillna(0) / 100 * valor_total
            )





            # # -----------------------------------
            # # Sincronizar SOMENTE campos editáveis
            # # -----------------------------------
            # df_parcelas.loc[df_editado.index, "numero"] = df_editado["numero"]
            # df_parcelas.loc[df_editado.index, "percentual"] = df_editado["percentual"]
            # df_parcelas.loc[df_editado.index, "data_prevista"] = df_editado["data_prevista"]

            # # Recalcular valor após edição
            # df_parcelas["valor"] = (
            #     df_parcelas["percentual"].fillna(0) / 100 * valor_total
            # )

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

                # Atualizar as datas dos relatórios correspondentes na coleção de relatórios. Dataprevista do relatório = data_prevista da parcela + 15 dias
                atualizar_datas_relatorios(col_projetos, codigo_projeto_atual)


                st.success("Parcelas salvas com sucesso!")
                time.sleep(3)
                st.rerun()



        # -------------------------------------------------------
        # Editar Relatórios

        if opcao_editar_cron == "Relatórios":



            st.markdown("#### Relatórios")


            # --------------------------------------------------
            # Coletar TODAS as entregas do projeto
            # --------------------------------------------------

            entregas_projeto = []

            plano = projeto.get("plano_trabalho", {})
            for componente in plano.get("componentes", []):
                for entrega in componente.get("entregas", []):
                    if entrega.get("entrega"):
                        entregas_projeto.append(entrega["entrega"])

            entregas_projeto = sorted(set(entregas_projeto))

            # Agora sim, valida se está vazio
            if not entregas_projeto:
                st.warning(
                    "Nenhuma entrega cadastrada para este projeto. "
                    "Cadastre as entregas no Plano de Trabalho antes de continuar."
                )


            # --------------------------------------------------
            # Parcelas
            # --------------------------------------------------
            parcelas = financeiro.get("parcelas", [])

            # Ordenar parcelas por número
            parcelas = sorted(
                [p for p in parcelas if p.get("numero") is not None],
                key=lambda x: x["numero"]
            )

            # Se não houver parcelas suficientes, não há relatórios
            if len(parcelas) < 2:
                st.caption("É necessário ter ao menos duas parcelas para gerar relatórios.")
            else:


                # --------------------------------------------------
                # Montar DataFrame base dos relatórios
                # (parcelas - última)
                # --------------------------------------------------
                linhas_relatorios = []

                for parcela in parcelas[:-1]:  # ignora a última parcela
                    numero = parcela["numero"]
                    data_parcela = pd.to_datetime(parcela["data_prevista"], errors="coerce")

                    data_relatorio = (
                        data_parcela + timedelta(days=15)
                        if not pd.isna(data_parcela)
                        else pd.NaT
                    )

                    linhas_relatorios.append(
                        {
                            "numero": numero,
                            "data_prevista": data_relatorio,
                            "entregas": [],
                        }
                    )

                df_relatorios_base = pd.DataFrame(linhas_relatorios)

                # --------------------------------------------------
                # Mesclar com relatórios já existentes no banco
                # (preserva entregas já salvas)
                # --------------------------------------------------
                relatorios_existentes = projeto.get("relatorios", [])

                if relatorios_existentes:
                    df_existente = pd.DataFrame(relatorios_existentes)

                    for _, row in df_existente.iterrows():
                        numero = row.get("numero")

                        if numero in df_relatorios_base["numero"].values:
                            idx = df_relatorios_base.index[
                                df_relatorios_base["numero"] == numero
                            ][0]

                            df_relatorios_base.at[idx, "entregas"] = row.get("entregas", [])


                # Garantir que entregas seja sempre lista
                df_relatorios_base["entregas"] = df_relatorios_base["entregas"].apply(
                    lambda x: x if isinstance(x, list) else []
                )

                # --------------------------------------------------
                # Editor (linhas fixas)
                # --------------------------------------------------
                df_editado = st.data_editor(
                    df_relatorios_base[["numero", "entregas", "data_prevista"]],
                    num_rows="fixed",
                    column_config={
                        "numero": st.column_config.NumberColumn(
                            "Número (auto)",
                            disabled=True,
                            width=5
                        ),
                        "entregas": st.column_config.MultiselectColumn(
                            "Entregas",
                            options=[""] + entregas_projeto,
                            help="Selecione as entregas relacionadas a este relatório",
                            width=800
                        ),
                        "data_prevista": st.column_config.DateColumn(
                            "Data prevista (auto)",
                            format="DD/MM/YYYY",
                            disabled=True,
                            width=20
                        ),
                    },
                    key="editor_relatorios",
                    hide_index=True
                )

                st.write("")

                # --------------------------------------------------
                # Salvar
                # --------------------------------------------------
                if st.button("Salvar relatórios", icon=":material/save:"):

                    relatorios_salvar = []

                    for _, row in df_editado.iterrows():

                        entregas = [e for e in row["entregas"] if e]

                        relatorios_salvar.append(
                            {
                                "numero": int(row["numero"]),
                                "entregas": entregas,
                                "data_prevista": (
                                    None
                                    if pd.isna(row["data_prevista"])
                                    else row["data_prevista"].date().isoformat()
                                ),
                            }
                        )

                    col_projetos.update_one(
                        {"codigo": codigo_projeto_atual},
                        {
                            "$set": {
                                "relatorios": relatorios_salvar
                            }
                        }
                    )

                    st.success("Relatórios salvos com sucesso!")
                    time.sleep(3)
                    st.rerun()






# --------------------------------------------------
# ABA ORÇAMENTO
# --------------------------------------------------


with orcamento:


    # ==================================================
    # PERMISSÃO E MODO DE EDIÇÃO
    # ==================================================
    usuario_interno = st.session_state.tipo_usuario in ["admin", "equipe"]

    with st.container(horizontal=True, horizontal_alignment="right"):
        if usuario_interno:
            modo_edicao = st.toggle("Modo de edição", key="editar_orcamento")
        else:
            modo_edicao = False



    st.markdown("#### Orçamento")
    st.write("")


    # ==================================================
    # NOTIFICAÇÕES PARA USUÁRIO INTERNO
    # ==================================================

    # ==================================================
    # Notificação de total do orçamento diferente do valor total do projeto
    # ==================================================

    if usuario_interno:

        valor_total_projeto = financeiro.get("valor_total")
        orcamento_salvo = financeiro.get("orcamento", [])

        if valor_total_projeto and orcamento_salvo:

            soma_orcamento = sum(
                item.get("valor_total", 0)
                for item in orcamento_salvo
                if item.get("valor_total") is not None
            )

            if round(soma_orcamento, 2) != round(valor_total_projeto, 2):

                soma_fmt = (
                    f"R\\$ {soma_orcamento:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )

                total_fmt = (
                    f"R\\$ {valor_total_projeto:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )


                st.warning(
                    f"O total do orçamento ({soma_fmt}) é diferente do valor total do projeto ({total_fmt}).",
                    icon=":material/warning:"
                )





    # ==================================================
    # MODO VISUALIZAÇÃO — ORÇAMENTO AGRUPADO POR CATEGORIA
    # ==================================================
    if not modo_edicao:

        # -----------------------------
        # Métrica do valor total
        # -----------------------------
        valor_total = financeiro.get("valor_total")

        if valor_total is not None:
            st.metric(
                label="Valor total do projeto",
                value=(
                    f"R$ {valor_total:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )
            )
        else:
            st.caption("Valor total do projeto ainda não cadastrado.")

        st.write("")

        # --------------------------------------------------
        # ESTADOS DO DIÁLOGO (inicialização segura)
        # --------------------------------------------------
        if "despesa_selecionada" not in st.session_state:
            st.session_state["despesa_selecionada"] = None

        if "despesa_selecionada_tabela_key" not in st.session_state:
            st.session_state["despesa_selecionada_tabela_key"] = None

        if "abrir_dialogo_despesa" not in st.session_state:
            st.session_state["abrir_dialogo_despesa"] = False

        # --------------------------------------------------
        # Dados do orçamento
        # --------------------------------------------------
        orcamento = financeiro.get("orcamento", [])

        if not orcamento:
            st.caption("Nenhuma despesa cadastrada no orçamento.")
            st.stop()

        df_orcamento = pd.DataFrame(orcamento)

        # Garantir colunas
        for col in [
            "categoria",
            "nome_despesa",
            "descricao_despesa",
            "unidade",
            "quantidade",
            "valor_unitario",
            "valor_total",
        ]:
            if col not in df_orcamento.columns:
                df_orcamento[col] = None

        # -----------------------------------
        # Formatação para exibição
        # -----------------------------------
        df_orcamento["Valor unitário"] = df_orcamento["valor_unitario"].apply(
            lambda x: (
                f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                if x not in [None, ""]
                else ""
            )
        )

        df_orcamento["Valor total"] = df_orcamento["valor_total"].apply(
            lambda x: (
                f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                if x not in [None, ""]
                else ""
            )
        )

        # --------------------------------------------------
        # Agrupar por categoria
        # --------------------------------------------------
        categorias = (
            df_orcamento["categoria"]
            .dropna()
            .unique()
            .tolist()
        )

        # --------------------------------------------------
        # CALLBACK PARA ABERTURA DO DIÁLOGO DE RELATOS
        # --------------------------------------------------
        def criar_callback_selecao_orcamento(dataframe_orc, chave_tabela):

            def handle_selecao():

                estado_tabela = st.session_state.get(chave_tabela, {})
                selecao = estado_tabela.get("selection", {})
                linhas = selecao.get("rows", [])

                if not linhas:
                    return

                idx = linhas[0]
                linha = dataframe_orc.iloc[idx]

                despesa_escolhida = {
                    "categoria": linha.get("categoria", ""),
                    "nome_despesa": linha.get("nome_despesa", ""),
                    "descricao_despesa": linha.get("descricao_despesa", ""),
                    "unidade": linha.get("unidade", ""),
                    "quantidade": linha.get("quantidade", 0),
                    "valor_unitario": linha.get("valor_unitario", 0),
                    "valor_total": linha.get("valor_total", 0),
                    "indice": idx,
                }

                # Compatibilidade com o diálogo
                despesa_escolhida["despesa"] = despesa_escolhida["nome_despesa"]
                despesa_escolhida["Despesa"] = despesa_escolhida["nome_despesa"]

                st.session_state["despesa_selecionada"] = despesa_escolhida
                st.session_state["despesa_selecionada_tabela_key"] = chave_tabela
                st.session_state["abrir_dialogo_despesa"] = True

            return handle_selecao

        # --------------------------------------------------
        # RENDERIZAÇÃO POR CATEGORIA
        # --------------------------------------------------
        for categoria in categorias:

            st.write("")
            st.write(f"**{categoria}**")
            # st.divider()

            df_cat = df_orcamento[df_orcamento["categoria"] == categoria].copy()

            df_vis = df_cat.rename(columns={
                "nome_despesa": "Despesa",
                "descricao_despesa": "Descrição",
                "unidade": "Unidade",
                "quantidade": "Quantidade",
            })

            colunas_vis = [
                "Despesa",
                "Descrição",
                "Unidade",
                "Quantidade",
                "Valor unitário",
                "Valor total",
            ]

            key_df = f"df_vis_orcamento_{categoria}"

            callback_selecao = criar_callback_selecao_orcamento(
                df_cat,
                key_df
            )

            st.dataframe(
                df_vis[colunas_vis],
                hide_index=True,
                selection_mode="single-row",
                key=key_df,
                on_select=callback_selecao,
                column_config={
                    "Despesa": st.column_config.TextColumn(width=220),
                    "Descrição": st.column_config.TextColumn(width=420),
                    "Unidade": st.column_config.TextColumn(width=120),
                    "Quantidade": st.column_config.NumberColumn(width=80),
                    "Valor unitário": st.column_config.TextColumn(width=120),
                    "Valor total": st.column_config.TextColumn(width=120),
                }
            )

        # --------------------------------------------------
        # ABRIR DIÁLOGO
        # --------------------------------------------------
        if st.session_state.get("abrir_dialogo_despesa"):
            dialog_relatos_fin()
            st.session_state["abrir_dialogo_despesa"] = False










    # ==================================================
    # MODO EDIÇÃO — CRUD DO ORÇAMENTO
    # ==================================================
    if modo_edicao:

        # -----------------------------------
        # Buscar categorias de despesa
        # -----------------------------------
        col_categorias_despesa = db["categorias_despesa"]

        categorias = list(
            col_categorias_despesa
            .find({}, {"categoria": 1})
            .sort("categoria", 1)
        )

        opcoes_categorias = [c["categoria"] for c in categorias]

        if not opcoes_categorias:
            st.warning(
                "Não há categorias de despesa cadastradas. "
                "Cadastre primeiro nas configurações auxiliares."
            )
            st.stop()

        # -----------------------------------
        # Dados atuais do orçamento
        # -----------------------------------
        orcamento_atual = financeiro.get("orcamento", [])

        if orcamento_atual:
            df_orcamento = pd.DataFrame(orcamento_atual)
        else:
            df_orcamento = pd.DataFrame(
                columns=[
                    "categoria",
                    "nome_despesa",
                    "descricao_despesa",
                    "unidade",
                    "quantidade",
                    "valor_unitario",
                ]
            )

        # Garantir colunas
        for col in [
            "categoria",
            "nome_despesa",
            "descricao_despesa",
            "unidade",
            "quantidade",
            "valor_unitario",
        ]:
            if col not in df_orcamento.columns:
                df_orcamento[col] = None

        # -----------------------------------
        # Calcular valores
        # -----------------------------------
        df_orcamento["quantidade"] = df_orcamento["quantidade"].fillna(0)
        df_orcamento["valor_unitario"] = df_orcamento["valor_unitario"].fillna(0)

        df_orcamento["valor_total"] = (
            df_orcamento["quantidade"] * df_orcamento["valor_unitario"]
        )

        # -----------------------------------
        # Formatação para exibição
        # -----------------------------------
        def format_brl(valor):
            return (
                f"R$ {valor:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            ) if valor else ""

        df_orcamento["valor_unitario_fmt"] = df_orcamento["valor_unitario"].apply(format_brl)
        df_orcamento["valor_total_fmt"] = df_orcamento["valor_total"].apply(format_brl)

        # -----------------------------------
        # Editor
        # -----------------------------------
        




        altura_editor = ajustar_altura_data_editor(
            df_orcamento,
            linhas_adicionais=1
        )

        df_editado = st.data_editor(
            df_orcamento[
                [
                    "categoria",
                    "nome_despesa",
                    "descricao_despesa",
                    "unidade",
                    "quantidade",
                    "valor_unitario_fmt",
                    "valor_total_fmt",
                ]
            ],
            num_rows="dynamic",
            height=altura_editor,
            column_config={
                "categoria": st.column_config.SelectboxColumn(
                    "Categoria de despesa",
                    options=opcoes_categorias,
                    required=True
                ),
                "nome_despesa": st.column_config.TextColumn(
                    "Despesa",
                    required=True
                ),
                "descricao_despesa": st.column_config.TextColumn(
                    "Descrição"
                ),
                "unidade": st.column_config.TextColumn(
                    "Unidade"
                ),
                "quantidade": st.column_config.NumberColumn(
                    "Quantidade",
                    min_value=0,
                    step=1
                ),
                "valor_unitario_fmt": st.column_config.TextColumn(
                    "Valor unitário (R$)"
                ),
                "valor_total_fmt": st.column_config.TextColumn(
                    "Valor total (auto)",
                    disabled=True
                ),
            },
            key="editor_orcamento",
        )



        st.write("")

        # -----------------------------------
        # Salvar
        # -----------------------------------
        if st.button("Salvar orçamento", icon=":material/save:"):

            df_salvar = df_editado.dropna(
                subset=["categoria", "nome_despesa"],
                how="any"
            ).copy()

            # Converter string → float
            def parse_brl(valor):
                if not valor:
                    return 0.0
                return float(
                    valor.replace("R$", "")
                    .replace(".", "")
                    .replace(",", ".")
                    .strip()
                )

            df_salvar["quantidade"] = df_salvar["quantidade"].fillna(0)
            df_salvar["valor_unitario"] = df_salvar["valor_unitario_fmt"].apply(parse_brl)
            df_salvar["valor_total"] = (
                df_salvar["quantidade"] * df_salvar["valor_unitario"]
            )

            orcamento_salvar = []

            for _, row in df_salvar.iterrows():
                orcamento_salvar.append(
                    {
                        "categoria": row["categoria"],
                        "nome_despesa": row["nome_despesa"],
                        "descricao_despesa": row.get("descricao_despesa"),
                        "unidade": row.get("unidade"),
                        "quantidade": float(row["quantidade"]),
                        "valor_unitario": float(row["valor_unitario"]),
                        "valor_total": float(row["valor_total"]),
                    }
                )

            col_projetos.update_one(
                {"codigo": codigo_projeto_atual},
                {
                    "$set": {
                        "financeiro.orcamento": orcamento_salvar
                    }
                }
            )

            st.success("Orçamento salvo com sucesso!")
            time.sleep(3)
            st.rerun()





# ###################################################################################################
# SIDEBAR DA PÁGINA DO PROJETO
# ###################################################################################################

sidebar_projeto()